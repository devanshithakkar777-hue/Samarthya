"""Rule-based red-flag checker for job, internship and scholarship messages.

It looks for patterns that official bodies warn about. It never says a message is genuine: finding no red flags
proves nothing. Nothing the student pastes is stored.
"""
import re

AICTE_ALERT = "https://aicte.gov.in/node/3163"          # AICTE alert on fraudulent job letters using AICTE/MoE identities, 23 Jan 2025
CYBER_PORTAL = "https://cybercrime.gov.in"              # National Cyber Crime Reporting Portal
OFFICIAL_AICTE_DOMAINS = ("aicte-india.org", "aicte.gov.in")

HELP = {
    "report": "If you have paid or shared bank or UPI details, call 1930 (national cyber-fraud helpline) at once and tell your bank. "
              "You can also file a complaint at cybercrime.gov.in. Keep screenshots, chats, UPI IDs and receipts.",
    "verify": "Check the employer yourself: find its website through a search (not through the message), call its published number, "
              "and ask your college placement cell.",
}

_FREE_MAIL = r"(?:gmail|yahoo|outlook|hotmail|rediffmail|proton(?:mail)?)\.(?:com|in|me)"

RULES = [
    {"id": "fee", "level": "high", "title": "Asks you to pay money",
     "why": "Genuine employers and the AICTE internship portal do not charge students to apply, be selected or get placed.",
     "pattern": r"(registration|processing|security|refundable|training|kit|certificate|verification|admission|booking|joining|application)\s+(fee|fees|charge|charges|deposit|amount)|pay\s+(rs\.?|₹|inr)?\s?\d|(send|transfer|deposit)\s+(rs\.?|₹|inr)?\s?\d|refundable",
     "source": AICTE_ALERT},
    {"id": "otp_bank", "level": "high", "title": "Asks for OTP, PIN, card, bank or UPI details",
     "why": "No genuine recruiter needs your OTP, card number, PIN or UPI PIN. Sharing them lets someone take money from your account.",
     "pattern": r"\botp\b|\bcvv\b|\bupi\s*pin\b|card\s*number|bank\s*(account|details|password)|net\s*banking|share.*(pin|password)",
     "source": CYBER_PORTAL},
    {"id": "guarantee", "level": "medium", "title": "Guarantees a job, placement or high earnings",
     "why": "Nobody can honestly guarantee a job. The AICTE portal states that applying does not guarantee an internship, stipend or job.",
     "pattern": r"100\s*%\s*(job|placement|guarantee)|guaranteed\s+(job|placement|selection|stipend|income)|earn\s+(up\s+to\s+)?(rs\.?|₹)?\s?\d[\d,]*\s*(/|per)\s*(day|week|hour)|easy\s+money|no\s+experience\s+needed.*(earn|salary)",
     "source": AICTE_ALERT},
    {"id": "no_interview", "level": "medium", "title": "Selected without an interview or application",
     "why": "Offers that arrive for jobs you never applied to, or with no interview, are a common trick to start asking for fees.",
     "pattern": r"(selected|shortlisted)\s+(without|directly)|no\s+interview|you\s+have\s+been\s+(selected|shortlisted)|direct\s+joining|congratulations.*(selected|offer)",
     "source": AICTE_ALERT},
    {"id": "urgency", "level": "medium", "title": "Pressure to act fast",
     "why": "Scammers rush you so you do not stop to check. Real offers allow you time to verify.",
     "pattern": r"(within|in)\s+(the\s+next\s+)?\d+\s*(hours?|hrs?|minutes?)|last\s+(date|chance|slot)|limited\s+(seats|slots|vacanc)|hurry|immediately|today\s+only|act\s+now",
     "source": CYBER_PORTAL},
    {"id": "chat_only", "level": "medium", "title": "Hiring only through WhatsApp or Telegram",
     "why": "Offers and interviews that run only through chat apps or personal numbers cannot be checked. The AICTE portal warns against links and payments outside the portal.",
     "pattern": r"whats\s?app|telegram|wa\.me|t\.me/|signal\s+group|dm\s+me|text\s+me",
     "source": AICTE_ALERT},
    {"id": "task_scam", "level": "high", "title": "Paid-task or investment style work",
     "why": "'Like, rate or complete tasks for pay', 'deposit to unlock earnings' and crypto or trading tasks are common online-fraud patterns.",
     "pattern": r"(like|rate|review|subscribe|follow)\s+.{0,40}(earn|pay|paid|reward)|task\s*(based|work)|unlock\s+(your\s+)?(earnings|tasks?)|usdt|crypto|bitcoin|trading\s+(group|tips|signals)|double\s+your",
     "source": CYBER_PORTAL},
    {"id": "free_mail", "level": "medium", "title": "Company message from a free personal email address",
     "why": "Established organisations normally write from their own domain, not a free personal mailbox.",
     "pattern": r"[\w.+-]+@" + _FREE_MAIL,
     "source": AICTE_ALERT},
    {"id": "short_link", "level": "medium", "title": "Shortened or unusual link",
     "why": "Shortened links hide where they lead. Open the employer's site yourself instead.",
     "pattern": r"(bit\.ly|tinyurl\.com|cutt\.ly|rb\.gy|t\.co|is\.gd|shorturl\.at|forms\.gle)/|https?://[^\s/]+\.(xyz|top|click|work|loan|buzz|icu)\b",
     "source": CYBER_PORTAL},
    {"id": "form", "level": "low", "title": "Application through a form or file instead of the employer's own system",
     "why": "The AICTE portal says applications outside the portal, such as a random form, are a red flag.",
     "pattern": r"google\s*form|fill\s+(this|the)\s+form|download\s+(the\s+)?(apk|app|file)|\.apk\b",
     "source": AICTE_ALERT},
]


def _impersonation(text: str) -> dict | None:
    low = text.lower()
    if "aicte" in low or "ministry of education" in low:
        domains = re.findall(r"[a-z0-9.-]+\.[a-z]{2,}", low)
        if domains and not any(any(d == o or d.endswith("." + o) for o in OFFICIAL_AICTE_DOMAINS) for d in domains if "aicte" in d):
            if any("aicte" in d for d in domains):
                return {"id": "impersonation", "level": "high", "title": "Uses AICTE's name with a different web address",
                        "why": "AICTE says it communicates only through aicte-india.org and aicte.gov.in, and has warned of fake letters from look-alike addresses.",
                        "source": AICTE_ALERT}
    return None


def check(text: str) -> dict:
    flags = []
    for r in RULES:
        mo = re.search(r["pattern"], text, re.I)
        if mo:
            flags.append({k: r[k] for k in ("id", "level", "title", "why", "source")} | {"matched": mo.group(0)[:60]})
    imp = _impersonation(text)
    if imp:
        flags.append(imp | {"matched": "AICTE / Ministry of Education"})
    order = {"high": 0, "medium": 1, "low": 2}
    flags.sort(key=lambda f: order[f["level"]])
    highs = sum(f["level"] == "high" for f in flags)
    if highs or len(flags) >= 3:
        verdict = "many_flags"
        summary = "This message has several signs that match known scams. Do not pay, share codes or click links until you have checked it another way."
    elif flags:
        verdict = "some_flags"
        summary = "This message has at least one sign that scams use. Check the sender through a channel you find yourself."
    else:
        verdict = "none_found"
        summary = "No red flags found by these simple checks. That does not mean the message is genuine. Always verify the employer yourself."
    return {"verdict": verdict, "summary": summary, "flags": flags, "help": HELP,
            "note": "Rule-based checks on the text you pasted. Nothing you paste is stored. This tool cannot tell whether an offer is real."}
