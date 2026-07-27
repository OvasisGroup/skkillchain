import pytest

from apps.authorization.models import Role

pytestmark = pytest.mark.django_db

EXPECTED_ROLE_CODES = {
    "guest",
    "student",
    "instructor",
    "organization",
    "affiliate",
    "moderator",
    "support_agent",
    "finance_officer",
    "content_reviewer",
    "administrator",
    "super_administrator",
}


def test_all_documented_roles_are_seeded():
    codes = set(Role.objects.values_list("code", flat=True))

    assert codes == EXPECTED_ROLE_CODES
