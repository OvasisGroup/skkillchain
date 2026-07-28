from datetime import timedelta

from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import generics, permissions, status
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.audit.services import record_event
from apps.catalog.models import Course
from apps.learning.models import Enrollment
from shared.crypto import decrypt, encrypt

from . import oauth_state
from .conferencing.base import ConferencingProviderError
from .conferencing.registry import get_provider
from .models import ConferencingAccount, LiveSession, LiveSessionRegistration
from .serializers import (
    ConferencingAccountSerializer,
    ConnectResponseSerializer,
    JoinResponseSerializer,
    LiveSessionCreateSerializer,
    LiveSessionSerializer,
    LiveSessionUpdateSerializer,
    RecordingSerializer,
    RegistrationSerializer,
)


def _owned_course_or_403(course_id, user):
    course = get_object_or_404(Course, pk=course_id)
    if course.owner_id != user.id:
        raise PermissionDenied("You do not own this course.")
    return course


def _hosted_session_or_403(live_session_id, user):
    live_session = get_object_or_404(LiveSession, pk=live_session_id)
    if live_session.host_id != user.id:
        raise PermissionDenied("You do not host this session.")
    return live_session


# ---------- Conferencing account connect/callback/list/revoke ----------


@extend_schema(tags=["Instructor"], request=None, responses={200: ConnectResponseSerializer})
class ConferencingAccountConnectView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, provider):
        provider_adapter = get_provider(provider)
        if provider_adapter is None:
            raise NotFound(f"Unknown conferencing provider '{provider}'")

        state = oauth_state.issue_state(request.user.id, provider)
        return Response({"authorization_url": provider_adapter.authorization_url(state)})


@extend_schema(tags=["Instructor"], request=None, responses={302: None})
class ConferencingAccountCallbackView(APIView):
    """
    Hit by the *browser*, redirected here by the provider after consent —
    not called by our own API client. Completes the token exchange, then
    redirects again to the frontend rather than returning JSON, since
    there's no XHR caller waiting on this response.
    """

    permission_classes = [permissions.AllowAny]

    def get(self, request, provider):
        from django.conf import settings

        code = request.query_params.get("code")
        state = request.query_params.get("state")
        state_data = oauth_state.resolve_state(state) if state else None

        if not code or state_data is None or state_data.get("provider") != provider:
            return HttpResponseRedirect(
                f"{settings.PUBLIC_APP_URL}/instructor/conferencing-accounts?error=invalid_state"
            )

        provider_adapter = get_provider(provider)
        if provider_adapter is None:
            return HttpResponseRedirect(
                f"{settings.PUBLIC_APP_URL}/instructor/conferencing-accounts?error=unknown_provider"
            )

        try:
            tokens = provider_adapter.exchange_code_for_tokens(code)
        except ConferencingProviderError:
            return HttpResponseRedirect(
                f"{settings.PUBLIC_APP_URL}/instructor/conferencing-accounts?error=token_exchange_failed"
            )

        from django.contrib.auth import get_user_model

        user = get_object_or_404(get_user_model(), pk=state_data["user_id"])

        # Replace any existing active connection for this provider — the
        # unique constraint only covers *active* (non-revoked) rows, so
        # revoke the old one first rather than fighting the constraint.
        ConferencingAccount.objects.filter(
            user=user, provider=provider, revoked_at__isnull=True
        ).update(revoked_at=timezone.now())

        account = ConferencingAccount.objects.create(
            user=user,
            provider=provider,
            access_token_encrypted=encrypt(tokens.access_token),
            refresh_token_encrypted=encrypt(tokens.refresh_token) if tokens.refresh_token else "",
            token_expires_at=timezone.now() + timedelta(seconds=tokens.expires_in),
        )
        record_event(
            actor=user,
            action="conferencing_account.connect",
            entity_type="ConferencingAccount",
            entity_id=account.id,
            request=request,
            payload={"provider": provider},
        )
        return HttpResponseRedirect(
            f"{settings.PUBLIC_APP_URL}/instructor/conferencing-accounts?connected={provider}"
        )


@extend_schema(tags=["Instructor"])
class ConferencingAccountListView(generics.ListAPIView):
    serializer_class = ConferencingAccountSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        return ConferencingAccount.objects.filter(user=self.request.user, revoked_at__isnull=True)


@extend_schema(tags=["Instructor"], responses={204: None})
class ConferencingAccountRevokeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, account_id):
        account = get_object_or_404(ConferencingAccount, pk=account_id, user=request.user)
        account.revoked_at = timezone.now()
        account.save(update_fields=["revoked_at"])
        record_event(
            actor=request.user,
            action="conferencing_account.revoke",
            entity_type="ConferencingAccount",
            entity_id=account.id,
            request=request,
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


# ---------- Live session scheduling (instructor) ----------


@extend_schema(
    tags=["Instructor"], request=LiveSessionCreateSerializer, responses={201: LiveSessionSerializer}
)
class LiveSessionScheduleView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, course_id):
        course = _owned_course_or_403(course_id, request.user)

        serializer = LiveSessionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        account = get_object_or_404(
            ConferencingAccount,
            pk=data["conferencing_account_id"],
            user=request.user,
            revoked_at__isnull=True,
        )
        if account.provider != data["provider"]:
            raise ValidationError("provider must match the connected conferencing account.")

        provider_adapter = get_provider(account.provider)
        access_token = decrypt(account.access_token_encrypted)
        try:
            meeting = provider_adapter.create_meeting(
                access_token,
                title=data["title"],
                description=data.get("description", ""),
                start_at=data["scheduled_start_at"],
                end_at=data["scheduled_end_at"],
            )
        except ConferencingProviderError as exc:
            raise ValidationError(f"Could not create the meeting: {exc}") from exc

        live_session = LiveSession.objects.create(
            course=course,
            host=request.user,
            conferencing_account=account,
            provider=account.provider,
            title=data["title"],
            description=data.get("description", ""),
            scheduled_start_at=data["scheduled_start_at"],
            scheduled_end_at=data["scheduled_end_at"],
            timezone=data.get("timezone", "UTC"),
            capacity=data.get("capacity"),
            is_recorded=data.get("is_recorded", True),
            external_meeting_id=meeting.external_meeting_id,
            join_url=meeting.join_url,
            host_join_url=meeting.host_join_url,
        )
        record_event(
            actor=request.user,
            action="live_session.schedule",
            entity_type="LiveSession",
            entity_id=live_session.id,
            request=request,
        )
        return Response(LiveSessionSerializer(live_session).data, status=status.HTTP_201_CREATED)


@extend_schema(
    tags=["Instructor"], request=LiveSessionUpdateSerializer, responses={200: LiveSessionSerializer}
)
class LiveSessionUpdateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, id):
        live_session = _hosted_session_or_403(id, request.user)
        if live_session.status != LiveSession.STATUS_SCHEDULED:
            raise ValidationError(f"Cannot reschedule a session that is '{live_session.status}'.")

        serializer = LiveSessionUpdateSerializer(live_session, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        record_event(
            actor=request.user,
            action="live_session.update",
            entity_type="LiveSession",
            entity_id=live_session.id,
            request=request,
        )
        return Response(LiveSessionSerializer(live_session).data)


@extend_schema(tags=["Instructor"], request=None, responses={200: LiveSessionSerializer})
class LiveSessionCancelView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, id):
        live_session = _hosted_session_or_403(id, request.user)
        if live_session.status == LiveSession.STATUS_CANCELED:
            raise ValidationError("Already canceled.")

        try:
            provider_adapter = get_provider(live_session.provider)
            access_token = decrypt(live_session.conferencing_account.access_token_encrypted)
            provider_adapter.cancel_meeting(access_token, live_session.external_meeting_id)
        except ConferencingProviderError as exc:
            # Best-effort: still cancel locally so students stop seeing it
            # as active, but keep this failure traceable rather than
            # silently swallowed.
            record_event(
                actor=request.user,
                action="live_session.provider_cancel_failed",
                entity_type="LiveSession",
                entity_id=live_session.id,
                request=request,
                payload={"error": str(exc)},
            )

        live_session.status = LiveSession.STATUS_CANCELED
        live_session.save(update_fields=["status"])
        record_event(
            actor=request.user,
            action="live_session.cancel",
            entity_type="LiveSession",
            entity_id=live_session.id,
            request=request,
        )
        return Response(LiveSessionSerializer(live_session).data)


@extend_schema(tags=["Instructor"])
class LiveSessionRegistrationsView(generics.ListAPIView):
    serializer_class = RegistrationSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        live_session = _hosted_session_or_403(self.kwargs["id"], self.request.user)
        return live_session.registrations.select_related("student")


# ---------- Live session discovery, registration, join (student) ----------


@extend_schema(tags=["Student"])
class CourseLiveSessionsView(generics.ListAPIView):
    serializer_class = LiveSessionSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None

    def get_queryset(self):
        return LiveSession.objects.filter(course_id=self.kwargs["course_id"]).exclude(
            status=LiveSession.STATUS_CANCELED
        )


@extend_schema(tags=["Student"])
class MyLiveSessionsView(generics.ListAPIView):
    serializer_class = LiveSessionSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        return LiveSession.objects.filter(
            registrations__student=self.request.user,
            registrations__status__in=[
                LiveSessionRegistration.STATUS_REGISTERED,
                LiveSessionRegistration.STATUS_ATTENDED,
            ],
        ).distinct()


@extend_schema(tags=["Student"], request=None, responses={201: None, 200: None})
class LiveSessionRegisterView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, id):
        live_session = get_object_or_404(LiveSession, pk=id)
        if live_session.status == LiveSession.STATUS_CANCELED:
            raise ValidationError("This session was canceled.")
        if (
            live_session.course_id
            and not Enrollment.objects.filter(
                student=request.user, course_id=live_session.course_id
            ).exists()
        ):
            raise PermissionDenied("You must be enrolled in this course to register.")

        if live_session.capacity is not None:
            current = live_session.registrations.filter(
                status__in=[
                    LiveSessionRegistration.STATUS_REGISTERED,
                    LiveSessionRegistration.STATUS_ATTENDED,
                ]
            ).count()
            if current >= live_session.capacity:
                raise ValidationError("This session is at capacity.")

        registration, created = LiveSessionRegistration.objects.get_or_create(
            live_session=live_session, student=request.user
        )
        if not created and registration.status == LiveSessionRegistration.STATUS_CANCELED:
            registration.status = LiveSessionRegistration.STATUS_REGISTERED
            registration.save(update_fields=["status"])
        if created:
            record_event(
                actor=request.user,
                action="live_session.register",
                entity_type="LiveSession",
                entity_id=live_session.id,
                request=request,
            )
        return Response(status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

    def delete(self, request, id):
        registration = LiveSessionRegistration.objects.filter(
            live_session_id=id, student=request.user
        ).first()
        if registration is None:
            raise NotFound("Not registered for this session.")
        registration.status = LiveSessionRegistration.STATUS_CANCELED
        registration.save(update_fields=["status"])
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(tags=["Student"], responses={200: JoinResponseSerializer})
class LiveSessionJoinView(APIView):
    """
    The security-critical endpoint of this milestone: a join URL is never
    handed out to anyone who isn't registered, or outside the join window
    — enforced here, server-side, not left to the client to hide a button.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, id):
        live_session = get_object_or_404(LiveSession, pk=id)
        registration = (
            LiveSessionRegistration.objects.filter(live_session=live_session, student=request.user)
            .exclude(status=LiveSessionRegistration.STATUS_CANCELED)
            .first()
        )
        if registration is None:
            raise PermissionDenied("You are not registered for this session.")

        now = timezone.now()
        window_opens_at = live_session.scheduled_start_at - timedelta(
            minutes=LiveSession.JOIN_WINDOW_MINUTES_BEFORE_START
        )
        if now < window_opens_at:
            raise PermissionDenied(
                f"Too early — the join link opens {LiveSession.JOIN_WINDOW_MINUTES_BEFORE_START} "
                "minutes before the session starts."
            )
        if now > live_session.scheduled_end_at:
            raise PermissionDenied("This session has ended.")
        if live_session.status == LiveSession.STATUS_CANCELED:
            raise PermissionDenied("This session was canceled.")

        if registration.joined_at is None:
            registration.joined_at = now
            registration.status = LiveSessionRegistration.STATUS_ATTENDED
            registration.save(update_fields=["joined_at", "status"])
            record_event(
                actor=request.user,
                action="live_session.join",
                entity_type="LiveSession",
                entity_id=live_session.id,
                request=request,
            )

        return Response({"join_url": live_session.join_url})


@extend_schema(tags=["Student"], responses={200: RecordingSerializer})
class LiveSessionRecordingView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, id):
        live_session = get_object_or_404(LiveSession, pk=id)
        is_host = live_session.host_id == request.user.id
        is_registered = LiveSessionRegistration.objects.filter(
            live_session=live_session, student=request.user
        ).exists()
        if not (is_host or is_registered):
            raise PermissionDenied("Not your session.")

        recording = getattr(live_session, "recording", None)
        if recording is None or not recording.playback_url:
            raise NotFound("Recording not yet available.")
        return Response(RecordingSerializer(recording).data)
