"""
Instructor and student user generation for the Django course seed.

All seeded accounts share one dev-only password (see SEED_PASSWORD) — this
command is for development/staging demo data, never for production use.
"""

import random

from apps.authorization.models import Role, UserRole
from apps.identity.models import Profile, User

from .content_bank import FIRST_NAMES, LAST_NAMES

SEED_PASSWORD = "SkillChain2026!"
INSTRUCTOR_EMAIL = "academy@skillschain.dev"
STUDENT_COUNT = 100
SEED_RNG_SEED = 20260728  # fixed seed keeps reruns producing identical data


def _get_role(code: str) -> Role:
    try:
        return Role.objects.get(code=code)
    except Role.DoesNotExist as exc:
        raise RuntimeError(
            f"Role '{code}' does not exist — run 'python manage.py migrate' first "
            "(platform roles are seeded by apps.authorization's migrations)."
        ) from exc


def _assign_role(user: User, role: Role) -> None:
    UserRole.objects.get_or_create(
        user=user, role=role, context_type=Role.SCOPE_PLATFORM, context_id=None
    )


def get_or_create_instructor() -> User:
    """SkillsChain Academy — the course's single instructor account."""
    instructor, created = User.objects.get_or_create(
        email=INSTRUCTOR_EMAIL,
        defaults={"is_active": True},
    )
    if created:
        instructor.set_password(SEED_PASSWORD)
        instructor.save(update_fields=["password"])

    Profile.objects.update_or_create(
        user=instructor,
        defaults={"first_name": "SkillsChain", "last_name": "Academy"},
    )
    _assign_role(instructor, _get_role("instructor"))
    return instructor


def get_or_create_students() -> list[User]:
    """100 deterministic student accounts, each with a Profile and the
    'student' platform role."""
    rng = random.Random(SEED_RNG_SEED)
    student_role = _get_role("student")

    students: list[User] = []
    for index in range(1, STUDENT_COUNT + 1):
        first_name = rng.choice(FIRST_NAMES)
        last_name = rng.choice(LAST_NAMES)
        email = f"{first_name.lower()}.{last_name.lower()}{index:03d}@example.com"

        user, created = User.objects.get_or_create(
            email=email,
            defaults={"is_active": True},
        )
        if created:
            user.set_password(SEED_PASSWORD)
            user.save(update_fields=["password"])

        Profile.objects.update_or_create(
            user=user,
            defaults={"first_name": first_name, "last_name": last_name},
        )
        _assign_role(user, student_role)
        students.append(user)

    return students
