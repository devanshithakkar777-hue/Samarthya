from types import SimpleNamespace

import pytest
from fastapi import Request

from app import deps
from app.config import Settings, _psycopg_url
from app.db import engine_options


def test_provider_urls_are_normalised_for_psycopg3():
    assert _psycopg_url("postgres://u:p@h/db?sslmode=require") == "postgresql+psycopg://u:p@h/db?sslmode=require"
    assert _psycopg_url("postgresql://u:p@h/db") == "postgresql+psycopg://u:p@h/db"
    assert _psycopg_url("postgresql+psycopg://u:p@h/db") == "postgresql+psycopg://u:p@h/db"
    s = Settings(database_url="postgresql://u:p@ep-x-pooler.h/db", direct_database_url="postgresql://u:p@ep-x.h/db")
    assert s.database_url.startswith("postgresql+psycopg://") and "-pooler" in s.database_url
    assert s.migration_url == "postgresql+psycopg://u:p@ep-x.h/db"  # migrations use the direct string
    assert Settings(database_url="postgresql://u:p@h/db").migration_url == "postgresql+psycopg://u:p@h/db"


def test_engine_options_disable_prepared_statements_and_recycle():
    o = engine_options(Settings(database_url="postgresql://u:p@h/db"))
    assert o["pool_pre_ping"] and o["connect_args"]["prepare_threshold"] is None and o["pool_recycle"] == 300


def _req(xff: str | None, peer="10.0.0.9"):
    headers = [(b"x-forwarded-for", xff.encode())] if xff is not None else []
    return Request({"type": "http", "headers": headers, "client": (peer, 1234), "method": "GET", "path": "/", "query_string": b""})


@pytest.mark.parametrize("hops,xff,expected", [
    (0, "1.1.1.1, 2.2.2.2", "10.0.0.9"),            # not behind a trusted proxy: header ignored
    (1, "forged, 203.0.113.7", "203.0.113.7"),      # one proxy: the last entry is the one it appended
    (2, "forged, 203.0.113.7, 10.1.1.1", "203.0.113.7"),  # two proxies
    (1, None, "10.0.0.9"),                          # header missing: fall back to the peer
])
def test_client_ip_only_trusts_configured_proxies(monkeypatch, hops, xff, expected):
    monkeypatch.setattr(deps, "get_settings", lambda: SimpleNamespace(trusted_proxy_hops=hops))
    assert deps.client_ip(_req(xff)) == expected


def test_forged_forwarded_for_cannot_dodge_the_limit(monkeypatch):
    monkeypatch.setattr(deps, "get_settings", lambda: SimpleNamespace(trusted_proxy_hops=1))
    limiter = deps.RateLimiter(limit=2, window_seconds=60)
    for fake in ("a", "b"):
        limiter(_req(f"{fake}, 203.0.113.7"))
    with pytest.raises(Exception) as e:
        limiter(_req("c, 203.0.113.7"))
    assert getattr(e.value, "status_code", None) == 429
