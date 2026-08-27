#!/usr/bin/env python3
"""Mechanically fetch and split MDRS crew-report archive pages into local,
gitignored per-report files.

This script does NOT interpret report content — it extracts only what the
site's own HTML markup structurally guarantees (title, permalink URL, raw
body HTML), never dates/sol/crew#/author parsed out of the body text
itself. Turning a report into a Mission/Event/Crew Member record is Stage 2
of the extraction pipeline, run by Claude Code, not scripted here. See
docs/superpowers/specs/2026-08-25-groundtruth-extraction-pipeline-design.md
§10 for why.

Usage:
    python scripts/fetch_mdrs_reports.py <start_page> <end_page> [output_dir]

Defaults: output_dir=sources-local/mdrs-crew-reports-raw
"""
import json
import sys
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://reports.marssociety.org/crew-reports/page/{page}/"

# robots.txt: Crawl-delay: 10 — non-negotiable, never lowered, not a flag.
CRAWL_DELAY_SECONDS = 10

USER_AGENT = (
    "GroundtruthProjectBot/0.1 (+https://github.com/annsabg/groundtruth; "
    "research/archival use for the Groundtruth analog-mission registry)"
)

MAX_RETRIES = 3


def parse_reports(html, page_number):
    """Split one archive page's HTML into individual report dicts. Only
    extracts what WordPress's own markup guarantees — title, permalink
    URL, and body HTML — never dates/crew/sol/author parsed out of the
    body text itself; that's free text a human typed into a template, not
    structured markup, and interpreting it is Stage 2's job, not this
    script's."""
    soup = BeautifulSoup(html, "html.parser")
    reports = []
    for article in soup.select("article.type-post"):
        title_link = article.select_one("h2.entry-title a")
        content = article.select_one("div.entry-content")
        if title_link is None or content is None:
            continue
        reports.append({
            "title": title_link.get_text(strip=True),
            "url": title_link.get("href"),
            "raw_html": str(content),
            "page_number": page_number,
        })
    return reports


def load_manifest(manifest_path):
    if manifest_path.exists():
        return json.loads(manifest_path.read_text())
    return {}


def save_manifest(manifest_path, manifest):
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True))


def fetch_page(url, session):
    """Fetch one page's HTML, retrying transient failures with exponential
    backoff (1s, 2s, 4s). Returns the response text, or None if the page
    doesn't exist (404 — the archive's actual end, not a transient
    failure) or every retry failed."""
    for attempt in range(MAX_RETRIES):
        try:
            response = session.get(url, timeout=30)
        except requests.RequestException:
            if attempt < MAX_RETRIES - 1:
                time.sleep(2 ** attempt)
            continue
        if response.status_code == 200:
            return response.text
        if response.status_code == 404:
            return None
        if attempt < MAX_RETRIES - 1:
            time.sleep(2 ** attempt)
    return None


def save_page(output_dir, page_number, html, reports):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / f"page-{page_number:04d}.html").write_text(html)
    (output_dir / f"page-{page_number:04d}-reports.json").write_text(
        json.dumps(reports, indent=2)
    )


def main():
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} <start_page> <end_page> [output_dir]", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
