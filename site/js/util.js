// util.js — small pure helpers shared across view modules. No dependency
// on db.js or the DOM, so these are importable and unit-testable
// (site-tests/util.test.js) without a browser.

// Escapes the five HTML-significant characters before interpolating
// untrusted/free-text data (event descriptions, citations, station
// names, etc.) into innerHTML. Contribution is open PR-based free-text
// JSON — a data-record reviewer checks citations and privacy, not
// markup — so this is a real guard, not theater, even though no current
// record actually contains any of these characters.
export function escapeHtml(value) {
  if (value === null || value === undefined) return "";
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

// Greedily wraps a label into lines no longer than maxLineLength
// characters (breaking on spaces, never mid-word), returning an array of
// lines. Chart.js renders an array-valued tick label as multiple lines —
// this is how a long free-text pattern_tag becomes readable on a chart
// axis instead of running off the edge or getting clipped. A label with
// no spaces long enough to break (single long word) is returned whole,
// unsplit, on one line.
export function wrapLabel(label, maxLineLength = 24) {
  const words = String(label).split(" ");
  const lines = [];
  let current = "";
  for (const word of words) {
    const candidate = current ? `${current} ${word}` : word;
    if (candidate.length > maxLineLength && current) {
      lines.push(current);
      current = word;
    } else {
      current = candidate;
    }
  }
  if (current) lines.push(current);
  return lines;
}

const AGE_BRACKETS = ["18-24", "25-34", "35-44", "45-54", "55-64", "65+", "Undisclosed"];

// Buckets an array of raw crew_member.age values (each either an integer,
// a numeric string, the literal string "undisclosed", or null/undefined
// per schema/crew_member.schema.json's oneOf) into age-bracket counts.
// Pure — no DB or DOM access — so it's fully unit-testable
// (site-tests/util.test.js) independent of patterns-view.js.
export function bracketAges(ages) {
  const buckets = Object.fromEntries(AGE_BRACKETS.map((b) => [b, 0]));
  ages.forEach((age) => {
    if (age === "undisclosed" || age === null || age === undefined) {
      buckets["Undisclosed"]++;
      return;
    }
    const n = Number(age);
    if (Number.isNaN(n)) {
      buckets["Undisclosed"]++;
      return;
    }
    if (n < 25) buckets["18-24"]++;
    else if (n < 35) buckets["25-34"]++;
    else if (n < 45) buckets["35-44"]++;
    else if (n < 55) buckets["45-54"]++;
    else if (n < 65) buckets["55-64"]++;
    else buckets["65+"]++;
  });
  return { labels: AGE_BRACKETS, values: AGE_BRACKETS.map((b) => buckets[b]) };
}

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
