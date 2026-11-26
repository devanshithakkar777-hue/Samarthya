FROM python:3.13-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y --no-install-recommends fonts-dejavu-core && rm -rf /var/lib/apt/lists/*
WORKDIR /srv
COPY pyproject.toml ./
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./
RUN pip install --no-cache-dir . && useradd -r app && chown -R app /srv
USER app
ENV PORT=8000 RUN_MIGRATIONS=1
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s CMD python -c "import os,urllib.request;urllib.request.urlopen('http://127.0.0.1:'+os.environ.get('PORT','8000')+'/healthz')" || exit 1
# Migrations run with DIRECT_DATABASE_URL when set (on Neon, the non-pooled string). Run a single instance; see DEPLOY.md.
CMD ["sh", "-c", "if [ \"$RUN_MIGRATIONS\" = \"1\" ]; then alembic upgrade head; fi && exec uvicorn app.main:create_app --factory --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers"]
