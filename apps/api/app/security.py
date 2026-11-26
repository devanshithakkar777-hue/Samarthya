import hashlib
import hmac
from datetime import datetime, timedelta, timezone

import jwt

from .config import get_settings
from .models import User


def create_token(user: User) -> str:
    s = get_settings()
    now = datetime.now(timezone.utc)
    payload = {"sub": str(user.id), "role": user.role.value, "iat": now,
               "exp": now + timedelta(hours=s.jwt_ttl_hours)}
    return jwt.encode(payload, s.jwt_secret, algorithm="HS256")


def decode_token(token: str) -> dict:
    return jwt.decode(token, get_settings().jwt_secret, algorithms=["HS256"])


def hash_code(email: str, code: str) -> str:
    key = get_settings().jwt_secret.encode()
    return hmac.new(key, f"{email.lower()}:{code}".encode(), hashlib.sha256).hexdigest()
