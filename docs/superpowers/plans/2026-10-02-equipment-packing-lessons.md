# Equipment & Packing Lessons Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an Equipment Item record type (what crews wished they'd brought, found essential, need spares of, or shouldn't bring — tagged by area), backfill it from existing incidents, and surface it as a filterable, printable packing checklist at `#/packing`.

**Architecture:** A new JSON-schema entity mirroring Operational Event, wired into the existing Python tooling (`build_db.py`, `validate.py`, `summarize_drafts.py`, `stats.py`) and CI. The site gets one new view module (`packing-view.js`) built on two new pure, unit-tested helpers (`buildEquipmentQuery` in `db.js`, `groupEquipmentItems` + `pickKnownFilters` in `util.js`). The backfill runs through the existing Stage 2 → 3 → 4 extraction pipeline and blocks on human review.

**Tech Stack:** Python 3.11 + jsonschema + pytest; framework-free ES modules + sql.js in the browser; `node --test` for site tests.

**Spec:** `docs/superpowers/specs/2026-10-02-equipment-packing-lessons-design.md`

## Global Constraints

- Area enum, exactly and in this order: `Food & Cooking`, `Water & Drinking`, `Personal Hygiene & Sanitation`, `Clothing & Thermal`, `Sleep & Personal Comfort`, `Medical & First Aid`, `Safety & Environmental Monitoring`, `Tools & Spare Parts`, `Power & Electronics`, `EVA Suits & Comms`, `Vehicles`, `Science & Lab`, `Morale & Recreation`.
- `advice_type` enum, exactly: `Wished Brought`, `Essential`, `Bring Spare`, `Don't Bring`.
- `item_id` pattern `^.+-EQP[0-9]{3}$`; `item_key` pattern `^[a-z0-9]+(-[a-z0-9]+)*$`.
- No quantity / weight / vendor fields.
- No real names anywhere in a record, including inside quoted `source_citation` text (decisions.md 2026-09-25).
- Stage 3 self-check is dispatched on Opus, in a fresh context.
- Raw source documents are never committed (`sources-local/` is gitignored).
- **Do not push to `main` until Task 8 is complete** — every push deploys the site, and the Packing tab must not go live empty. Commit locally only.
- Commit messages end with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.

## Review Focus

1. A filter value containing `&` or `'` (`Water & Drinking`, `Don't Bring`) must survive the URL round trip intact — pinned in Task 6 (router test).
2. A hand-edited or stale link with an unknown filter value (`?area=Water`) must be ignored, not select nothing or break the view — pinned in Task 6 (`pickKnownFilters` test).
3. Two crews giving *conflicting* advice for the same `item_key` (one `Bring Spare`, one `Don't Bring`) must stay visible as two rows, not merge into one — pinned in Task 6 (`groupEquipmentItems` groups by area + advice_type + item_key).
4. One mission contributing two records with the same key must count as 1 crew, not 2 — pinned in Task 6.
5. Clicking a packing row after changing a filter must still expand it (the stacked-listener bug fixed in `b854ab6`) — pinned in Task 7's manual browser check, and by binding the handler once per element.

---

## File Structure

| File | Responsibility |
|---|---|
| `schema/equipment_item.schema.json` (new) | Equipment Item record contract |
| `schema/source.schema.json` | `covers` gains `"equipment"` |
| `data/equipment_items/.gitkeep` (new) | Keeps the dir in git so CI's validate loop doesn't crash on a missing path |
| `tests/fixtures/valid_equipment_item.json`, `invalid_equipment_item.json` (new) | Schema fixtures |
| `scripts/build_db.py` | `equipment_item` table |
| `scripts/validate.py` | Equipment Item reference checks |
| `scripts/summarize_drafts.py` | Compact draft line for equipment items |
| `scripts/stats.py` | Equipment Item count + advice_type breakdown |
| `.github/workflows/validate.yml` | Validate `data/equipment_items/` |
| `docs/extraction-workflow.md`, `CONTRIBUTING.md` | Extraction rules + vocabulary docs |
| `site/js/db.js` | `buildEquipmentQuery(filters)` |
| `site/js/util.js` | `groupEquipmentItems(rows)`, `pickKnownFilters(query, allowed)` |
| `site/js/event-list.js` | Export existing `linkHtmlFor` for reuse |
| `site/js/packing-view.js` (new) | Packing tab view |
| `site/js/app.js`, `site/index.html`, `site/css/style.css` | Route, nav link, styles + print stylesheet |

---

### Task 1: Equipment Item schema, fixtures, CI validation

**Files:**
- Create: `schema/equipment_item.schema.json`, `tests/fixtures/valid_equipment_item.json`, `tests/fixtures/invalid_equipment_item.json`, `data/equipment_items/.gitkeep`
- Modify: `schema/source.schema.json` (`covers` enum), `.github/workflows/validate.yml`
- Test: `tests/test_validate.py`

**Interfaces:**
- Produces: the schema file and `tests/fixtures/valid_equipment_item.json` (`item_id` `FMARS-C16-2024-EQP001`, `mission_id` `FMARS-C16-2024`, `station` `FMARS`, `area` `Vehicles`, `advice_type` `Wished Brought`, `item_key` `atv-spark-plugs`, `related_events` `["FMARS-C16-2024-EVT001"]`) — used by Tasks 2 and 3.

- [ ] **Step 1: Write the fixtures**

`tests/fixtures/valid_equipment_item.json`:
```json
{
  "item_id": "FMARS-C16-2024-EQP001",
  "mission_id": "FMARS-C16-2024",
  "station": "FMARS",
  "item": "Spark plugs matched to each ATV model",
  "area": "Vehicles",
  "advice_type": "Wished Brought",
  "rationale": "Only one of five ATVs was operational on arrival; one had failed ignition and replacement parts were not available in Resolute.",
  "item_key": "atv-spark-plugs",
  "related_events": ["FMARS-C16-2024-EVT001"],
  "source_id": "SRC-flashline-crew-reports",
  "source_citation": "FMARS Crew 16 Daily Report, Crew Engineer, 2024-06-19",
  "confidence": "B",
  "verified_by": "ASG"
}
```

`tests/fixtures/invalid_equipment_item.json` (bad `area`, missing `rationale`):
```json
{
  "item_id": "FMARS-C16-2024-EQP001",
  "mission_id": "FMARS-C16-2024",
  "station": "FMARS",
  "item": "Snacks",
  "area": "Snacks",
  "advice_type": "Wished Brought",
  "source_citation": "FMARS Crew 16 Daily Report",
  "confidence": "B",
  "verified_by": "ASG"
}
```

- [ ] **Step 2: Write the failing tests** — append to `tests/test_validate.py`:

```python
def _equipment_variant(tmp_path, **changes):
    """Copy of the valid equipment fixture with fields changed; a value of
    None deletes the field. Returns the path of the written variant."""
    import json
    record = json.loads((FIXTURES / "valid_equipment_item.json").read_text())
    for key, value in changes.items():
        if value is None:
            record.pop(key, None)
        else:
            record[key] = value
    path = tmp_path / "variant.json"
    path.write_text(json.dumps(record))
    return path


def test_equipment_item_schema_accepts_valid_record():
    errors = validate_file(SCHEMA / "equipment_item.schema.json", FIXTURES / "valid_equipment_item.json")
    assert errors == []


def test_equipment_item_schema_rejects_invalid_record():
    errors = validate_file(SCHEMA / "equipment_item.schema.json", FIXTURES / "invalid_equipment_item.json")
    assert len(errors) >= 2  # bad area AND missing rationale


def test_equipment_item_schema_rejects_unknown_area(tmp_path):
    path = _equipment_variant(tmp_path, area="Hygiene")
    assert validate_file(SCHEMA / "equipment_item.schema.json", path) != []


def test_equipment_item_schema_rejects_unknown_advice_type(tmp_path):
    path = _equipment_variant(tmp_path, advice_type="Nice to Have")
    assert validate_file(SCHEMA / "equipment_item.schema.json", path) != []


def test_equipment_item_schema_rejects_missing_rationale(tmp_path):
    path = _equipment_variant(tmp_path, rationale=None)
    assert validate_file(SCHEMA / "equipment_item.schema.json", path) != []


def test_equipment_item_schema_rejects_malformed_item_key(tmp_path):
    for bad in ["Spare Comms", "spare_comms", "-spare", "spare--comms"]:
        path = _equipment_variant(tmp_path, item_key=bad)
        assert validate_file(SCHEMA / "equipment_item.schema.json", path) != [], bad


def test_equipment_item_schema_rejects_malformed_item_id(tmp_path):
    path = _equipment_variant(tmp_path, item_id="FMARS-C16-2024-EQ1")
    assert validate_file(SCHEMA / "equipment_item.schema.json", path) != []


def test_equipment_item_schema_accepts_record_without_optional_fields(tmp_path):
    path = _equipment_variant(tmp_path, item_key=None, related_events=None, source_id=None)
    assert validate_file(SCHEMA / "equipment_item.schema.json", path) == []


def test_equipment_item_schema_rejects_quantity_field(tmp_path):
    path = _equipment_variant(tmp_path, quantity=4)
    assert validate_file(SCHEMA / "equipment_item.schema.json", path) != []


def test_source_schema_accepts_equipment_in_covers(tmp_path):
    import json
    record = json.loads((FIXTURES / "valid_source.json").read_text())
    record["covers"] = ["events", "equipment"]
    path = tmp_path / "source.json"
    path.write_text(json.dumps(record))
    assert validate_file(SCHEMA / "source.schema.json", path) == []
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `pytest tests/test_validate.py -v -k "equipment"`
Expected: FAIL — `FileNotFoundError` for `schema/equipment_item.schema.json`, and the `covers` test fails on `'equipment' is not one of [...]`.

- [ ] **Step 4: Write the schema** — `schema/equipment_item.schema.json`:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://groundtruth.dev/schema/equipment_item.schema.json",
  "title": "Equipment Item",
  "type": "object",
  "properties": {
    "item_id": {
      "type": "string",
      "pattern": "^.+-EQP[0-9]{3}$",
      "description": "Format {mission_id}-EQP{NNN}."
    },
    "mission_id": {"type": "string"},
    "station": {
      "enum": ["FMARS", "MDRS", "LunAres", "HI-SEAS", "AMADEE", "Other"],
      "description": "The single station this advice applies to. Must be one of mission.stations for this item's mission_id (checked by scripts/validate.py's check_references())."
    },
    "item": {
      "type": "string",
      "minLength": 1,
      "description": "Short, specific item name, e.g. 'Spark plugs matched to each ATV model'."
    },
    "area": {
      "enum": [
        "Food & Cooking", "Water & Drinking", "Personal Hygiene & Sanitation",
        "Clothing & Thermal", "Sleep & Personal Comfort", "Medical & First Aid",
        "Safety & Environmental Monitoring", "Tools & Spare Parts",
        "Power & Electronics", "EVA Suits & Comms", "Vehicles", "Science & Lab",
        "Morale & Recreation"
      ],
      "description": "Closed list. Adding an area is a deliberate schema change — see CONTRIBUTING.md."
    },
    "advice_type": {
      "enum": ["Wished Brought", "Essential", "Bring Spare", "Don't Bring"],
      "description": "Essential requires the crew's own emphasis in the source — having packed something is not enough. See docs/extraction-workflow.md."
    },
    "rationale": {
      "type": "string",
      "minLength": 1,
      "description": "Why, in the source's own terms."
    },
    "item_key": {
      "type": "string",
      "pattern": "^[a-z0-9]+(-[a-z0-9]+)*$",
      "description": "Open grouping key: records about the same item across missions share a key (e.g. 'spare-comms-earpiece'). Vocabulary grows from data, like event.pattern_tag. Assigned or confirmed at Stage 4 review, never invented speculatively at Stage 2."
    },
    "related_events": {
      "type": "array",
      "items": {"type": "string"},
      "description": "Event IDs this advice derives from. Empty or absent for advice not tied to an incident."
    },
    "source_id": {
      "type": "string",
      "description": "References Source.source_id. Optional for parity with Event, but should be set on every real record."
    },
    "source_citation": {"type": "string", "minLength": 1},
    "confidence": {
      "enum": ["A", "B", "C", "D"],
      "description": "A: formal engineering report. B: daily narrative report. C: journalist/XO report. D: secondhand/inferred."
    },
    "verified_by": {"type": "string", "minLength": 1}
  },
  "required": [
    "item_id", "mission_id", "station", "item", "area", "advice_type",
    "rationale", "source_citation", "confidence", "verified_by"
  ],
  "additionalProperties": false
}
```

- [ ] **Step 5: Extend source `covers`** — in `schema/source.schema.json`, change
`"items": {"enum": ["events", "crew", "research"]},` to
`"items": {"enum": ["events", "crew", "research", "equipment"]},`.

- [ ] **Step 6: Run tests to verify they pass**

Run: `pytest tests/test_validate.py -v`
Expected: all PASS.

- [ ] **Step 7: Keep the data dir and add it to CI**

```bash
mkdir -p data/equipment_items && touch data/equipment_items/.gitkeep
```

In `.github/workflows/validate.yml`, change the loop header to
`for entity in mission crew_member event research_project source equipment_item; do`
and add a case line after `source) dir=sources ;;`:
```yaml
              equipment_item) dir=equipment_items ;;
```

Verify locally: `python scripts/validate.py schema/equipment_item.schema.json data/equipment_items/`
Expected: `All files in data/equipment_items valid against equipment_item.schema.json.`

- [ ] **Step 8: Commit**

```bash
git add schema/equipment_item.schema.json schema/source.schema.json tests/fixtures/valid_equipment_item.json tests/fixtures/invalid_equipment_item.json tests/test_validate.py data/equipment_items/.gitkeep .github/workflows/validate.yml
git commit -m "Add Equipment Item schema, fixtures, and CI validation

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 2: equipment_item table in the database + stats

**Files:**
- Modify: `scripts/build_db.py` (`ENTITIES`), `scripts/stats.py`, `groundtruth.sqlite` (rebuilt)
- Test: `tests/test_build_db.py`, `tests/test_stats.py`

**Interfaces:**
- Consumes: `schema/equipment_item.schema.json`, `tests/fixtures/valid_equipment_item.json` (Task 1).
- Produces: SQLite table `equipment_item` with columns `item_id, mission_id, station, item, area, advice_type, rationale, item_key, related_events (JSON text), source_id, source_citation, confidence, verified_by` — queried by Task 6/7.

- [ ] **Step 1: Write the failing tests**

In `tests/test_build_db.py`:
- add `"equipment_item": "equipment_item.schema.json",` to `SCHEMA_FILES`;
- add `"equipment_items": "valid_equipment_item.json",` to the `mapping` in `_write_fixture_data_dir`;
- change the table assertion in `test_build_database_creates_sqlite_with_all_tables` to
  `assert tables == {"mission", "crew_member", "event", "research_project", "source", "equipment_item"}`;
- append:

```python
def test_build_database_inserts_equipment_item_with_json_encoded_related_events(tmp_path):
    data_dir = _write_fixture_data_dir(tmp_path)
    output_path = tmp_path / "groundtruth.sqlite"

    build_database(str(data_dir), str(output_path))

    conn = sqlite3.connect(output_path)
    row = conn.execute(
        "SELECT item_id, area, advice_type, item_key, related_events FROM equipment_item"
    ).fetchone()
    assert row[:4] == ("FMARS-C16-2024-EQP001", "Vehicles", "Wished Brought", "atv-spark-plugs")
    assert json.loads(row[4]) == ["FMARS-C16-2024-EVT001"]
    conn.close()
```

In `tests/test_stats.py`:
- add `"equipment_items": "valid_equipment_item.json",` to the `mapping` in `_write_fixture_data_dir`;
- in `test_generate_stats_summarizes_the_dataset` add
  `assert "Equipment Items: 1 (Wished Brought: 1)" in summary`;
- in `test_generate_stats_handles_empty_database` add
  `assert "Equipment Items: 0" in summary`.

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_build_db.py tests/test_stats.py -v`
Expected: FAIL — `KeyError: 'equipment_item'` in the schema-drift test, missing table, missing stats line.

- [ ] **Step 3: Add the entity** — in `scripts/build_db.py`, add after the `"source"` entry in `ENTITIES`:

```python
    "equipment_item": (
        "equipment_items",
        ["item_id", "mission_id", "station", "item", "area", "advice_type", "rationale",
         "item_key", "related_events", "source_id", "source_citation", "confidence",
         "verified_by"],
    ),
```
(`related_events` is already in `COMPLEX_COLUMNS`, so it's JSON-encoded with no further change.)

- [ ] **Step 4: Add the stats line** — in `scripts/stats.py`, after the `Research Projects` line:

```python
    equipment_count = conn.execute("SELECT COUNT(*) FROM equipment_item").fetchone()[0]
    equipment_by_advice = conn.execute(
        "SELECT advice_type, COUNT(*) FROM equipment_item GROUP BY advice_type ORDER BY COUNT(*) DESC"
    ).fetchall()
    if equipment_by_advice:
        breakdown = ", ".join(f"{t}: {c}" for t, c in equipment_by_advice)
        lines.append(f"Equipment Items: {equipment_count} ({breakdown})")
    else:
        lines.append(f"Equipment Items: {equipment_count}")
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest -v`
Expected: all PASS.

- [ ] **Step 6: Rebuild the committed database** (CI diffs it against a fresh build)

Run: `python scripts/build_db.py && sqlite3 groundtruth.sqlite "SELECT COUNT(*) FROM equipment_item"`
Expected: `Built groundtruth.sqlite from data/` then `0`.

- [ ] **Step 7: Commit**

```bash
git add scripts/build_db.py scripts/stats.py tests/test_build_db.py tests/test_stats.py groundtruth.sqlite
git commit -m "Add equipment_item table to the database and stats snapshot

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 3: Reference checks for Equipment Items

**Files:**
- Modify: `scripts/validate.py` (`check_references`)
- Test: `tests/test_validate.py`

**Interfaces:**
- Consumes: data layout `data/equipment_items/*.json` (Task 1).
- Produces: `check_references(data_dir)` also reports equipment-item errors, each prefixed `equipment_items/{filename}:`.

- [ ] **Step 1: Write the failing tests** — append to `tests/test_validate.py`:

```python
def _refs_data_dir(tmp_path, equipment_record):
    """Minimal data/ tree: mission M1 at FMARS, event E1, source S1, plus
    one equipment item record."""
    import json
    data_dir = tmp_path / "data"
    for sub in ["missions", "events", "crew_members", "research_projects", "sources", "equipment_items"]:
        (data_dir / sub).mkdir(parents=True)
    (data_dir / "missions" / "m1.json").write_text(json.dumps({"mission_id": "M1", "stations": ["FMARS"]}))
    (data_dir / "events" / "e1.json").write_text(
        json.dumps({"event_id": "E1", "mission_id": "M1", "station": "FMARS", "related_events": []})
    )
    (data_dir / "sources" / "s1.json").write_text(json.dumps({"source_id": "S1", "mission_ids": ["M1"]}))
    (data_dir / "equipment_items" / "q1.json").write_text(json.dumps(equipment_record))
    return data_dir


_GOOD_EQUIPMENT = {
    "item_id": "M1-EQP001", "mission_id": "M1", "station": "FMARS",
    "source_id": "S1", "related_events": ["E1"],
}


def test_check_references_accepts_valid_equipment_item(tmp_path):
    assert check_references(_refs_data_dir(tmp_path, _GOOD_EQUIPMENT)) == []


def test_check_references_detects_equipment_item_orphaned_mission_id(tmp_path):
    errors = check_references(_refs_data_dir(tmp_path, {**_GOOD_EQUIPMENT, "mission_id": "M9", "station": None}))
    assert any("equipment_items/q1.json" in e and "M9" in e for e in errors)


def test_check_references_detects_equipment_item_orphaned_related_event(tmp_path):
    errors = check_references(_refs_data_dir(tmp_path, {**_GOOD_EQUIPMENT, "related_events": ["E1", "E7"]}))
    assert any("equipment_items/q1.json" in e and "E7" in e for e in errors)


def test_check_references_detects_equipment_item_orphaned_source_id(tmp_path):
    errors = check_references(_refs_data_dir(tmp_path, {**_GOOD_EQUIPMENT, "source_id": "S9"}))
    assert any("equipment_items/q1.json" in e and "S9" in e for e in errors)


def test_check_references_detects_equipment_item_station_not_in_mission_stations(tmp_path):
    errors = check_references(_refs_data_dir(tmp_path, {**_GOOD_EQUIPMENT, "station": "MDRS"}))
    assert any("equipment_items/q1.json" in e and "MDRS" in e for e in errors)


def test_check_references_tolerates_missing_equipment_items_dir(tmp_path):
    import json
    data_dir = tmp_path / "data"
    for sub in ["missions", "events", "crew_members", "research_projects", "sources"]:
        (data_dir / sub).mkdir(parents=True)
    (data_dir / "missions" / "m1.json").write_text(json.dumps({"mission_id": "M1"}))
    assert check_references(data_dir) == []
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_validate.py -v -k "equipment_item and check_references"`
Expected: the four `detects_*` tests FAIL (no errors reported); `accepts_valid` and `tolerates_missing` PASS already.

- [ ] **Step 3: Implement** — in `scripts/validate.py`, insert immediately before `return errors` at the end of `check_references`:

```python
    # Equipment Items: same reference rules as Events — mission_id,
    # source_id, related_events must resolve, and station must be one of
    # the mission's stations.
    for p in (data_dir / "equipment_items").glob("*.json"):
        record = json.loads(p.read_text())
        mission_id = record.get("mission_id")
        if mission_id is not None:
            _check("equipment_items", p.name, "mission_id", mission_id, mission_ids, "Mission")
        source_id = record.get("source_id")
        if source_id is not None:
            _check("equipment_items", p.name, "source_id", source_id, source_ids, "Source")
        for value in record.get("related_events") or []:
            _check("equipment_items", p.name, "related_events", value, event_ids, "Event")
        station = record.get("station")
        if station is not None and mission_id in mission_stations:
            if station not in mission_stations[mission_id]:
                errors.append(
                    f"equipment_items/{p.name}: station '{station}' is not in mission "
                    f"'{mission_id}''s stations {sorted(mission_stations[mission_id])}"
                )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest -v && python scripts/validate.py --check-refs data`
Expected: all PASS; `All cross-references resolve.`

- [ ] **Step 5: Commit**

```bash
git add scripts/validate.py tests/test_validate.py
git commit -m "Check Equipment Item cross-references in validate.py

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 4: Draft review line + extraction docs

**Files:**
- Modify: `scripts/summarize_drafts.py`, `docs/extraction-workflow.md`, `CONTRIBUTING.md`
- Test: `tests/test_summarize_drafts.py`

**Interfaces:**
- Produces: `format_equipment_item(r: dict) -> str`; `summarize_directory` picks up an `equipment_items/` subdirectory under heading `EQUIPMENT ITEMS`. Used in Task 8's Stage 4.

- [ ] **Step 1: Write the failing tests** — add `format_equipment_item` to the import list at the top of `tests/test_summarize_drafts.py`, then append:

```python
def test_format_equipment_item_includes_area_advice_key_and_events():
    record = {
        "item_id": "FMARS-TEST-2026-EQP001",
        "area": "Vehicles",
        "advice_type": "Bring Spare",
        "item": "ATV tyre repair kit",
        "rationale": "Two flat tyres in the first week and no replacements available locally.",
        "item_key": "atv-tyre-repair-kit",
        "related_events": ["FMARS-TEST-2026-EVT004"],
    }
    line = format_equipment_item(record)
    assert "\n" not in line
    assert "EQP001" in line
    assert "[Vehicles/Bring Spare]" in line
    assert "ATV tyre repair kit" in line
    assert "key: atv-tyre-repair-kit" in line
    assert "FMARS-TEST-2026-EVT004" in line


def test_format_equipment_item_handles_missing_optional_fields():
    record = {
        "item_id": "FMARS-TEST-2026-EQP002",
        "area": "Food & Cooking",
        "advice_type": "Essential",
        "item": "Hot sauce",
        "rationale": "Crew called it a morale essential.",
    }
    line = format_equipment_item(record)
    assert "key: -" in line
    assert "events: -" in line


def test_summarize_directory_includes_equipment_items(tmp_path):
    (tmp_path / "equipment_items").mkdir()
    (tmp_path / "equipment_items" / "a.json").write_text(json.dumps({
        "item_id": "X-EQP001", "area": "Vehicles", "advice_type": "Essential",
        "item": "Starter fluid", "rationale": "Needed to start ATVs in the cold.",
    }))
    output = summarize_directory(tmp_path)
    assert "EQUIPMENT ITEMS (1)" in output
    assert "X-EQP001" in output
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_summarize_drafts.py -v`
Expected: FAIL — `ImportError: cannot import name 'format_equipment_item'`.

- [ ] **Step 3: Implement** — in `scripts/summarize_drafts.py`:
- add `("equipment_items", "EQUIPMENT ITEMS", "format_equipment_item"),` as the last entry of `_ENTITY_TYPES`;
- update the module docstring's subdirectory list to `sources/, missions/, crew_members/, events/, research_projects/, equipment_items/`;
- add after `format_research_project`:

```python
def format_equipment_item(r: dict) -> str:
    events = ", ".join(r.get("related_events") or []) or "-"
    return (
        f"{r.get('item_id', '?')} [{r.get('area', '?')}/{r.get('advice_type', '?')}] "
        f"{r.get('item', '?')} -- {truncate(r.get('rationale', ''), 90)} "
        f"(key: {r.get('item_key') or '-'}; events: {events})"
    )
```
- add `"format_equipment_item": format_equipment_item,` to `_FORMATTERS`.

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_summarize_drafts.py -v`
Expected: all PASS.

- [ ] **Step 5: Update `docs/extraction-workflow.md`**
- In the Stage 2 prompt, change `[Mission / Crew Member / Operational Event / Research Project]` to `[Mission / Crew Member / Operational Event / Research Project / Equipment Item]`.
- In Stage 4, change "required on all four entity types (Mission, Crew Member, Operational Event, Research Project)" to "required on all five entity types (Mission, Crew Member, Operational Event, Research Project, Equipment Item)".
- Add a new section after "Self-check (Stage 3)":

```markdown
## Equipment Item extraction rules

Equipment Items (`schema/equipment_item.schema.json`) capture packing
advice: what a crew wished they'd brought, found essential, needs spares
of, or shouldn't bring. One record per distinct item — a lesson naming
five parts is five records, each with `related_events` pointing at the
event it came from.

- **Explicit only.** Record an item only when the source names it, or
  clearly implies it ("we had no X and needed it"). Never infer advice
  from a failure alone — "the pump failed" is not "bring a spare pump".
  Stage 3 should flag any advice the source doesn't actually give.
- **`Essential` requires the crew's own emphasis** ("critical",
  "couldn't have managed without"). Having packed something isn't enough.
- **`item_key`:** reuse an existing key (`SELECT DISTINCT item_key FROM
  equipment_item`) when it's clearly the same item; otherwise leave it
  unset. Keys are assigned or confirmed at Stage 4, never invented at
  Stage 2.
- **`area`** is a closed list — see CONTRIBUTING.md. If nothing fits,
  flag it at Stage 4 rather than forcing a poor fit.
- Every existing rule still applies: no real names (including inside
  quoted citations), cite specific locations.
```

- [ ] **Step 6: Update `CONTRIBUTING.md`** — in the "Controlled vocabularies" section, append this paragraph:

```markdown
Equipment Items (`schema/equipment_item.schema.json`) follow the same
split: `area` and `advice_type` are closed enums, while `item_key` is an
open grouping key in lowercase-with-dashes form (e.g.
`spare-comms-earpiece`) shared by records about the same item across
missions. Reuse an existing key whenever it's genuinely the same item;
see docs/extraction-workflow.md's "Equipment Item extraction rules".
```

- [ ] **Step 7: Commit**

```bash
git add scripts/summarize_drafts.py tests/test_summarize_drafts.py docs/extraction-workflow.md CONTRIBUTING.md
git commit -m "Summarize Equipment Item drafts and document extraction rules

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 5: Site query builder

**Files:**
- Modify: `site/js/db.js`
- Test: `site-tests/db.test.js`

**Interfaces:**
- Produces: `buildEquipmentQuery(filters: {station?, area?, advice_type?}) -> {sql: string, params: string[]}`; rows ordered by `item, mission_id`. Used by Task 7.

- [ ] **Step 1: Write the failing tests** — change the import in `site-tests/db.test.js` to `import { buildEventsQuery, buildEquipmentQuery } from "../site/js/db.js";` and append:

```js
test("buildEquipmentQuery: no filters returns every item", () => {
  const { sql, params } = buildEquipmentQuery({});
  assert.equal(sql, "SELECT * FROM equipment_item ORDER BY item, mission_id");
  assert.deepEqual(params, []);
});

test("buildEquipmentQuery: each filter maps to its own column", () => {
  assert.deepEqual(buildEquipmentQuery({ station: "FMARS" }), {
    sql: "SELECT * FROM equipment_item WHERE station = ? ORDER BY item, mission_id",
    params: ["FMARS"],
  });
  assert.deepEqual(buildEquipmentQuery({ area: "Water & Drinking" }), {
    sql: "SELECT * FROM equipment_item WHERE area = ? ORDER BY item, mission_id",
    params: ["Water & Drinking"],
  });
  assert.deepEqual(buildEquipmentQuery({ advice_type: "Don't Bring" }), {
    sql: "SELECT * FROM equipment_item WHERE advice_type = ? ORDER BY item, mission_id",
    params: ["Don't Bring"],
  });
});

test("buildEquipmentQuery: combined filters are ANDed in station, area, advice_type order", () => {
  const { sql, params } = buildEquipmentQuery({
    advice_type: "Essential", station: "FMARS", area: "Vehicles",
  });
  assert.equal(
    sql,
    "SELECT * FROM equipment_item WHERE station = ? AND area = ? AND advice_type = ? ORDER BY item, mission_id"
  );
  assert.deepEqual(params, ["FMARS", "Vehicles", "Essential"]);
});

test("buildEquipmentQuery: undefined filter values are ignored", () => {
  const { sql, params } = buildEquipmentQuery({ station: undefined, area: "Vehicles" });
  assert.equal(sql, "SELECT * FROM equipment_item WHERE area = ? ORDER BY item, mission_id");
  assert.deepEqual(params, ["Vehicles"]);
});
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `node --test site-tests/db.test.js`
Expected: FAIL — `buildEquipmentQuery` is not exported.

- [ ] **Step 3: Implement** — append to `site/js/db.js`:

```js
// Filters the packing checklist (packing-view.js). Ordered by item name so
// records about the same item from different crews sit together before
// groupEquipmentItems() (util.js) merges them.
export function buildEquipmentQuery(filters) {
  const clauses = [];
  const params = [];
  for (const column of ["station", "area", "advice_type"]) {
    if (filters[column]) {
      clauses.push(`${column} = ?`);
      params.push(filters[column]);
    }
  }
  const where = clauses.length ? ` WHERE ${clauses.join(" AND ")}` : "";
  return { sql: `SELECT * FROM equipment_item${where} ORDER BY item, mission_id`, params };
}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `node --test site-tests/*.test.js`
Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add site/js/db.js site-tests/db.test.js
git commit -m "Add buildEquipmentQuery for the packing checklist

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 6: Grouping + filter-sanitizing helpers, URL round trip

**Files:**
- Modify: `site/js/util.js`
- Test: `site-tests/util.test.js`, `site-tests/router.test.js`

**Interfaces:**
- Produces:
  - `groupEquipmentItems(rows: object[]) -> Array<{area: string, advice_type: string, item: string, item_key: string|null, records: object[], crewCount: number}>` — rows sharing `area` + `advice_type` + non-empty `item_key` become one group (first-seen order, `item` from the first record); rows with no `item_key` are their own group; `crewCount` = distinct `mission_id`s.
  - `pickKnownFilters(query: object, allowed: {[field]: string[]}) -> object` — keeps only fields named in `allowed` whose value is in that field's list.

- [ ] **Step 1: Write the failing tests** — change the import in `site-tests/util.test.js` to `import { escapeHtml, bracketAges, wrapLabel, groupEquipmentItems, pickKnownFilters } from "../site/js/util.js";` and append:

```js
const eq = (overrides) => ({
  item_id: "M1-EQP001", mission_id: "M1", area: "Vehicles", advice_type: "Bring Spare",
  item: "Spark plugs", item_key: "atv-spark-plugs", ...overrides,
});

test("groupEquipmentItems: same area + advice_type + item_key merge into one group", () => {
  const groups = groupEquipmentItems([
    eq({ item_id: "M1-EQP001", mission_id: "M1" }),
    eq({ item_id: "M2-EQP001", mission_id: "M2", item: "ATV spark plugs" }),
  ]);
  assert.equal(groups.length, 1);
  assert.equal(groups[0].records.length, 2);
  assert.equal(groups[0].crewCount, 2);
  assert.equal(groups[0].item, "Spark plugs"); // first-seen record's name
});

test("groupEquipmentItems: two records from one mission count as one crew", () => {
  const groups = groupEquipmentItems([
    eq({ item_id: "M1-EQP001" }),
    eq({ item_id: "M1-EQP002" }),
  ]);
  assert.equal(groups.length, 1);
  assert.equal(groups[0].crewCount, 1);
});

test("groupEquipmentItems: conflicting advice for the same key stays as separate groups", () => {
  const groups = groupEquipmentItems([
    eq({ item_id: "M1-EQP001", advice_type: "Bring Spare" }),
    eq({ item_id: "M2-EQP001", mission_id: "M2", advice_type: "Don't Bring" }),
  ]);
  assert.equal(groups.length, 2);
  assert.deepEqual(groups.map((g) => g.advice_type), ["Bring Spare", "Don't Bring"]);
});

test("groupEquipmentItems: records without an item_key are never merged", () => {
  const groups = groupEquipmentItems([
    eq({ item_id: "M1-EQP001", item_key: null, item: "Spark plugs" }),
    eq({ item_id: "M2-EQP001", mission_id: "M2", item_key: null, item: "Spark plugs" }),
    eq({ item_id: "M3-EQP001", mission_id: "M3", item_key: "", item: "Spark plugs" }),
  ]);
  assert.equal(groups.length, 3);
  groups.forEach((g) => assert.equal(g.crewCount, 1));
});

test("groupEquipmentItems: empty input gives no groups", () => {
  assert.deepEqual(groupEquipmentItems([]), []);
});

test("pickKnownFilters: keeps only known fields with allowed values", () => {
  const allowed = { area: ["Vehicles", "Water & Drinking"], advice_type: ["Essential"] };
  assert.deepEqual(
    pickKnownFilters({ area: "Water & Drinking", advice_type: "Essential", junk: "x" }, allowed),
    { area: "Water & Drinking", advice_type: "Essential" }
  );
});

test("pickKnownFilters: drops stale or hand-edited values", () => {
  const allowed = { area: ["Vehicles"], advice_type: ["Essential"] };
  assert.deepEqual(pickKnownFilters({ area: "Water", advice_type: "essential" }, allowed), {});
});
```

Append to `site-tests/router.test.js`:

```js
test("routeToHash/parseHash: filter values with '&' and apostrophes round-trip intact", () => {
  const query = { area: "Water & Drinking", advice_type: "Don't Bring", station: "FMARS" };
  const hash = routeToHash("packing", null, query);
  assert.deepEqual(parseHash(hash), { view: "packing", param: null, query });
});
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `node --test site-tests/*.test.js`
Expected: util tests FAIL — `groupEquipmentItems`/`pickKnownFilters` not exported. The router round-trip test should already PASS (it pins existing `URLSearchParams` behaviour); if it fails, stop and report — the route encoding needs fixing before Task 7.

- [ ] **Step 3: Implement** — append to `site/js/util.js`:

```js
// Merges packing-checklist rows that describe the same item: same area,
// same advice_type, same non-empty item_key. advice_type is part of the
// key on purpose — if one crew says "Bring Spare" and another "Don't
// Bring" for the same item, both rows must stay visible rather than one
// silently absorbing the other. Rows with no item_key are never merged.
// crewCount counts distinct missions, so two records from one mission's
// report count once.
export function groupEquipmentItems(rows) {
  const groups = [];
  const byKey = new Map();
  for (const row of rows) {
    const key = row.item_key ? `${row.area}|${row.advice_type}|${row.item_key}` : null;
    let group = key ? byKey.get(key) : undefined;
    if (!group) {
      group = {
        area: row.area,
        advice_type: row.advice_type,
        item: row.item,
        item_key: row.item_key || null,
        records: [],
        crewCount: 0,
      };
      groups.push(group);
      if (key) byKey.set(key, group);
    }
    group.records.push(row);
  }
  for (const group of groups) {
    group.crewCount = new Set(group.records.map((r) => r.mission_id)).size;
  }
  return groups;
}

// Keeps only query-string filters whose value is one the view actually
// offers — a stale or hand-edited link (?area=Water) is ignored rather
// than selecting nothing. Same graceful-degradation rule as incidents-view.js.
export function pickKnownFilters(query, allowed) {
  const picked = {};
  for (const [field, values] of Object.entries(allowed)) {
    if (query[field] && values.includes(query[field])) picked[field] = query[field];
  }
  return picked;
}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `node --test site-tests/*.test.js`
Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add site/js/util.js site-tests/util.test.js site-tests/router.test.js
git commit -m "Add equipment grouping and filter-sanitizing helpers

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 7: Packing tab view, nav, styles, print

**Files:**
- Create: `site/js/packing-view.js`
- Modify: `site/js/event-list.js` (export `linkHtmlFor`), `site/js/app.js`, `site/index.html`, `site/css/style.css`

**Interfaces:**
- Consumes: `buildEquipmentQuery` (Task 5), `groupEquipmentItems`, `pickKnownFilters` (Task 6), `runQuery`, `getDistinctStations` (`db.js`), `routeToHash` (`router.js`), `escapeHtml` (`util.js`), `linkHtmlFor(urlOrReference: string) -> string` (`event-list.js`, exported in this task).
- Produces: `renderPacking(container, param, query)` registered as route `packing`.

This task is DOM wiring over already-tested helpers; verification is a manual browser check (Step 7), matching how the other views are verified.

- [ ] **Step 1: Export `linkHtmlFor`** — in `site/js/event-list.js`, change `function linkHtmlFor(urlOrReference) {` to `export function linkHtmlFor(urlOrReference) {`.

- [ ] **Step 2: Create `site/js/packing-view.js`**

```js
// packing-view.js — the packing checklist: Equipment Item records
// (what crews wished they'd brought, found essential, need spares of, or
// shouldn't bring), filterable by station/area/advice and printable.
// Grouping and filter sanitizing are pure helpers in util.js; this module
// is only DOM wiring.
import { runQuery, buildEquipmentQuery, getDistinctStations } from "./db.js";
import { escapeHtml, groupEquipmentItems, pickKnownFilters } from "./util.js";
import { linkHtmlFor } from "./event-list.js";
import { routeToHash } from "./router.js";

// Same order as schema/equipment_item.schema.json's area enum — headings
// render in this order.
const AREAS = [
  "Food & Cooking", "Water & Drinking", "Personal Hygiene & Sanitation",
  "Clothing & Thermal", "Sleep & Personal Comfort", "Medical & First Aid",
  "Safety & Environmental Monitoring", "Tools & Spare Parts",
  "Power & Electronics", "EVA Suits & Comms", "Vehicles", "Science & Lab",
  "Morale & Recreation",
];
const ADVICE_TYPES = ["Wished Brought", "Essential", "Bring Spare", "Don't Bring"];

function currentFilters(container) {
  const get = (sel) => container.querySelector(sel)?.value || undefined;
  return {
    station: get("#packing-station"),
    area: get("#packing-area"),
    advice_type: get("#packing-advice"),
  };
}

// history.replaceState, not location.hash — see incidents-view.js's syncUrl.
function syncUrl(container) {
  history.replaceState(null, "", routeToHash("packing", null, currentFilters(container)));
}

function optionsHtml(values) {
  return values.map((v) => `<option value="${escapeHtml(v)}">${escapeHtml(v)}</option>`).join("");
}

function recordDetailHtml(r) {
  const related = JSON.parse(r.related_events || "[]");
  const incidentLink = related.length
    ? ` · <a href="#/missions/${escapeHtml(r.mission_id)}">related incident on the mission page</a>`
    : "";
  return `
    <div class="packing-record">
      <p><strong>${escapeHtml(r.mission_id)}</strong> (${escapeHtml(r.advice_type)})${incidentLink}</p>
      <p>${escapeHtml(r.rationale)}</p>
      <button class="packing-source-toggle" data-item-id="${escapeHtml(r.item_id)}">See source</button>
      <div class="source-panel" style="display:none;"></div>
    </div>
  `;
}

function groupRowHtml(group) {
  const crews = group.crewCount > 1
    ? `<span class="crew-count">flagged by ${group.crewCount} crews</span>`
    : "";
  return `
    <li class="packing-item">
      <div class="packing-summary">
        <span class="packing-box" aria-hidden="true"></span>
        <span class="packing-name">${escapeHtml(group.item)}</span>
        <span class="advice-badge">${escapeHtml(group.advice_type)}</span>
        ${crews}
      </div>
      <div class="packing-detail" style="display:none;">
        ${group.records.map(recordDetailHtml).join("")}
      </div>
    </li>
  `;
}

function checklistHtml(groups) {
  if (!groups.length) return "<p>No packing advice matches these filters.</p>";
  return AREAS.map((area) => {
    const inArea = groups.filter((g) => g.area === area);
    if (!inArea.length) return "";
    const pack = inArea.filter((g) => g.advice_type !== "Don't Bring");
    const skip = inArea.filter((g) => g.advice_type === "Don't Bring");
    return `
      <section class="packing-area">
        <h3>${escapeHtml(area)}</h3>
        ${pack.length ? `<ul class="packing-items">${pack.map(groupRowHtml).join("")}</ul>` : ""}
        ${skip.length ? `<h4>Don't bring</h4><ul class="packing-items packing-dont">${skip.map(groupRowHtml).join("")}</ul>` : ""}
      </section>
    `;
  }).join("");
}

function sourcePanelHtml(itemId) {
  const rows = runQuery(
    `SELECT q.source_citation, s.url_or_reference
     FROM equipment_item q LEFT JOIN source s ON q.source_id = s.source_id
     WHERE q.item_id = ?`,
    [itemId]
  );
  if (!rows.length) return "<p>No linked source on record.</p>";
  return `<p>${escapeHtml(rows[0].source_citation)}</p>` + linkHtmlFor(rows[0].url_or_reference);
}

// Delegated click handler, bound once per list element — the list is
// re-rendered in place on every filter change, and re-binding would stack
// handlers that cancel each other's toggle (see commit b854ab6).
function attachListeners(listEl) {
  if (listEl.dataset.listenersAttached) return;
  listEl.dataset.listenersAttached = "true";
  listEl.addEventListener("click", (e) => {
    const sourceBtn = e.target.closest(".packing-source-toggle");
    if (sourceBtn) {
      const panel = sourceBtn.nextElementSibling;
      if (panel.style.display === "none") {
        panel.innerHTML = sourcePanelHtml(sourceBtn.dataset.itemId);
        panel.style.display = "block";
      } else {
        panel.style.display = "none";
      }
      return;
    }
    if (e.target.closest(".packing-detail")) return;
    const row = e.target.closest(".packing-item");
    if (row) {
      const detail = row.querySelector(".packing-detail");
      detail.style.display = detail.style.display === "none" ? "block" : "none";
    }
  });
}

function renderResults(container) {
  const listEl = container.querySelector(".packing-list");
  const { sql, params } = buildEquipmentQuery(currentFilters(container));
  listEl.innerHTML = checklistHtml(groupEquipmentItems(runQuery(sql, params)));
  attachListeners(listEl);
}

export function renderPacking(container, param, query = {}) {
  const stations = getDistinctStations();
  container.innerHTML = `
    <div class="incidents-layout">
      <button class="mock-button" id="filter-toggle">Filters</button>
      <aside class="filters-sidebar" id="filters-sidebar">
        <label>Station<br>
          <select id="packing-station"><option value="">All</option>${optionsHtml(stations)}</select>
        </label><br><br>
        <label>Area<br>
          <select id="packing-area"><option value="">All</option>${optionsHtml(AREAS)}</select>
        </label><br><br>
        <label>Advice<br>
          <select id="packing-advice"><option value="">All</option>${optionsHtml(ADVICE_TYPES)}</select>
        </label><br><br>
        <button class="mock-button" id="print-checklist">Print checklist</button>
      </aside>
      <section class="packing-list"></section>
    </div>
  `;

  const sidebar = container.querySelector("#filters-sidebar");
  container.querySelector("#filter-toggle").addEventListener("click", () => sidebar.classList.toggle("open"));
  container.querySelector("#print-checklist").addEventListener("click", () => window.print());

  const initial = pickKnownFilters(query, { station: stations, area: AREAS, advice_type: ADVICE_TYPES });
  if (initial.station) container.querySelector("#packing-station").value = initial.station;
  if (initial.area) container.querySelector("#packing-area").value = initial.area;
  if (initial.advice_type) container.querySelector("#packing-advice").value = initial.advice_type;

  container.querySelectorAll(".filters-sidebar select").forEach((sel) => {
    sel.addEventListener("change", () => {
      renderResults(container);
      syncUrl(container);
    });
  });

  renderResults(container);
  syncUrl(container);
}
```

- [ ] **Step 3: Register the route** — in `site/js/app.js` add `import { renderPacking } from "./packing-view.js";` after the incidents import, and `packing: renderPacking,` after `incidents: renderIncidents,` in `views`.

- [ ] **Step 4: Add the nav link** — in `site/index.html`, after the Incidents link:
```html
    <a href="#/packing" data-nav="packing">Packing</a>
```

- [ ] **Step 5: Add styles** — in `site/css/style.css`, after the `.event-list { flex: 1; }` rule:

```css
.packing-list {
  flex: 1;
}

.packing-area h3 {
  margin: 1.25rem 0 0.5rem;
}

.packing-area h4 {
  margin: 0.75rem 0 0.4rem;
  color: var(--muted, inherit);
}

.packing-items {
  list-style: none;
  margin: 0;
  padding: 0;
}

.packing-item {
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 0.5rem 0.75rem;
  margin-bottom: 0.5rem;
  cursor: pointer;
}

.packing-item:hover {
  border-color: var(--accent);
}

.packing-summary {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: 0.5rem;
}

.packing-name {
  flex: 1;
  min-width: 10rem;
}

.advice-badge,
.crew-count {
  font-size: 0.8rem;
  border: 1px solid var(--border);
  border-radius: 999px;
  padding: 0.05rem 0.5rem;
  white-space: nowrap;
}

.packing-box {
  display: none;
  width: 0.9em;
  height: 0.9em;
  border: 1.5px solid currentColor;
  border-radius: 2px;
}

.packing-detail {
  margin-top: 0.5rem;
  padding-top: 0.5rem;
  border-top: 1px solid var(--border);
}

@media print {
  nav.main-nav,
  .filters-sidebar,
  #filter-toggle,
  .packing-detail {
    display: none !important;
  }
  .packing-box {
    display: inline-block;
  }
  .packing-item {
    border: none;
    padding: 0.15rem 0;
    margin: 0;
    break-inside: avoid;
  }
  .packing-area {
    break-inside: avoid-page;
  }
}
```
Check `style.css`'s `:root` for the actual name of a muted-text token; if one exists use it in `.packing-area h4` instead of `var(--muted, inherit)`.

- [ ] **Step 6: Run the automated suites**

Run: `node --test site-tests/*.test.js && pytest -q`
Expected: all PASS.

- [ ] **Step 7: Manual browser check with temporary data**

Build a scratch site with throwaway equipment records (never committed):
```bash
S=$(mktemp -d) && mkdir -p $S/data $S/site/data && cp -r data/. $S/data/
cat > $S/data/equipment_items/FMARS-C16-2024-EQP001.json <<'EOF'
{"item_id":"FMARS-C16-2024-EQP001","mission_id":"FMARS-C16-2024","station":"FMARS","item":"Spark plugs matched to each ATV model","area":"Vehicles","advice_type":"Bring Spare","rationale":"Test record.","item_key":"atv-spark-plugs","related_events":["FMARS-C16-2024-EVT006"],"source_id":"SRC-flashline-crew-reports","source_citation":"Test citation","confidence":"B","verified_by":"TEST"}
EOF
cat > $S/data/equipment_items/FMARS-C15-2023-EQP001.json <<'EOF'
{"item_id":"FMARS-C15-2023-EQP001","mission_id":"FMARS-C15-2023","station":"FMARS","item":"ATV spark plugs","area":"Vehicles","advice_type":"Bring Spare","rationale":"Test record.","item_key":"atv-spark-plugs","source_citation":"Test citation","confidence":"B","verified_by":"TEST"}
EOF
cat > $S/data/equipment_items/FMARS-C16-2024-EQP002.json <<'EOF'
{"item_id":"FMARS-C16-2024-EQP002","mission_id":"FMARS-C16-2024","station":"FMARS","item":"Extra personal laptops","area":"Power & Electronics","advice_type":"Don't Bring","rationale":"Test record.","source_citation":"Test citation","confidence":"B","verified_by":"TEST"}
EOF
cat > $S/data/equipment_items/FMARS-C16-2024-EQP003.json <<'EOF'
{"item_id":"FMARS-C16-2024-EQP003","mission_id":"FMARS-C16-2024","station":"FMARS","item":"Personal LifeStraw","area":"Water & Drinking","advice_type":"Bring Spare","rationale":"Test record.","source_citation":"Test citation","confidence":"B","verified_by":"TEST"}
EOF
cp -r site/. $S/site/ && python scripts/build_db.py $S/data $S/site/data/groundtruth.sqlite
cd $S/site && python3 -m http.server 8799   # pick a free port if taken
```
Open `http://localhost:8799/#/packing` and confirm (check the page title is "Groundtruth — Analog Mission Registry" — another app may hold the port):
1. Three area sections render in enum order: Water & Drinking, Power & Electronics, Vehicles; Power & Electronics shows only a "Don't bring" sub-list.
2. The spark-plugs row is one row with "flagged by 2 crews".
3. Click a row → expands; click again → collapses. Change any filter, then click a row → still expands (Review Focus 5). Click "See source" → citation shows.
4. Set Area to "Water & Drinking" and Advice to "Bring Spare"; the address bar shows them; reload → selections restored.
5. Visit `#/packing?area=Water` → no filter selected, all items shown.
6. Filter to a combination with no items → "No packing advice matches these filters."
7. Print preview → no nav/sidebar, rows show tick boxes, no expanded detail.
8. Phone-width (375px) → Filters toggle button works, no horizontal scroll.
9. Incidents and Missions tabs still work; nav highlights "Packing" on the new tab.

Stop the server and delete `$S`.

- [ ] **Step 8: Commit**

```bash
git add site/js/packing-view.js site/js/event-list.js site/js/app.js site/index.html site/css/style.css
git commit -m "Add Packing tab: filterable, printable equipment checklist

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 8: Backfill Equipment Items from existing incidents (human-gated)

This is pipeline work, not code. It follows `docs/extraction-workflow.md` exactly, with the Equipment Item rules added in Task 4. **It blocks on human review at Step 6 — do not copy anything into `data/` or push before the human approves.**

**Files:**
- Create (local, gitignored): `sources-local/hypatia-iii-brief/`, `sources-local/flashline-crew-reports/`, `sources-local/equipment-backfill/drafts/equipment_items/*.json`
- Create (committed, after approval): `data/equipment_items/*.json`, rebuilt `groundtruth.sqlite`
- Modify (after approval): `data/sources/*.json` whose `covers` should gain `"equipment"`; `handoff.md`, `decisions.md`

- [ ] **Step 1: Bring the two primary sources local** (Path B; they're outside the repo today)

```bash
mkdir -p sources-local/hypatia-iii-brief sources-local/flashline-crew-reports
T="$HOME/Documents/Other Work/The Huge Analog Mission Database (THAMB)"
cp "$T/Hypatia_III_Mission_Brief_v2.docx" "$T/Hypatia_III_Mission_Brief_v2.extracted.txt" sources-local/hypatia-iii-brief/
cp "$T/Flashline Crew Reports.pdf" sources-local/flashline-crew-reports/
pdftotext -layout "sources-local/flashline-crew-reports/Flashline Crew Reports.pdf" sources-local/flashline-crew-reports/flashline-crew-reports.txt
```
If `pdftotext` is missing, extract with `python -c "import pypdf"`-based code or ask the human; do not proceed without a text version. FMARS-C19-2026 sources are already in `sources-local/FMARS-C19-2026/*.txt`.

- [ ] **Step 2: List candidate events**

```bash
sqlite3 -header groundtruth.sqlite "SELECT event_id, source_id, source_citation, lesson, response FROM event
 WHERE lesson LIKE '%bring%' OR lesson LIKE '%pack%' OR lesson LIKE '%spare%' OR lesson LIKE '%kit%'
    OR lesson LIKE '%replacement%' OR lesson LIKE '%redundan%' OR response LIKE '%spare%'
    OR system_category = 'Logistics' ORDER BY event_id"
```
Read every event's lesson in the output and keep the ones naming a physical item. Expect roughly 18; the query is a starting point, not the scope.

- [ ] **Step 3: Stage 2 — draft records**

For each candidate, open the passage its `source_citation` points to in the local text, and draft one Equipment Item per distinct item into `sources-local/equipment-backfill/drafts/equipment_items/{item_id}.json`:
- `item_id` numbered per mission from `EQP001` in event order;
- `related_events: [<event_id>]`, `source_id` / `confidence` inherited from the event; `source_citation` pointing at the specific passage;
- `verified_by: "PENDING_HUMAN_REVIEW"`;
- `item_key` only when two drafts are clearly the same item — otherwise omit;
- also draft any explicit packing advice in the surrounding passage the event didn't capture (`related_events` omitted for those).
Apply every rule in "Equipment Item extraction rules" (Task 4 Step 5).

Then: `python scripts/validate.py schema/equipment_item.schema.json sources-local/equipment-backfill/drafts/equipment_items/`
Expected: all valid.

- [ ] **Step 4: Stage 3 — fresh Opus self-check**

Dispatch a fresh subagent with `model: "opus"` (not a continuation), giving it the local source text paths and the drafts directory, with the prompt:

> "Here is the original source text, and here are draft Equipment Item records claimed to be extracted from it. Re-read the source and flag any claim in each draft you cannot verify against the actual text — the item itself, the advice_type (especially any 'Essential' without the crew's own emphasis, or advice inferred from a failure rather than stated), the rationale, the citation location. Also flag any real person's name anywhere in a record, including inside quoted citation text."

- [ ] **Step 5: Apply flags once**

Fix the flagged drafts (one Stage 2 retry, informed by the flags), then re-run Step 4 on the changed drafts only. If anything is flagged a second time, stop retrying and carry both drafts and both flag sets into Step 6.

- [ ] **Step 6: STOP — human review (Stage 4)**

Run `python scripts/summarize_drafts.py sources-local/equipment-backfill/drafts` and present the compact view to the human, along with: any unresolved Stage 3 flags, proposed `item_key` groupings, and any item where no `area` fit well. **Wait for explicit approval / edits / rejections. Do not proceed without it.**

- [ ] **Step 7: Commit approved records**

For approved drafts only: copy to `data/equipment_items/`, set `verified_by` to the reviewer's initials, apply agreed `item_key`s. Add `"equipment"` to `covers` in each `data/sources/*.json` that supplied an item. Then:
```bash
python scripts/validate.py schema/equipment_item.schema.json data/equipment_items/
python scripts/validate.py schema/source.schema.json data/sources/
python scripts/validate.py --check-refs data
python scripts/build_db.py && python scripts/stats.py
pytest -q && node --test site-tests/*.test.js
```
Expected: all valid, all refs resolve, stats shows the new Equipment Items count, all tests pass.

Spot-check the real data in a browser using Task 7 Step 7's server recipe with the real `data/` (no test records), then:
```bash
git add data/equipment_items/ data/sources/ groundtruth.sqlite
git commit -m "Add N Equipment Items backfilled from existing incident sources

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

- [ ] **Step 8: Update handoff.md and decisions.md, then ask before pushing**

Rewrite `handoff.md`'s current state (Equipment Item entity shipped, counts, next steps) and add a `decisions.md` entry for the Equipment Item design (link the spec). Commit. Then **ask the human before `git push`** — the push deploys the Packing tab and the card-expansion fix (`b854ab6`) to the live site.
