// patterns-view.js — dashboard grid of tiles; click a data-dense tile to
// expand it full-width with a Chart.js chart. Sparse metrics (mission
// count, research project count) stay as small static counters.
import { runQuery } from "./db.js";

let chartInstance = null;

function eventTypeData() {
  const rows = runQuery("SELECT event_type, COUNT(*) as n FROM event GROUP BY event_type ORDER BY n DESC");
  return { labels: rows.map((r) => r.event_type), values: rows.map((r) => r.n) };
}

function patternTagData() {
  const rows = runQuery(
    `SELECT pattern_tag, COUNT(*) as n FROM event
     WHERE pattern_tag IS NOT NULL AND pattern_tag != ''
     GROUP BY pattern_tag ORDER BY n DESC LIMIT 8`
  );
  return { labels: rows.map((r) => r.pattern_tag), values: rows.map((r) => r.n) };
}

function crewGenderData() {
  const rows = runQuery("SELECT gender, COUNT(*) as n FROM crew_member GROUP BY gender ORDER BY n DESC");
  return { labels: rows.map((r) => r.gender), values: rows.map((r) => r.n) };
}

// age is stored as either an integer or the literal string "undisclosed"
// (schema/crew_member.schema.json's oneOf). Bracketing happens here, in
// JS, not SQL — the exact age is never rendered anywhere in the UI, only
// these bucket counts (spec §8: brackets shown, raw value stays queryable
// directly in groundtruth.sqlite for anyone who wants it).
function crewAgeData() {
  const rows = runQuery("SELECT age FROM crew_member");
  const buckets = { "18-24": 0, "25-34": 0, "35-44": 0, "45-54": 0, "55-64": 0, "65+": 0, "Undisclosed": 0 };
  rows.forEach((r) => {
    if (r.age === "undisclosed" || r.age === null || r.age === undefined) {
      buckets["Undisclosed"]++;
      return;
    }
    const n = Number(r.age);
    if (n < 25) buckets["18-24"]++;
    else if (n < 35) buckets["25-34"]++;
    else if (n < 45) buckets["35-44"]++;
    else if (n < 55) buckets["45-54"]++;
    else if (n < 65) buckets["55-64"]++;
    else buckets["65+"]++;
  });
  return { labels: Object.keys(buckets), values: Object.values(buckets) };
}

const TILE_DATA = {
  "event-types": { title: "Event types", fn: eventTypeData, chart: "pie" },
  "pattern-tags": { title: "Top pattern tags", fn: patternTagData, chart: "bar" },
  "crew-gender": { title: "Crew gender", fn: crewGenderData, chart: "pie" },
  "crew-age": { title: "Crew age (brackets)", fn: crewAgeData, chart: "bar" },
};

function renderChart(canvasEl, type, data) {
  if (chartInstance) chartInstance.destroy();
  chartInstance = new Chart(canvasEl, {
    type,
    data: {
      labels: data.labels,
      datasets: [{ data: data.values, backgroundColor: ["#2b6cb0", "#c0392b", "#27ae60", "#b8860b", "#8e44ad", "#16a085", "#d35400"] }],
    },
    options: {
      // Without this, Chart.js sizes the canvas from its own aspect ratio
      // against the expanded tile's full grid width (~950px), producing a
      // ~918x918px chart. maintainAspectRatio: false lets the fixed-height
      // .chart-container (CSS) govern size instead.
      maintainAspectRatio: false,
    },
  });
}

function expandTile(container, tileKey, updateHash = true) {
  const gridEl = container.querySelector(".card-grid");
  const meta = TILE_DATA[tileKey];
  if (!meta) return renderGrid(container);
  if (updateHash) window.navigateTo("patterns", tileKey);
  gridEl.innerHTML = `
    <div class="tile expanded">
      <button class="mock-button" data-back>← back to grid</button>
      <h3>${meta.title}</h3>
      <div class="chart-container">
        <canvas id="pattern-chart"></canvas>
      </div>
    </div>
  `;
  gridEl.querySelector("[data-back]").addEventListener("click", () => {
    window.navigateTo("patterns", null);
    renderGrid(container);
  });
  renderChart(gridEl.querySelector("#pattern-chart"), meta.chart, meta.fn());
}

function renderGrid(container) {
  const missionCount = runQuery("SELECT COUNT(*) as n FROM mission")[0].n;
  const researchCount = runQuery("SELECT COUNT(*) as n FROM research_project")[0].n;
  const gridEl = container.querySelector(".card-grid");
  gridEl.innerHTML = `
    <div class="tile" data-tile="event-types">📊 Event types</div>
    <div class="tile" data-tile="pattern-tags">📈 Top pattern tags</div>
    <div class="tile" data-tile="crew-gender">👥 Crew gender</div>
    <div class="tile" data-tile="crew-age">🎂 Crew age (brackets)</div>
    <div class="tile">${missionCount} Missions</div>
    <div class="tile">${researchCount} Research Projects</div>
  `;
  gridEl.querySelectorAll("[data-tile]").forEach((el) => {
    el.addEventListener("click", () => expandTile(container, el.dataset.tile));
  });
}

export function renderPatterns(container, param) {
  container.innerHTML = `<h1>Patterns</h1><div class="card-grid"></div>`;
  if (param && TILE_DATA[param]) {
    // Deep link, e.g. #/patterns/event-types — expand directly, no need to
    // re-navigate since the hash already reflects this state.
    expandTile(container, param, false);
  } else {
    renderGrid(container);
  }
}
