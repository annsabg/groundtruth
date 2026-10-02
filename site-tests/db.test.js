import { test } from "node:test";
import assert from "node:assert/strict";
import { buildEventsQuery, buildEquipmentQuery } from "../site/js/db.js";

test("buildEventsQuery: no filters returns unfiltered query", () => {
  const { sql, params } = buildEventsQuery({});
  assert.equal(sql, "SELECT * FROM event ORDER BY mission_id, sol");
  assert.deepEqual(params, []);
});

test("buildEventsQuery: station filter matches the event's own station column", () => {
  const { sql, params } = buildEventsQuery({ station: "FMARS" });
  assert.match(sql, /WHERE station = \?/);
  assert.deepEqual(params, ["FMARS"]);
});

test("buildEventsQuery: combines multiple filters with AND", () => {
  const { sql, params } = buildEventsQuery({
    system_category: "Power",
    significance: "High",
  });
  assert.match(sql, /WHERE system_category = \? AND significance = \?/);
  assert.deepEqual(params, ["Power", "High"]);
});

test("buildEventsQuery: event_type filter", () => {
  const { sql, params } = buildEventsQuery({ event_type: "Crew Dynamics" });
  assert.match(sql, /event_type = \?/);
  assert.deepEqual(params, ["Crew Dynamics"]);
});

test("buildEventsQuery: mission_id filter", () => {
  const { sql, params } = buildEventsQuery({ mission_id: "FMARS-C16-2024" });
  assert.match(sql, /WHERE mission_id = \?/);
  assert.deepEqual(params, ["FMARS-C16-2024"]);
});

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
