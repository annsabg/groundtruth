import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from validate import validate_file, validate_directory, check_references

FIXTURES = Path(__file__).parent / "fixtures"
SCHEMA = Path(__file__).parent.parent / "schema"


def test_validate_file_valid_returns_no_errors():
    errors = validate_file(FIXTURES / "generic.schema.json", FIXTURES / "valid_generic.json")
    assert errors == []


def test_validate_file_invalid_returns_errors():
    errors = validate_file(FIXTURES / "generic.schema.json", FIXTURES / "invalid_generic.json")
    assert len(errors) == 1
    assert "count" in errors[0]


def test_validate_directory_reports_only_invalid_files():
    results = validate_directory(FIXTURES / "generic.schema.json", FIXTURES, pattern="*_generic.json")
    assert "invalid_generic.json" in results
    assert "valid_generic.json" not in results


def test_check_references_detects_orphaned_mission_id(tmp_path):
    import json
    data_dir = tmp_path / "data"
    for sub in ["missions", "events", "crew_members", "research_projects", "sources"]:
        (data_dir / sub).mkdir(parents=True)
    (data_dir / "missions" / "m1.json").write_text(json.dumps({"mission_id": "M1"}))
    (data_dir / "events" / "e1.json").write_text(
        json.dumps({"event_id": "E1", "mission_id": "M2", "related_events": []})
    )  # M2 doesn't exist anywhere

    errors = check_references(data_dir)
    assert any("M2" in e for e in errors)


def test_check_references_accepts_valid_cross_references(tmp_path):
    import json
    data_dir = tmp_path / "data"
    for sub in ["missions", "events", "crew_members", "research_projects", "sources"]:
        (data_dir / sub).mkdir(parents=True)
    (data_dir / "missions" / "m1.json").write_text(json.dumps({"mission_id": "M1"}))
    (data_dir / "events" / "e1.json").write_text(
        json.dumps({"event_id": "E1", "mission_id": "M1", "related_events": []})
    )
    (data_dir / "events" / "e2.json").write_text(
        json.dumps({"event_id": "E2", "mission_id": "M1", "related_events": ["E1"]})
    )

    errors = check_references(data_dir)
    assert errors == []


def test_check_references_detects_orphaned_principal_investigator(tmp_path):
    import json
    data_dir = tmp_path / "data"
    for sub in ["missions", "events", "crew_members", "research_projects", "sources"]:
        (data_dir / sub).mkdir(parents=True)
    (data_dir / "missions" / "m1.json").write_text(json.dumps({"mission_id": "M1"}))
    (data_dir / "research_projects" / "rp1.json").write_text(
        json.dumps({
            "research_project_id": "RP1",
            "mission_ids": ["M1"],
            "principal_investigators": ["M1-CM99"],  # crew_member_id-shaped, doesn't resolve
        })
    )

    errors = check_references(data_dir)
    assert any("M1-CM99" in e for e in errors)


def test_check_references_accepts_valid_principal_investigator(tmp_path):
    import json
    data_dir = tmp_path / "data"
    for sub in ["missions", "events", "crew_members", "research_projects", "sources"]:
        (data_dir / sub).mkdir(parents=True)
    (data_dir / "missions" / "m1.json").write_text(json.dumps({"mission_id": "M1"}))
    (data_dir / "crew_members" / "cm1.json").write_text(
        json.dumps({"crew_member_id": "M1-CM01", "mission_id": "M1"})
    )
    (data_dir / "research_projects" / "rp1.json").write_text(
        json.dumps({
            "research_project_id": "RP1",
            "mission_ids": ["M1"],
            "principal_investigators": ["M1-CM01"],
        })
    )

    errors = check_references(data_dir)
    assert errors == []


def test_check_references_ignores_non_crew_member_shaped_principal_investigator(tmp_path):
    # External researchers (not represented as Crew Member records) aren't
    # flagged just because they aren't in crew_member_ids — only values that
    # actually look like a crew_member_id reference are checked.
    import json
    data_dir = tmp_path / "data"
    for sub in ["missions", "events", "crew_members", "research_projects", "sources"]:
        (data_dir / sub).mkdir(parents=True)
    (data_dir / "missions" / "m1.json").write_text(json.dumps({"mission_id": "M1"}))
    (data_dir / "research_projects" / "rp1.json").write_text(
        json.dumps({
            "research_project_id": "RP1",
            "mission_ids": ["M1"],
            "principal_investigators": ["Some External Researcher"],
        })
    )

    errors = check_references(data_dir)
    assert errors == []


def test_check_references_detects_orphaned_event_source_id(tmp_path):
    import json
    data_dir = tmp_path / "data"
    for sub in ["missions", "events", "crew_members", "research_projects", "sources"]:
        (data_dir / sub).mkdir(parents=True)
    (data_dir / "missions" / "m1.json").write_text(json.dumps({"mission_id": "M1"}))
    (data_dir / "events" / "e1.json").write_text(
        json.dumps({"event_id": "E1", "mission_id": "M1", "source_id": "SRC-nonexistent"})
    )

    errors = check_references(data_dir)
    assert any("SRC-nonexistent" in e for e in errors)


def test_check_references_accepts_valid_event_source_id(tmp_path):
    import json
    data_dir = tmp_path / "data"
    for sub in ["missions", "events", "crew_members", "research_projects", "sources"]:
        (data_dir / sub).mkdir(parents=True)
    (data_dir / "missions" / "m1.json").write_text(json.dumps({"mission_id": "M1"}))
    (data_dir / "sources" / "s1.json").write_text(json.dumps({"source_id": "SRC-real"}))
    (data_dir / "events" / "e1.json").write_text(
        json.dumps({"event_id": "E1", "mission_id": "M1", "source_id": "SRC-real"})
    )

    errors = check_references(data_dir)
    assert errors == []


def test_mission_schema_accepts_valid_record():
    errors = validate_file(SCHEMA / "mission.schema.json", FIXTURES / "valid_mission.json")
    assert errors == []


def test_mission_schema_rejects_invalid_record():
    errors = validate_file(SCHEMA / "mission.schema.json", FIXTURES / "invalid_mission.json")
    assert len(errors) >= 1


def test_mission_schema_rejects_malformed_date():
    # Regression test for the format_checker gap found during planning:
    # without it, this passes silently instead of failing.
    import json
    record = json.loads((FIXTURES / "valid_mission.json").read_text())
    record["start_date"] = "not-a-date"
    bad_path = FIXTURES / "_tmp_bad_date_mission.json"
    bad_path.write_text(json.dumps(record))
    try:
        errors = validate_file(SCHEMA / "mission.schema.json", bad_path)
        assert len(errors) >= 1
        assert any("date" in e.lower() or "format" in e.lower() for e in errors)
    finally:
        bad_path.unlink()


def test_crew_member_schema_accepts_valid_record():
    errors = validate_file(SCHEMA / "crew_member.schema.json", FIXTURES / "valid_crew_member.json")
    assert errors == []


def test_crew_member_schema_rejects_invalid_record():
    errors = validate_file(SCHEMA / "crew_member.schema.json", FIXTURES / "invalid_crew_member.json")
    assert len(errors) >= 1


def test_crew_member_schema_accepts_undisclosed_age():
    # Public crew bios rarely state exact age — this is the escape hatch,
    # matching the pattern gender/nationality already use.
    import json
    record = json.loads((FIXTURES / "valid_crew_member.json").read_text())
    record["age"] = "undisclosed"
    tmp_path = FIXTURES / "_tmp_undisclosed_age.json"
    tmp_path.write_text(json.dumps(record))
    try:
        errors = validate_file(SCHEMA / "crew_member.schema.json", tmp_path)
        assert errors == []
    finally:
        tmp_path.unlink()


def test_event_schema_accepts_valid_record():
    errors = validate_file(SCHEMA / "event.schema.json", FIXTURES / "valid_event.json")
    assert errors == []


def test_event_schema_rejects_invalid_record():
    errors = validate_file(SCHEMA / "event.schema.json", FIXTURES / "invalid_event.json")
    assert len(errors) >= 1


def test_research_project_schema_accepts_valid_record():
    errors = validate_file(SCHEMA / "research_project.schema.json", FIXTURES / "valid_research_project.json")
    assert errors == []


def test_research_project_schema_rejects_invalid_record():
    errors = validate_file(SCHEMA / "research_project.schema.json", FIXTURES / "invalid_research_project.json")
    assert len(errors) >= 1


def test_source_schema_accepts_valid_record():
    errors = validate_file(SCHEMA / "source.schema.json", FIXTURES / "valid_source.json")
    assert errors == []


def test_source_schema_rejects_invalid_record():
    errors = validate_file(SCHEMA / "source.schema.json", FIXTURES / "invalid_source.json")
    assert len(errors) >= 1
