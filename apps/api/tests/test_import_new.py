"""The importer loads the new entity types as drafts, from CSV or JSON, with typed columns."""
import json

from sqlalchemy import select

from app import cli, models as m
from .factories import make_user, session


def test_json_and_csv_imports_create_drafts_with_typed_fields(tmp_path):
    make_user("editor@example.org", m.UserRole.editor)
    scen = [{"slug": "imp-sc", "title": "Imported", "pillar": "case", "brief": "b", "dimensions": ["ethics"], "difficulty": 1, "minutes": 5,
             "nodes": [{"key": "a", "text": "t", "end": True, "debrief": "d"}], "source_url": "https://example.org/imp", "source_title": "S",
             "source_publisher": "P", "source_kind": "official"}]
    jf = tmp_path / "scenarios.json"
    jf.write_text(json.dumps(scen))
    assert cli.import_csv("scenarios", str(jf), "editor@example.org") == 1
    cf = tmp_path / "opps.csv"
    cf.write_text("slug,title,organisation,kind,description,eligibility,apply_url,deadline,rolling,min_year,streams,source_url\n"
                  "imp-op,Intern,Org,internship,d,e,https://example.org/a,2027-01-31,false,2,Engineering;Science,https://example.org/imp\n",
                  encoding="utf-8")
    assert cli.import_csv("opportunities", str(cf), "editor@example.org") == 1
    with session() as db:
        sc = db.scalar(select(m.Scenario))
        op = db.scalar(select(m.Opportunity))
        assert sc.status == m.Status.draft and sc.nodes[0]["key"] == "a"
        assert op.status == m.Status.draft and op.streams == ["Engineering", "Science"] and op.min_year == 2 and op.rolling is False
        assert op.deadline.isoformat() == "2027-01-31"
