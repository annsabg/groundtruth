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
from datetime import datetime, timezone
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


class _NotFound:
    """Sentinel distinguishing a real 404 (the page doesn't exist — a
    permanent condition) from a fetch that failed after exhausting
    retries (transient — worth retrying on a future resume). The two
    need different manifest treatment; see crawl()."""
    def __repr__(self):
        return "NOT_FOUND"


NOT_FOUND = _NotFound()


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
    """Fetch one page's HTML, retrying transient failures. Sleeps at
    least CRAWL_DELAY_SECONDS between attempts — robots.txt's Crawl-delay
    is a floor on requests to this host generally, not just between
    pages, so a fast-failing retry (e.g. connection refused) must not
    re-hit the server sooner than that even though 2**attempt alone
    would allow it. In practice, with MAX_RETRIES=3, this means every
    retry sleeps exactly CRAWL_DELAY_SECONDS, not a real exponential
    ramp — etiquette takes priority over faster backoff here. Returns
    the response text, or NOT_FOUND if the page doesn't exist (404 — the
    archive's actual end, a permanent condition, not a transient
    failure), or None if every retry failed."""
    for attempt in range(MAX_RETRIES):
        try:
            response = session.get(url, timeout=30)
        except requests.RequestException:
            if attempt < MAX_RETRIES - 1:
                time.sleep(max(2 ** attempt, CRAWL_DELAY_SECONDS))
            continue
        if response.status_code == 200:
            if response.encoding is None:
                response.encoding = "utf-8"
            return response.text
        if response.status_code == 404:
            return NOT_FOUND
        if attempt < MAX_RETRIES - 1:
            time.sleep(max(2 ** attempt, CRAWL_DELAY_SECONDS))
    return None


def save_page(output_dir, page_number, html, reports):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / f"page-{page_number:04d}.html").write_text(html)
    (output_dir / f"page-{page_number:04d}-reports.json").write_text(
        json.dumps(reports, indent=2)
    )


def crawl(start_page, end_page, output_dir, fetch_fn=fetch_page, delay=CRAWL_DELAY_SECONDS):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = output_dir / "manifest.json"
    manifest = load_manifest(manifest_path)

    session = requests.Session()
    session.headers["User-Agent"] = USER_AGENT

    for page_number in range(start_page, end_page + 1):
        key = str(page_number)
        # "fetched" and "not_found" are both terminal states — resuming
        # a run should never re-hit a page confirmed not to exist, same
        # as it never re-fetches one already successfully captured.
        if manifest.get(key, {}).get("status") in ("fetched", "not_found"):
            print(f"page {page_number}: already {manifest[key]['status']}, skipping")
            continue

        url = BASE_URL.format(page=page_number)
        html = fetch_fn(url, session)

        if html is NOT_FOUND:
            print(f"page {page_number}: not found (archive end), skipping")
            manifest[key] = {
                "status": "not_found",
                "fetched_at": datetime.now(timezone.utc).isoformat(),
            }
            save_manifest(manifest_path, manifest)
            time.sleep(delay)
            continue

        if html is None:
            print(f"page {page_number}: failed to fetch, skipping")
            manifest[key] = {
                "status": "failed",
                "fetched_at": datetime.now(timezone.utc).isoformat(),
            }
            save_manifest(manifest_path, manifest)
            time.sleep(delay)
            continue

        reports = parse_reports(html, page_number)
        save_page(output_dir, page_number, html, reports)
        manifest[key] = {
            "status": "fetched",
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "report_count": len(reports),
        }
        save_manifest(manifest_path, manifest)
        print(f"page {page_number}: fetched, {len(reports)} reports")

        time.sleep(delay)

    return manifest


def main():
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} <start_page> <end_page> [output_dir]", file=sys.stderr)
        sys.exit(2)
    start_page = int(sys.argv[1])
    end_page = int(sys.argv[2])
    output_dir = sys.argv[3] if len(sys.argv) > 3 else "sources-local/mdrs-crew-reports-raw"
    crawl(start_page, end_page, output_dir)


if __name__ == "__main__":
    main()
