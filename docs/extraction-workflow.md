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
> candidate [Mission / Crew Member / Operational Event / Research Project / Equipment Item] records matching schema/[entity].schema.json. Cite the
> specific location in the source for each record's source_citation."

Output: a list of draft JSON records, not yet written to `data/`.

## Self-check (Stage 3)

In a **fresh** Claude Code call (new conversation or explicitly told to
disregard prior context) — not a continuation of the extraction call —
**dispatched on a stronger model than Stage 2 used** (e.g. Opus if
Stage 2 ran on Sonnet). Stage 2 is bulk, semi-mechanical drafting work
where a mid-tier model is cost-effective; Stage 3's entire job is
catching what Stage 2 missed, so it's worth paying for the more capable
model on this one call per batch rather than the whole pipeline. This
isn't hypothetical: dispatched as a stronger-model fresh check, Stage 3
has twice caught real, non-trivial problems the extractor missed (a
systemic real-name leak inside quoted citation text, and a fabricated
causal claim) — see decisions.md's 2026-09-25 and 2026-09-27 entries.

> "Here is the original source text, and here are draft records claimed
> to be extracted from it. Re-read the source and flag any claim in each
> draft you cannot verify against the actual text — dates, numbers,
> names, causal claims, outcomes."

If flagged: go back to Stage 2 once, informed by the specific flags. Run
Stage 3 again on the new draft. If it fails a second time, stop — take
both drafts and both flag sets to human review (next step) rather than
retrying further.

## Equipment Item extraction rules

Equipment Items (`schema/equipment_item.schema.json`) capture packing
advice: what a crew wished they'd brought, found essential, needs spares
of, recommended to bring, or shouldn't bring. One record per distinct item — a lesson naming
five parts is five records, each with `related_events` pointing at the
event it came from.

- **Explicit only.** Record an item only when the source names it, or
  clearly implies it ("we had no X and needed it"). Never infer advice
  from a failure alone — "the pump failed" is not "bring a spare pump".
  Stage 3 should flag any advice the source doesn't actually give.
- **`Essential` requires the crew's own emphasis** ("critical",
  "couldn't have managed without"). Having packed something isn't enough.
- **`Recommended`** is for advice to bring an item the crew already had,
  where the advice comes from a planner/brief or the source without the
  crew's own complaint or emphasis. The rationale must say who gave the
  advice. Never use `Wished Brought` for an item the crew had.
- **`item_key`:** reuse an existing key (`SELECT DISTINCT item_key FROM
  equipment_item`) when it's clearly the same item; otherwise leave it
  unset. Keys are assigned or confirmed at Stage 4, never invented at
  Stage 2.
- **`area`** is a closed list — see CONTRIBUTING.md. If nothing fits,
  flag it at Stage 4 rather than forcing a poor fit.
- Every existing rule still applies: no real names (including inside
  quoted citations), cite specific locations.

## Human review (Stage 4)

For each draft (with any self-check flags attached):
- Approve as-is, edit, or reject.
- On approval: write the record to `data/{entity_dir}/{id}.json`, fill in
  `verified_by` with your initials — required on all five entity types
  (Mission, Crew Member, Operational Event, Research Project, Equipment Item), not just
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
