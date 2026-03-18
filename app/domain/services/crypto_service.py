"""
Helpers para criptografar/descriptografar senhas sensíveis (Apple App-Specific Password).
Usa Fernet (AES-128-CBC + HMAC) da biblioteca cryptography.
"""
import base64
import hashlib
from cryptography.fernet import Fernet
from app.infrastructure.settings import settings


def _get_fernet() -> Fernet:
    """Returns a Fernet instance keyed from APPLE_ENCRYPTION_KEY or derived from SECRET_KEY."""
    if settings.APPLE_ENCRYPTION_KEY:
        key = settings.APPLE_ENCRYPTION_KEY.encode()
    else:
        # Derive 32-byte key from SECRET_KEY using SHA-256, then base64url-encode
        digest = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
        key = base64.urlsafe_b64encode(digest)
    return Fernet(key)


def encrypt_password(plaintext: str) -> str:
    """Encrypts plaintext and returns a base64-encoded token string."""
    return _get_fernet().encrypt(plaintext.encode()).decode()


def decrypt_password(token: str) -> str:
    """Decrypts a token produced by encrypt_password and returns the original plaintext."""
    return _get_fernet().decrypt(token.encode()).decode()
