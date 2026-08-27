import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from fetch_mdrs_reports import parse_reports, load_manifest, save_manifest

FIXTURES = Path(__file__).parent / "fixtures"


def test_parse_reports_extracts_title_url_and_body():
    html = (FIXTURES / "mdrs_archive_page_sample.html").read_text()
    reports = parse_reports(html, page_number=42)

    assert len(reports) == 2

    first = reports[0]
    assert first["title"] == "GreenHab Report – Sample Day A"
    assert first["url"] == "https://reports.marssociety.org/2026/01/01/greenhab-report-sample-a/"
    assert "placeholder report body text" in first["raw_html"]
    assert first["page_number"] == 42

    second = reports[1]
    assert second["title"] == "EVA Report – Sample Day B"
    assert second["url"] == "https://reports.marssociety.org/2026/01/01/eva-report-sample-b/"


def test_parse_reports_returns_empty_list_when_no_articles():
    html = "<main id=\"main\"></main>"
    assert parse_reports(html, page_number=1) == []


def test_load_manifest_returns_empty_dict_when_file_does_not_exist(tmp_path):
    manifest_path = tmp_path / "manifest.json"
    assert load_manifest(manifest_path) == {}


def test_save_then_load_manifest_round_trips(tmp_path):
    manifest_path = tmp_path / "manifest.json"
    data = {"1": {"status": "fetched", "report_count": 10}}
    save_manifest(manifest_path, data)

    assert json.loads(manifest_path.read_text()) == data
    assert load_manifest(manifest_path) == data
