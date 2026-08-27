import { test } from "node:test";
import assert from "node:assert/strict";
import { escapeHtml, bracketAges } from "../site/js/util.js";

const AGE_BRACKETS = ["18-24", "25-34", "35-44", "45-54", "55-64", "65+", "Undisclosed"];

function zeroCounts() {
  return AGE_BRACKETS.map(() => 0);
}

function expectBracket(bracket, count) {
  const values = zeroCounts();
  values[AGE_BRACKETS.indexOf(bracket)] = count;
  return { labels: AGE_BRACKETS, values };
}

test("escapeHtml: escapes each HTML-significant character individually", () => {
  assert.equal(escapeHtml("&"), "&amp;");
  assert.equal(escapeHtml("<"), "&lt;");
  assert.equal(escapeHtml(">"), "&gt;");
  assert.equal(escapeHtml('"'), "&quot;");
  assert.equal(escapeHtml("'"), "&#39;");
});

test("escapeHtml: a string with none of the special characters is returned unchanged", () => {
  assert.equal(escapeHtml("FMARS-C16-2024, Sol 12"), "FMARS-C16-2024, Sol 12");
});

test("escapeHtml: null and undefined both return an empty string", () => {
  assert.equal(escapeHtml(null), "");
  assert.equal(escapeHtml(undefined), "");
});

test("bracketAges: 24 and 25 land in different buckets (18-24 vs 25-34)", () => {
  assert.deepEqual(bracketAges([24]), expectBracket("18-24", 1));
  assert.deepEqual(bracketAges([25]), expectBracket("25-34", 1));
});

test("bracketAges: 34 and 35 land in different buckets (25-34 vs 35-44)", () => {
  assert.deepEqual(bracketAges([34]), expectBracket("25-34", 1));
  assert.deepEqual(bracketAges([35]), expectBracket("35-44", 1));
});

test("bracketAges: 44 and 45 land in different buckets (35-44 vs 45-54)", () => {
  assert.deepEqual(bracketAges([44]), expectBracket("35-44", 1));
  assert.deepEqual(bracketAges([45]), expectBracket("45-54", 1));
});

test("bracketAges: 54 and 55 land in different buckets (45-54 vs 55-64)", () => {
  assert.deepEqual(bracketAges([54]), expectBracket("45-54", 1));
  assert.deepEqual(bracketAges([55]), expectBracket("55-64", 1));
});

test("bracketAges: 64 and 65 land in different buckets (55-64 vs 65+)", () => {
  assert.deepEqual(bracketAges([64]), expectBracket("55-64", 1));
  assert.deepEqual(bracketAges([65]), expectBracket("65+", 1));
});

test("bracketAges: the literal string \"undisclosed\" buckets as Undisclosed", () => {
  assert.deepEqual(bracketAges(["undisclosed"]), expectBracket("Undisclosed", 1));
});

test("bracketAges: null buckets as Undisclosed", () => {
  assert.deepEqual(bracketAges([null]), expectBracket("Undisclosed", 1));
});

test("bracketAges: a numeric-string age buckets as a number, not Undisclosed", () => {
  assert.deepEqual(bracketAges(["30"]), expectBracket("25-34", 1));
});

test("bracketAges: an empty input array leaves all buckets at zero", () => {
  assert.deepEqual(bracketAges([]), { labels: AGE_BRACKETS, values: zeroCounts() });
});
