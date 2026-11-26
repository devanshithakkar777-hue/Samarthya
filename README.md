# Samarthya: Every Potential Deserves an Opportunity

Release 1 (careers core): a free public-welfare platform that shows students what their degree can lead to, what each career asks for, and the next step, with every fact sourced and dated.

- `apps/api`: FastAPI + PostgreSQL. Rules-based matching, provenance gate, four-eyes publishing, audit log, email-code sign-in, data export and deletion.
- `apps/web`: Next.js (App Router), TypeScript, Tailwind. Hybrid 3D hero that switches off for reduced motion, data saver, slow networks and weak devices. Design tokens live in `apps/web/design/tokens.json` and the build fails if any text/background pair misses its WCAG contrast target.

## Product rules enforced in code
Sourced and dated facts only. Four separate fit answers (degree, interests, readiness, hiring pages), never a combined score. Requirement tiers (required, commonly preferred, recommended, stand-out). Nothing is published until a second person reviews it. Links out to official hiring pages only. No streaks or leaderboards. Anonymous use on-device, optional account, full export and delete.

## Run locally
```
# database
createdb / use Postgres 16; create users and DBs samarthya_dev, samarthya_test (see apps/api/tests/conftest.py)
cd apps/api && pip install -e ".[dev]"
export DATABASE_URL=postgresql+psycopg://samarthya:samarthya@localhost:5432/samarthya_dev JWT_SECRET=$(python -c "import secrets;print(secrets.token_urlsafe(48))")
alembic upgrade head
python -m app.cli seed-dev        # SAMPLE data only; refuses in production
uvicorn app.main:create_app --factory --port 8000
cd ../web && npm ci && API_URL=http://localhost:8000 npm run dev
```
Sign-in codes in dev are held in memory (no email is sent). Tests: `cd apps/api && pytest`, `cd apps/web && npm test && npm run typecheck`.

## Deploy
```
cp .env.example .env     # fill in every value; SMTP is required in production
docker compose up -d --build
docker compose exec api python -m app.cli make-admin you@example.com
```
Put a TLS-terminating proxy (Caddy, nginx, a cloud load balancer) in front of the `web` service. The API is not exposed publicly; the web app reaches it on the private network and proxies browser calls, keeping the sign-in token in an httpOnly cookie.

## Adding real content
There is deliberately no real career data in the repository. Read `content/EDITOR_GUIDE.md`. Content enters as drafts, each tied to a source (URL, publisher, date), then is submitted, reviewed by a different person and published. Editors work in the web workspace at `/admin` (sign in with an editor email; an admin grants roles with `python -m app.cli make-admin` or `POST /v1/admin/users/{id}/role`). CSV templates are in `content/templates/`. Or use the admin API (`/v1/admin`, docs at `/docs` outside production) or bulk-load drafts with `python -m app.cli import <kind> file.csv`. Items not re-verified for 180 days are flagged "may be out of date" automatically; `GET /v1/admin/stale` lists them.

## Phase 3 features
- **Ask** (`/ask`, `POST /v1/ask`): retrieval-only. Every sentence is copied from a published, sourced field and cited; otherwise it replies "I do not have a sourced answer to that yet." It refuses predictions, guarantees and salary estimates. Unanswered questions (text only, no identity) appear in the workspace as the content to-do list. No language model is used; if one is added later it may only rephrase retrieved passages and must pass the eval set.
- **Eval set:** `apps/api/tests/eval_ask_set.py` holds 50 questions (answerable, out-of-scope, predictive) run by `pytest` on every change. It uses a fake knowledge base; replace and extend it with real student questions from the unanswered list.
- **Weekly briefing** (`/briefing`): grouped by week, tied to related roles, with a source on every item. Editors write items in the workspace and a different reviewer approves them.
- **Homepage:** six-scene story with a lazy-loaded 3D backdrop (React Three Fiber, GSAP ScrollTrigger). 3D loads only on capable devices; with reduced motion, data saver, slow networks or weak devices the same content shows as plain HTML. Content never depends on 3D.
- **Checks:** `scripts/a11y_check.py` (axe, WCAG 2.2 AA) and `scripts/budget_check.py` (JS budget on the plain path) run in CI.

## Known limits before wide launch
- The content workspace (`/admin`) covers drafting, review and publishing for the main content types; bulk edits and a student-feedback tracker are not built yet.
- The rate limiter is per process; move it to Redis before running more than one API instance.
- Email-code sign-in only; phone OTP is deferred.
- Real content, verified sources and a content reviewer are required to launch. Without them the site correctly shows empty states.
- The 3D scenes are deliberately simple (a ring of seven structures, connecting lines, particles). The brief's custom architectural models need the contract 3D artist; the scene code is a placeholder for that work, with the same fallbacks.
- All six destinations (Learn, Explore, Practise, Build, Live, Connect) are built. Their content libraries are empty or draft until authored and approved by named reviewers. See BUILD_STATUS.md.

## Deploying

Pilot hosting is Render (web + API) with Neon Postgres: see [DEPLOY.md](DEPLOY.md), `render.yaml` and `.env.example`. A self-hosted alternative is `docker-compose.yml`.
