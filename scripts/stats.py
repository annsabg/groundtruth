#!/usr/bin/env python3
"""Print a plain-text snapshot of groundtruth.sqlite: record counts per
entity, event_type breakdown, top recurring pattern_tags, and crew data
coverage. Read-only — no new infrastructure, just SELECT/GROUP BY over
what build_db.py already built.

Usage:
    python scripts/stats.py [sqlite_path]

Defaults to groundtruth.sqlite in the current directory.
"""
import sqlite3
import sys


def generate_stats(sqlite_path="groundtruth.sqlite") -> str:
    conn = sqlite3.connect(sqlite_path)
    lines = ["Groundtruth — dataset snapshot", ""]

    mission_count = conn.execute("SELECT COUNT(*) FROM mission").fetchone()[0]
    lines.append(f"Missions: {mission_count}")

    event_count = conn.execute("SELECT COUNT(*) FROM event").fetchone()[0]
    event_by_type = conn.execute(
        "SELECT event_type, COUNT(*) FROM event GROUP BY event_type ORDER BY COUNT(*) DESC"
    ).fetchall()
    if event_by_type:
        breakdown = ", ".join(f"{t}: {c}" for t, c in event_by_type)
        lines.append(f"Events: {event_count} ({breakdown})")
    else:
        lines.append(f"Events: {event_count}")

    top_tags = conn.execute(
        """SELECT pattern_tag, COUNT(*) as c FROM event
           WHERE pattern_tag IS NOT NULL AND pattern_tag != ''
           GROUP BY pattern_tag ORDER BY c DESC LIMIT 5"""
    ).fetchall()
    if top_tags:
        tag_summary = ", ".join(f'"{t}" ({c})' for t, c in top_tags)
        lines.append(f"Top pattern_tags: {tag_summary}")

    crew_count = conn.execute("SELECT COUNT(*) FROM crew_member").fetchone()[0]
    expected_crew = conn.execute("SELECT SUM(crew_size) FROM mission").fetchone()[0] or 0
    lines.append(f"Crew Members: {crew_count} of {expected_crew} known crew slots filled")

    research_count = conn.execute("SELECT COUNT(*) FROM research_project").fetchone()[0]
    lines.append(f"Research Projects: {research_count}")

    # Vocabulary-drift signal: "Other" is a legal escape hatch in several
    # enums (stations, primary_role, field_of_expertise, domain), but heavy
    # use of it usually means the controlled vocabulary needs extending,
    # not that "Other" is genuinely the right answer that often. Surfacing
    # the count makes that drift visible instead of silent.
    other_counts = {
        "mission.stations": conn.execute(
            "SELECT COUNT(*) FROM mission WHERE stations LIKE '%\"Other\"%'"
        ).fetchone()[0],
        "crew_member.primary_role": conn.execute(
            "SELECT COUNT(*) FROM crew_member WHERE primary_role = 'Other'"
        ).fetchone()[0],
        "crew_member.field_of_expertise": conn.execute(
            "SELECT COUNT(*) FROM crew_member WHERE field_of_expertise LIKE '%\"Other\"%'"
        ).fetchone()[0],
        "research_project.domain": conn.execute(
            "SELECT COUNT(*) FROM research_project WHERE domain = 'Other'"
        ).fetchone()[0],
    }
    flagged = {field: count for field, count in other_counts.items() if count > 0}
    if flagged:
        summary = ", ".join(f"{field}: {count}" for field, count in flagged.items())
        lines.append(f"'Other' usage (consider extending the vocabulary if this grows): {summary}")

    conn.close()
    return "\n".join(lines)


def main():
    sqlite_path = sys.argv[1] if len(sys.argv) > 1 else "groundtruth.sqlite"
    print(generate_stats(sqlite_path))


if __name__ == "__main__":
    main()
