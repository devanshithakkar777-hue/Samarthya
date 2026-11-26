import hmac
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..config import get_settings
from ..models import OtpCode, User, UserRole
from ..security import hash_code
from .email import send_sign_in_code


class OtpError(Exception):
    def __init__(self, message: str, status: int = 400):
        super().__init__(message)
        self.message, self.status = message, status


def request_code(db: Session, email: str) -> None:
    """Always behaves the same whether or not the address has an account."""
    s = get_settings()
    email = email.strip().lower()
    since = datetime.now(timezone.utc) - timedelta(hours=1)
    recent = db.scalar(select(func.count()).select_from(OtpCode)
                       .where(OtpCode.email == email, OtpCode.created_at >= since)) or 0
    if recent >= s.otp_requests_per_hour:
        raise OtpError("Too many codes requested. Please try again later.", 429)
    code = f"{secrets.randbelow(1_000_000):06d}"
    db.add(OtpCode(email=email, code_hash=hash_code(email, code),
                   expires_at=datetime.now(timezone.utc) + timedelta(minutes=s.otp_ttl_minutes)))
    db.commit()
    send_sign_in_code(email, code)


def verify_code(db: Session, email: str, code: str) -> User:
    s = get_settings()
    email = email.strip().lower()
    now = datetime.now(timezone.utc)
    row = db.scalar(select(OtpCode).where(OtpCode.email == email, OtpCode.consumed_at.is_(None))
                    .order_by(OtpCode.created_at.desc()).limit(1))
    if row is None or row.expires_at < now:
        raise OtpError("That code is not valid. Please request a new one.")
    if row.attempts >= s.otp_max_attempts:
        raise OtpError("Too many attempts. Please request a new code.", 429)
    row.attempts += 1
    if not hmac.compare_digest(row.code_hash, hash_code(email, code.strip())):
        db.commit()
        raise OtpError("That code is not valid. Please request a new one.")
    row.consumed_at = now
    user = db.scalar(select(User).where(User.email == email))
    if user is None:
        user = User(email=email, role=UserRole.student)
        db.add(user)
    if s.admin_bootstrap_email and email == s.admin_bootstrap_email.strip().lower():
        user.role = UserRole.admin
    db.commit()
    return user
