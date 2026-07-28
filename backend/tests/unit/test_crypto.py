import pytest
from django.core.exceptions import SuspiciousOperation

from shared.crypto import decrypt, encrypt


def test_encrypt_decrypt_round_trip():
    plaintext = "JBSWY3DPEHPK3PXP"  # looks like a real TOTP secret

    ciphertext = encrypt(plaintext)

    assert ciphertext != plaintext
    assert decrypt(ciphertext) == plaintext


def test_ciphertext_is_not_deterministic():
    # Fernet includes a random nonce/IV per call — two encryptions of the
    # same plaintext must not be comparable/identical at rest.
    plaintext = "same-secret"

    assert encrypt(plaintext) != encrypt(plaintext)


def test_decrypt_rejects_tampered_ciphertext():
    ciphertext = encrypt("original-secret")
    tampered = ciphertext[:-4] + ("A" * 4)

    with pytest.raises(SuspiciousOperation):
        decrypt(tampered)


def test_decrypt_rejects_garbage_input():
    with pytest.raises(SuspiciousOperation):
        decrypt("not-a-real-fernet-token")
