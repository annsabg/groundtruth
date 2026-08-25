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
