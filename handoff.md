# Handoff

*Rewritten each session. Reflects current state, not history — see
decisions.md for the why-log.*

## Current state (v0.1 complete — all 19 tasks, plus a post-merge final-review fix wave)

Full data layer, seed data, and tooling are all in place and validated
end-to-end. Repo scaffolding, all five JSON schemas (Mission, Crew Member,
Event, Research Project, Source), `validate.py` (schema validation +
referential-integrity checking via `--check-refs`, including a
`principal_investigators` -> `crew_member_id` check), `build_db.py`,
`scripts/stats.py` (read-only summary/reporting over the built
`groundtruth.sqlite` — counts, breakdowns by station/event_type/domain),
`CONTRIBUTING.md`, CI (schema validation + `--check-refs` + a
`groundtruth.sqlite`-matches-`data/` check + `pytest` on every PR),
`README.md`, `docs/extraction-workflow.md`, and this file all exist and
are committed. The full `pytest` suite (23 tests) passes.

Task 19 (`scripts/stats.py`) is done — v0.1's 19-task plan is fully
complete. A final whole-branch review after Task 19 found several
pre-merge issues (a real name leaked into test fixtures, organization
names in crew citation quotes creating re-identification risk, missing
`principal_investigators` reference checking, no CI check that
`groundtruth.sqlite` matches `data/`, no schema-drift guard on
`build_db.py`'s `ENTITIES` dict, and a stale handoff doc) — all fixed in
one follow-up pass; see `decisions.md`'s 2026-08-26 entries for what was
found and why.

`data/` is populated with real, cited, human-verified records — sourced
from the Hypatia III Mission Brief and the Flashline Crew Reports PDF via
the two-pass extraction workflow, across two extraction rounds (Tasks
14+15) plus a targeted crew-discovery pass (Task 16) and a hand-curated
research-project pass (Task 17):

| Entity            | Count | Notes |
|--------------------|------:|-------|
| Mission            | 5     | FMARS Crews 15–18 (2023–2025) + MARS160-2017 |
| Operational Event   | 60    | 46 from Task 14 (Hypatia brief) + 14 from Task 15 (Flashline reports) |
| Crew Member         | 29    | 5/7/4/7/6 across FMARS C15/C16/C17/C18, 6 for MARS160-2017 |
| Research Project    | 3     | RP-001/RP-002 (FMARS C15), RP-003 (FMARS C16) — hand-curated |
| Source              | 6     | citation registry, keyed by `source_id` + `mission_ids[]` |

Missions span 2017-07-01 to 2025-07-31, all at FMARS (MARS160-2017 also
touches MDRS). `event_type` breakdown confirms Task 15's broadened
extraction actually diversified the data beyond Failure/Near-Miss:

```
Crew Dynamics          5
Failure                28
Near-Miss               5
Observation              7
Process Innovation       9
Success/Best Practice    6
```

`groundtruth.sqlite` is built fresh from `data/` (Task 18, Step 3) and
spot-checked directly against the entity counts above. The "regenerable
from git" backup claim has been proven, not just asserted: a clone into a
genuinely separate `/tmp` directory, a fresh venv, `pip install -r
requirements.txt`, and `python scripts/build_db.py` reproduced identical
counts (mission=5, event=60, crew_member=29, research_project=3,
source=6) with nothing manually copied in.

## What's next

v0.1 is done — no v0.1 plan tasks remain. Next work is v0.2-scoped. In
priority order, per this fix wave's `decisions.md` entries and the Known
Gaps below:

1. **Process Flashline Crew Reports pages 83-95** (the Mars160/FMARS-leg
   section) — the top v0.2 data-population priority. See decisions.md,
   2026-08-26 "Mars160 pages 83-95... were never processed" — this is
   real, unprocessed primary-source content (~430 lines), not a
   previously-resolved item. Requires active attention to the no-real-names
   discipline; see that entry for why.
2. **Add an "unknown" option to Event's `sol` and/or a confidence field to
   Mission** — see decisions.md, 2026-08-26 "structural
   uncertainty-disclosure gap on `sol` and Mission-level facts." Currently
   ~34/60 Event records carry an inferred `sol` that reads as fact to any
   query.
3. Extend seed data to LunAres/HI-SEAS/AMADEE stations.
4. Revisit the Research Project sourcing strategy (decisions.md,
   2026-08-26 "Research Project sourcing strategy left unsolved").
5. Any future privacy check (automated or manual) must be whole-repository
   in scope, not `data/`-scoped — see decisions.md, 2026-08-26 "the
   real-name-leak pattern, and the rule it establishes."

## Known gaps

- **Research Project sourcing strategy is unsolved** (decisions.md,
  2026-08-26 entry). v0.1's 3 records are thin and hand-curated, all from
  the two sources already used for Events/Crew, not pipeline-sourced.
  `domain` enum also has no "Environmental Science" option — RP-002/RP-003
  are filed under `Biology` as the closest fit (Task 17).
- **Controlled vocabularies (stations, roles, domains) only reflect
  FMARS/MDRS/Mars160** — will need extension for LunAres/HI-SEAS/AMADEE
  once seed data covers those stations.
- **RP-001 `sample_size.n_crew` (5) doesn't match `FMARS-C15-2023`'s
  `crew_size` (6).** Not yet explained (could be legitimate non-universal
  study participation, or a sourcing gap) — unresolved, found during Task
  18's final review.
- **Flashline Crew Reports pages 83-95 (the Mars160/FMARS-leg section)
  were never extracted** — not a deliberate scope decision but a Task 15
  dispatch scoping error (the controller incorrectly stated this content
  didn't exist in the source; it does, ~430 lines of primary daily
  reports). Mars160 currently has thinner coverage (5 events, 6 crew
  members) than the FMARS-only missions as a direct result. Top v0.2
  data-population priority — see decisions.md, 2026-08-26 "Mars160 pages
  83-95... were never processed."
- **`sol` (Event) and Mission-level facts have no structured
  uncertainty/confidence option** — ~34/60 Event records carry an
  inferred `sol` that reads as fact to any query; Mission has no
  confidence field analogous to Event's A-D. v0.2 schema candidate — see
  decisions.md, 2026-08-26 "structural uncertainty-disclosure gap on
  `sol` and Mission-level facts."
- **Resolved:** `FMARS-C15-2023-EVT010` (reagent/coliform-kit storage
  incident) was found mis-tagged — primary-source evidence showed it
  actually belongs to Crew 16, not Crew 15 — and was retagged to
  `FMARS-C16-2024-EVT034` during Task 15 (commit `509671c`). No longer an
  open item; noted here only for the historical record.
- **`FMARS-C17-2025` `crew_size` (6) exceeds its 4 documented Crew Member
  records.** Task 16 flagged this; the coordinator left it as-is since 4
  documented crew doesn't prove the true total is only 4 (roster may be
  incomplete). Unresolved.
- **Privacy checks must be whole-repository in scope, not `data/`-scoped.**
  Two real-name leaks (Task 14's crew-name leak into free-text fields, and
  this final-review fix wave's leak into `tests/fixtures/`) were both
  caught only by a human reading actual content, not by any scoped
  automated check. `CONTRIBUTING.md`'s privacy rule is now explicit that
  it applies repo-wide — see decisions.md, 2026-08-26 "the real-name-leak
  pattern, and the rule it establishes."
