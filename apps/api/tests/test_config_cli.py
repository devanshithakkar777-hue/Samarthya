import csv

import pytest

from app import models as m
from app.cli import import_csv
from app.config import Settings
from .factories import make_user, session


def test_prod_refuses_weak_or_missing_settings():
    with pytest.raises(ValueError):
        Settings(env="prod", jwt_secret="short", smtp_host="smtp.example.org")
    with pytest.raises(ValueError):
        Settings(env="prod", jwt_secret="x" * 40, smtp_host="")
    with pytest.raises(ValueError):
        Settings(env="prod", jwt_secret="x" * 40, smtp_host="s", allow_self_review=True)
    with pytest.raises(Exception):
        Settings(env="prod", jwt_secret="x" * 40, smtp_host="s")  # no JOURNAL_KEY
    assert Settings(env="prod", jwt_secret="x" * 40, smtp_host="s", journal_key="j" * 40).env == "prod"
    with pytest.raises(Exception):
        Settings(env="prod", jwt_secret="x" * 40, smtp_host="s", journal_key="j" * 40, llm_provider="anthropic")  # needs key and model


def test_csv_import_creates_drafts_with_sources(tmp_path, capsys):
    make_user("ed@example.org", m.UserRole.editor)
    f = tmp_path / "sectors.csv"
    with open(f, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["slug", "name", "summary", "source_url", "source_title", "source_publisher", "source_kind", "last_verified"])
        w.writerow(["imp-one", "Imported One", "s", "https://example.org/a", "A", "Pub", "official", "2026-01-01"])
        w.writerow(["imp-two", "Imported Two", "s", "https://example.org/a", "A", "Pub", "official", "2026-01-01"])
        w.writerow(["imp-one", "Duplicate slug", "s", "https://example.org/a", "A", "Pub", "official", "2026-01-01"])
    assert import_csv("sectors", str(f), "ed@example.org") == 2
    with session() as db:
        rows = db.query(m.Sector).order_by(m.Sector.slug).all()
        assert [r.status for r in rows] == [m.Status.draft, m.Status.draft]
        assert db.query(m.Source).count() == 1 and rows[0].source_id == rows[1].source_id
    assert "row 4" in capsys.readouterr().err
