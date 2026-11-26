"""Safety helpers: crisis signals, contact-detail blocking, and the always-visible crisis resources.

The crisis resources below are fixed in code on purpose. They must show even if no wellness content has been
published yet. Each has an official source and the date it was last checked. A reviewer should re-check them
before launch and at every release (see BUILD_STATUS.md).
"""
import re

CRISIS_CHECKED_ON = "2026-11-26"
CRISIS_RESOURCES = [
    {"name": "Tele-MANAS (Government of India, free, 24x7, around 20 languages)",
     "phone": "14416", "alt_phone": "1-800-891-4416",
     "source": "https://pib.gov.in/PressReleasePage.aspx?PRID=2022057", "source_title": "PIB, Ministry of Health and Family Welfare"},
    {"name": "KIRAN mental health rehabilitation helpline (Government of India, free, 24x7)",
     "phone": "1800-599-0019", "alt_phone": None,
     "source": "https://pib.gov.in/PressReleasePage.aspx?PRID=1652240", "source_title": "PIB, Ministry of Social Justice and Empowerment"},
    {"name": "Emergency services (police, ambulance, fire)",
     "phone": "112", "alt_phone": None,
     "source": "https://www.mha.gov.in/en/commoncontent/emergency-response-support-system-erss", "source_title": "Ministry of Home Affairs, ERSS"},
]

_CRISIS = re.compile(
    r"\b(kill myself|end my life|end it all|want to die|wanna die|don'?t want to (live|be alive)|no reason to live|"
    r"suicid\w*|self[- ]?harm\w*|hurt myself|cut myself|better off dead|take my own life|"
    r"jaan de d\w+|marna chahta|marna chahti|mar jaana chahta|mar jana chahti)\b", re.I)


def crisis_signal(text: str) -> bool:
    """True if the text contains wording that suggests the writer may be in danger. A safety net, not a diagnosis."""
    return bool(_CRISIS.search(text or ""))


_PHONE = re.compile(r"(?<!\d)(?:\+?91[\s-]?)?[6-9]\d{4}[\s-]?\d{5}(?!\d)")
_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
_HANDLE = re.compile(r"(?:whatsapp|telegram|insta(?:gram)?|snap(?:chat)?)\s*[:@-]?\s*\S+", re.I)


_APPS = r"(?:whatsapp|telegram|insta(?:gram)?|snap(?:chat)?|discord|signal)"
_OFFER = re.compile(rf"\b(?:me|my|dm|id|number|handle)\b.{{0,24}}\b{_APPS}\b|\b{_APPS}\b.{{0,24}}\b(?:me|my|dm|id|number|handle)\b", re.I)


def contains_contact_details(text: str) -> bool:
    return bool(_PHONE.search(text) or _EMAIL.search(text) or _HANDLE.search(text) or _OFFER.search(text))
