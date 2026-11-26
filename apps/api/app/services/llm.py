"""Optional AI companion (providers: anthropic, gemini, groq, openrouter). Off unless LLM_PROVIDER, LLM_API_KEY and LLM_MODEL are all set.

Rules the companion follows (also stated to the model):
- answer from the passages it is given and cite them by number; say plainly when they do not cover the question;
- label general advice as a suggestion, separate from sourced facts;
- never diagnose, never replace a professional, send people in distress to the crisis resources;
- encourage the student to reason for themselves rather than hand over a finished answer to copy.
Nothing is stored: messages are not saved by this service.
"""
import json
import re

import urllib.error
import urllib.request

from ..config import get_settings


class LlmUnavailable(Exception):
    pass


def enabled() -> bool:
    s = get_settings()
    return bool(s.llm_provider and s.llm_api_key and s.llm_model)


SYSTEM = """You are the Samarthya companion for students in India. Be warm, brief and honest.
Rules:
1. Use the numbered PASSAGES as your facts. Cite them like [1]. If they do not answer the question, say so plainly; do not invent facts, figures, salaries, fees, dates or eligibility.
2. Anything not in the passages is a SUGGESTION. Start such sentences with "Suggestion:" so the student can tell them apart from sourced facts.
3. Never predict whether the student will get a job or admission. Never diagnose a medical or mental condition and never act as a therapist or doctor. If the student seems distressed, be kind, encourage them to talk to someone they trust, and point them to the crisis resources shown on the page.
4. Help the student think. Ask a guiding question or explain the method instead of only giving a finished answer they could copy.
5. Do not write the student's resume lines, interview answers or assignments for them to submit as their own. Help them improve their own words.
6. Keep answers under 200 words unless asked for more. Reply in the language the student writes in."""


OPENAI_COMPATIBLE = {  # providers that speak the OpenAI chat format
    "groq": "https://api.groq.com/openai/v1/chat/completions",
    "openrouter": "https://openrouter.ai/api/v1/chat/completions",
}
PROVIDERS = {"anthropic", "gemini", *OPENAI_COMPATIBLE}


def _post(url: str, headers: dict, body: dict) -> dict:
    req = urllib.request.Request(url, data=json.dumps(body).encode(), method="POST",
                                 headers={"content-type": "application/json", **headers})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:  # noqa: S310  (fixed https endpoints from the table above)
            return json.loads(r.read())
    except (urllib.error.URLError, TimeoutError, ValueError) as e:  # the service must keep working when the provider is down
        raise LlmUnavailable("The companion is not available right now.") from e


def _call(system: str, user: str, max_tokens: int = 600) -> str:
    s = get_settings()
    p = s.llm_provider
    if p not in PROVIDERS:
        raise LlmUnavailable("Unsupported LLM provider")
    if p == "anthropic":
        data = _post("https://api.anthropic.com/v1/messages",
                     {"x-api-key": s.llm_api_key, "anthropic-version": "2023-06-01"},
                     {"model": s.llm_model, "max_tokens": max_tokens, "system": system,
                      "messages": [{"role": "user", "content": user}]})
        return "".join(b.get("text", "") for b in data.get("content", []) if b.get("type") == "text").strip()
    if p == "gemini":  # key goes in a header, never in the URL, so it cannot appear in logs
        data = _post(f"https://generativelanguage.googleapis.com/v1beta/models/{s.llm_model}:generateContent",
                     {"x-goog-api-key": s.llm_api_key},
                     {"systemInstruction": {"parts": [{"text": system}]},
                      "contents": [{"role": "user", "parts": [{"text": user}]}],
                      "generationConfig": {"maxOutputTokens": max_tokens}})
        parts = ((data.get("candidates") or [{}])[0].get("content") or {}).get("parts") or []
        return "".join(x.get("text", "") for x in parts).strip()
    data = _post(OPENAI_COMPATIBLE[p], {"authorization": f"Bearer {s.llm_api_key}"},
                 {"model": s.llm_model, "max_tokens": max_tokens,
                  "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]})
    return ((data.get("choices") or [{}])[0].get("message") or {}).get("content", "").strip()


def chat(question: str, passages: list[dict]) -> dict:
    ctx = "\n\n".join(f"[{i + 1}] {p['title']}: {p['text']}" for i, p in enumerate(passages)) or "(no passages found)"
    text = _call(SYSTEM, f"PASSAGES:\n{ctx}\n\nSTUDENT QUESTION:\n{question}")
    used = sorted({int(n) for n in re.findall(r"\[(\d+)\]", text) if 0 < int(n) <= len(passages)})
    text = re.sub(r"\[(\d+)\]", lambda mo: mo.group(0) if 0 < int(mo.group(1)) <= len(passages) else "", text)
    return {"answer": text, "citations": [passages[i - 1] | {"n": i} for i in used]}


def evaluate(question: str, guidance: str, answer: str) -> dict:
    """Feedback on an open answer against the question's guidance. The student's own words are never rewritten."""
    system = (SYSTEM.split("Rules:")[0] + "You give feedback on a student's practice answer. Compare it with the GUIDANCE. "
              "Return only JSON: {\"strengths\": [str], \"improvements\": [str], \"scores\": {\"accuracy\": 1-5, \"depth\": 1-5, \"clarity\": 1-5, \"relevance\": 1-5}}. "
              "You cannot judge whether the experiences are true; do not comment on honesty. Do not write a better answer for them.")
    raw = _call(system, f"QUESTION:\n{question}\n\nGUIDANCE:\n{guidance}\n\nANSWER:\n{answer}", 500)
    try:
        data = json.loads(raw[raw.index("{"): raw.rindex("}") + 1])
    except (ValueError, json.JSONDecodeError) as e:
        raise LlmUnavailable("The feedback could not be read. Please try again.") from e
    scores = {k: max(1, min(5, int(v))) for k, v in (data.get("scores") or {}).items()
              if k in ("accuracy", "depth", "clarity", "relevance") and str(v).lstrip("-").isdigit()}
    return {"strengths": [str(x)[:300] for x in data.get("strengths", [])][:4],
            "improvements": [str(x)[:300] for x in data.get("improvements", [])][:4], "scores": scores}
