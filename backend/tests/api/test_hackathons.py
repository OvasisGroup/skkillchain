import base64
from datetime import timedelta

import pytest
from django.utils import timezone

from apps.hackathons.models import Hackathon, HackathonRegistration, HackathonSubmission

# Smallest possible valid PNG (1x1 transparent pixel) — real image bytes are
# required since ImageField validation actually decodes the file via Pillow.
_ONE_PIXEL_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
)

pytestmark = pytest.mark.django_db

NOW = timezone.now()


@pytest.fixture
def organizer(django_user_model):
    return django_user_model.objects.create_user(email="organizer@example.com", password="x")


@pytest.fixture
def student(django_user_model):
    return django_user_model.objects.create_user(email="student@example.com", password="x")


def _hackathon(organizer_user, *, status=Hackathon.STATUS_DRAFT, **kwargs):
    defaults = {
        "title": "Test Hackathon",
        "registration_deadline": NOW + timedelta(days=5),
        "submission_deadline": NOW + timedelta(days=10),
        "starts_at": NOW + timedelta(days=6),
        "ends_at": NOW + timedelta(days=10),
    }
    defaults.update(kwargs)
    hackathon = Hackathon.objects.create(organizer=organizer_user, **defaults)
    hackathon.status = status
    if status == Hackathon.STATUS_PUBLISHED:
        hackathon.published_at = timezone.now()
    hackathon.save(update_fields=["status", "published_at"])
    return hackathon


def _registration(hackathon, participant_user, **kwargs):
    return HackathonRegistration.objects.create(
        hackathon=hackathon, participant=participant_user, **kwargs
    )


class TestHackathonListView:
    def test_lists_only_published(self, api_client, organizer):
        _hackathon(
            organizer,
            status=Hackathon.STATUS_PUBLISHED,
            title="Live",
            starts_at=NOW + timedelta(days=1),
            ends_at=NOW + timedelta(days=2),
        )
        _hackathon(organizer, title="Still a Draft")

        response = api_client.get("/api/v1/hackathons/?scope=all")

        titles = [item["title"] for item in response.data["results"]]
        assert titles == ["Live"]

    def test_default_scope_is_active(self, api_client, organizer):
        active = _hackathon(
            organizer,
            status=Hackathon.STATUS_PUBLISHED,
            title="Active Now",
            starts_at=NOW - timedelta(hours=1),
            ends_at=NOW + timedelta(hours=1),
        )
        _hackathon(
            organizer,
            status=Hackathon.STATUS_PUBLISHED,
            title="Not Started Yet",
            starts_at=NOW + timedelta(days=1),
            ends_at=NOW + timedelta(days=2),
        )

        response = api_client.get("/api/v1/hackathons/")

        titles = [item["title"] for item in response.data["results"]]
        assert titles == [active.title]

    def test_scope_upcoming(self, api_client, organizer):
        _hackathon(
            organizer,
            status=Hackathon.STATUS_PUBLISHED,
            title="Active Now",
            starts_at=NOW - timedelta(hours=1),
            ends_at=NOW + timedelta(hours=1),
        )
        upcoming = _hackathon(
            organizer,
            status=Hackathon.STATUS_PUBLISHED,
            title="Later",
            starts_at=NOW + timedelta(days=1),
            ends_at=NOW + timedelta(days=2),
        )

        response = api_client.get("/api/v1/hackathons/?scope=upcoming")

        titles = [item["title"] for item in response.data["results"]]
        assert titles == [upcoming.title]

    def test_scope_completed(self, api_client, organizer):
        completed = _hackathon(
            organizer,
            status=Hackathon.STATUS_PUBLISHED,
            title="Done",
            starts_at=NOW - timedelta(days=5),
            ends_at=NOW - timedelta(days=1),
        )
        _hackathon(
            organizer,
            status=Hackathon.STATUS_PUBLISHED,
            title="Active Now",
            starts_at=NOW - timedelta(hours=1),
            ends_at=NOW + timedelta(hours=1),
        )

        response = api_client.get("/api/v1/hackathons/?scope=completed")

        titles = [item["title"] for item in response.data["results"]]
        assert titles == [completed.title]

    def test_invalid_scope_rejected(self, api_client):
        response = api_client.get("/api/v1/hackathons/?scope=bogus")

        assert response.status_code == 400

    def test_filters_by_host_type(self, api_client, organizer):
        _hackathon(
            organizer,
            status=Hackathon.STATUS_PUBLISHED,
            title="Internal",
            host_type=Hackathon.HOST_INTERNAL,
            starts_at=NOW - timedelta(hours=1),
            ends_at=NOW + timedelta(hours=1),
        )
        _hackathon(
            organizer,
            status=Hackathon.STATUS_PUBLISHED,
            title="Partnered",
            host_type=Hackathon.HOST_PARTNER,
            partner_name="Acme",
            starts_at=NOW - timedelta(hours=1),
            ends_at=NOW + timedelta(hours=1),
        )

        response = api_client.get("/api/v1/hackathons/?scope=active&host_type=partner")

        titles = [item["title"] for item in response.data["results"]]
        assert titles == ["Partnered"]


class TestHackathonDetailView:
    def test_draft_hidden_from_public(self, api_client, organizer):
        hackathon = _hackathon(organizer)

        response = api_client.get(f"/api/v1/hackathons/{hackathon.id}/")

        assert response.status_code == 404

    def test_draft_visible_to_organizer(self, api_client, organizer):
        hackathon = _hackathon(organizer)
        api_client.force_authenticate(user=organizer)

        response = api_client.get(f"/api/v1/hackathons/{hackathon.id}/")

        assert response.status_code == 200

    def test_draft_hidden_from_other_authenticated_user(self, api_client, organizer, student):
        hackathon = _hackathon(organizer)
        api_client.force_authenticate(user=student)

        response = api_client.get(f"/api/v1/hackathons/{hackathon.id}/")

        assert response.status_code == 404

    def test_published_includes_registered_count_and_winners(self, api_client, organizer, student):
        hackathon = _hackathon(organizer, status=Hackathon.STATUS_PUBLISHED)
        _registration(hackathon, student)

        response = api_client.get(f"/api/v1/hackathons/{hackathon.id}/")

        assert response.status_code == 200
        assert response.data["registered_count"] == 1
        assert response.data["winners"] == []


class TestHackathonRegisterView:
    def test_requires_authentication(self, api_client, organizer):
        hackathon = _hackathon(organizer, status=Hackathon.STATUS_PUBLISHED)

        response = api_client.post(f"/api/v1/hackathons/{hackathon.id}/register/")

        assert response.status_code == 401

    def test_register_creates_registration(self, api_client, organizer, student):
        hackathon = _hackathon(organizer, status=Hackathon.STATUS_PUBLISHED)
        api_client.force_authenticate(user=student)

        response = api_client.post(
            f"/api/v1/hackathons/{hackathon.id}/register/",
            {"team_name": "Byte Me"},
            format="json",
        )

        assert response.status_code == 201
        registration = HackathonRegistration.objects.get(hackathon=hackathon, participant=student)
        assert registration.team_name == "Byte Me"
        assert registration.status == HackathonRegistration.STATUS_REGISTERED

    def test_reregister_is_idempotent(self, api_client, organizer, student):
        hackathon = _hackathon(organizer, status=Hackathon.STATUS_PUBLISHED)
        _registration(hackathon, student)
        api_client.force_authenticate(user=student)

        response = api_client.post(
            f"/api/v1/hackathons/{hackathon.id}/register/", {}, format="json"
        )

        assert response.status_code == 200
        assert HackathonRegistration.objects.filter(hackathon=hackathon).count() == 1

    def test_registration_closed_after_deadline(self, api_client, organizer, student):
        hackathon = _hackathon(
            organizer,
            status=Hackathon.STATUS_PUBLISHED,
            registration_deadline=NOW - timedelta(days=1),
            starts_at=NOW + timedelta(hours=1),
            submission_deadline=NOW + timedelta(days=1),
            ends_at=NOW + timedelta(days=1),
        )
        api_client.force_authenticate(user=student)

        response = api_client.post(
            f"/api/v1/hackathons/{hackathon.id}/register/", {}, format="json"
        )

        assert response.status_code == 400

    def test_registration_blocked_when_at_capacity(
        self, api_client, organizer, student, django_user_model
    ):
        hackathon = _hackathon(organizer, status=Hackathon.STATUS_PUBLISHED, capacity=1)
        _registration(hackathon, student)
        other = django_user_model.objects.create_user(email="other@example.com", password="x")
        api_client.force_authenticate(user=other)

        response = api_client.post(
            f"/api/v1/hackathons/{hackathon.id}/register/", {}, format="json"
        )

        assert response.status_code == 400

    def test_withdraw(self, api_client, organizer, student):
        hackathon = _hackathon(organizer, status=Hackathon.STATUS_PUBLISHED)
        registration = _registration(hackathon, student)
        api_client.force_authenticate(user=student)

        response = api_client.delete(f"/api/v1/hackathons/{hackathon.id}/register/")

        assert response.status_code == 204
        registration.refresh_from_db()
        assert registration.status == HackathonRegistration.STATUS_WITHDRAWN

    def test_withdraw_without_registration_404s(self, api_client, organizer, student):
        hackathon = _hackathon(organizer, status=Hackathon.STATUS_PUBLISHED)
        api_client.force_authenticate(user=student)

        response = api_client.delete(f"/api/v1/hackathons/{hackathon.id}/register/")

        assert response.status_code == 404


class TestHackathonSubmissionView:
    def test_requires_registration(self, api_client, organizer, student):
        hackathon = _hackathon(organizer, status=Hackathon.STATUS_PUBLISHED)
        api_client.force_authenticate(user=student)

        response = api_client.post(
            f"/api/v1/hackathons/{hackathon.id}/submission/", {"title": "Nope"}, format="json"
        )

        assert response.status_code == 403

    def test_creates_submission_for_registered_student(self, api_client, organizer, student):
        hackathon = _hackathon(organizer, status=Hackathon.STATUS_PUBLISHED)
        _registration(hackathon, student)
        api_client.force_authenticate(user=student)

        response = api_client.post(
            f"/api/v1/hackathons/{hackathon.id}/submission/",
            {"title": "AI Study Buddy", "repo_url": "https://github.com/example/repo"},
            format="json",
        )

        assert response.status_code == 201
        assert HackathonSubmission.objects.filter(
            registration__hackathon=hackathon, registration__participant=student
        ).exists()

    def test_resubmission_updates_in_place(self, api_client, organizer, student):
        hackathon = _hackathon(organizer, status=Hackathon.STATUS_PUBLISHED)
        registration = _registration(hackathon, student)
        HackathonSubmission.objects.create(registration=registration, title="First draft")
        api_client.force_authenticate(user=student)

        response = api_client.post(
            f"/api/v1/hackathons/{hackathon.id}/submission/",
            {"title": "Final version"},
            format="json",
        )

        assert response.status_code == 200
        assert HackathonSubmission.objects.filter(registration=registration).count() == 1
        assert HackathonSubmission.objects.get(registration=registration).title == "Final version"

    def test_blocked_after_submission_deadline(self, api_client, organizer, student):
        hackathon = _hackathon(
            organizer,
            status=Hackathon.STATUS_PUBLISHED,
            submission_deadline=NOW - timedelta(hours=1),
            starts_at=NOW - timedelta(days=1),
            ends_at=NOW + timedelta(days=1),
        )
        _registration(hackathon, student)
        api_client.force_authenticate(user=student)

        response = api_client.post(
            f"/api/v1/hackathons/{hackathon.id}/submission/", {"title": "Too late"}, format="json"
        )

        assert response.status_code == 400


class TestMyHackathonRegistrationsView:
    def test_requires_authentication(self, api_client):
        response = api_client.get("/api/v1/students/me/hackathons/")

        assert response.status_code == 401

    def test_lists_only_own_registrations(self, api_client, organizer, student, django_user_model):
        hackathon = _hackathon(organizer, status=Hackathon.STATUS_PUBLISHED)
        _registration(hackathon, student)
        other = django_user_model.objects.create_user(email="other@example.com", password="x")
        _registration(hackathon, other)
        api_client.force_authenticate(user=student)

        response = api_client.get("/api/v1/students/me/hackathons/")

        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["hackathon"]["id"] == str(hackathon.id)


class TestOrganizerHackathonListCreateView:
    def test_requires_authentication(self, api_client):
        response = api_client.get("/api/v1/organizer/hackathons/")

        assert response.status_code == 401

    def test_lists_only_own_hackathons(self, api_client, organizer, student):
        _hackathon(organizer, title="Mine")
        _hackathon(student, title="Not mine")
        api_client.force_authenticate(user=organizer)

        response = api_client.get("/api/v1/organizer/hackathons/")

        titles = [item["title"] for item in response.data["results"]]
        assert titles == ["Mine"]

    def test_create_starts_as_draft(self, api_client, organizer):
        api_client.force_authenticate(user=organizer)

        response = api_client.post(
            "/api/v1/organizer/hackathons/",
            {
                "title": "New Hackathon",
                "registration_deadline": (NOW + timedelta(days=5)).isoformat(),
                "submission_deadline": (NOW + timedelta(days=10)).isoformat(),
                "starts_at": (NOW + timedelta(days=6)).isoformat(),
                "ends_at": (NOW + timedelta(days=10)).isoformat(),
            },
            format="json",
        )

        assert response.status_code == 201
        assert response.data["status"] == "draft"

    def test_partner_host_requires_partner_name(self, api_client, organizer):
        api_client.force_authenticate(user=organizer)

        response = api_client.post(
            "/api/v1/organizer/hackathons/",
            {
                "title": "New Hackathon",
                "host_type": "partner",
                "registration_deadline": (NOW + timedelta(days=5)).isoformat(),
                "submission_deadline": (NOW + timedelta(days=10)).isoformat(),
                "starts_at": (NOW + timedelta(days=6)).isoformat(),
                "ends_at": (NOW + timedelta(days=10)).isoformat(),
            },
            format="json",
        )

        assert response.status_code == 400
        assert "partner_name" in response.data["errors"]

    def test_rejects_out_of_order_deadlines(self, api_client, organizer):
        api_client.force_authenticate(user=organizer)

        response = api_client.post(
            "/api/v1/organizer/hackathons/",
            {
                "title": "New Hackathon",
                "registration_deadline": (NOW + timedelta(days=10)).isoformat(),
                "submission_deadline": (NOW + timedelta(days=5)).isoformat(),
                "starts_at": (NOW + timedelta(days=6)).isoformat(),
                "ends_at": (NOW + timedelta(days=10)).isoformat(),
            },
            format="json",
        )

        assert response.status_code == 400


class TestOrganizerHackathonDetailView:
    def test_owner_can_view_and_edit(self, api_client, organizer):
        hackathon = _hackathon(organizer)
        api_client.force_authenticate(user=organizer)

        response = api_client.patch(
            f"/api/v1/organizer/hackathons/{hackathon.id}/", {"title": "Renamed"}, format="json"
        )

        assert response.status_code == 200
        assert response.data["title"] == "Renamed"

    def test_non_owner_forbidden(self, api_client, organizer, student):
        hackathon = _hackathon(organizer)
        api_client.force_authenticate(user=student)

        response = api_client.get(f"/api/v1/organizer/hackathons/{hackathon.id}/")

        assert response.status_code == 403


class TestHackathonPublishCancelViews:
    def test_owner_can_publish_draft(self, api_client, organizer):
        hackathon = _hackathon(organizer)
        api_client.force_authenticate(user=organizer)

        response = api_client.post(f"/api/v1/organizer/hackathons/{hackathon.id}/publish/")

        assert response.status_code == 200
        assert response.data["status"] == "published"

    def test_cannot_publish_already_published(self, api_client, organizer):
        hackathon = _hackathon(organizer, status=Hackathon.STATUS_PUBLISHED)
        api_client.force_authenticate(user=organizer)

        response = api_client.post(f"/api/v1/organizer/hackathons/{hackathon.id}/publish/")

        assert response.status_code == 400

    def test_non_owner_cannot_publish(self, api_client, organizer, student):
        hackathon = _hackathon(organizer)
        api_client.force_authenticate(user=student)

        response = api_client.post(f"/api/v1/organizer/hackathons/{hackathon.id}/publish/")

        assert response.status_code == 403

    def test_owner_can_cancel(self, api_client, organizer):
        hackathon = _hackathon(organizer, status=Hackathon.STATUS_PUBLISHED)
        api_client.force_authenticate(user=organizer)

        response = api_client.post(f"/api/v1/organizer/hackathons/{hackathon.id}/cancel/")

        assert response.status_code == 200
        assert response.data["status"] == "canceled"

    def test_non_owner_cannot_cancel(self, api_client, organizer, student):
        hackathon = _hackathon(organizer, status=Hackathon.STATUS_PUBLISHED)
        api_client.force_authenticate(user=student)

        response = api_client.post(f"/api/v1/organizer/hackathons/{hackathon.id}/cancel/")

        assert response.status_code == 403


class TestOrganizerHackathonRegistrationsView:
    def test_owner_sees_roster(self, api_client, organizer, student):
        hackathon = _hackathon(organizer, status=Hackathon.STATUS_PUBLISHED)
        _registration(hackathon, student, team_name="Byte Me")
        api_client.force_authenticate(user=organizer)

        response = api_client.get(f"/api/v1/organizer/hackathons/{hackathon.id}/registrations/")

        assert response.status_code == 200
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["participant"]["email"] == student.email

    def test_non_owner_forbidden(self, api_client, organizer, student):
        hackathon = _hackathon(organizer, status=Hackathon.STATUS_PUBLISHED)
        api_client.force_authenticate(user=student)

        response = api_client.get(f"/api/v1/organizer/hackathons/{hackathon.id}/registrations/")

        assert response.status_code == 403


class TestHackathonWinnerCreateView:
    def _registration_with_submission(self, hackathon, participant):
        registration = _registration(hackathon, participant)
        HackathonSubmission.objects.create(registration=registration, title="Winning Entry")
        return registration

    def test_owner_declares_winner(self, api_client, organizer, student):
        hackathon = _hackathon(organizer, status=Hackathon.STATUS_PUBLISHED)
        registration = self._registration_with_submission(hackathon, student)
        api_client.force_authenticate(user=organizer)

        response = api_client.post(
            f"/api/v1/organizer/hackathons/{hackathon.id}/winners/",
            {
                "registration_id": str(registration.id),
                "placement": 1,
                "prize_description": "$1,000",
            },
            format="json",
        )

        assert response.status_code == 201
        assert response.data["placement"] == 1

    def test_requires_a_submission(self, api_client, organizer, student):
        hackathon = _hackathon(organizer, status=Hackathon.STATUS_PUBLISHED)
        registration = _registration(hackathon, student)
        api_client.force_authenticate(user=organizer)

        response = api_client.post(
            f"/api/v1/organizer/hackathons/{hackathon.id}/winners/",
            {"registration_id": str(registration.id), "placement": 1},
            format="json",
        )

        assert response.status_code == 400

    def test_duplicate_placement_rejected(self, api_client, organizer, student, django_user_model):
        hackathon = _hackathon(organizer, status=Hackathon.STATUS_PUBLISHED)
        reg_a = self._registration_with_submission(hackathon, student)
        other = django_user_model.objects.create_user(email="other@example.com", password="x")
        reg_b = self._registration_with_submission(hackathon, other)
        api_client.force_authenticate(user=organizer)
        api_client.post(
            f"/api/v1/organizer/hackathons/{hackathon.id}/winners/",
            {"registration_id": str(reg_a.id), "placement": 1},
            format="json",
        )

        response = api_client.post(
            f"/api/v1/organizer/hackathons/{hackathon.id}/winners/",
            {"registration_id": str(reg_b.id), "placement": 1},
            format="json",
        )

        assert response.status_code == 400

    def test_non_owner_forbidden(self, api_client, organizer, student):
        hackathon = _hackathon(organizer, status=Hackathon.STATUS_PUBLISHED)
        registration = self._registration_with_submission(hackathon, student)
        api_client.force_authenticate(user=student)

        response = api_client.post(
            f"/api/v1/organizer/hackathons/{hackathon.id}/winners/",
            {"registration_id": str(registration.id), "placement": 1},
            format="json",
        )

        assert response.status_code == 403


class TestHackathonAdminCancelView:
    def test_forbidden_without_permission(self, api_client, organizer):
        hackathon = _hackathon(organizer, status=Hackathon.STATUS_PUBLISHED)
        api_client.force_authenticate(user=organizer)

        response = api_client.post(f"/api/v1/admin/hackathons/{hackathon.id}/cancel/")

        assert response.status_code == 403

    def test_administrator_can_force_cancel(self, api_client, organizer, django_user_model):
        from apps.authorization.models import Role, UserRole

        hackathon = _hackathon(organizer, status=Hackathon.STATUS_PUBLISHED)
        admin = django_user_model.objects.create_user(email="admin@example.com", password="x")
        UserRole.objects.create(user=admin, role=Role.objects.get(code="administrator"))
        api_client.force_authenticate(user=admin)

        response = api_client.post(f"/api/v1/admin/hackathons/{hackathon.id}/cancel/")

        assert response.status_code == 200
        assert response.data["status"] == "canceled"


class TestAdminHackathonGalleryImageListCreateView:
    def _admin(self, django_user_model):
        from apps.authorization.models import Role, UserRole

        admin = django_user_model.objects.create_user(
            email="gallery-admin@example.com", password="x"
        )
        UserRole.objects.create(user=admin, role=Role.objects.get(code="administrator"))
        return admin

    def test_video_url_only_succeeds(self, api_client, organizer, django_user_model):
        hackathon = _hackathon(organizer, status=Hackathon.STATUS_PUBLISHED)
        api_client.force_authenticate(user=self._admin(django_user_model))

        response = api_client.post(
            f"/api/v1/admin/hackathons/{hackathon.id}/gallery-images/",
            {"video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "caption": "Demo day"},
            format="json",
        )

        assert response.status_code == 201
        assert response.data["video_url"] == "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        assert not response.data["image"]

    def test_image_only_succeeds(self, api_client, organizer, django_user_model):
        from django.core.files.uploadedfile import SimpleUploadedFile

        hackathon = _hackathon(organizer, status=Hackathon.STATUS_PUBLISHED)
        api_client.force_authenticate(user=self._admin(django_user_model))
        image = SimpleUploadedFile("photo.png", _ONE_PIXEL_PNG, content_type="image/png")

        response = api_client.post(
            f"/api/v1/admin/hackathons/{hackathon.id}/gallery-images/",
            {"image": image, "caption": "Opening ceremony"},
            format="multipart",
        )

        assert response.status_code == 201
        assert response.data["image"]
        assert not response.data["video_url"]

    def test_both_image_and_video_url_rejected(self, api_client, organizer, django_user_model):
        from django.core.files.uploadedfile import SimpleUploadedFile

        hackathon = _hackathon(organizer, status=Hackathon.STATUS_PUBLISHED)
        api_client.force_authenticate(user=self._admin(django_user_model))
        image = SimpleUploadedFile("photo.png", _ONE_PIXEL_PNG, content_type="image/png")

        response = api_client.post(
            f"/api/v1/admin/hackathons/{hackathon.id}/gallery-images/",
            {"image": image, "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"},
            format="multipart",
        )

        assert response.status_code == 400

    def test_neither_image_nor_video_url_rejected(self, api_client, organizer, django_user_model):
        hackathon = _hackathon(organizer, status=Hackathon.STATUS_PUBLISHED)
        api_client.force_authenticate(user=self._admin(django_user_model))

        response = api_client.post(
            f"/api/v1/admin/hackathons/{hackathon.id}/gallery-images/",
            {"caption": "Nothing attached"},
            format="json",
        )

        assert response.status_code == 400

    def test_forbidden_without_permission(self, api_client, organizer):
        hackathon = _hackathon(organizer, status=Hackathon.STATUS_PUBLISHED)
        api_client.force_authenticate(user=organizer)

        response = api_client.post(
            f"/api/v1/admin/hackathons/{hackathon.id}/gallery-images/",
            {"video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"},
            format="json",
        )

        assert response.status_code == 403
