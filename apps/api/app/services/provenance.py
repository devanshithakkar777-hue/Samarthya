from datetime import date, timedelta

from ..config import get_settings


def provenance(obj, source=None) -> dict:
    """The source and freshness shown beside every fact."""
    src = source if source is not None else getattr(obj, "source", None)
    lv = getattr(obj, "last_verified", None)
    stale = lv is None or (date.today() - lv) > timedelta(days=get_settings().stale_days)
    return {
        "source": None if src is None else {
            "url": src.url, "title": src.title, "publisher": src.publisher, "kind": src.kind.value,
            "published_on": src.published_on.isoformat() if src.published_on else None},
        "last_verified": lv.isoformat() if lv else None,
        "stale": stale,
    }
