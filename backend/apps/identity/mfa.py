import pyotp
from django.core import signing

_MFA_CHALLENGE_SALT = "identity.mfa-challenge"
_MFA_CHALLENGE_MAX_AGE_SECONDS = 300  # 5 minutes


def generate_secret() -> str:
    return pyotp.random_base32()


def provisioning_uri(secret: str, email: str, issuer: str = "SkillChain") -> str:
    return pyotp.totp.TOTP(secret).provisioning_uri(name=email, issuer_name=issuer)


def verify_code(secret: str, code: str) -> bool:
    # valid_window=1 tolerates the code from one 30s step before/after now,
    # covering ordinary clock drift between server and authenticator app.
    return pyotp.totp.TOTP(secret).verify(code, valid_window=1)


def issue_login_challenge_token(user) -> str:
    """Short-lived, tamper-proof token identifying *who* passed the password
    check, without granting any API access itself — exchanged for real JWTs
    at POST /auth/mfa/login-verify once the TOTP code is also correct."""
    return signing.dumps({"user_id": str(user.id)}, salt=_MFA_CHALLENGE_SALT)


def resolve_login_challenge_token(token: str) -> str | None:
    try:
        data = signing.loads(
            token, salt=_MFA_CHALLENGE_SALT, max_age=_MFA_CHALLENGE_MAX_AGE_SECONDS
        )
    except signing.BadSignature:
        return None
    return data.get("user_id")
