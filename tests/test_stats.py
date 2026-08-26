import json
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from build_db import build_database
from stats import generate_stats

FIXTURES = Path(__file__).parent / "fixtures"


def _write_fixture_data_dir(tmp_path):
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
        (target_dir / fixture_name).write_text(json.dumps(content))
    return data_dir


def test_generate_stats_summarizes_the_dataset(tmp_path):
    data_dir = _write_fixture_data_dir(tmp_path)
    sqlite_path = tmp_path / "groundtruth.sqlite"
    build_database(str(data_dir), str(sqlite_path))

    summary = generate_stats(str(sqlite_path))

    assert "Missions: 1" in summary
    assert "Events: 1" in summary
    assert "Failure" in summary  # the event_type breakdown
    assert "Crew Members: 1" in summary
    assert "Research Projects: 1" in summary


def test_generate_stats_handles_empty_database(tmp_path):
    # Task 1's initial state — data/ exists but every subdir is empty.
    data_dir = tmp_path / "data"
    for sub in ["missions", "crew_members", "events", "research_projects", "sources"]:
        (data_dir / sub).mkdir(parents=True)
    sqlite_path = tmp_path / "groundtruth.sqlite"
    build_database(str(data_dir), str(sqlite_path))

    summary = generate_stats(str(sqlite_path))

    assert "Missions: 0" in summary
    assert "Events: 0" in summary


def test_generate_stats_flags_other_usage_as_vocabulary_drift_signal(tmp_path):
    data_dir = _write_fixture_data_dir(tmp_path)
    # Overwrite the mission fixture with one that uses the "Other" escape
    # hatch, to prove the drift signal actually fires.
    mission = json.loads((FIXTURES / "valid_mission.json").read_text())
    mission["stations"] = ["Other"]
    mission["stations_other_detail"] = "A hypothetical station not yet in the enum"
    (data_dir / "missions" / "valid_mission.json").write_text(json.dumps(mission))

    sqlite_path = tmp_path / "groundtruth.sqlite"
    build_database(str(data_dir), str(sqlite_path))

    summary = generate_stats(str(sqlite_path))

    assert "'Other' usage" in summary
    assert "mission.stations: 1" in summary
