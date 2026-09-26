import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from summarize_drafts import (
    truncate,
    format_source,
    format_mission,
    format_crew_member,
    format_event,
    format_research_project,
    summarize_directory,
)


def test_truncate_leaves_short_text_untouched():
    assert truncate("short", 140) == "short"


def test_truncate_cuts_long_text_and_marks_it():
    text = "a" * 200
    result = truncate(text, 140)
    assert len(result) == 143  # 140 chars + "..."
    assert result.endswith("...")


def test_truncate_does_not_break_a_word_mid_way():
    text = "one two three four five six seven eight nine ten"
    result = truncate(text, 20)
    assert not result.rstrip(".").endswith(("o", "t", "f", "s", "n"))  # crude: no mid-word cut check below
    assert result.endswith("...")
    # the word right before the ellipsis should be whole, i.e. present in the original text as a token
    last_word = result[:-3].rstrip().split(" ")[-1]
    assert last_word in text.split(" ")


def test_format_source_is_one_line():
    record = {
        "source_id": "SRC-test",
        "source_type": "crew_blog",
        "covers": ["events", "crew"],
        "url_or_reference": "https://example.com/reports",
    }
    line = format_source(record)
    assert "\n" not in line
    assert "SRC-test" in line
    assert "crew_blog" in line
    assert "events" in line and "crew" in line


def test_format_mission_includes_key_facts():
    record = {
        "mission_id": "FMARS-TEST-2026",
        "crew_designation": "Crew Test",
        "stations": ["FMARS"],
        "start_date": "2026-01-01",
        "end_date": "2026-01-10",
        "crew_size": 4,
    }
    line = format_mission(record)
    assert "FMARS-TEST-2026" in line
    assert "Crew Test" in line
    assert "2026-01-01" in line and "2026-01-10" in line
    assert "4" in line


def test_format_crew_member_includes_role_and_expertise():
    record = {
        "crew_member_id": "FMARS-TEST-2026-CM01",
        "primary_role": "Commander",
        "gender": "male",
        "nationality": "undisclosed",
        "age": "undisclosed",
        "field_of_expertise": {"category": "Engineering", "detail": "Some very long detail " * 20},
    }
    line = format_crew_member(record)
    assert "FMARS-TEST-2026-CM01" in line
    assert "Commander" in line
    assert "Engineering" in line
    assert "\n" not in line


def test_format_event_includes_sol_category_and_outcome():
    record = {
        "event_id": "FMARS-TEST-2026-EVT001",
        "sol": 3,
        "system_category": "Power",
        "event_type": "Failure",
        "significance": "High",
        "description": "The generator stopped working.",
        "outcome": "Resolved",
    }
    line = format_event(record)
    assert "EVT001" in line
    assert "Sol 3" in line
    assert "Power" in line and "Failure" in line and "High" in line
    assert "Resolved" in line


def test_format_event_handles_missing_outcome_gracefully():
    record = {
        "event_id": "FMARS-TEST-2026-EVT002",
        "sol": 1,
        "system_category": "Water",
        "event_type": "Observation",
        "significance": "Low",
        "description": "Something was observed.",
    }
    line = format_event(record)
    assert "EVT002" in line
    assert "\n" not in line


def test_format_research_project_includes_title_and_domain():
    record = {
        "research_project_id": "RP-999",
        "title": "A Study of Things",
        "domain": "Psychology",
        "principal_investigators": ["FMARS-TEST-2026-CM02"],
        "publication_status": "Unpublished",
    }
    line = format_research_project(record)
    assert "RP-999" in line
    assert "A Study of Things" in line
    assert "Psychology" in line


def test_summarize_directory_groups_by_entity_type_and_sorts_within_group(tmp_path):
    (tmp_path / "missions").mkdir()
    (tmp_path / "events").mkdir()

    (tmp_path / "missions" / "FMARS-TEST-2026.json").write_text(json.dumps({
        "mission_id": "FMARS-TEST-2026", "crew_designation": "Crew Test",
        "stations": ["FMARS"], "start_date": "2026-01-01", "end_date": "2026-01-10",
        "crew_size": 4,
    }))
    (tmp_path / "events" / "FMARS-TEST-2026-EVT002.json").write_text(json.dumps({
        "event_id": "FMARS-TEST-2026-EVT002", "sol": 2, "system_category": "Water",
        "event_type": "Observation", "significance": "Low", "description": "b",
    }))
    (tmp_path / "events" / "FMARS-TEST-2026-EVT001.json").write_text(json.dumps({
        "event_id": "FMARS-TEST-2026-EVT001", "sol": 1, "system_category": "Power",
        "event_type": "Failure", "significance": "High", "description": "a",
    }))

    report = summarize_directory(tmp_path)

    assert "MISSIONS" in report.upper()
    assert "EVENTS" in report.upper()
    # events sorted by filename (EVT001 before EVT002) regardless of dict insertion order
    assert report.index("EVT001") < report.index("EVT002")


def test_summarize_directory_skips_entity_types_with_no_files(tmp_path):
    (tmp_path / "missions").mkdir()
    (tmp_path / "missions" / "FMARS-TEST-2026.json").write_text(json.dumps({
        "mission_id": "FMARS-TEST-2026", "crew_designation": "Crew Test",
        "stations": ["FMARS"], "start_date": "2026-01-01", "end_date": "2026-01-10",
        "crew_size": 4,
    }))

    report = summarize_directory(tmp_path)
    assert "EVENTS" not in report.upper()
