# Contributing to Groundtruth

Groundtruth is a structured, citable registry — its value depends on every
entry being verifiable against a real source. This document defines what a
valid submission looks like and how it gets reviewed.

## What you can contribute

- A new **Mission**, **Crew Member**, **Operational Event**, **Research
  Project**, or **Source** record, as one JSON file.
- A correction to an existing record (edit the JSON file, explain the
  correction and its source in the PR description).

## Before you submit

1. **Every record must cite a real source.** `source_citation` (or, for
   Source records, `url_or_reference`) must point to something a reviewer
   can actually check — a URL, a named document, a specific report and date.
   "I remember this happening" is not a valid citation.
2. **Never include a crew member's real name anywhere** — not in
   `source_citation`, not in `description`, not in any free-text field.
   Crew Member records are pseudonymous by design (see the design spec,
   §5); an Event's `description` that names someone defeats that.
3. **Validate locally before opening a PR:**
   ```bash
   pip install -r requirements-dev.txt
   python scripts/validate.py schema/event.schema.json data/events/YOUR-NEW-FILE.json
   ```
   (swap `event`/`events` for whichever entity type you're adding)
4. **Check that any ID you referenced actually resolves:** if your record
   sets `mission_id`, `related_events`, or `comparable_studies`, run
   `python scripts/validate.py --check-refs data` — schema validation
   alone doesn't catch a typo'd or nonexistent ID.
5. **Rebuild the database and commit the result:**
   ```bash
   python scripts/build_db.py
   git add data/ groundtruth.sqlite
   ```
   `groundtruth.sqlite` is a generated artifact — it must always reflect
   what's in `data/`. A PR that changes `data/` without regenerating
   `groundtruth.sqlite` will fail review.

## Confidence ratings (Operational Event records)

Rate how reliable the source is, not how important the event is:

- **A** — formal engineering report
- **B** — daily narrative report
- **C** — journalist/XO report
- **D** — secondhand or inferred

## Review process (v0.1)

For v0.1, with a single active contributor, review means: the submitter
re-reads the record against its cited source one more time before merging,
and fills in `verified_by` with their initials. This is intentionally
lightweight now and will tighten (a second reviewer required) once there
are multiple regular contributors — see `decisions.md` for why this
tradeoff was made rather than requiring a second reviewer from day one.

**Before committing, check `git diff` for changes to files you didn't mean
to touch — not just the new ones.** An AI-assisted extraction session
working on unrelated records has, in principle, no guardrail stopping it
from silently editing an already-committed record it happened to read
along the way. CI (below) catches *invalid* records, not *unintentionally
changed* ones — `git diff --stat` before every commit is still the whole
defense against a silent, schema-valid edit to a record you didn't mean
to touch. If it ever shows a file you didn't intend to change, stop and
find out why before committing.

## Controlled vocabularies

Fields like `pattern_tag` and `field_of_expertise.detail` are intentionally
open-ended (see the design spec §4.3) — new values are expected as new
missions and stations get added. Fields like `stations`, `event_type`, and
`system_category` are closed enums defined in `schema/*.schema.json` — if
your record genuinely needs a new value in one of those, propose the schema
change in the same PR and explain why the existing options don't fit.

## Licensing

By contributing, you agree your data contributions are licensed CC BY 4.0
and your code/schema contributions are licensed MIT — see `LICENSE-DATA`
and `LICENSE-CODE`.
