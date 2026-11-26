"""Obviously fake content for tests. None of this is real career data."""
from datetime import date

from sqlalchemy.orm import Session

from app import models as m
from app.db import get_engine
from app.security import create_token
from sqlalchemy.orm import sessionmaker


def session() -> Session:
    return sessionmaker(bind=get_engine(), expire_on_commit=False)()


def make_user(email: str, role: m.UserRole = m.UserRole.student) -> tuple[m.User, dict]:
    with session() as db:
        u = m.User(email=email, role=role)
        db.add(u)
        db.commit()
        return u, {"Authorization": f"Bearer {create_token(u)}"}


def make_source(db: Session, url: str = "https://example.org/source") -> m.Source:
    s = m.Source(url=url, title="Test source", publisher="Test publisher", kind=m.SourceKind.official)
    db.add(s)
    db.flush()
    return s


def published(db: Session, model, src: m.Source, **kw):
    obj = model(status=m.Status.published, source_id=src.id, last_verified=date.today(), **kw)
    db.add(obj)
    db.flush()
    return obj


def seed_core() -> dict:
    """Two degrees, two sectors, two roles, one skill, one employer, all published."""
    with session() as db:
        src = make_source(db)
        bcom = published(db, m.Qualification, src, slug="test-degree-a", degree="Test Degree A", level="undergraduate",
                         duration_years=3)
        btech = published(db, m.Qualification, src, slug="test-degree-b", degree="Test Degree B",
                          level="undergraduate", duration_years=4)
        s1 = published(db, m.Sector, src, slug="test-sector-one", name="Test Sector One", summary="Fake sector one.")
        s2 = published(db, m.Sector, src, slug="test-sector-two", name="Test Sector Two", summary="Fake sector two.")
        skill = published(db, m.Skill, src, slug="test-skill", name="Test Skill", category="Testing",
                          overview="A fake skill.")
        role1 = published(db, m.Role, src, slug="test-role-one", title="Test Role One", job_family="Family",
                          sector_id=s1.id, description="Fake role one.")
        role2 = published(db, m.Role, src, slug="test-role-two", title="Test Role Two", job_family="Family",
                          sector_id=s2.id, description="Fake role two.")
        db.add(m.RoleQualification(role_id=role1.id, qualification_id=bcom.id))
        reqs = [
            m.RoleRequirement(role_id=role1.id, type=m.RequirementType.skill, tier=m.Tier.mandatory,
                              label="Know the test skill", skill_id=skill.id, position=1),
            m.RoleRequirement(role_id=role1.id, type=m.RequirementType.internship, tier=m.Tier.mandatory,
                              label="One internship", position=2),
            m.RoleRequirement(role_id=role1.id, type=m.RequirementType.certification, tier=m.Tier.common_preference,
                              label="A certificate", position=3),
            m.RoleRequirement(role_id=role1.id, type=m.RequirementType.experience, tier=m.Tier.differentiator,
                              label="A side project", position=4),
            m.RoleRequirement(role_id=role2.id, type=m.RequirementType.skill, tier=m.Tier.mandatory,
                              label="Another thing", position=1),
        ]
        db.add_all(reqs)
        db.add(m.QualificationSector(qualification_id=bcom.id, sector_id=s1.id, strength=3,
                                     reason="Test Degree A leads directly into Test Sector One.",
                                     source_id=src.id, last_verified=date.today()))
        co = published(db, m.Company, src, slug="test-company", name="Test Company", summary="Fake company.")
        db.add(m.CompanyRole(company_id=co.id, role_id=role1.id, careers_url="https://example.org/careers",
                             last_verified=date.today()))
        db.commit()
        return {"src": src.id, "bcom": bcom.slug, "btech": btech.slug, "s1": s1.slug, "s2": s2.slug,
                "skill": skill.slug, "role1": role1.slug, "role2": role2.slug,
                "req_ids": [r.id for r in reqs], "role1_id": role1.id}
