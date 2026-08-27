import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import requests

from fetch_mdrs_reports import parse_reports, load_manifest, save_manifest, fetch_page, save_page

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


class FakeResponse:
    def __init__(self, status_code, text=""):
        self.status_code = status_code
        self.text = text


class FakeSession:
    """Returns canned responses/exceptions in order, one per .get() call —
    lets tests exercise fetch_page's retry logic without a real network
    call or a real sleep."""
    def __init__(self, results):
        self.results = list(results)
        self.calls = []

    def get(self, url, timeout=None):
        self.calls.append(url)
        result = self.results.pop(0)
        if isinstance(result, Exception):
            raise result
        return result


def test_fetch_page_returns_text_on_first_success(monkeypatch):
    monkeypatch.setattr("fetch_mdrs_reports.time.sleep", lambda seconds: None)
    session = FakeSession([FakeResponse(200, "<html>ok</html>")])
    assert fetch_page("http://example.test/x", session) == "<html>ok</html>"
    assert len(session.calls) == 1


def test_fetch_page_returns_none_immediately_on_404(monkeypatch):
    monkeypatch.setattr("fetch_mdrs_reports.time.sleep", lambda seconds: None)
    session = FakeSession([FakeResponse(404)])
    assert fetch_page("http://example.test/x", session) is None
    assert len(session.calls) == 1  # no retries for a real 404


def test_fetch_page_retries_transient_failures_then_succeeds(monkeypatch):
    monkeypatch.setattr("fetch_mdrs_reports.time.sleep", lambda seconds: None)
    session = FakeSession([
        requests.RequestException("boom"),
        requests.RequestException("boom again"),
        FakeResponse(200, "<html>recovered</html>"),
    ])
    assert fetch_page("http://example.test/x", session) == "<html>recovered</html>"
    assert len(session.calls) == 3


def test_fetch_page_returns_none_after_exhausting_retries(monkeypatch):
    monkeypatch.setattr("fetch_mdrs_reports.time.sleep", lambda seconds: None)
    session = FakeSession([
        requests.RequestException("boom"),
        requests.RequestException("boom"),
        requests.RequestException("boom"),
    ])
    assert fetch_page("http://example.test/x", session) is None
    assert len(session.calls) == 3  # MAX_RETRIES, no more


def test_save_page_writes_html_and_reports_json(tmp_path):
    reports = [{"title": "T", "url": "http://x", "raw_html": "<p>x</p>", "page_number": 7}]
    save_page(tmp_path, 7, "<html>full page</html>", reports)

    html_file = tmp_path / "page-0007.html"
    reports_file = tmp_path / "page-0007-reports.json"
    assert html_file.read_text() == "<html>full page</html>"
    assert json.loads(reports_file.read_text()) == reports


def test_save_page_creates_output_dir_if_missing(tmp_path):
    output_dir = tmp_path / "does-not-exist-yet"
    save_page(output_dir, 1, "<html></html>", [])
    assert (output_dir / "page-0001.html").exists()
