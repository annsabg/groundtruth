#!/usr/bin/env python3
"""Validate JSON records against a JSON Schema file.

Usage:
    python scripts/validate.py <schema.json> <file_or_directory>

Exits 0 if everything validates, 1 otherwise (with errors printed).
"""
import json
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


def main():
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <schema.json> <file_or_directory>", file=sys.stderr)
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
