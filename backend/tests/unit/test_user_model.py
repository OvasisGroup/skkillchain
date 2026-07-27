import pytest
from django.contrib.auth import get_user_model
from django.db.utils import IntegrityError

User = get_user_model()


@pytest.mark.django_db
def test_create_user_normalizes_email_and_hashes_password():
    user = User.objects.create_user(email="Student@Example.com", password="a-strong-password")

    assert user.email == "Student@example.com"
    assert user.password != "a-strong-password"
    assert user.check_password("a-strong-password")
    assert user.is_active is True
    assert user.is_staff is False


@pytest.mark.django_db
def test_create_superuser_sets_staff_and_superuser_flags():
    admin = User.objects.create_superuser(email="admin@example.com", password="a-strong-password")

    assert admin.is_staff is True
    assert admin.is_superuser is True


@pytest.mark.django_db
def test_create_user_without_email_raises():
    with pytest.raises(ValueError):
        User.objects.create_user(email="", password="a-strong-password")


@pytest.mark.django_db
def test_email_must_be_unique():
    User.objects.create_user(email="dup@example.com", password="a-strong-password")
    with pytest.raises(IntegrityError):
        User.objects.create_user(email="dup@example.com", password="another-password")
