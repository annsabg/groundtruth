# Handoff

*Rewritten each session. Reflects current state, not history — see
decisions.md for the why-log.*

## Current state (as of Task 18, v0.1 complete)

Full data layer, seed data, and tooling are all in place and validated
end-to-end. Repo scaffolding, all five JSON schemas (Mission, Crew Member,
Event, Research Project, Source), `validate.py` (schema validation +
referential-integrity checking via `--check-refs`), `build_db.py`,
`CONTRIBUTING.md`, CI (schema validation + `--check-refs` + `pytest` on
every PR), `README.md`, `docs/extraction-workflow.md`, and this file all
exist and are committed. The full `pytest` suite (20 tests) passes.

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

Task 19: `scripts/stats.py` — a read-only summary/reporting tool over the
built `groundtruth.sqlite` (counts, breakdowns by station/event_type/
domain, etc.). No other v0.1 plan tasks remain after that.

Beyond v0.1: extend seed data to LunAres/HI-SEAS/AMADEE stations, revisit
the Research Project sourcing strategy (see decisions.md), and resolve
the open discrepancies listed below.

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
- **Flashline Crew Reports pages 83–95 (the Mars160/FMARS-leg section)
  were deliberately not extracted in Task 15**, per that task's brief.
  Mars160 currently has only 5 events despite this section containing
  additional relevant detail (e.g. an Aug 10–11 crew-tension narrative
  possibly related to existing `MARS160-2017-EVT003`/`EVT005`) — flagged
  in task-15-report.md as a real, currently-open gap for a future task.
- **Probable mission mis-tag on `FMARS-C15-2023-EVT010`** (reagent/
  coliform-kit storage incident) — Task 15 found primary-source evidence
  this incident actually belongs to Crew 16, not Crew 15, but deliberately
  did not correct it (outside that task's edit scope). Still open;
  recommend retagging in a future correction pass.
- **`FMARS-C17-2025` `crew_size` (6) exceeds its 4 documented Crew Member
  records.** Task 16 flagged this; the coordinator left it as-is since 4
  documented crew doesn't prove the true total is only 4 (roster may be
  incomplete). Unresolved.
