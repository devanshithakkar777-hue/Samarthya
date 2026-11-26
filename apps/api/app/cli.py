"""Command line tools: python -m app.cli <command>

  import <entity> <file.csv> --as <editor email>   load rows as drafts for review
  make-admin <email>                               grant the admin role to an existing account
  seed-dev                                         load clearly fake sample content (refuses in prod)

CSV rules for `import`: header row of field names from the editable fields of that entity.
Use `source_url`, `source_title`, `source_publisher`, `source_kind` instead of `source_id`;
the source is created when new. Use `<x>_slug` columns (sector_slug, skill_slug, role_slug,
company_slug, qualification_slug) instead of numeric ids. Everything lands as a draft.
"""
import argparse
import csv
import sys

from sqlalchemy import select

from . import models as m
from .config import get_settings
from .db import get_db
from .services import curation as cur

SLUG_FIELDS = {"sector_slug": (m.Sector, "sector_id"), "skill_slug": (m.Skill, "skill_id"),
               "role_slug": (m.Role, "role_id"), "company_slug": (m.Company, "company_id"),
               "qualification_slug": (m.Qualification, "qualification_id")}


def _db():
    return next(get_db())


def _coerce(model, data: dict) -> dict:
    """Turn text from a CSV cell (or a JSON value) into the type the column holds. Lists may be written a;b;c."""
    import json
    from datetime import date

    from sqlalchemy import JSON, Boolean, Date, Integer
    cols = model.__table__.columns
    for key in list(data):
        col = cols.get(key)
        v = data[key]
        if col is None or not isinstance(v, str):
            continue
        t = col.type
        if isinstance(t, Boolean):
            data[key] = v.strip().lower() in ("1", "true", "yes")
        elif isinstance(t, Integer) and not key.endswith("_id"):
            data[key] = int(v)
        elif isinstance(t, Date):
            data[key] = date.fromisoformat(v.strip())
        elif isinstance(t, JSON):
            v = v.strip()
            data[key] = json.loads(v) if v[:1] in "[{" else [x.strip() for x in v.split(";") if x.strip()]
    return data


def _rows(path: str):
    """Rows from a .csv file, or from a .json file holding a list of objects."""
    if path.lower().endswith(".json"):
        import json
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list) or not all(isinstance(x, dict) for x in data):
            sys.exit("A .json import must be a list of objects")
        yield from enumerate(data, start=1)
    else:
        with open(path, newline="", encoding="utf-8-sig") as f:
            yield from enumerate(csv.DictReader(f), start=2)


def import_csv(entity: str, path: str, editor_email: str) -> int:
    db = _db()
    editor = db.scalar(select(m.User).where(m.User.email == editor_email.lower()))
    if editor is None or editor.role == m.UserRole.student:
        sys.exit("The --as account must exist and be an editor, reviewer or admin")
    n = 0
    if True:
        for lineno, row in _rows(path):
            data = {k: v for k, v in row.items() if k and v not in (None, "", [])}
            try:
                if "source_url" in data:
                    url = data.pop("source_url")
                    src = db.scalar(select(m.Source).where(m.Source.url == url))
                    if src is None:
                        src = m.Source(url=url, title=data.pop("source_title", url),
                                       publisher=data.pop("source_publisher", "Unknown"),
                                       kind=m.SourceKind(data.pop("source_kind", "third_party")))
                        db.add(src)
                        db.flush()
                    else:
                        for k in ("source_title", "source_publisher", "source_kind"):
                            data.pop(k, None)
                    data["source_id"] = src.id
                for key, (model, fk) in SLUG_FIELDS.items():
                    if key in data:
                        obj = db.scalar(select(model).where(model.slug == data.pop(key)))
                        if obj is None:
                            raise ValueError(f"{key} not found")
                        data[fk] = obj.id
                for key in ("price_inr", "duration_hours", "strength", "position", "year_of_study", "duration_years"):
                    if key in data:
                        data[key] = int(data[key])
                for key in ("certificate", "sponsored"):
                    if key in data and isinstance(data[key], str):
                        data[key] = data[key].strip().lower() in ("1", "true", "yes")
                if entity in cur.REVIEWABLE:
                    _coerce(cur.REVIEWABLE[entity][0], data)
                cur.create(db, editor, entity, data)
                n += 1
            except Exception as e:  # report the row and keep going
                db.rollback()
                detail = getattr(e, "detail", str(e))
                print(f"row {lineno}: {detail}", file=sys.stderr)
    print(f"imported {n} row(s) into {entity} as drafts")
    return n


def enrich_csv(entity: str, path: str, editor_email: str) -> int:
    """Update existing rows by slug (fields from the CSV, source replaced). Rows stay drafts."""
    db = _db()
    editor = db.scalar(select(m.User).where(m.User.email == editor_email.lower()))
    if editor is None or editor.role == m.UserRole.student:
        sys.exit("The --as account must exist and be an editor, reviewer or admin")
    model = cur.get_entry(entity)[0]
    n = 0
    if True:
        for lineno, row in _rows(path):
            data = {k: v for k, v in row.items() if k and v not in (None, "", [])}
            try:
                obj = db.scalar(select(model).where(model.slug == data.pop("slug")))
                if obj is None:
                    raise ValueError("slug not found")
                url = data.pop("source_url")
                src = db.scalar(select(m.Source).where(m.Source.url == url))
                if src is None:
                    src = m.Source(url=url, title=data.pop("source_title", url), publisher=data.pop("source_publisher", "Unknown"),
                                   kind=m.SourceKind(data.pop("source_kind", "official")))
                    db.add(src)
                    db.flush()
                else:
                    for k in ("source_title", "source_publisher", "source_kind"):
                        data.pop(k, None)
                data["source_id"] = src.id
                if "duration_years" in data:
                    data["duration_years"] = int(data["duration_years"])
                cur.update(db, editor, entity, obj.id, data)
                n += 1
            except Exception as e:
                db.rollback()
                print(f"row {lineno}: {getattr(e, 'detail', str(e))}", file=sys.stderr)
    print(f"enriched {n} row(s) in {entity}; they remain drafts")
    return n


def make_admin(email: str) -> None:
    db = _db()
    u = db.scalar(select(m.User).where(m.User.email == email.lower()))
    if u is None:
        sys.exit("No account with that email. Sign in once first.")
    u.role = m.UserRole.admin
    db.commit()
    print(f"{email} is now admin")


def seed_dev() -> None:
    if get_settings().env == "prod":
        sys.exit("seed-dev is for local development only and refuses to run in prod")
    from datetime import date

    db = _db()
    if db.scalar(select(m.Sector).limit(1)) is not None:
        sys.exit("Database already has content; not seeding")
    src = m.Source(url="https://example.org/sample", title="SAMPLE DATA, not real", publisher="Local development",
                   kind=m.SourceKind.third_party)
    db.add(src)
    db.flush()
    kw = dict(status=m.Status.published, source_id=src.id, last_verified=date.today())
    q = m.Qualification(slug="sample-degree", degree="Sample Degree", level="undergraduate", duration_years=3, **kw)
    sec = m.Sector(slug="sample-sector", name="Sample Sector", summary="SAMPLE DATA for local development only.", **kw)
    db.add_all([q, sec])
    db.flush()
    role = m.Role(slug="sample-role", title="Sample Role", job_family="Sample", sector_id=sec.id,
                  description="SAMPLE DATA. Replace with curated, sourced content.", **kw)
    db.add(role)
    db.flush()
    db.add_all([m.RoleQualification(role_id=role.id, qualification_id=q.id),
                m.RoleRequirement(role_id=role.id, type=m.RequirementType.skill, tier=m.Tier.mandatory,
                                  label="Sample mandatory item", position=1),
                m.RoleRequirement(role_id=role.id, type=m.RequirementType.certification, tier=m.Tier.recommended,
                                  label="Sample recommended item", position=2),
                m.QualificationSector(qualification_id=q.id, sector_id=sec.id, strength=3,
                                      reason="SAMPLE reason.", source_id=src.id, last_verified=date.today()),
                m.RoadmapStep(qualification_id=q.id, year_of_study=1, title="Sample first-year step",
                              detail="SAMPLE DATA.", position=1, **kw)])
    db.commit()
    print("sample content loaded (clearly marked SAMPLE; never load it in production)")


def main() -> None:
    p = argparse.ArgumentParser(prog="python -m app.cli")
    sub = p.add_subparsers(dest="cmd", required=True)
    i = sub.add_parser("import")
    i.add_argument("entity", choices=sorted(list(cur.REVIEWABLE) + list(cur.LINKED)))
    i.add_argument("file")
    i.add_argument("--as", dest="editor", required=True)
    e = sub.add_parser("enrich")
    e.add_argument("entity", choices=["qualifications"])
    e.add_argument("file")
    e.add_argument("--as", dest="editor", required=True)
    a = sub.add_parser("make-admin")
    a.add_argument("email")
    sub.add_parser("seed-dev")
    args = p.parse_args()
    if args.cmd == "import":
        import_csv(args.entity, args.file, args.editor)
    elif args.cmd == "enrich":
        enrich_csv(args.entity, args.file, args.editor)
    elif args.cmd == "make-admin":
        make_admin(args.email)
    else:
        seed_dev()


if __name__ == "__main__":
    main()
