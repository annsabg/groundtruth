# Extraction Workflow

This is the runnable procedure behind the extraction pipeline design
(`docs/superpowers/specs/2026-08-25-groundtruth-extraction-pipeline-design.md`).
There is no standalone script for this — it's run through Claude Code,
one stage at a time, per source.

## Prerequisites

- The source document exists locally under `sources-local/` (native
  format) — see the pipeline spec §5.2 for the convention.
- `schema/*.schema.json` and `scripts/validate.py` are in place (they are,
  as of this plan's Task 7).

## Path A — agent-discovered source

1. Ask Claude Code: "Search for [operational log / crew roster] sources
   for [mission or station]." It proposes candidates with URLs.
2. Review each candidate. Approve or reject.
3. For each approved candidate, write a `data/sources/{source_id}.json`
   record (`discovery_method: agent`) per `schema/source.schema.json`.
4. Continue to "Extraction" below.

## Path B — manually supplied source

1. You already have the document (e.g. downloaded a PDF).
2. Save it under `sources-local/{a-descriptive-name}/` in its native
   format, plus a plain-text/markdown extraction alongside it.
3. Write a `data/sources/{source_id}.json` record (`discovery_method:
   manual`) per `schema/source.schema.json` — `mission_ids` can list
   multiple missions if the source spans more than one.
4. Continue to "Extraction" below.

## Extraction (Stage 2)

Ask Claude Code, for the approved source:

> "Read [source]. First identify mission boundaries within it (which
> mission each part belongs to). Then, within each mission, extract
> candidate [Mission / Crew Member / Operational Event / Research
> Project] records matching schema/[entity].schema.json. Cite the
> specific location in the source for each record's source_citation."

Output: a list of draft JSON records, not yet written to `data/`.

## Self-check (Stage 3)

In a **fresh** Claude Code call (new conversation or explicitly told to
disregard prior context) — not a continuation of the extraction call:

> "Here is the original source text, and here are draft records claimed
> to be extracted from it. Re-read the source and flag any claim in each
> draft you cannot verify against the actual text — dates, numbers,
> names, causal claims, outcomes."

If flagged: go back to Stage 2 once, informed by the specific flags. Run
Stage 3 again on the new draft. If it fails a second time, stop — take
both drafts and both flag sets to human review (next step) rather than
retrying further.

## Human review (Stage 4)

For each draft (with any self-check flags attached):
- Approve as-is, edit, or reject.
- On approval: write the record to `data/{entity_dir}/{id}.json`, fill in
  `verified_by` with your initials — required on all four entity types
  (Mission, Crew Member, Operational Event, Research Project), not just
  Events.
- Validate immediately: `python scripts/validate.py
  schema/{entity}.schema.json data/{entity_dir}/{id}.json`

## Build (Stage 5)

After all records for this batch are committed:

```bash
python scripts/build_db.py
git add data/ groundtruth.sqlite
git commit -m "Add [N] records from [source]"
```
