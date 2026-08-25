# Decisions

Append-only log of non-obvious architectural choices and why they were
made. Never edit or delete an existing entry — if a decision changes, add
a new entry explaining the change and referencing the old one.

## 2026-08-25 — SQLite as the canonical data artifact, not flat CSV

Chosen specifically so a future website/query layer can filter, join, and
aggregate without a data-layer rewrite. CSV would have been simpler to
diff in PRs, but the whole point of this project includes an eventual
insight-extraction interface (design spec §3.1) — SQLite serves that
without deferring the format decision to a rewrite later.

## 2026-08-25 — Mission promoted to a first-class entity

Originally "Mission ID" was just a free-text tag on Incident/Research
records. Promoted to its own entity (with `stations`, dates, crew size,
institutional/volunteer status) once crew demographic tracking was added
— crew and event data both need to be sliceable by station/date/type, and
a tag string can't carry that.

## 2026-08-25 — Crew data: pseudonymous IDs, but demographics fully open

Real names never appear anywhere in the dataset. Demographics (gender,
nationality, age, expertise) are stored raw and published under CC BY 4.0
with no access-control tier — a deliberate choice to keep the whole
dataset genuinely open rather than building a restricted-data tier.
Accepted tradeoff: exact age + gender + nationality + expertise in a crew
of 5-7 carries real re-identification risk against public crew rosters.
Mitigation is pseudonymization + (future) bracketed display, not access
restriction.

## 2026-08-25 — Incident renamed and broadened to Operational Event

The original schema only had room for things going wrong. Real mission
logs also contain successes, process innovations, and crew dynamics
patterns worth tracking — added `event_type`, renamed `severity` to
`significance` (impact regardless of positive/negative), renamed
`resolution` to `response`, generalized `failure_type` to `pattern_tag`
and `resolution_outcome` to `outcome` so the same fields work across all
event types.

## 2026-08-25 — Extraction pipeline: two-pass (extract + independent self-check), retry once, then escalate to human

Hallucination risk in AI-assisted extraction is mitigated by a second,
independent AI pass that re-reads the source and flags unverifiable
claims in the first pass's draft — before any human sees it. If flagged,
one retry (informed by what was flagged); a second failure escalates to
a human with both attempts' context, rather than retrying indefinitely.

## 2026-08-25 — Raw source documents never committed to the repo

Citations (URL/document reference) are committed; the PDFs/pages
themselves stay local. Avoids redistributing potentially copyrighted
compiled report text, keeps the repo focused on structured data. Local
working copies live in a gitignored `sources-local/{mission_id}/`
directory for pipeline re-runs across sessions.

## 2026-08-26 — Source registry keyed by source_id + mission_ids[], not {mission_id}.json

The pipeline spec's original `data/sources/{mission_id}.json` would
duplicate a multi-mission source's metadata across every mission file it
covers (e.g. the Flashline Crew Reports PDF spans four missions).
Resolved to match the pattern Research Project already uses:
`data/sources/{source_id}.json` with a `mission_ids` array.

## 2026-08-26 — Source discovery runs through Claude Code, not a coded search script

No `scripts/discover_sources.py`, no search API integration. Discovery
tasks vary too much to script cleanly (targeted single-document review vs.
"crawl this whole station archive"), and this is low-frequency,
high-supervision work — an agent-run documented workflow fits better than
building and maintaining bespoke search infrastructure.

**Scope of "no proprietary dependencies, fully open," stated explicitly:**
this applies to the shipped repo's *runtime* — anyone can clone
`groundtruth`, run `pip install -r requirements.txt`, and use
`validate.py`/`build_db.py`/`stats.py` with zero paid services, zero
vendor lock-in, fully offline. It does **not** claim the *curation
process* that produced the data is reproducible without a specific
vendor's product — Stages 1–4 of the extraction pipeline are run through
Claude Code specifically, and there's no requirement or expectation that
a contributor use that particular tool. A contributor could run the same
four stages by hand, or with a different AI assistant, or with no AI at
all (read a report, write the JSON directly) — the schema and review
workflow don't care how a draft record was produced, only that it's
correctly structured, cited, and reviewed before being committed.

## 2026-08-26 — Research Project sourcing strategy left unsolved for v0.1

Unlike Events and Crew data, research projects run at analog missions
don't reliably show up in sol reports — they're scattered across
conference listings, PI pages, and papers. v0.1's Research Project seed
data is expected to be thin/hand-curated rather than pipeline-sourced.
Revisit once Events/Crew extraction is running and there's a clearer
picture of what can reuse the same approach.

## 2026-08-26 — Fresh-eyes review of the implementation plan; several fixes applied before any code was written

Dispatched a review agent with zero prior context on this project to read
both specs and the plan cold. Findings and fixes:

- `build_db.py` declared every SQLite column as TEXT, which silently
  coerces integer values (`crew_size`, `sol`, `age`) to strings on
  round-trip — reproduced independently, confirmed real. Fixed by
  declaring those three columns INTEGER.
- `age` was required-and-strictly-integer with no escape hatch, unlike
  `gender`/`nationality` which both allow `undisclosed`. Public crew bios
  rarely state exact age — this would have blocked real Crew Member
  records. Added the same `undisclosed` option.
- `stations: "Other"` had no companion free-text field despite the design
  spec explicitly promising one ("+ free text if Other"). Added
  `stations_other_detail`, required when `stations` contains `"Other"`.
- `.gitignore` (as drafted) didn't actually exclude `*.pdf`/`*.docx`/
  `sources-local/` — the raw-source-exclusion principle both specs state
  was unenforced. Fixed.
- `mission_id`, `related_events`, `comparable_studies`, `mission_ids` were
  unchecked strings — nothing caught a reference to an ID that doesn't
  exist. Added `check_references()` / `--check-refs` to `validate.py`,
  wired into CI and the final integration task.
- The CI question (flagged as open in the design spec, never resolved)
  was decided explicitly: yes — a minimal GitHub Actions workflow running
  `pytest` + schema validation + `--check-refs` on every PR.
- Task 15's dedup instruction ("skip if it's a clean duplicate") wasn't
  an executable rule. Replaced with a concrete same-incident test
  (mission + sol±1 + system_category + named equipment/situation match).
- Task 1 didn't say where the `groundtruth` repo physically gets created,
  which the restore-test task then silently assumed was this THAMB
  planning workspace — contradicting the File Structure section. Fixed
  both: Task 1 now says explicitly to create/clone `groundtruth`
  separately; the restore test auto-detects the repo root instead of
  hardcoding a path.
- `verified_by` existed only on the Operational Event schema, despite
  Mission, Crew Member, and Research Project all going through the same
  Stage 4 human-review gate (pipeline spec §4). Added `verified_by` as a
  required field to all three.
