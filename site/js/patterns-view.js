// patterns-view.js — dashboard grid of tiles; click a data-dense tile to
// expand it full-width with a Chart.js chart. Sparse metrics (mission
// count, research project count) stay as small static counters.
import { runQuery } from "./db.js";
import { bracketAges, wrapLabel } from "./util.js";

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
  return { labels: rows.map((r) => wrapLabel(r.pattern_tag)), values: rows.map((r) => r.n) };
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
  return bracketAges(rows.map((r) => r.age));
}

const TILE_DATA = {
  "event-types": { title: "Event types", fn: eventTypeData, chart: "pie" },
  // indexAxis: "y" — pattern tags are free-text and can run long (e.g.
  // "winter closure checklist gap (valve left closed)"); a vertical bar
  // chart squeezes each label under a narrow bar and truncates it. A
  // horizontal bar gives each tag its own full-width row instead, and
  // patternTagData() wraps each label onto multiple lines (wrapLabel())
  // so it fits the standard chart width without truncating either.
  // autoSkip: false — with 2-line labels, Chart.js's default y-axis
  // autoSkip decides it can't fit all 8 categories without overlap and
  // silently drops every other tick label; force every label to draw.
  // tall: true gives the .chart-container more height to match.
  "pattern-tags": {
    title: "Top pattern tags",
    fn: patternTagData,
    chart: "bar",
    chartOptions: { indexAxis: "y", scales: { y: { ticks: { autoSkip: false } } } },
    tall: true,
  },
  "crew-gender": { title: "Crew gender", fn: crewGenderData, chart: "pie" },
  "crew-age": { title: "Crew age (brackets)", fn: crewAgeData, chart: "bar" },
};

function renderChart(canvasEl, type, data, chartOptions = {}) {
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
      plugins: {
        // Chart.js's default legend for a single-series bar chart shows
        // one swatch labeled "undefined" (no dataset.label was ever set)
        // — meaningless noise since the axis labels already say what's
        // being counted. Pie charts keep their default legend: there it's
        // a real per-slice color key, not a per-dataset one.
        legend: { display: type !== "bar" },
      },
      ...chartOptions,
    },
  });
}

function expandTile(container, tileKey) {
  const gridEl = container.querySelector(".card-grid");
  const meta = TILE_DATA[tileKey];
  if (!meta) return renderGrid(container);
  gridEl.innerHTML = `
    <div class="tile expanded">
      <button class="mock-button" data-back>← back to grid</button>
      <h3>${meta.title}</h3>
      <div class="chart-container${meta.tall ? " chart-container--tall" : ""}">
        <canvas id="pattern-chart"></canvas>
      </div>
    </div>
  `;
  gridEl.querySelector("[data-back]").addEventListener("click", () => {
    window.navigateTo("patterns", null);
  });
  renderChart(gridEl.querySelector("#pattern-chart"), meta.chart, meta.fn(), meta.chartOptions);
}

function renderGrid(container) {
  if (chartInstance) {
    chartInstance.destroy();
    chartInstance = null;
  }
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
    el.addEventListener("click", () => window.navigateTo("patterns", el.dataset.tile));
  });
}

export function renderPatterns(container, param) {
  container.innerHTML = `<h1>Patterns</h1><div class="card-grid"></div>`;
  if (param && Object.prototype.hasOwnProperty.call(TILE_DATA, param)) {
    expandTile(container, param);
  } else {
    renderGrid(container);
  }
}
