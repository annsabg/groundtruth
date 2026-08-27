import { test } from "node:test";
import assert from "node:assert/strict";
import { buildEventsQuery } from "../site/js/db.js";

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
