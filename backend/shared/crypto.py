"""
Field-level encryption for secrets stored at rest — MFA TOTP secrets today,
conferencing OAuth tokens (docs/02-database §Live Sessions) in a later
milestone. Deliberately explicit encrypt()/decrypt() calls at the point of
use rather than a transparent model field: fewer surprises about what's
actually encrypted in the database.
"""

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from django.core.exceptions import SuspiciousOperation


def _fernet() -> Fernet:
    return Fernet(settings.FIELD_ENCRYPTION_KEY)


def encrypt(plaintext: str) -> str:
    return _fernet().encrypt(plaintext.encode()).decode()


def decrypt(ciphertext: str) -> str:
    try:
        return _fernet().decrypt(ciphertext.encode()).decode()
    except InvalidToken as exc:
        raise SuspiciousOperation(
            "Could not decrypt value with the configured encryption key."
        ) from exc
