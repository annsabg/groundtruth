import { test } from "node:test";
import assert from "node:assert/strict";
import { parseHash, routeToHash } from "../site/js/router.js";

test("parseHash: empty hash is the landing view", () => {
  assert.deepEqual(parseHash(""), { view: "landing", param: null, query: {} });
  assert.deepEqual(parseHash("#"), { view: "landing", param: null, query: {} });
  assert.deepEqual(parseHash("#/"), { view: "landing", param: null, query: {} });
});

test("parseHash: view with no param", () => {
  assert.deepEqual(parseHash("#/patterns"), { view: "patterns", param: null, query: {} });
});

test("parseHash: view with a param", () => {
  assert.deepEqual(parseHash("#/missions/FMARS-C16-2024"), {
    view: "missions",
    param: "FMARS-C16-2024",
    query: {},
  });
});

test("parseHash: view with query params, no path param", () => {
  assert.deepEqual(parseHash("#/incidents?station=FMARS&significance=High"), {
    view: "incidents",
    param: null,
    query: { station: "FMARS", significance: "High" },
  });
});

test("parseHash: view with a path param and query params together", () => {
  assert.deepEqual(parseHash("#/incidents/FMARS?significance=High"), {
    view: "incidents",
    param: "FMARS",
    query: { significance: "High" },
  });
});

test("parseHash: empty-string query values are dropped, not kept as blanks", () => {
  assert.deepEqual(parseHash("#/incidents?station=FMARS&significance="), {
    view: "incidents",
    param: null,
    query: { station: "FMARS" },
  });
});

test("routeToHash: builds a hash from view + param", () => {
  assert.equal(routeToHash("missions", "FMARS-C16-2024"), "#/missions/FMARS-C16-2024");
  assert.equal(routeToHash("patterns"), "#/patterns");
});

test("routeToHash: builds a hash from view + query, no path param", () => {
  assert.equal(
    routeToHash("incidents", null, { station: "FMARS", significance: "High" }),
    "#/incidents?station=FMARS&significance=High"
  );
});

test("routeToHash: an empty query object produces no trailing '?'", () => {
  assert.equal(routeToHash("incidents", null, {}), "#/incidents");
});

test("routeToHash: falsy query values are omitted from the query string", () => {
  assert.equal(
    routeToHash("incidents", null, { station: "FMARS", significance: "" }),
    "#/incidents?station=FMARS"
  );
});

test("routeToHash: round-trips through parseHash", () => {
  const hash = routeToHash("incidents", null, { station: "FMARS", event_type: "Failure" });
  assert.deepEqual(parseHash(hash), {
    view: "incidents",
    param: null,
    query: { station: "FMARS", event_type: "Failure" },
  });
});
