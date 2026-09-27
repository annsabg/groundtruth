# Handoff

*Rewritten each session. Reflects current state, not history — see
decisions.md for the why-log.*

## Current state

**`main`: v0.1 (data layer) + v0.2 (browsable site) + v0.3-mdrs-pilot
(fetch tooling) all merged and pushed. This session shipped the
Incidents-view shareable-links feature, committed FMARS's 2026 mission
(Crew 19, "Tiriganiaq") end to end, activated visitor analytics, built a
reusable draft-review tool, and — the actual resume point — has a
second full batch (Mars160/FMARS pages 83-95) drafted, Stage-3-checked,
and fix-applied, but sitting unreviewed and uncommitted in
`sources-local/flashline-pages-83-95/drafts/` because the session ended
before human review happened. Nothing from the MDRS pilot has reached
`data/` yet — the Crew 335 draft from several sessions ago was never
saved to disk and no longer exists except as a summary in this file's
history; picking MDRS back up means re-extracting from
`sources-local/mdrs-crew-reports-raw/`, not resuming a saved draft.**

**Next session should start here:** review
`sources-local/flashline-pages-83-95/drafts/` (run
`python scripts/summarize_drafts.py sources-local/flashline-pages-83-95/drafts`
for the compact view), then either commit it (copy into `data/`, fill
`verified_by`, `build_db.py`, commit+push per Stage 4/5 —
see the "This session" write-up below for full context) or send back
specific changes first. Nothing else blocks on this; it's just waiting
for the human-review step that didn't get to happen.

### v0.1 — data layer (complete, on `main`)

Full data layer, seed data, and tooling: five JSON schemas (Mission, Crew
Member, Event, Research Project, Source), `validate.py` (schema +
`--check-refs` referential-integrity checking), `build_db.py`,
`scripts/stats.py`, `CONTRIBUTING.md`, CI, `README.md`,
`docs/extraction-workflow.md`.

| Entity            | Count | Notes |
|--------------------|------:|-------|
| Mission            | 6     | FMARS Crews 15–19 (2023–2026) + MARS160-2017 |
| Operational Event   | 71    | Hypatia brief + Flashline reports + FMARS-C19-2026 sol reports |
| Crew Member         | 34 of 37 known slots | 5/7/4/7/5 across FMARS C15–C19, 6 for MARS160-2017 |
| Research Project    | 6     | RP-001–003 (FMARS C15/C16, hand-curated) + RP-004–006 (FMARS C19) |
| Source              | 8     | citation registry, keyed by `source_id` + `mission_ids[]` |

v0.1's original 5/60/29/3/6 counts held through v0.2 and the v0.3-pilot
merge (both were tooling/site-only, no `data/` change) — this session's
FMARS-C19-2026 addition (below) is the first change to these numbers
since v0.1 itself. Run `python scripts/stats.py` for the live snapshot,
including the "34 of 37" gap — see `FMARS-C17-2025`'s known
crew_size/crew_member-count mismatch in Known Gaps.

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

### This session — FMARS Crew 19 (Tiriganiaq, July 2026): full pipeline round-trip, Stages 1-5

User asked to pull FMARS's 2026 mission reports "from the site." Found
and fetched all 8 available sol reports (sols 1-6, 8, 9 — sol 7 was
never published under any listing checked) from
`fmars.marssociety.org/flashline-station-misson-updates/`, plus a "Meet
the Crew" bio page that resolved most crew-expertise ambiguity the sol
reports alone couldn't. Saved raw + extracted-text copies to
`sources-local/FMARS-C19-2026/` (gitignored) with a fetch-provenance
manifest, same pattern as the MDRS pilot.

**Stage 2 (extraction)** drafted 22 records — 1 Mission
(`FMARS-C19-2026`, crew of 5, 2026-07-15 to 2026-07-23), 2 Sources, 5
Crew Members, 11 Operational Events, 3 Research Projects — as JSON files
under a local `drafts/` staging directory (not written to `data/` yet).
Notable calls made during extraction, not silently glossed over:
- The bio page lists 6 people under "Crew 19," but the sol reports are
  explicit only 5 were physically on-site (the 6th ran a Mars-dust
  experiment remotely) — documented, only 5 Crew Member records made.
- Sol 7's ATV-mud-miring incident has no primary report; reconstructed
  from a Sol 8 retrospective mention, confidence marked accordingly.
- One crew member's stated pronouns conflict within the source itself
  (she/her then they/them for the same person, likely a templated-bio
  copy artifact) — gender left `undisclosed` rather than picked
  arbitrarily.

**Stage 3 (fresh-context self-check)**, dispatched as an independent
subagent with zero prior context, found real, non-trivial problems —
this is exactly what the two-pass design exists to catch:
1. **Systemic real-name leak, 16 of 22 files.** Every *structured* field
   correctly kept real names out (bios on this source, unlike most prior
   FMARS sources, used real full names throughout) — but real names were
   still being reproduced verbatim inside *quoted* `source_citation`/
   `citation`/`methodology_notes` text, on the mistaken assumption that
   quoting a source exempts it from the no-real-names rule. It does not.
   Worst instance: `RP-005`'s `methodology_notes` claimed a name "is not
   reproduced here" while that same name appeared, unredacted, in the
   same file's `citation` field two fields earlier — a self-contradiction
   caught by the review, not by the extractor. Fixed across all 16 files
   by redacting every quoted name to `[name redacted]` or a role tag.
   **New, sharper form of the 2026-08-26 "real-name-leak pattern" rule:
   quoting a source is not an exemption — see decisions.md.**
2. **A fabricated causal claim** in one event (`EVT003`): drafted as "a
   GPS malfunction caused the team to misjudge the distance," when the
   source actually describes these as two separate, uncorrelated facts.
   Rewrote to stop asserting causation the source doesn't support; also
   reclassified `Near-Miss` → `Failure` since the source explicitly says
   "no compromise to crew safety."
3. **A date misattribution**: the ATV tire puncture was drafted as
   happening Sol 7 (same day as the mud-miring); the source's own "went
   flat yesterday" (relative to the Sol 9 report) places it Sol 8.
   Re-anchored the event and fixed the dependent event's description.

**Stage 4 (human review)** was an explicitly light pass, not a deep
one — the user said so directly and approved committing on that basis
rather than have it wait. Recorded here as-is, not overstated:
`verified_by`/`approved_by` on these 22 records reflect that level of
review, not a from-scratch independent check of every field. The user
also asked for a faster/friendlier review format for future batches —
raw JSON file browsing was "not very user friendly" — noted as an open
item below.

**Stage 5**: `build_db.py` rebuilt `groundtruth.sqlite`, `--check-refs`
passed clean across the whole `data/` tree, all 81 tests still pass,
committed and pushed to `main` (commit `7e9f252`). The staging
`drafts/` directory was deleted after commit; the raw fetched
sources (`sol-*.html`/`.txt`, `meet-the-crew.html`/`.txt`,
`manifest.json`) remain under `sources-local/FMARS-C19-2026/` for any
future re-check.

### This session — visitor analytics, and a real draft-review tool

Two smaller asks landed cleanly:

- **GoatCounter analytics** wired into `site/index.html` (privacy-friendly:
  no cookies, no consent banner). Activated with the user's real site
  code (`groundtruth.goatcounter.com`) — not just placeholder-wired, live.
  Documented in `CONTRIBUTING.md`.
- **`scripts/summarize_drafts.py`** (+ `tests/test_summarize_drafts.py`,
  11 tests): turns any Stage 2 `drafts/{sources,missions,crew_members,
  events,research_projects}/*.json` directory into one skimmable line per
  record. Built specifically because reviewing FMARS-C19-2026's 22 raw
  JSON files directly was "not very user friendly" (the user's words).
  Used for real on the very next batch (below) — this is now the actual
  review step, not a one-off chat summary.

### This session — Mars160/FMARS pages 83-95: Stage 2+3 done, Stage 4 never happened (session ended first)

"Process Flashline Crew Reports pages 83-95" (top data-population
priority since 2026-08-26) turned out to mean the **Mars160/FMARS-leg
Final Mission Report + 12→actually-19 daily Commander Reports**
(2017-07-20 through 2017-08-11) — content that **adds to the existing
`MARS160-2017` mission**, not a new one. Found the local source
(`~/Documents/Other Work/The Huge Analog Mission Database (THAMB)/
Flashline Crew Reports.pdf`, plus an already-extracted `.txt` twin with
page markers) — a *very* useful discovery: THAMB is Anna's separate
planning workspace outside this repo, referenced in decisions.md's
2026-08-26 entry but not previously located this concretely. Pages
83-95 extracted to `sources-local/flashline-pages-83-95/pages-83-95.txt`.

**Stage 2** drafted 10 records, staged at
`sources-local/flashline-pages-83-95/drafts/`:
- 1 **Source update** (not a new record — extends the existing
  `SRC-flashline-crew-reports` to also cover `MARS160-2017` and
  `research`).
- 5 **new Operational Events** (`MARS160-2017-EVT006`–`EVT010`): a
  3+-week pre-landing weather delay that killed the mission's entire
  planned engineering workstream (high significance — new, previously
  undocumented context); a fuel-conserving generator schedule; two
  separate rain-disrupted EVAs; a ground-conditions-blocked probe
  installation.
- 4 **new Research Projects** (`RP-007`–`RP-010`): patterned-ground/
  impact-lithology geology, extremophile-biosignature/Arctic-microbial
  biology, an MDRS-vs-FMARS crew-cohesion psychology study (8-test
  battery), and 360°/stereograph imaging + habitat VR/3D documentation —
  the richest science-program material of any source in this dataset
  so far.
- **This source uses crew members' real names throughout** (unlike most
  prior FMARS sources) — the sharpened 2026-09-25 rule (quotes aren't
  exempt) was applied from the start this time, not discovered after
  the fact.
- **Deliberately not touched**: this same primary source independently
  confirms specific real dates for all 5 *existing* `MARS160-2017`
  events (`EVT001`-`EVT005`, currently sourced from a secondary
  synthesis brief with vague placeholder sols) — Sol 1 = 2017-07-20 is
  explicitly stated ("First day in Sim"), so exact sols are now
  derivable. Left those 5 records alone rather than silently revise
  already-approved data outside a dedicated review — flagged as a
  follow-up in Known Gaps instead.

**Stage 3** (fresh-context subagent, zero prior context) found 4 minor,
all-fixed issues, and confirmed the important negatives held: **zero
real-name leaks**, **zero fabricated claims**, **zero duplicates of
EVT001-005**. Fixed:
1. `EVT010`'s redacted-quote placeholder tags (`[Geologist A]`/`[Geologist B]`)
   were reused inconsistently, misattributing one redacted individual's
   actions to the other's tag — same two people, wrong tag on two of
   the three mentions.
2. `EVT008`'s citation misattributed its quote to "August 6th... recounting
   the prior days" when it's actually the July 24th report directly — a
   plain mislabel, quote itself was accurate.
3. `RP-007`/`RP-010`'s `comparable_studies` cross-reference was
   one-directional (`RP-010→RP-007` but not back) — this dataset's own
   stated precedent (RP-002↔RP-003) is bidirectional; made it match.
4. The Source-record update said "12 daily Commander Reports" —
   independently grepped and recounted at **19** — fixed.

**Stage 4 (human review) has not happened.** The batch was presented to
the user in the compact `summarize_drafts.py` format, but the session
ended (user closing the window) before they gave a go/no-go. **Nothing
has been copied into `data/`; nothing has been committed.** This is the
literal, complete resume point for next session — see "Current state"
above.

## What's next

**Start here — the actual resume point:**

1. **Review and commit (or send back) the Mars160/FMARS pages 83-95
   batch**, staged at `sources-local/flashline-pages-83-95/drafts/`.
   Run `python scripts/summarize_drafts.py sources-local/flashline-pages-83-95/drafts`
   for the compact view. Already Stage-3-checked and fix-applied — just
   needs the human review that didn't happen before the session ended.
   On approval: copy into `data/`, fill `verified_by`, `python
   scripts/build_db.py`, `git add data/ groundtruth.sqlite`, commit,
   push (Stage 4/5, same mechanics as FMARS-C19-2026's commit `7e9f252`).

Then, in priority order (FMARS-first remains the user's confirmed
immediate use case; MDRS and further stations are "grow it later"):

2. **Give FMARS-C19-2026's drafted records a real deep review**,
   whenever there's time — its Stage 4 was explicitly light, not deep.
   Nothing blocks this; corrections would just be ordinary edits + a
   `validate.py`/`build_db.py` re-run.
3. **Upgrade `MARS160-2017-EVT001`–`EVT005`'s sols/citations/confidence**
   using the newly-found primary source (`sources-local/flashline-pages-83-95/`)
   — their real dates are now derivable (Sol 1 = 2017-07-20), instead of
   the placeholder sols they currently carry from a secondary synthesis
   brief. Deliberately not done in the pages-83-95 batch itself (see
   that write-up above) — a separate, dedicated revision pass.
4. **Resume the Crew 335 (MDRS) draft** when MDRS coverage becomes the
   priority again — re-running Stage 2 from
   `sources-local/mdrs-crew-reports-raw/`, not resuming a saved draft
   (the prior draft was never written to disk and no longer exists).
5. **Decide on the full ~715-page MDRS crawl** (same "when MDRS becomes
   priority" caveat). At `Crawl-delay: 10`, that's ~2+ hours minimum — a
   background job, not interactive.
6. Extend the shareable-filtered-links pattern (Incidents view only so
   far) to Missions/Patterns if useful once used in practice.
7. Carried over from v0.1 (untouched this session, still open — see
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
- **Resolved (drafted, not yet committed):** Flashline Crew Reports
  pages 83-95 were extracted this session — see "What's next" #1 above
  for the exact resume step. Not a gap anymore once that batch lands in
  `data/`.
- **`MARS160-2017-EVT001`–`EVT005` carry placeholder sols from a
  secondary source**, even though their real dates are now derivable
  from the primary source found this session — see "What's next" #3.
- **`sol` (Event) and Mission-level facts have no structured
  uncertainty/confidence option** — v0.2 schema candidate; see
  decisions.md, 2026-08-26 "structural uncertainty-disclosure gap."
- **`FMARS-C17-2025` `crew_size` (6) exceeds its 4 documented Crew Member
  records.** Left as-is (Task 16); unresolved.
- **Privacy checks must be whole-repository in scope, not `data/`-scoped,
  AND quoted text is not exempt from the no-real-names rule** (decisions.md,
  2026-08-26 "the real-name-leak pattern"; sharpened this session — see
  the 2026-09-25 entry). The FMARS-C19-2026 extraction correctly kept
  real names out of every structured field but reproduced them verbatim
  inside quoted citation text in 16 of 22 draft files, caught only by the
  Stage 3 fresh-context self-check, not by the extractor itself. Fixed,
  but the underlying trap — "I'm just quoting the source" — will recur
  on any future source (like this one) that uses real names instead of
  titles/pseudonyms in its own prose. Check for it explicitly.
- **FMARS-C19-2026-CM05's gender is `undisclosed` due to a genuine
  source conflict** (she/her and they/them both used for the same person
  in the same bio paragraph, likely a templated-bio copy artifact) — not
  an oversight, a deliberate non-guess. See that record's
  `source_citation` for the full reasoning if revisited.
- **Resolved:** `FMARS-C15-2023-EVT010` mis-tag — see prior handoff
  entries; no longer open, noted for the historical record only.
