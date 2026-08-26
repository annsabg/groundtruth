#!/usr/bin/env python3
"""Validate JSON records against a JSON Schema file.

Usage:
    python scripts/validate.py <schema.json> <file_or_directory>

Exits 0 if everything validates, 1 otherwise (with errors printed).
"""
import json
import re
import sys
from pathlib import Path

import jsonschema


def validate_file(schema_path, json_path) -> list[str]:
    """Validate one JSON file against one schema. Returns a list of
    human-readable error strings; empty list means valid."""
    schema = json.loads(Path(schema_path).read_text())
    data = json.loads(Path(json_path).read_text())
    # format_checker is required — jsonschema does NOT enforce "format": "date"
    # (or any format keyword) by default, silently. Verified empirically during
    # planning: without this, a garbage string like "not-a-date" passes validation.
    validator = jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker())
    errors = sorted(validator.iter_errors(data), key=lambda e: e.path)
    return [f"{'/'.join(str(p) for p in e.path) or '(root)'}: {e.message}" for e in errors]


def validate_directory(schema_path, dir_path, pattern="*.json") -> dict[str, list[str]]:
    """Validate every JSON file in a directory (non-recursive) matching
    `pattern` against one schema. Returns {filename: [errors]} only for
    files that have errors."""
    results = {}
    for json_path in sorted(Path(dir_path).glob(pattern)):
        errors = validate_file(schema_path, json_path)
        if errors:
            results[json_path.name] = errors
    return results


CREW_MEMBER_ID_LIKE = re.compile(r".+-CM\d{2}$")


def check_references(data_dir) -> list[str]:
    """Cross-file referential-integrity check: does every ID referenced from
    one record (mission_id, related_events, comparable_studies, mission_ids,
    principal_investigators) actually resolve to a record with that ID
    committed under data/? Schema validation alone can't catch this — these
    fields are typed as plain strings, not real foreign keys. Returns a list
    of human-readable error strings; empty means every cross-reference
    resolves."""
    data_dir = Path(data_dir)

    def _ids(subdir, id_field):
        ids = set()
        for p in (data_dir / subdir).glob("*.json"):
            record = json.loads(p.read_text())
            if id_field in record:
                ids.add(record[id_field])
        return ids

    mission_ids = _ids("missions", "mission_id")
    event_ids = _ids("events", "event_id")
    research_ids = _ids("research_projects", "research_project_id")
    crew_member_ids = _ids("crew_members", "crew_member_id")

    errors = []

    def _check(subdir, filename, field, value, valid_ids, label):
        if value not in valid_ids:
            errors.append(f"{subdir}/{filename}: {field} '{value}' does not resolve to any committed {label}")

    for subdir in ("crew_members", "events"):
        for p in (data_dir / subdir).glob("*.json"):
            record = json.loads(p.read_text())
            value = record.get("mission_id")
            if value is not None:
                _check(subdir, p.name, "mission_id", value, mission_ids, "Mission")

    for subdir in ("research_projects", "sources"):
        for p in (data_dir / subdir).glob("*.json"):
            record = json.loads(p.read_text())
            for value in record.get("mission_ids") or []:
                _check(subdir, p.name, "mission_ids", value, mission_ids, "Mission")

    for p in (data_dir / "events").glob("*.json"):
        record = json.loads(p.read_text())
        for value in record.get("related_events") or []:
            _check("events", p.name, "related_events", value, event_ids, "Event")

    for p in (data_dir / "research_projects").glob("*.json"):
        record = json.loads(p.read_text())
        for value in record.get("comparable_studies") or []:
            _check("research_projects", p.name, "comparable_studies", value, research_ids, "Research Project")

    # principal_investigators isn't a strict foreign key: some PIs are
    # external researchers with no Crew Member record. Only flag a value
    # that LOOKS like it's trying to be a crew_member_id (matches the
    # {mission_id}-CM{NN} format) but doesn't resolve — that's a typo'd
    # reference, not a plain external-researcher name.
    for p in (data_dir / "research_projects").glob("*.json"):
        record = json.loads(p.read_text())
        for value in record.get("principal_investigators") or []:
            if CREW_MEMBER_ID_LIKE.match(value) and value not in crew_member_ids:
                errors.append(
                    f"research_projects/{p.name}: principal_investigators '{value}' "
                    f"looks like a crew_member_id but does not resolve to any committed Crew Member"
                )

    return errors


def main():
    if len(sys.argv) == 3 and sys.argv[1] == "--check-refs":
        errors = check_references(sys.argv[2])
        if not errors:
            print("All cross-references resolve.")
            sys.exit(0)
        for err in errors:
            print(f"  - {err}")
        sys.exit(1)

    if len(sys.argv) != 3:
        print(
            f"Usage: {sys.argv[0]} <schema.json> <file_or_directory>\n"
            f"   or: {sys.argv[0]} --check-refs <data_dir>",
            file=sys.stderr,
        )
        sys.exit(2)

    schema_path = Path(sys.argv[1])
    target = Path(sys.argv[2])

    if target.is_dir():
        results = validate_directory(schema_path, target)
        if not results:
            print(f"All files in {target} valid against {schema_path.name}.")
            sys.exit(0)
        for filename, errors in results.items():
            print(f"{filename}:")
            for err in errors:
                print(f"  - {err}")
        sys.exit(1)
    else:
        errors = validate_file(schema_path, target)
        if not errors:
            print(f"{target.name} valid against {schema_path.name}.")
            sys.exit(0)
        print(f"{target.name}:")
        for err in errors:
            print(f"  - {err}")
        sys.exit(1)


if __name__ == "__main__":
    main()
