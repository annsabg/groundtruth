import json
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from build_db import ENTITIES, build_database

FIXTURES = Path(__file__).parent / "fixtures"
SCHEMA = Path(__file__).parent.parent / "schema"

# entity name -> schema file, so a schema field change is caught even if
# nobody remembers to update ENTITIES in build_db.py to match.
SCHEMA_FILES = {
    "mission": "mission.schema.json",
    "crew_member": "crew_member.schema.json",
    "event": "event.schema.json",
    "research_project": "research_project.schema.json",
    "source": "source.schema.json",
}


def _write_fixture_data_dir(tmp_path):
    """Set up a minimal data/ tree from the existing test fixtures."""
    data_dir = tmp_path / "data"
    mapping = {
        "missions": "valid_mission.json",
        "crew_members": "valid_crew_member.json",
        "events": "valid_event.json",
        "research_projects": "valid_research_project.json",
        "sources": "valid_source.json",
    }
    for subdir, fixture_name in mapping.items():
        target_dir = data_dir / subdir
        target_dir.mkdir(parents=True)
        content = json.loads((FIXTURES / fixture_name).read_text())
        (target_dir / f"{fixture_name}").write_text(json.dumps(content))
    return data_dir


def test_build_database_creates_sqlite_with_all_tables(tmp_path):
    data_dir = _write_fixture_data_dir(tmp_path)
    output_path = tmp_path / "groundtruth.sqlite"

    build_database(str(data_dir), str(output_path))

    assert output_path.exists()
    conn = sqlite3.connect(output_path)
    tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert tables == {"mission", "crew_member", "event", "research_project", "source"}
    conn.close()


def test_build_database_inserts_correct_row_data(tmp_path):
    data_dir = _write_fixture_data_dir(tmp_path)
    output_path = tmp_path / "groundtruth.sqlite"

    build_database(str(data_dir), str(output_path))

    conn = sqlite3.connect(output_path)
    row = conn.execute("SELECT mission_id, crew_size FROM mission").fetchone()
    assert row == ("FMARS-C16-2024", 7)

    row = conn.execute("SELECT event_id, significance FROM event").fetchone()
    assert row == ("FMARS-C16-2024-EVT001", "High")
    conn.close()


def test_entities_columns_match_schema_properties():
    # Guards against schema drift: if a schema gains (or loses) a field but
    # ENTITIES in build_db.py isn't updated to match, that field would
    # silently vanish from the database (or a stale column would silently
    # persist) with no error. This catches drift in either direction.
    for entity, schema_filename in SCHEMA_FILES.items():
        schema = json.loads((SCHEMA / schema_filename).read_text())
        schema_fields = set(schema["properties"].keys())
        entity_columns = set(ENTITIES[entity][1])
        assert entity_columns == schema_fields, (
            f"{entity}: ENTITIES columns {entity_columns} != "
            f"schema properties {schema_fields} "
            f"(diff: only in ENTITIES={entity_columns - schema_fields}, "
            f"only in schema={schema_fields - entity_columns})"
        )


def test_build_database_is_idempotent_overwrite(tmp_path):
    data_dir = _write_fixture_data_dir(tmp_path)
    output_path = tmp_path / "groundtruth.sqlite"

    build_database(str(data_dir), str(output_path))
    build_database(str(data_dir), str(output_path))  # run twice

    conn = sqlite3.connect(output_path)
    count = conn.execute("SELECT COUNT(*) FROM mission").fetchone()[0]
    assert count == 1  # not duplicated
    conn.close()
