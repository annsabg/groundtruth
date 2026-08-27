# Handoff

*Rewritten each session. Reflects current state, not history — see
decisions.md for the why-log.*

## Current state

**`main`: v0.1 (data layer) + v0.2 (browsable site) complete and merged.
`v0.3-mdrs-pilot`: fetch tooling built, tested, and piloted — not yet
merged, and nothing from it has reached `data/` yet.**

### v0.1 — data layer (complete, on `main`)

Full data layer, seed data, and tooling: five JSON schemas (Mission, Crew
Member, Event, Research Project, Source), `validate.py` (schema +
`--check-refs` referential-integrity checking), `build_db.py`,
`scripts/stats.py`, `CONTRIBUTING.md`, CI, `README.md`,
`docs/extraction-workflow.md`.

| Entity            | Count | Notes |
|--------------------|------:|-------|
| Mission            | 5     | FMARS Crews 15–18 (2023–2025) + MARS160-2017 |
| Operational Event   | 60    | Hypatia brief + Flashline reports |
| Crew Member         | 29    | 5/7/4/7/6 across FMARS C15/C16/C17/C18, 6 for MARS160-2017 |
| Research Project    | 3     | RP-001/RP-002 (FMARS C15), RP-003 (FMARS C16) — hand-curated |
| Source              | 6     | citation registry, keyed by `source_id` + `mission_ids[]` |

These counts are unchanged since v0.1 — neither v0.2 (site-only) nor the
v0.3 pilot branch (fetch-tooling-only, still unmerged) has added to
`data/`.

### v0.2 — browsable site (complete, on `main`)

`site/`: framework-free static app — hash router (`router.js`), sql.js
(self-hosted `site/lib/sql-wasm.*`) + Chart.js for in-browser querying,
`db.js` query helpers, landing page, Missions/Incidents tabs with sidebar
filters, event detail expand-in-place with opt-in source verification,
Patterns dashboard (expand-to-chart), About page. `event.station` was
added (schema + data backfill) so a multi-site mission like
`MARS160-2017` (`stations: [FMARS, MDRS]`) can have each event correctly
matched to the one station it actually happened at, not both. Deployed
via `.github/workflows/deploy-pages.yml` — builds a fresh
`groundtruth.sqlite` from `data/` and publishes `site/` + that database to
GitHub Pages on every push to `main`.

### v0.3-mdrs-pilot — MDRS bulk-fetch tooling (this session, unmerged)

Branch `v0.3-mdrs-pilot`, plan
`docs/superpowers/plans/2026-08-27-groundtruth-mdrs-fetch-pilot-implementation.md`.
Built `scripts/fetch_mdrs_reports.py` — mechanically fetches and splits
MDRS crew-report archive pages (`reports.marssociety.org/crew-reports/`)
into local, gitignored per-report JSON; deliberately does **not**
interpret content (no date/sol/crew# parsing) — that stays Stage 2,
run by Claude Code, not scripted. Resumable via a JSON manifest,
respects `robots.txt`'s `Crawl-delay: 10` as a hard floor on every retry
sleep (not just between pages), distinguishes a genuine 404
(`NOT_FOUND` sentinel, permanent, skipped on resume) from exhausted
retries (`None`, transient, retried on resume). 48 tests pass
(`pytest -v` from repo root, after `pip install -r requirements-dev.txt`
— `requests`/`beautifulsoup4` aren't in `requirements.txt`, so a fresh
venv needs the dev file explicitly).

Commits this session: the four build-out commits (`b64438f`..`51ae1fb`),
then a final-review fix wave (`5a1226b`) — mkdir-before-manifest-write,
retry-floor, `fetched_at` timestamps, the `NOT_FOUND` sentinel, and
README/CONTRIBUTING docs. A scoped re-review of that fix-wave commit
found no correctness issues (two very minor non-blocking notes only —
see decisions.md if picking this back up).

**Pilot run against the real site (pages 1–5) is done and verified:**
5/5 pages fetched, 0 failures, 50 reports total (10/page), output at
`sources-local/mdrs-crew-reports-raw/` (gitignored — `manifest.json` +
`page-000N.html` + `page-000N-reports.json` per page). Confirmed real,
readable content, not an error page. **This manifest predates the
fix-wave commit** (fetched at 10:32–10:33, fix wave landed 14:27) — it
still satisfies the plan's Task 5 success criteria since this range had
zero failures either way, but the fix-wave's failure-path code (mkdir
recovery, `NOT_FOUND` handling) hasn't actually been exercised against
the live site yet, only against tests.

**A live Stage 2 (extraction) walkthrough was run this session** against
page 1's reports, per `docs/extraction-workflow.md`. Two findings:

1. **Mission-boundary identification matters even within one archive
   page** — page 1 is not one mission. 9 of its 10 reports are MDRS Crew
   330 (sols 15–17, ~Feb 28–Mar 4 2026); the 10th is a Crew 335 Mission
   Summary (Apr 19–May 2 2026) that happened to post the same day. Naively
   treating "one archive page" as "one mission" would have been wrong.
2. Drafted a full record set for **Crew 335** (rich single narrative
   source, dates/crew-size/location all directly stated): one Mission
   record (`MDRS-C335-2026`), five Crew Member records (pseudonymous,
   real names in the source text never carried into any drafted field),
   one Source record, and identified (not yet drafted) five Research
   Project candidates named in the summary. **None of this was written to
   `data/`** — it's Stage 2 output only, `verified_by`/`approved_by` left
   as `PENDING_HUMAN_REVIEW` placeholders. Stage 3 (fresh-context
   self-check) has not run on it yet.
   Deliberately did **not** attempt a Mission record for Crew 330 — sols
   15–17 alone don't bound a mission's start/end date; that needs an
   earlier archive page (an announcement or Sol 1 report), not this page
   alone.

## What's next

Pick one of these up next session — the Crew 335 drafts above are ready
to resume from immediately, nothing about them expires:

1. **Resume the Crew 335 draft**: run Stage 3 (fresh-context self-check
   against the source), then Stage 4 (human review → commit to `data/`,
   fill `verified_by`/`approved_by`, `validate.py`, `build_db.py`). This
   would be `data/`'s first MDRS-sourced records and the first real test
   of the full pipeline against this new source.
2. **Decide on `v0.3-mdrs-pilot` → `main`**: the fetch script itself is
   done, tested, and pilot-verified independent of whether any MDRS
   report has been carried through to a committed record yet. Could merge
   now (script + tests only, no data change) or wait until at least one
   record closes the loop end-to-end — your call.
3. **Decide on the full ~715-page crawl.** At `Crawl-delay: 10`, that's
   ~2+ hours minimum — a background job, not interactive. No decision
   made yet; the pilot was explicitly scoped to not presuppose this.
4. Carried over from v0.1 (untouched this session, still open — see
   decisions.md's 2026-08-26 entries for full context on each):
   - **Process Flashline Crew Reports pages 83-95** (Mars160/FMARS-leg
     section, ~430 unprocessed lines) — top v0.1-era data-population
     priority, still outstanding.
   - Add an "unknown" option to Event's `sol` and/or a confidence field
     to Mission.
   - Extend seed data to LunAres/HI-SEAS/AMADEE stations.
   - Revisit the Research Project sourcing strategy.

## Known gaps

- **MDRS extraction must re-run mission-boundary identification on every
  page, not assume page-per-mission** — see "v0.3-mdrs-pilot" above. Only
  discovered this session; applies to all future MDRS pages, including
  any full-archive crawl.
- **Research Project sourcing strategy is unsolved** (decisions.md,
  2026-08-26 entry). v0.1's 3 records are thin and hand-curated.
  `domain` enum also has no "Environmental Science" option.
- **Controlled vocabularies (stations, roles, domains) only reflect
  FMARS/MDRS/Mars160** — will need extension for LunAres/HI-SEAS/AMADEE.
- **RP-001 `sample_size.n_crew` (5) doesn't match `FMARS-C15-2023`'s
  `crew_size` (6).** Unresolved.
- **Flashline Crew Reports pages 83-95 were never extracted** — top
  data-population priority; see decisions.md, 2026-08-26 "Mars160 pages
  83-95... were never processed."
- **`sol` (Event) and Mission-level facts have no structured
  uncertainty/confidence option** — v0.2 schema candidate; see
  decisions.md, 2026-08-26 "structural uncertainty-disclosure gap."
- **`FMARS-C17-2025` `crew_size` (6) exceeds its 4 documented Crew Member
  records.** Left as-is (Task 16); unresolved.
- **Privacy checks must be whole-repository in scope, not `data/`-scoped**
  (decisions.md, 2026-08-26 "the real-name-leak pattern"). Reaffirmed this
  session: the Crew 335 source text contains five real names in prose;
  none were carried into any drafted field (schema has no `name` field on
  Crew Member by design) — verify this discipline holds if this draft is
  picked back up by a different session/tool.
- **Resolved:** `FMARS-C15-2023-EVT010` mis-tag — see prior handoff
  entries; no longer open, noted for the historical record only.
