"""Encryption at rest for the wellness journal."""
import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken

from ..config import get_settings


def _fernet() -> Fernet:
    s = get_settings()
    # Any secret of 32+ characters works: the Fernet key is derived from it. Losing or changing it makes
    # existing journal entries unreadable, so back it up with the other secrets (see DEPLOY.md).
    # Development and tests derive it from the JWT secret; production refuses to start without JOURNAL_KEY.
    secret = s.journal_key.strip() or ("dev:" + s.jwt_secret)
    return Fernet(base64.urlsafe_b64encode(hashlib.sha256(("journal:" + secret).encode()).digest()))


def encrypt(text: str) -> str:
    return _fernet().encrypt(text.encode()).decode()


def decrypt(token: str) -> str:
    try:
        return _fernet().decrypt(token.encode()).decode()
    except InvalidToken:
        return "[This entry cannot be read: the encryption key has changed.]"
