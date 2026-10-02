# Equipment & Packing Lessons — Design

*2026-10-02. Status: approved in brainstorming, pending spec review.*

## 1. Purpose

Crews' equipment lessons — what they wished they'd brought, what proved
essential, what to bring spares of, what wasn't worth the weight — are
already in Groundtruth's sources, but today they're buried inside
Operational Event `lesson` text (≈18 of 71 events), often several items
per lesson, and advice not tied to any incident isn't captured at all.

This feature makes them first-class records, tagged by living/operational
area (food, hygiene, water, …), and surfaces them as a filterable packing
checklist.

**Priority order** (agreed): a crew-facing checklist first; cross-mission
pattern analysis later. The data model must support the later analysis
without re-extraction, but no analysis UI is built now.

**Success criteria**

- A crew heading to a given station can open `#/packing`, filter by
  station/area, and print a usable checklist.
- Every item traces to a source citation and passes the same
  Stage 2 → Stage 3 → Stage 4 pipeline as every other record.
- Items recommended by several crews can be grouped (via `item_key`)
  so recurrence analysis is possible later.

## 2. Data model

New entity **Equipment Item**: `schema/equipment_item.schema.json`,
records in `data/equipment_items/{item_id}.json`, table `equipment_item`.

| Field | Req. | Type / values | Notes |
|---|---|---|---|
| `item_id` | ✓ | pattern `^.+-EQP[0-9]{3}$` | `{mission_id}-EQP{NNN}`, mirrors `-EVT{NNN}` |
| `mission_id` | ✓ | string | Must reference an existing Mission |
| `station` | ✓ | same enum as `event.station` | Must be one of the mission's `stations` |
| `item` | ✓ | string, minLength 1 | Short, specific name ("Spark plugs matched to ATV models") |
| `area` | ✓ | enum, see below | Closed list; adding an area is a deliberate schema change |
| `advice_type` | ✓ | `Wished Brought`, `Essential`, `Bring Spare`, `Don't Bring` | |
| `rationale` | ✓ | string, minLength 1 | Why, in the source's terms |
| `item_key` | — | pattern `^[a-z0-9]+(-[a-z0-9]+)*$` | Open grouping key, e.g. `spare-comms-earpiece`; same key = same item across missions. Vocabulary grows from data, like `pattern_tag`. |
| `related_events` | — | array of event IDs | Events the advice derives from; empty/absent for non-incident advice |
| `source_id` | — | string | References Source; optional for parity with Event, but set on every real record |
| `source_citation` | ✓ | string, minLength 1 | Specific location in the source |
| `confidence` | ✓ | `A`/`B`/`C`/`D` | Same meaning as on Event |
| `verified_by` | ✓ | string, minLength 1 | Reviewer initials |

`additionalProperties: false`.

**Area enum (13):** `Food & Cooking`, `Water & Drinking`,
`Personal Hygiene & Sanitation`, `Clothing & Thermal`,
`Sleep & Personal Comfort`, `Medical & First Aid`,
`Safety & Environmental Monitoring`, `Tools & Spare Parts`,
`Power & Electronics`, `EVA Suits & Comms`, `Vehicles`, `Science & Lab`,
`Morale & Recreation`.

**Deliberately excluded:** quantity, weight, vendor/model. Sources rarely
state them; mostly-empty fields invite fabrication. Revisit if real data
shows otherwise.

**Source schema change:** `source.covers` enum gains `"equipment"`.

## 3. Tooling changes

- `scripts/build_db.py` — add `equipment_item` to `ENTITIES`
  (`related_events` stored the same way as on Event).
- `scripts/validate.py --check-refs` — for every equipment item:
  `mission_id` exists; `station` ∈ that mission's `stations`;
  `source_id` exists (if set); every `related_events` entry exists.
- `scripts/summarize_drafts.py` — handle an `equipment_items/` draft
  subdirectory with a compact one-line format:
  `{item_id} [{area}/{advice_type}] {item} — {rationale…} (key: {item_key|—}; events: …)`.
- `scripts/stats.py` — include the Equipment Item count.
- `CONTRIBUTING.md` — document the entity, area list, and `item_key`
  conventions.

## 4. Extraction pipeline

### 4.1 One-time backfill from existing events

1. **Candidates:** query events whose `lesson`/`response` names a
   physical item to bring, spare, or leave behind (≈18 today). This list
   is a starting point, not the scope boundary.
2. **Stage 2:** for each candidate, re-open the event's original source
   in `sources-local/` (not just the event's lesson text) and draft one
   Equipment Item per distinct item, `related_events` → that event,
   inheriting its `source_id`/`source_citation`/`confidence`. Advice in
   the surrounding source text that the event didn't capture is drafted
   too. Drafts go to `sources-local/equipment-backfill/drafts/equipment_items/`.
3. **Stage 3:** fresh-context check dispatched on Opus (stronger than
   Stage 2), verifying each draft against the source text — with
   particular attention to inferred advice not actually stated.
4. **Stage 4:** human review via `summarize_drafts.py`; approved records
   copied to `data/equipment_items/` with `verified_by`, then
   `build_db.py`.

### 4.2 Going forward

`docs/extraction-workflow.md` Stage 2 prompt adds Equipment Item to the
entity list. Stages 3–5 unchanged.

### 4.3 Extraction rules (to be added to the workflow doc)

- **Explicit only.** Record an item only when the source names it or
  clearly implies it ("we had no X and needed it"). Do not infer advice
  from a failure alone ("pump failed" ≠ "bring a spare pump").
- **`Essential` requires the crew's own emphasis** ("critical",
  "couldn't have managed without") — having packed something isn't enough.
- **`item_key`:** reuse an existing key when clearly the same item;
  otherwise leave it unset. Keys are assigned or confirmed at Stage 4,
  never invented speculatively at Stage 2.
- Existing rules apply unchanged: no real names (including inside quoted
  citations), one record per distinct claim, cite specific locations.

## 5. Site

New **Packing** tab, route `#/packing`, nav order Missions · Incidents ·
Packing · Patterns · About.

- **Filters** (sidebar, same pattern as Incidents): Station, Area,
  Advice kind. Synced to the URL query string via
  `routeToHash` + `history.replaceState`; unknown values in a hand-edited
  link are ignored.
- **Layout:** grouped by area (headings in enum order, empty areas
  hidden). Within an area, `Wished Brought` / `Essential` / `Bring Spare`
  rows first; `Don't Bring` rows in a separate sub-list after them.
- **Grouping:** records sharing an `item_key` render as one row with a
  "flagged by N crews" badge (N = distinct `mission_id`s); records with no
  key render individually.
- **Row expand-in-place:** shows each contributing record's mission,
  rationale, a link to the mission page (`#/missions/{mission_id}`) when
  `related_events` is set, and the opt-in "See source" toggle. Delegated
  click handler bound once per list element (see commit `b854ab6`).
- **Print stylesheet:** hides nav/sidebar, renders rows as tick-box
  lines, expanded detail hidden.
- **Out of scope for v1:** persistent in-browser tick state, recurrence
  charts on the Patterns tab, per-event pages.

**Code layout:** `site/js/packing-view.js` (view);
`buildEquipmentQuery(filters)` in `site/js/db.js`;
`groupEquipmentItems(rows)` in `site/js/util.js` (pure, testable);
route registered in `app.js`; nav link in `site/index.html`.

## 6. Testing

**Python (pytest):** schema fixtures — a valid record, and invalid ones
(bad `area`, bad `advice_type`, missing `rationale`, malformed
`item_key`); `check_references` rejects an unknown `related_events` ID
and a station outside the mission's stations; `build_db` creates the
`equipment_item` table with the expected columns.

**JS (node --test):** `buildEquipmentQuery` for no filters, each single
filter, and combined filters; `groupEquipmentItems` merges same-key
records, keeps keyless records separate, and counts distinct missions;
router parses `#/packing?…` query filters.

**Manual:** local build in a browser — filters, URL sync, expand/collapse
after filter changes, print preview.

## 7. Delivery order

1. Schema + tooling (build, validate, summarize, stats, docs).
2. Backfill batch through Stages 2–4 (blocks on human review).
3. Site view — buildable and testable against draft data before step 2
   completes, but not deployed until approved records are in `data/`.
