import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from validate import validate_file, validate_directory

FIXTURES = Path(__file__).parent / "fixtures"


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
