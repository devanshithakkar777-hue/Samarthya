import logging
import smtplib
from email.message import EmailMessage

from ..config import get_settings

log = logging.getLogger("samarthya.email")
# Outside prod, sent messages are kept here so tests and local development can read the code.
OUTBOX: list[dict] = []


def send_sign_in_code(email: str, code: str) -> None:
    s = get_settings()
    subject = "Your Samarthya sign-in code"
    body = (f"Your sign-in code is {code}. It works for {s.otp_ttl_minutes} minutes.\n\n"
            "If you did not ask for this, you can ignore this message.")
    if s.env != "prod":
        OUTBOX.append({"to": email, "code": code})
        log.info("sign-in code for %s: %s (dev outbox, not emailed)", email, code)
        return
    msg = EmailMessage()
    msg["From"], msg["To"], msg["Subject"] = s.mail_from, email, subject
    msg.set_content(body)
    with smtplib.SMTP(s.smtp_host, s.smtp_port, timeout=15) as smtp:
        smtp.starttls()
        if s.smtp_user:
            smtp.login(s.smtp_user, s.smtp_password)
        smtp.send_message(msg)
