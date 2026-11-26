import logging
import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from .config import get_settings
from .db import get_engine
from .routers import admin, auth, connect, content, institution, me, me_build, me_family, me_learn, me_life, public, reports, tools, me_more

log = logging.getLogger("samarthya")
# anything personal or signed-in is never cached, by browsers or by a shared proxy
PRIVATE_PREFIXES = ("/v1/me", "/v1/admin", "/v1/moderation", "/v1/org-admin", "/v1/auth", "/v1/community", "/v1/mentors", "/v1/institution", "/v1/portfolios", "/v1/parent-view", "/v1/mentor-sessions", "/v1/employer", "/v1/professional", "/v1/credentials")


def configure_logging(level: str) -> None:
    logging.basicConfig(level=level.upper(), format="%(asctime)s %(levelname)s %(name)s %(message)s", force=True)


def create_app() -> FastAPI:
    s = get_settings()
    configure_logging(s.log_level)
    app = FastAPI(title="Samarthya API", version="0.1.0",
                  docs_url=None if s.env == "prod" else "/docs",
                  redoc_url=None, openapi_url=None if s.env == "prod" else "/openapi.json")
    app.add_middleware(CORSMiddleware, allow_origins=s.cors_list, allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
                       allow_headers=["Authorization", "Content-Type"], max_age=600)

    @app.middleware("http")
    async def headers(request: Request, call_next):
        started = time.monotonic()
        resp = await call_next(request)
        if request.url.path not in ("/healthz",):  # method, path and status only: no query strings, no personal data
            log.info("%s %s %s %.0fms", request.method, ("/v1/parent-view/-" if request.url.path.startswith("/v1/parent-view/") else request.url.path), resp.status_code, (time.monotonic() - started) * 1000)
        resp.headers["X-Content-Type-Options"] = "nosniff"
        resp.headers["Referrer-Policy"] = "no-referrer"
        resp.headers["X-Frame-Options"] = "DENY"
        public_content = request.method == "GET" and request.url.path.startswith("/v1/") and not any(
            request.url.path.startswith(p) for p in PRIVATE_PREFIXES)
        resp.headers["Cache-Control"] = "public, max-age=60" if public_content else "no-store"
        return resp

    @app.exception_handler(Exception)
    async def unhandled(request: Request, exc: Exception):
        log.exception("unhandled error on %s %s", request.method, request.url.path)
        return JSONResponse({"detail": "Something went wrong on our side."}, status_code=500)

    @app.get("/healthz", include_in_schema=False)
    def healthz():
        return {"ok": True}

    @app.get("/readyz", include_in_schema=False)
    def readyz():
        with get_engine().connect() as c:
            c.execute(text("select 1"))
        return {"ok": True}

    for r in (public.router, auth.router, me.router, reports.router, admin.router, content.router, me_learn.router, me_build.router,
              me_build.public_router, me_life.router, connect.router, connect.admin_router, institution.router, tools.router, me_family.router, me_family.public_router, me_more.router):
        app.include_router(r)
    return app


app = create_app()
