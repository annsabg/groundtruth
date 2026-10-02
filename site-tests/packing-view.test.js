import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { AREAS, ADVICE_TYPES } from "../site/js/packing-view.js";

const schema = JSON.parse(
  readFileSync(new URL("../schema/equipment_item.schema.json", import.meta.url), "utf8")
);

test("AREAS matches the schema's area enum", () => {
  assert.deepEqual(AREAS, schema.properties.area.enum);
});

test("ADVICE_TYPES matches the schema's advice_type enum", () => {
  assert.deepEqual(ADVICE_TYPES, schema.properties.advice_type.enum);
});
