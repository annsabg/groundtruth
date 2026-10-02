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


def test_check_references_detects_event_station_not_in_mission_stations(tmp_path):
    import json
    data_dir = tmp_path / "data"
    for sub in ["missions", "events", "crew_members", "research_projects", "sources"]:
        (data_dir / sub).mkdir(parents=True)
    (data_dir / "missions" / "m1.json").write_text(
        json.dumps({"mission_id": "M1", "stations": ["FMARS"]})
    )
    (data_dir / "events" / "e1.json").write_text(
        json.dumps({"event_id": "E1", "mission_id": "M1", "station": "MDRS"})
    )

    errors = check_references(data_dir)
    assert any("station" in e and "MDRS" in e for e in errors)


def test_check_references_accepts_event_station_in_mission_stations(tmp_path):
    import json
    data_dir = tmp_path / "data"
    for sub in ["missions", "events", "crew_members", "research_projects", "sources"]:
        (data_dir / sub).mkdir(parents=True)
    (data_dir / "missions" / "m1.json").write_text(
        json.dumps({"mission_id": "M1", "stations": ["FMARS", "MDRS"]})
    )
    (data_dir / "events" / "e1.json").write_text(
        json.dumps({"event_id": "E1", "mission_id": "M1", "station": "MDRS"})
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


def _equipment_variant(tmp_path, **changes):
    """Copy of the valid equipment fixture with fields changed; a value of
    None deletes the field. Returns the path of the written variant."""
    import json
    record = json.loads((FIXTURES / "valid_equipment_item.json").read_text())
    for key, value in changes.items():
        if value is None:
            record.pop(key, None)
        else:
            record[key] = value
    path = tmp_path / "variant.json"
    path.write_text(json.dumps(record))
    return path


def test_equipment_item_schema_accepts_valid_record():
    errors = validate_file(SCHEMA / "equipment_item.schema.json", FIXTURES / "valid_equipment_item.json")
    assert errors == []


def test_equipment_item_schema_rejects_invalid_record():
    errors = validate_file(SCHEMA / "equipment_item.schema.json", FIXTURES / "invalid_equipment_item.json")
    assert len(errors) >= 2  # bad area AND missing rationale


def test_equipment_item_schema_rejects_unknown_area(tmp_path):
    path = _equipment_variant(tmp_path, area="Hygiene")
    assert validate_file(SCHEMA / "equipment_item.schema.json", path) != []


def test_equipment_item_schema_rejects_unknown_advice_type(tmp_path):
    path = _equipment_variant(tmp_path, advice_type="Nice to Have")
    assert validate_file(SCHEMA / "equipment_item.schema.json", path) != []


def test_equipment_item_schema_rejects_missing_rationale(tmp_path):
    path = _equipment_variant(tmp_path, rationale=None)
    assert validate_file(SCHEMA / "equipment_item.schema.json", path) != []


def test_equipment_item_schema_rejects_malformed_item_key(tmp_path):
    for bad in ["Spare Comms", "spare_comms", "-spare", "spare--comms"]:
        path = _equipment_variant(tmp_path, item_key=bad)
        assert validate_file(SCHEMA / "equipment_item.schema.json", path) != [], bad


def test_equipment_item_schema_rejects_malformed_item_id(tmp_path):
    path = _equipment_variant(tmp_path, item_id="FMARS-C16-2024-EQ1")
    assert validate_file(SCHEMA / "equipment_item.schema.json", path) != []


def test_equipment_item_schema_accepts_record_without_optional_fields(tmp_path):
    path = _equipment_variant(tmp_path, item_key=None, related_events=None, source_id=None)
    assert validate_file(SCHEMA / "equipment_item.schema.json", path) == []


def test_equipment_item_schema_rejects_quantity_field(tmp_path):
    path = _equipment_variant(tmp_path, quantity=4)
    assert validate_file(SCHEMA / "equipment_item.schema.json", path) != []


def test_source_schema_accepts_equipment_in_covers(tmp_path):
    import json
    record = json.loads((FIXTURES / "valid_source.json").read_text())
    record["covers"] = ["events", "equipment"]
    path = tmp_path / "source.json"
    path.write_text(json.dumps(record))
    assert validate_file(SCHEMA / "source.schema.json", path) == []


def _refs_data_dir(tmp_path, equipment_record):
    """Minimal data/ tree: mission M1 at FMARS, event E1, source S1, plus
    one equipment item record."""
    import json
    data_dir = tmp_path / "data"
    for sub in ["missions", "events", "crew_members", "research_projects", "sources", "equipment_items"]:
        (data_dir / sub).mkdir(parents=True)
    (data_dir / "missions" / "m1.json").write_text(json.dumps({"mission_id": "M1", "stations": ["FMARS"]}))
    (data_dir / "events" / "e1.json").write_text(
        json.dumps({"event_id": "E1", "mission_id": "M1", "station": "FMARS", "related_events": []})
    )
    (data_dir / "sources" / "s1.json").write_text(json.dumps({"source_id": "S1", "mission_ids": ["M1"]}))
    (data_dir / "equipment_items" / "q1.json").write_text(json.dumps(equipment_record))
    return data_dir


_GOOD_EQUIPMENT = {
    "item_id": "M1-EQP001", "mission_id": "M1", "station": "FMARS",
    "source_id": "S1", "related_events": ["E1"],
}


def test_check_references_accepts_valid_equipment_item(tmp_path):
    assert check_references(_refs_data_dir(tmp_path, _GOOD_EQUIPMENT)) == []


def test_check_references_detects_equipment_item_orphaned_mission_id(tmp_path):
    errors = check_references(_refs_data_dir(tmp_path, {**_GOOD_EQUIPMENT, "mission_id": "M9", "station": None}))
    assert any("equipment_items/q1.json" in e and "M9" in e for e in errors)


def test_check_references_detects_equipment_item_orphaned_related_event(tmp_path):
    errors = check_references(_refs_data_dir(tmp_path, {**_GOOD_EQUIPMENT, "related_events": ["E1", "E7"]}))
    assert any("equipment_items/q1.json" in e and "E7" in e for e in errors)


def test_check_references_detects_equipment_item_orphaned_source_id(tmp_path):
    errors = check_references(_refs_data_dir(tmp_path, {**_GOOD_EQUIPMENT, "source_id": "S9"}))
    assert any("equipment_items/q1.json" in e and "S9" in e for e in errors)


def test_check_references_detects_equipment_item_station_not_in_mission_stations(tmp_path):
    errors = check_references(_refs_data_dir(tmp_path, {**_GOOD_EQUIPMENT, "station": "MDRS"}))
    assert any("equipment_items/q1.json" in e and "MDRS" in e for e in errors)


def test_check_references_tolerates_missing_equipment_items_dir(tmp_path):
    import json
    data_dir = tmp_path / "data"
    for sub in ["missions", "events", "crew_members", "research_projects", "sources"]:
        (data_dir / sub).mkdir(parents=True)
    (data_dir / "missions" / "m1.json").write_text(json.dumps({"mission_id": "M1"}))
    assert check_references(data_dir) == []
