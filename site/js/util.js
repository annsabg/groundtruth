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
