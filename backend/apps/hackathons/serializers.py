from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.identity.serializers import ProfileSerializer

from .models import (
    Hackathon,
    HackathonGalleryImage,
    HackathonRegistration,
    HackathonSubmission,
    HackathonWinner,
)

User = get_user_model()


class OrganizerSummarySerializer(serializers.Serializer):
    id = serializers.UUIDField()
    email = serializers.EmailField()


class HackathonSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Hackathon
        fields = ["id", "title", "slug", "starts_at", "ends_at", "status"]


class HackathonListSerializer(serializers.ModelSerializer):
    organizer = OrganizerSummarySerializer(read_only=True)
    phase = serializers.CharField(read_only=True)

    class Meta:
        model = Hackathon
        fields = [
            "id",
            "title",
            "slug",
            "summary",
            "cover_image",
            "host_type",
            "partner_name",
            "prize_summary",
            "organizer",
            "registration_deadline",
            "submission_deadline",
            "starts_at",
            "ends_at",
            "capacity",
            "status",
            "phase",
        ]


class ParticipantSummarySerializer(serializers.Serializer):
    id = serializers.UUIDField()
    email = serializers.EmailField()
    profile = ProfileSerializer(read_only=True)


class HackathonSubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = HackathonSubmission
        fields = ["id", "title", "summary", "repo_url", "demo_url", "submitted_at"]
        read_only_fields = ["id", "submitted_at"]


class HackathonWinnerSerializer(serializers.ModelSerializer):
    submission = HackathonSubmissionSerializer(read_only=True)
    participant = serializers.SerializerMethodField()

    class Meta:
        model = HackathonWinner
        fields = ["id", "placement", "prize_description", "submission", "participant", "announced_at"]

    @extend_schema_field(ParticipantSummarySerializer)
    def get_participant(self, winner):
        return ParticipantSummarySerializer(winner.submission.registration.participant).data


class HackathonGalleryImageSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(required=False, allow_null=True)
    video_url = serializers.URLField(required=False, allow_blank=True, max_length=500)

    class Meta:
        model = HackathonGalleryImage
        fields = ["id", "image", "video_url", "caption", "sort_order"]

    def validate(self, attrs):
        # Mirrors HackathonGalleryImage.clean() — enforced here too since
        # partial (PATCH-style) updates and this endpoint's create path
        # don't otherwise call full_clean().
        has_image = bool(attrs.get("image")) if "image" in attrs else bool(self.instance and self.instance.image)
        has_video = bool(attrs.get("video_url")) if "video_url" in attrs else bool(self.instance and self.instance.video_url)
        if has_image == has_video:
            raise serializers.ValidationError("Provide exactly one of image or video_url, not both.")
        return attrs


class HackathonDetailSerializer(serializers.ModelSerializer):
    organizer = OrganizerSummarySerializer(read_only=True)
    phase = serializers.CharField(read_only=True)
    is_registration_open = serializers.BooleanField(read_only=True)
    registered_count = serializers.IntegerField(read_only=True)
    winners = serializers.SerializerMethodField()
    gallery_images = HackathonGalleryImageSerializer(many=True, read_only=True)

    class Meta:
        model = Hackathon
        fields = [
            "id",
            "title",
            "slug",
            "summary",
            "description",
            "cover_image",
            "host_type",
            "partner_name",
            "partner_url",
            "requirements",
            "prize_summary",
            "organizer",
            "registration_opens_at",
            "registration_deadline",
            "submission_deadline",
            "starts_at",
            "ends_at",
            "capacity",
            "registered_count",
            "status",
            "phase",
            "is_registration_open",
            "published_at",
            "winners",
            "gallery_images",
            "created_at",
            "updated_at",
        ]

    @extend_schema_field(HackathonWinnerSerializer(many=True))
    def get_winners(self, hackathon):
        return HackathonWinnerSerializer(
            hackathon.winners.select_related(
                "submission__registration__participant__profile"
            ),
            many=True,
        ).data


class HackathonWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hackathon
        fields = [
            "id",
            "title",
            "slug",
            "status",
            "summary",
            "description",
            "cover_image",
            "host_type",
            "partner_name",
            "partner_url",
            "requirements",
            "prize_summary",
            "registration_opens_at",
            "registration_deadline",
            "submission_deadline",
            "starts_at",
            "ends_at",
            "capacity",
        ]
        read_only_fields = ["id", "slug", "status"]

    def validate(self, attrs):
        def get(field):
            return attrs.get(field, getattr(self.instance, field, None))

        host_type = get("host_type")
        if host_type == Hackathon.HOST_PARTNER and not get("partner_name"):
            raise serializers.ValidationError(
                {"partner_name": "Required when host_type is 'partner'."}
            )

        opens_at = get("registration_opens_at")
        reg_deadline = get("registration_deadline")
        submission_deadline = get("submission_deadline")
        starts_at = get("starts_at")
        ends_at = get("ends_at")

        if opens_at and reg_deadline and opens_at > reg_deadline:
            raise serializers.ValidationError(
                {"registration_opens_at": "Must be before registration_deadline."}
            )
        if reg_deadline and submission_deadline and reg_deadline > submission_deadline:
            raise serializers.ValidationError(
                {"registration_deadline": "Must be at or before submission_deadline."}
            )
        if submission_deadline and ends_at and submission_deadline > ends_at:
            raise serializers.ValidationError(
                {"submission_deadline": "Must be at or before ends_at."}
            )
        if starts_at and ends_at and starts_at > ends_at:
            raise serializers.ValidationError({"starts_at": "Must be before ends_at."})
        return attrs


class HackathonRegistrationSerializer(serializers.ModelSerializer):
    hackathon = HackathonSummarySerializer(read_only=True)
    submission = HackathonSubmissionSerializer(read_only=True)

    class Meta:
        model = HackathonRegistration
        fields = [
            "id",
            "hackathon",
            "team_name",
            "motivation",
            "status",
            "registered_at",
            "submission",
        ]


class RegistrationCreateSerializer(serializers.Serializer):
    team_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    motivation = serializers.CharField(required=False, allow_blank=True)


class OrganizerRegistrationSerializer(serializers.ModelSerializer):
    participant = ParticipantSummarySerializer(read_only=True)
    submission = HackathonSubmissionSerializer(read_only=True)

    class Meta:
        model = HackathonRegistration
        fields = [
            "id",
            "participant",
            "team_name",
            "motivation",
            "status",
            "registered_at",
            "submission",
        ]


class WinnerCreateSerializer(serializers.Serializer):
    registration_id = serializers.UUIDField()
    placement = serializers.IntegerField(min_value=1)
    prize_description = serializers.CharField(max_length=300, required=False, allow_blank=True)
