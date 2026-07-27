import pytest

from apps.catalog.models import Course, InvalidCourseTransition

pytestmark = pytest.mark.django_db


@pytest.fixture
def course(django_user_model):
    owner = django_user_model.objects.create_user(email="instructor@example.com", password="x")
    return Course.objects.create(title="Advanced Django at Scale", owner=owner)


class TestCourseSlug:
    def test_slug_is_generated_from_title(self, course):
        assert course.slug == "advanced-django-at-scale"

    def test_duplicate_titles_get_distinct_slugs(self, django_user_model):
        owner = django_user_model.objects.create_user(email="another@example.com", password="x")
        first = Course.objects.create(title="Python Basics", owner=owner)
        second = Course.objects.create(title="Python Basics", owner=owner)

        assert first.slug != second.slug
        assert second.slug == "python-basics-2"


class TestCourseLifecycle:
    def test_new_course_starts_as_draft(self, course):
        assert course.status == Course.STATUS_DRAFT

    def test_submit_for_review_from_draft(self, course):
        course.submit_for_review()
        assert course.status == Course.STATUS_SUBMITTED

    def test_cannot_submit_an_already_submitted_course(self, course):
        course.submit_for_review()
        with pytest.raises(InvalidCourseTransition):
            course.submit_for_review()

    def test_approve_requires_submitted_status(self, course):
        with pytest.raises(InvalidCourseTransition):
            course.approve()

    def test_full_happy_path_to_published(self, course):
        course.submit_for_review()
        course.approve()
        course.publish()

        assert course.status == Course.STATUS_PUBLISHED
        assert course.published_at is not None

    def test_cannot_publish_without_approval(self, course):
        course.submit_for_review()
        with pytest.raises(InvalidCourseTransition):
            course.publish()

    def test_reject_sets_reason_and_clears_on_resubmit(self, course):
        course.submit_for_review()
        course.reject("Audio quality is too low")

        assert course.status == Course.STATUS_REJECTED
        assert course.rejection_reason == "Audio quality is too low"

        course.submit_for_review()
        assert course.status == Course.STATUS_SUBMITTED
        assert course.rejection_reason == ""

    def test_cannot_reject_a_draft(self, course):
        with pytest.raises(InvalidCourseTransition):
            course.reject("not ready")

    def test_archive_requires_published_status(self, course):
        with pytest.raises(InvalidCourseTransition):
            course.archive()

        course.submit_for_review()
        course.approve()
        course.publish()
        course.archive()
        assert course.status == Course.STATUS_ARCHIVED
