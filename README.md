# Groundtruth

*An Analog Mission Registry.*

Groundtruth is an open, structured registry of operational and research
knowledge from the volunteer analog space mission sector — FMARS, MDRS,
LunAres, HI-SEAS, AMADEE, and beyond. The kind of sector institutional
literature largely ignores.

## The problem

Three waste streams in non-institutional analog mission research:

1. **Operational knowledge waste.** Engineering insights, failure modes,
   and lessons learned sit in narrative PDF reports on poorly-maintained
   websites, never reaching the people planning future missions. Every
   crew rediscovers the same generator failures, the same suit problems.
2. **Research comparability waste.** Studies run across missions use
   inconsistent instruments and reporting formats, so results can't be
   pooled — separately, they're anecdotes.
3. **Research registry gap.** No structured record exists of what research
   has actually been run at these missions, with what methods, what
   findings, published or not.

The knowledge exists. It just has no address.

## What's here

Four linked entity types, each stored as one JSON file per record under
`data/`, validated against a JSON Schema in `schema/`, and compiled into a
single queryable `groundtruth.sqlite`:

- **Mission** — station(s), crew designation, dates, institutional vs.
  volunteer, mission goal.
- **Crew Member** — pseudonymous (no names), role, gender, nationality,
  age, field of expertise.
- **Operational Event** — not just failures: successes, process
  innovations, crew dynamics, and observations too, each with a
  `pattern_tag` and `outcome` so recurring patterns are queryable, not
  just narrated.
- **Research Project** — what's been studied, by whom, with what methods,
  published or not.

Plus a **Source** registry tracking what document/page each record was
extracted from.

## Why this shape

- **SQLite, not flat CSV** — so a future browsable/queryable interface can
  sit on top without a data-layer rewrite. See the design spec §3.1 for
  what that interface is meant to do.
- **Pseudonymous crew data, fully open** — no names, but demographics are
  published in full under CC BY 4.0, not gated behind an access-control
  layer. See design spec §5 for the reasoning and the tradeoff.
- **JSON files as the contribution unit, SQLite as the generated artifact**
  — PRs are reviewable text diffs; `groundtruth.sqlite` is rebuilt from
  `data/`, never hand-edited. See `CONTRIBUTING.md`.

## Using this data

```bash
pip install -r requirements.txt   # jsonschema, for validation only
python scripts/validate.py schema/event.schema.json data/events/
python scripts/build_db.py        # rebuilds groundtruth.sqlite from data/
```

Or just query `groundtruth.sqlite` directly with any SQLite client — it's
committed and always current.

## Running the site locally

The site (`site/`) is a static, framework-free app that loads
`groundtruth.sqlite` via `fetch()` — this requires a real HTTP server,
opening `index.html` directly via `file://` will not work.

```bash
python scripts/build_db.py                          # ensure it's current
cp groundtruth.sqlite site/data/groundtruth.sqlite \
  2>/dev/null || (mkdir -p site/data && cp groundtruth.sqlite site/data/groundtruth.sqlite)
cd site && python3 -m http.server 8000
```

Then open `http://localhost:8000/`. `site/data/` is local-only — never
commit it (it's gitignored); the deployed site assembles its own fresh
copy at deploy time (see `.github/workflows/deploy-pages.yml`).

To run the site's own JS tests: `node --test site-tests/*.test.js` (the
bare-directory form, `node --test site-tests/`, does not work on all Node
versions — always glob the files explicitly).

## Current dataset

Run `python scripts/stats.py` for a snapshot of what's actually in
`groundtruth.sqlite` right now — record counts, event type breakdown,
most common recurring patterns, and crew data coverage.

## Contributing

See `CONTRIBUTING.md`. Short version: cite a real source, never include a
crew member's real name, validate before you open a PR.

## License

- **Data** (`data/`, `groundtruth.sqlite`): [CC BY 4.0](LICENSE-DATA)
- **Code and schema** (`scripts/`, `schema/`): [MIT](LICENSE-CODE)

## Status

v0.2 — schema, seed data from FMARS Crews 15–18 and Mars160, and a
browsable static site (`site/`) on top of `groundtruth.sqlite`: Missions
(actual mission records — station, dates, crew size, goal — drilling into
each one's own incidents), Incidents (a filterable cross-mission event
list for pattern-hunting), a Patterns dashboard, and an About page. The
site is deployed via GitHub Actions to GitHub Pages on every push to
`main` — **merging to `main` now triggers a live public deployment**, not
just a data-repo commit. See `.github/workflows/deploy-pages.yml`.
