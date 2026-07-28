from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.utils import timezone

from apps.identity.models import MFAFactor, OAuthIdentity, Profile

from .models import DataErasureRequest, LegalHold


def request_erasure(user) -> DataErasureRequest:
    erasure_request = DataErasureRequest.objects.create(user=user)

    active_hold = LegalHold.objects.filter(user=user, released_at__isnull=True).first()
    if active_hold is not None:
        erasure_request.status = DataErasureRequest.STATUS_BLOCKED
        erasure_request.block_reason = active_hold.reason
        erasure_request.save(update_fields=["status", "block_reason"])
        return erasure_request

    _erase_user_data(user)
    erasure_request.status = DataErasureRequest.STATUS_COMPLETED
    erasure_request.completed_at = timezone.now()
    erasure_request.save(update_fields=["status", "completed_at"])
    return erasure_request


def _erase_user_data(user) -> None:
    """
    Anonymizes PII in place. The User row itself is kept (id only) because
    Order/Payment all PROTECT-FK to it — hard-deleting the account would
    violate financial retention requirements regardless of this request.
    """
    user.email = f"erased-user-{user.id}@erased.invalid"
    user.is_active = False
    user.set_unusable_password()
    user.save(update_fields=["email", "is_active", "password"])

    Profile.objects.filter(user=user).update(first_name="", last_name="", avatar_url="")
    OAuthIdentity.objects.filter(user=user).delete()
    MFAFactor.objects.filter(user=user).delete()


def place_legal_hold(user_id, reason: str) -> LegalHold:
    get_object_or_404(get_user_model(), pk=user_id)
    return LegalHold.objects.create(user_id=user_id, reason=reason)


def release_legal_hold(hold_id) -> LegalHold:
    hold = get_object_or_404(LegalHold, pk=hold_id)
    hold.released_at = timezone.now()
    hold.save(update_fields=["released_at"])
    return hold
