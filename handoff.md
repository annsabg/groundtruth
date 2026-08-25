# Handoff

*Rewritten each session. Reflects current state, not history — see
decisions.md for the why-log.*

## Current state (as of Task 11, implementation in progress)

Repo scaffolding, all five JSON schemas (Mission, Crew Member, Event,
Research Project, Source), `validate.py`, `build_db.py`, `CONTRIBUTING.md`,
`README.md`, and this file all exist and are committed. Full test suite
(`pytest`) passes. `data/` directories exist but are empty except for
`.gitkeep` — no real records committed yet.

## What's next

Seed data population (plan Tasks 12-17): formalize the extraction workflow
as a document (`docs/extraction-workflow.md`), then actually run it
against the Hypatia III Mission Brief's incident register and the
Flashline Crew Reports PDF to populate `data/events/` and `data/missions/`,
then a separate discovery pass for `data/crew_members/`, then whatever
Research Project data is realistically available (see decisions.md,
2026-08-26 entry — this one's expected to be thin).

## Known gaps

- Research Project sourcing strategy is unsolved (decisions.md).
- Controlled vocabularies (stations, roles, domains) only reflect
  FMARS/MDRS/Mars160 — will need extension for LunAres/HI-SEAS/AMADEE.
- No referential-integrity check on FK-shaped fields (mission_id,
  related_events, comparable_studies) — a record can cite an ID that
  doesn't resolve to any committed file, and nothing catches it yet.
