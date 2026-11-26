import os

os.environ["ENV"] = "test"
os.environ["DATABASE_URL"] = os.environ.get(
    "TEST_DATABASE_URL", "postgresql+psycopg://samarthya:samarthya@localhost:5432/samarthya_test")
os.environ["JWT_SECRET"] = "test-secret-test-secret-test-secret-0000"
os.environ["ALLOW_SELF_REVIEW"] = "false"
os.environ["ADMIN_BOOTSTRAP_EMAIL"] = ""

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.db import get_engine
from app.main import app
from app.routers import auth as auth_router
from app.routers import public as public_router
from app.routers import reports as reports_router
from app.services.email import OUTBOX


@pytest.fixture(scope="session", autouse=True)
def migrated():
    cfg = Config(os.path.join(os.path.dirname(__file__), "..", "alembic.ini"))
    cfg.set_main_option("script_location", os.path.join(os.path.dirname(__file__), "..", "alembic"))
    command.upgrade(cfg, "head")
    yield


@pytest.fixture(autouse=True)
def clean(migrated):
    with get_engine().begin() as c:
        names = [r[0] for r in c.execute(text(
            "select tablename from pg_tables where schemaname='public' and tablename <> 'alembic_version'"))]
        c.execute(text("TRUNCATE " + ", ".join(names) + " RESTART IDENTITY CASCADE"))
    OUTBOX.clear()
    for lim in (public_router.fit_limit, public_router.ask_limit, auth_router.auth_limit, reports_router.report_limit, reports_router.participate_limit):
        lim.reset()
    yield


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c
