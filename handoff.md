# Handoff

*Rewritten each session. Reflects current state, not history — see
decisions.md for the why-log.*

## Current state

**`main`: v0.1 (data layer) + v0.2 (browsable site) + v0.3-mdrs-pilot
(fetch tooling) all merged and pushed. This session also shipped a small
Incidents-view feature (shareable filtered links) directly to `main`.
Nothing from the MDRS pilot has reached `data/` yet — the Crew 335 draft
from the prior session is still the resume point.**

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

### This session — v0.3-mdrs-pilot merged; Incidents view gets shareable filtered links

`v0.3-mdrs-pilot` fast-forward-merged into `main` and pushed (no `data/`
change — fetch tooling and tests only, same as it was on the branch).

User's stated need: preparing as crew engineer for an FMARS mission,
wants to search prior missions for weak points (by system — Power,
ATVs/Transport, EVA Suits & Comms, Hab Structure, etc.) and what
solutions worked or didn't, and share specific findings with another
crew member. The Incidents view's filters and each event's
Response/Lesson/Outcome fields already covered the "search for problems
and solutions" need — confirmed by inspecting `schema/event.schema.json`
and the existing filter UI before building anything. The one real gap
was sharing: filter selections lived only in the DOM, so there was no
way to hand someone a link to, say, "all Power failures at FMARS."

Closed that gap: `router.js`'s `parseHash`/`routeToHash` now carry a
query-string component alongside the existing view/path-param, and
`incidents-view.js` syncs its four filters into the URL on every change
via `history.replaceState` (not `location.hash`, to avoid a full
hashchange re-render collapsing the sidebar on every filter click), plus
a "Copy link to this view" button. A shared link fully restores both the
filter selections and the result list on load. The old single-station
path deep link (`#/incidents/FMARS`) still works as a fallback. 7 new
router tests + verified live in a real browser (Playwright against a
locally-built `groundtruth.sqlite`) — filter-then-copy-link and
load-a-filtered-link were both exercised end to end, not just unit
tested. 81 tests total pass (33 JS + 48 Python).

**Confirmed user priority for data coverage: FMARS first** (that's what
they're actually preparing for), MDRS and other stations to grow in
later — this re-orders the "what's next" list below relative to prior
sessions, which had been MDRS-pilot-driven.

Only the Incidents view got shareable links this session. Missions and
Patterns views don't have this yet — not asked for, not built.

## What's next

Pick one of these up next session. Reordered this session to put FMARS
data-completeness first — the user's confirmed, immediate use case is
FMARS crew-engineer prep, with MDRS (and further stations) explicitly a
"grow it later" goal, not the current priority:

1. **Process Flashline Crew Reports pages 83-95** (Mars160/FMARS-leg
   section, ~430 unprocessed lines) — this is FMARS/Mars160 content
   already in scope for the immediate use case, and has been the top
   v0.1-era data-population priority since 2026-08-26. Directly grows the
   dataset the crew-engineer search feature (this session) now makes
   shareable.
2. **Resume the Crew 335 (MDRS) draft** when MDRS coverage becomes the
   priority again: run Stage 3 (fresh-context self-check against the
   source), then Stage 4 (human review → commit to `data/`). Nothing
   about this draft expires — safe to leave parked.
3. **Decide on the full ~715-page MDRS crawl** (same "when MDRS becomes
   priority" caveat). At `Crawl-delay: 10`, that's ~2+ hours minimum — a
   background job, not interactive.
4. Extend the shareable-filtered-links pattern (this session, Incidents
   view only) to Missions/Patterns if useful once used in practice.
5. Carried over from v0.1 (untouched this session, still open — see
   decisions.md's 2026-08-26 entries for full context on each):
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
