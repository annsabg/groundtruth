#!/usr/bin/env python3
"""Summarize Stage 2/3 extraction-pipeline draft records for fast human review.

Usage:
    python scripts/summarize_drafts.py <drafts_dir>

Reads a drafts directory laid out like data/ (sources/, missions/,
crew_members/, events/, research_projects/ subdirectories of *.json
files, as produced by a Stage 2 extraction) and prints one compact line
per record, grouped by entity type and sorted by filename — so a human
reviewer can scan a whole batch in one screen instead of opening every
raw JSON file individually (see docs/extraction-workflow.md's Stage 4).

This only reformats for skimming; it is not a substitute for opening a
specific record's full JSON (and its source_citation) when a flagged
line warrants a closer look.
"""
import json
import sys
from pathlib import Path

# (subdirectory name, section heading, formatter function name) — formatter
# functions are resolved by name below, once they're defined.
_ENTITY_TYPES = [
    ("sources", "SOURCES", "format_source"),
    ("missions", "MISSIONS", "format_mission"),
    ("crew_members", "CREW MEMBERS", "format_crew_member"),
    ("events", "EVENTS", "format_event"),
    ("research_projects", "RESEARCH PROJECTS", "format_research_project"),
]


def truncate(text: str, length: int = 140) -> str:
    """Shortens text to at most `length` chars, breaking on a word boundary,
    never on a `format_*` field a reviewer might otherwise misread as complete."""
    if len(text) <= length:
        return text
    cut = text[:length].rsplit(" ", 1)[0]
    return cut + "..."


def format_source(r: dict) -> str:
    covers = ", ".join(r.get("covers", []))
    return (
        f"{r.get('source_id', '?')} [{r.get('source_type', '?')}] "
        f"covers={covers or '-'} -- {truncate(r.get('url_or_reference', ''), 90)}"
    )


def format_mission(r: dict) -> str:
    stations = ", ".join(r.get("stations", []))
    return (
        f"{r.get('mission_id', '?')} -- \"{r.get('crew_designation', '?')}\" "
        f"@ {stations or '?'}, {r.get('start_date', '?')}..{r.get('end_date', '?')}, "
        f"crew={r.get('crew_size', '?')}"
    )


def format_crew_member(r: dict) -> str:
    expertise = r.get("field_of_expertise", {}) or {}
    detail = truncate(expertise.get("detail", ""), 70)
    return (
        f"{r.get('crew_member_id', '?')} -- {r.get('primary_role', '?')}, "
        f"{r.get('gender', '?')}/{r.get('nationality', '?')}/age={r.get('age', '?')}, "
        f"expertise={expertise.get('category', '?')} ({detail})"
    )


def format_event(r: dict) -> str:
    outcome = r.get("outcome") or "-"
    desc = truncate(r.get("description", ""), 100)
    return (
        f"{r.get('event_id', '?')} Sol {r.get('sol', '?')} "
        f"[{r.get('system_category', '?')}/{r.get('event_type', '?')}/{r.get('significance', '?')}] "
        f"-- {desc} => outcome={outcome}"
    )


def format_research_project(r: dict) -> str:
    pis = ", ".join(r.get("principal_investigators", [])) or "-"
    title = truncate(r.get("title", ""), 90)
    return (
        f"{r.get('research_project_id', '?')} -- \"{title}\" "
        f"domain={r.get('domain', '?')} PI={pis} pub={r.get('publication_status', '?')}"
    )


_FORMATTERS = {
    "format_source": format_source,
    "format_mission": format_mission,
    "format_crew_member": format_crew_member,
    "format_event": format_event,
    "format_research_project": format_research_project,
}


def summarize_directory(drafts_dir: Path) -> str:
    drafts_dir = Path(drafts_dir)
    sections = []
    for subdir_name, heading, formatter_name in _ENTITY_TYPES:
        subdir = drafts_dir / subdir_name
        if not subdir.is_dir():
            continue
        files = sorted(subdir.glob("*.json"))
        if not files:
            continue
        formatter = _FORMATTERS[formatter_name]
        lines = [f"  {formatter(json.loads(f.read_text()))}" for f in files]
        sections.append(f"{heading} ({len(files)})\n" + "\n".join(lines))
    return "\n\n".join(sections)


def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <drafts_dir>", file=sys.stderr)
        sys.exit(1)
    print(summarize_directory(Path(sys.argv[1])))


if __name__ == "__main__":
    main()
