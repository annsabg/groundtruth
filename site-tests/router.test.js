import { test } from "node:test";
import assert from "node:assert/strict";
import { parseHash, routeToHash } from "../site/js/router.js";

test("parseHash: empty hash is the landing view", () => {
  assert.deepEqual(parseHash(""), { view: "landing", param: null });
  assert.deepEqual(parseHash("#"), { view: "landing", param: null });
  assert.deepEqual(parseHash("#/"), { view: "landing", param: null });
});

test("parseHash: view with no param", () => {
  assert.deepEqual(parseHash("#/patterns"), { view: "patterns", param: null });
});

test("parseHash: view with a param", () => {
  assert.deepEqual(parseHash("#/missions/FMARS-C16-2024"), {
    view: "missions",
    param: "FMARS-C16-2024",
  });
});

test("routeToHash: builds a hash from view + param", () => {
  assert.equal(routeToHash("missions", "FMARS-C16-2024"), "#/missions/FMARS-C16-2024");
  assert.equal(routeToHash("patterns"), "#/patterns");
});
