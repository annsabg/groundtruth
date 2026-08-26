#!/usr/bin/env python3
"""Compile all JSON records under data/ into a single queryable SQLite file.

Usage:
    python scripts/build_db.py [data_dir] [output_path]

Defaults: data_dir=data, output_path=groundtruth.sqlite
"""
import json
import sqlite3
import sys
from pathlib import Path

# entity name -> (data subdirectory, table columns in insertion order)
ENTITIES = {
    "mission": (
        "missions",
        ["mission_id", "stations", "stations_other_detail", "crew_designation",
         "institutional_or_volunteer", "start_date", "end_date", "location",
         "mission_goal", "crew_size", "source_citation", "verified_by"],
    ),
    "crew_member": (
        "crew_members",
        ["crew_member_id", "mission_id", "primary_role", "secondary_roles", "gender",
         "nationality", "age", "field_of_expertise", "source_citation", "verified_by"],
    ),
    "event": (
        "events",
        ["event_id", "mission_id", "sol", "event_type", "system_category", "significance",
         "description", "response", "lesson", "pattern_tag", "outcome", "related_events",
         "confidence", "source_id", "source_citation", "verified_by"],
    ),
    "research_project": (
        "research_projects",
        ["research_project_id", "mission_ids", "domain", "title", "principal_investigators",
         "sample_size", "duration", "methods", "instruments", "key_findings",
         "publication_status", "citation", "comparable_studies", "methodology_notes",
         "verified_by"],
    ),
    "source": (
        "sources",
        ["source_id", "mission_ids", "url_or_reference", "source_type", "covers",
         "date_range_or_sols", "discovery_method", "approved_by", "approved_date"],
    ),
}

# Columns whose value is a list/object and must be JSON-encoded as TEXT.
COMPLEX_COLUMNS = {
    "stations", "secondary_roles", "field_of_expertise", "related_events",
    "mission_ids", "principal_investigators", "sample_size", "instruments",
    "comparable_studies", "covers",
}

# Columns that must be declared INTEGER, not TEXT. This matters: SQLite's
# TEXT-affinity columns silently coerce bound integer values to the TEXT
# storage class on insert (verified directly — INSERT 7 into a TEXT column,
# SELECT it back, get '7' not 7). Declaring these as INTEGER keeps them
# actual integers on round-trip.
INTEGER_COLUMNS = {"crew_size", "sol", "age"}


def _create_tables(conn):
    for table, (_, columns) in ENTITIES.items():
        col_defs = ", ".join(
            f'"{c}" {"INTEGER" if c in INTEGER_COLUMNS else "TEXT"}' for c in columns
        )
        conn.execute(f'CREATE TABLE IF NOT EXISTS "{table}" ({col_defs})')


def _load_records(data_dir, subdir):
    records = []
    dir_path = Path(data_dir) / subdir
    if not dir_path.exists():
        return records
    for json_path in sorted(dir_path.glob("*.json")):
        records.append(json.loads(json_path.read_text()))
    return records


def build_database(data_dir="data", output_path="groundtruth.sqlite"):
    output = Path(output_path)
    if output.exists():
        output.unlink()  # rebuild from scratch every time — never a stale partial DB

    conn = sqlite3.connect(output)
    _create_tables(conn)

    for table, (subdir, columns) in ENTITIES.items():
        records = _load_records(data_dir, subdir)
        for record in records:
            values = []
            for col in columns:
                value = record.get(col)
                if col in COMPLEX_COLUMNS and value is not None:
                    value = json.dumps(value)
                values.append(value)
            placeholders = ", ".join("?" for _ in columns)
            col_names = ", ".join(f'"{c}"' for c in columns)
            conn.execute(f'INSERT INTO "{table}" ({col_names}) VALUES ({placeholders})', values)

    conn.commit()
    conn.close()


def main():
    data_dir = sys.argv[1] if len(sys.argv) > 1 else "data"
    output_path = sys.argv[2] if len(sys.argv) > 2 else "groundtruth.sqlite"
    build_database(data_dir, output_path)
    print(f"Built {output_path} from {data_dir}/")


if __name__ == "__main__":
    main()
