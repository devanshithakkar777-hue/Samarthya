import time
from collections import defaultdict, deque

import jwt
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from .config import get_settings
from .db import get_db
from .models import User, UserRole
from .security import decode_token

bearer = HTTPBearer(auto_error=False)


def optional_user(creds: HTTPAuthorizationCredentials | None = Depends(bearer),
                  db: Session = Depends(get_db)) -> User | None:
    if creds is None:
        return None
    try:
        data = decode_token(creds.credentials)
    except jwt.PyJWTError:
        raise HTTPException(401, "Invalid or expired sign-in")
    return db.get(User, int(data["sub"]))


def current_user(user: User | None = Depends(optional_user)) -> User:
    if user is None:
        raise HTTPException(401, "Sign in required")
    return user


def require_role(*roles: UserRole):
    def dep(user: User = Depends(current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(403, "You do not have access to this")
        return user
    return dep


editor_or_above = require_role(UserRole.editor, UserRole.reviewer, UserRole.admin)
reviewer_or_above = require_role(UserRole.reviewer, UserRole.admin)
admin_only = require_role(UserRole.admin)


def client_ip(request: Request) -> str:
    """The caller's address. X-Forwarded-For is only believed for the configured number of trusted proxies,
    counted from the right: each trusted proxy appends the address it saw, so anything further left is
    supplied by the client and can be forged."""
    hops = get_settings().trusted_proxy_hops
    peer = request.client.host if request.client else "unknown"
    if hops <= 0:
        return peer
    parts = [p.strip() for p in request.headers.get("x-forwarded-for", "").split(",") if p.strip()]
    return parts[-hops] if len(parts) >= hops else (parts[0] if parts else peer)


class RateLimiter:
    """Small per-process sliding window limiter for unauthenticated routes.

    Good enough for a single instance; move the counters to Redis before running several.
    """

    def __init__(self, limit: int, window_seconds: int):
        self.limit, self.window = limit, window_seconds
        self.hits: dict[str, deque] = defaultdict(deque)

    def __call__(self, request: Request) -> None:
        ip = client_ip(request)
        now = time.monotonic()
        q = self.hits[ip]
        while q and now - q[0] > self.window:
            q.popleft()
        if len(q) >= self.limit:
            raise HTTPException(429, "Too many requests. Please slow down.")
        q.append(now)

    def reset(self) -> None:
        self.hits.clear()
