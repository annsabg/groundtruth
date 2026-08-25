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

## Contributing

See `CONTRIBUTING.md`. Short version: cite a real source, never include a
crew member's real name, validate before you open a PR.

## License

- **Data** (`data/`, `groundtruth.sqlite`): [CC BY 4.0](LICENSE-DATA)
- **Code and schema** (`scripts/`, `schema/`): [MIT](LICENSE-CODE)

## Status

v0.1 — schema and initial seed data from FMARS Crews 15–18 and Mars160.
Not a website yet; see the design spec for why that's a deliberate,
scoped-for choice rather than an oversight.
