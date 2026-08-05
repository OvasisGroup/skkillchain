from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import OpenApiExample, OpenApiParameter, extend_schema
from rest_framework import generics, permissions, status
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.audit.services import record_event
from apps.authorization.permissions import HasPermission
from shared.api.pagination import (
    EndsAtDescCursorPagination,
    RegisteredAtCursorPagination,
    StartsAtCursorPagination,
)

from .models import Hackathon, HackathonRegistration, HackathonSubmission, HackathonWinner
from .serializers import (
    HackathonDetailSerializer,
    HackathonListSerializer,
    HackathonRegistrationSerializer,
    HackathonSubmissionSerializer,
    HackathonWinnerSerializer,
    HackathonWriteSerializer,
    OrganizerRegistrationSerializer,
    RegistrationCreateSerializer,
    WinnerCreateSerializer,
)

_REGISTERED_STATUS = HackathonRegistration.STATUS_REGISTERED

_WITH_REGISTERED_COUNT = Count(
    "registrations", filter=Q(registrations__status=_REGISTERED_STATUS)
)


def _owned_hackathon_or_403(hackathon_id, user):
    hackathon = get_object_or_404(Hackathon, pk=hackathon_id)
    if hackathon.organizer_id != user.id:
        raise PermissionDenied("You do not organize this hackathon.")
    return hackathon


_HACKATHON_EXAMPLE = {
    "id": "1c2d3e4f-5a6b-7c8d-9e0f-1a2b3c4d5e6f",
    "title": "SkillChain Global AI Hackathon",
    "slug": "skillchain-global-ai-hackathon",
    "summary": "Build an AI-powered learning tool in 48 hours.",
    "cover_image": None,
    "host_type": "partner",
    "partner_name": "Acme Labs",
    "prize_summary": "$10,000 in prizes",
    "organizer": {"id": "b6a5b6c0-9b1e-4c9a-9b7a-1f2e3d4c5b6a", "email": "team@skillchain.example"},
    "registration_deadline": "2026-03-01T00:00:00Z",
    "submission_deadline": "2026-03-14T23:59:00Z",
    "starts_at": "2026-03-08T00:00:00Z",
    "ends_at": "2026-03-15T00:00:00Z",
    "capacity": 500,
    "status": "published",
    "phase": "upcoming",
}


# ---------- Public / student browsing ----------


@extend_schema(
    tags=["Hackathons"],
    parameters=[
        OpenApiParameter(
            "scope",
            str,
            description="active (default) | upcoming | completed | all — filters by the "
            "hackathon's derived phase.",
        ),
        OpenApiParameter("host_type", str, description="Filter by internal/partner."),
    ],
    description="Lists published hackathons, defaulting to the ones currently running "
    "('active'). Canceled hackathons are excluded unless scope=all.",
    examples=[OpenApiExample("Hackathon", value=_HACKATHON_EXAMPLE, response_only=True)],
)
class HackathonListView(generics.ListAPIView):
    serializer_class = HackathonListSerializer
    permission_classes = [permissions.AllowAny]

    @property
    def pagination_class(self):
        scope = self.request.query_params.get("scope", "active")
        return EndsAtDescCursorPagination if scope == "completed" else StartsAtCursorPagination

    def get_queryset(self):
        now = timezone.now()
        scope = self.request.query_params.get("scope", "active")
        qs = Hackathon.objects.filter(status=Hackathon.STATUS_PUBLISHED).select_related("organizer")

        if scope == "upcoming":
            qs = qs.filter(starts_at__gt=now)
        elif scope == "active":
            qs = qs.filter(starts_at__lte=now, ends_at__gte=now)
        elif scope == "completed":
            qs = qs.filter(ends_at__lt=now)
        elif scope != "all":
            raise ValidationError("scope must be one of: active, upcoming, completed, all.")

        if host_type := self.request.query_params.get("host_type"):
            qs = qs.filter(host_type=host_type)

        return qs


@extend_schema(
    tags=["Hackathons"],
    responses={200: HackathonDetailSerializer},
    description="Gets a published (or canceled) hackathon's full detail, including its "
    "winners. The organizer can also see their own draft hackathon through this same "
    "endpoint; anyone else gets a 404, identical to a nonexistent hackathon.",
    examples=[
        OpenApiExample(
            "Hackathon detail",
            value={
                **_HACKATHON_EXAMPLE,
                "description": "48 hours to build something that helps people learn faster.",
                "partner_url": "https://acmelabs.example.com",
                "requirements": "Teams of up to 4. Original work only. Must submit a public repo.",
                "registration_opens_at": "2026-02-01T00:00:00Z",
                "registered_count": 128,
                "is_registration_open": True,
                "published_at": "2026-02-01T00:00:00Z",
                "winners": [],
                "created_at": "2026-01-20T00:00:00Z",
                "updated_at": "2026-01-20T00:00:00Z",
            },
            response_only=True,
        )
    ],
)
class HackathonDetailView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, id):
        hackathon = get_object_or_404(
            Hackathon.objects.select_related("organizer").annotate(
                registered_count=_WITH_REGISTERED_COUNT
            ),
            pk=id,
        )
        is_owner = request.user.is_authenticated and hackathon.organizer_id == request.user.id
        if hackathon.status == Hackathon.STATUS_DRAFT and not is_owner:
            raise NotFound("No hackathon found matching the query.")
        return Response(HackathonDetailSerializer(hackathon).data)


class HackathonRegisterView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        tags=["Hackathons"],
        request=RegistrationCreateSerializer,
        responses={201: None, 200: None},
        description="Registers the current user for a hackathon. Returns 200 (not 201) if "
        "already registered. Fails with 400 if registration is closed or the hackathon is at "
        "capacity.",
        examples=[
            OpenApiExample(
                "Register",
                value={"team_name": "Byte Me", "motivation": "We want to prototype an AI tutor."},
                request_only=True,
            )
        ],
    )
    def post(self, request, id):
        hackathon = get_object_or_404(Hackathon, pk=id)
        if not hackathon.is_registration_open:
            raise ValidationError("Registration is not open for this hackathon.")

        existing = HackathonRegistration.objects.filter(
            hackathon=hackathon, participant=request.user
        ).first()
        if existing and existing.status == HackathonRegistration.STATUS_REGISTERED:
            return Response(status=status.HTTP_200_OK)

        if hackathon.capacity is not None:
            current = hackathon.registrations.filter(status=_REGISTERED_STATUS).count()
            if current >= hackathon.capacity:
                raise ValidationError("This hackathon is at capacity.")

        serializer = RegistrationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if existing:
            existing.status = HackathonRegistration.STATUS_REGISTERED
            existing.team_name = serializer.validated_data.get("team_name", existing.team_name)
            existing.motivation = serializer.validated_data.get("motivation", existing.motivation)
            existing.save(update_fields=["status", "team_name", "motivation"])
        else:
            HackathonRegistration.objects.create(
                hackathon=hackathon, participant=request.user, **serializer.validated_data
            )

        record_event(
            actor=request.user,
            action="hackathon.register",
            entity_type="Hackathon",
            entity_id=hackathon.id,
            request=request,
        )
        return Response(status=status.HTTP_201_CREATED)

    @extend_schema(
        tags=["Hackathons"],
        responses={204: None},
        description="Withdraws the current user's registration from a hackathon.",
    )
    def delete(self, request, id):
        registration = HackathonRegistration.objects.filter(
            hackathon_id=id, participant=request.user
        ).exclude(status=HackathonRegistration.STATUS_WITHDRAWN).first()
        if registration is None:
            raise NotFound("Not registered for this hackathon.")
        registration.status = HackathonRegistration.STATUS_WITHDRAWN
        registration.save(update_fields=["status"])
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(
    tags=["Hackathons"],
    request=HackathonSubmissionSerializer,
    responses={200: HackathonSubmissionSerializer, 201: HackathonSubmissionSerializer},
    description="Creates or replaces the current user's project submission for a hackathon "
    "they're registered for. Fails with 400 after the submission deadline has passed.",
    examples=[
        OpenApiExample(
            "Submit",
            value={
                "title": "AI Study Buddy",
                "summary": "A chatbot that quizzes you on your own course notes.",
                "repo_url": "https://github.com/example/ai-study-buddy",
                "demo_url": "https://ai-study-buddy.example.com",
            },
            request_only=True,
        )
    ],
)
class HackathonSubmissionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, id):
        hackathon = get_object_or_404(Hackathon, pk=id)
        registration = HackathonRegistration.objects.filter(
            hackathon=hackathon, participant=request.user, status=_REGISTERED_STATUS
        ).first()
        if registration is None:
            raise PermissionDenied("You must be registered for this hackathon to submit.")
        if timezone.now() > hackathon.submission_deadline:
            raise ValidationError("The submission deadline has passed.")

        submission = getattr(registration, "submission", None)
        serializer = HackathonSubmissionSerializer(
            instance=submission, data=request.data, partial=submission is not None
        )
        serializer.is_valid(raise_exception=True)
        created = submission is None
        submission = serializer.save(registration=registration)

        record_event(
            actor=request.user,
            action="hackathon.submit" if created else "hackathon.resubmit",
            entity_type="Hackathon",
            entity_id=hackathon.id,
            request=request,
        )
        return Response(
            HackathonSubmissionSerializer(submission).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


@extend_schema(
    tags=["Hackathons"],
    description="Lists the current user's own hackathon registrations, most recent first.",
    examples=[
        OpenApiExample(
            "Registration",
            value={
                "id": "d4e5f6a7-...",
                "hackathon": {**{k: _HACKATHON_EXAMPLE[k] for k in ("id", "title", "slug", "starts_at", "ends_at", "status")}},
                "team_name": "Byte Me",
                "motivation": "We want to prototype an AI tutor.",
                "status": "registered",
                "registered_at": "2026-02-05T10:00:00Z",
                "submission": None,
            },
            response_only=True,
        )
    ],
)
class MyHackathonRegistrationsView(generics.ListAPIView):
    serializer_class = HackathonRegistrationSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = RegisteredAtCursorPagination

    def get_queryset(self):
        return (
            HackathonRegistration.objects.filter(participant=self.request.user)
            .select_related("hackathon", "submission")
        )


# ---------- Organizer: create, manage, and post hackathons ----------


@extend_schema(
    tags=["HackathonOrganizer"],
    description="Lists hackathons the current user organizes, most recently created first.",
)
class OrganizerHackathonListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Hackathon.objects.filter(organizer=self.request.user)

    def get_serializer_class(self):
        return HackathonListSerializer if self.request.method == "GET" else HackathonWriteSerializer

    @extend_schema(
        tags=["HackathonOrganizer"],
        request=HackathonWriteSerializer,
        responses={201: HackathonWriteSerializer},
        description="Creates a new hackathon, either hosted internally or in partnership with "
        "another organization (host_type='partner', with partner_name required). Starts as a "
        "draft — call the publish endpoint to make it visible to students.",
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

    def perform_create(self, serializer):
        hackathon = serializer.save(organizer=self.request.user)
        record_event(
            actor=self.request.user,
            action="hackathon.create",
            entity_type="Hackathon",
            entity_id=hackathon.id,
            request=self.request,
        )


@extend_schema(
    tags=["HackathonOrganizer"],
    description="Gets or updates a hackathon the current user organizes.",
)
class OrganizerHackathonDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = HackathonWriteSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return _owned_hackathon_or_403(self.kwargs["id"], self.request.user)


@extend_schema(
    tags=["HackathonOrganizer"],
    request=None,
    responses={200: HackathonListSerializer},
    description="Publishes a draft hackathon, making it visible to students.",
)
class HackathonPublishView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, id):
        hackathon = _owned_hackathon_or_403(id, request.user)
        try:
            hackathon.publish()
        except Exception as exc:
            raise ValidationError(str(exc)) from exc
        record_event(
            actor=request.user,
            action="hackathon.publish",
            entity_type="Hackathon",
            entity_id=hackathon.id,
            request=request,
        )
        return Response(HackathonListSerializer(hackathon).data)


@extend_schema(
    tags=["HackathonOrganizer"],
    request=None,
    responses={200: HackathonListSerializer},
    description="Cancels a hackathon the current user organizes.",
)
class HackathonCancelView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, id):
        hackathon = _owned_hackathon_or_403(id, request.user)
        try:
            hackathon.cancel()
        except Exception as exc:
            raise ValidationError(str(exc)) from exc
        record_event(
            actor=request.user,
            action="hackathon.cancel",
            entity_type="Hackathon",
            entity_id=hackathon.id,
            request=request,
        )
        return Response(HackathonListSerializer(hackathon).data)


@extend_schema(
    tags=["HackathonOrganizer"],
    description="Lists everyone registered for a hackathon the current user organizes, "
    "including their submission if they have one — the organizer's roster view.",
)
class OrganizerHackathonRegistrationsView(generics.ListAPIView):
    serializer_class = OrganizerRegistrationSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = RegisteredAtCursorPagination

    def get_queryset(self):
        hackathon = _owned_hackathon_or_403(self.kwargs["id"], self.request.user)
        return hackathon.registrations.select_related(
            "participant", "participant__profile", "submission"
        )


@extend_schema(
    tags=["HackathonOrganizer"],
    request=WinnerCreateSerializer,
    responses={201: HackathonWinnerSerializer},
    description="Declares a winner for a hackathon the current user organizes: a placement "
    "(1st, 2nd, ...) tied to one registration's submission. The registration must have "
    "submitted a project.",
    examples=[
        OpenApiExample(
            "Declare winner",
            value={
                "registration_id": "d4e5f6a7-...",
                "placement": 1,
                "prize_description": "$5,000 grand prize",
            },
            request_only=True,
        )
    ],
)
class HackathonWinnerCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, id):
        hackathon = _owned_hackathon_or_403(id, request.user)
        serializer = WinnerCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        registration = get_object_or_404(
            HackathonRegistration, pk=data["registration_id"], hackathon=hackathon
        )
        submission = getattr(registration, "submission", None)
        if submission is None:
            raise ValidationError("This registration has no submission to award.")

        if HackathonWinner.objects.filter(hackathon=hackathon, placement=data["placement"]).exists():
            raise ValidationError(f"Placement {data['placement']} is already taken.")
        if HackathonWinner.objects.filter(hackathon=hackathon, submission=submission).exists():
            raise ValidationError("This submission has already been declared a winner.")

        winner = HackathonWinner.objects.create(
            hackathon=hackathon,
            submission=submission,
            placement=data["placement"],
            prize_description=data.get("prize_description", ""),
        )
        record_event(
            actor=request.user,
            action="hackathon.winner_declare",
            entity_type="Hackathon",
            entity_id=hackathon.id,
            request=request,
            payload={"placement": winner.placement, "submission_id": str(submission.id)},
        )
        return Response(HackathonWinnerSerializer(winner).data, status=status.HTTP_201_CREATED)


# ---------- Moderation override ----------


@extend_schema(
    tags=["Admin"],
    request=None,
    responses={200: HackathonListSerializer},
    description="Force-cancels any hackathon — for platform moderation, not the organizer's "
    "own controls (see the Hackathon Organizer cancel endpoint for that).",
)
class HackathonAdminCancelView(APIView):
    permission_classes = [HasPermission]
    required_permission = "hackathons.manage"

    def post(self, request, id):
        hackathon = get_object_or_404(Hackathon, pk=id)
        try:
            hackathon.cancel()
        except Exception as exc:
            raise ValidationError(str(exc)) from exc
        record_event(
            actor=request.user,
            action="hackathon.admin_cancel",
            entity_type="Hackathon",
            entity_id=hackathon.id,
            request=request,
        )
        return Response(HackathonListSerializer(hackathon).data)
