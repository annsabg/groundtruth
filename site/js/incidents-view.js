// incidents-view.js — sidebar filters + cross-mission incident list.
// This is for pattern-hunting across missions (all Power failures
// everywhere, all High-significance incidents at FMARS, etc). For actual
// mission records (dates, crew size, goal) and drilling into one
// mission's own incidents, see missions-view.js.
import { runQuery, buildEventsQuery, getDistinctStations } from "./db.js";
import { escapeHtml } from "./util.js";
import { renderEventListInto } from "./event-list.js";

const CATEGORIES = [
  "Power", "Water", "ATVs/Transport", "EVA Suits & Comms", "Hab Structure",
  "Air Quality", "Medical/Safety", "Logistics", "Meteorological",
  "Operational/Process", "Scientific", "Psychological",
];
const SIGNIFICANCES = ["High", "Medium", "Low"];
const EVENT_TYPES = [
  "Failure", "Near-Miss", "Success/Best Practice", "Process Innovation",
  "Crew Dynamics", "Observation", "Other",
];

function currentFilters(container) {
  const get = (sel) => container.querySelector(sel)?.value || undefined;
  return {
    station: get("#filter-station"),
    system_category: get("#filter-category"),
    significance: get("#filter-significance"),
    event_type: get("#filter-event-type"),
  };
}

function renderResults(container) {
  const listEl = container.querySelector(".event-list");
  const { sql, params } = buildEventsQuery(currentFilters(container));
  const events = runQuery(sql, params);
  renderEventListInto(listEl, events);
}

function optionsHtml(values) {
  return values.map((v) => `<option value="${escapeHtml(v)}">${escapeHtml(v)}</option>`).join("");
}

export function renderIncidents(container, param) {
  const stations = getDistinctStations();
  container.innerHTML = `
    <div class="incidents-layout">
      <button class="mock-button" id="filter-toggle">Filters</button>
      <aside class="filters-sidebar" id="filters-sidebar">
        <label>Station<br>
          <select id="filter-station"><option value="">All</option>${optionsHtml(stations)}</select>
        </label><br><br>
        <label>Category<br>
          <select id="filter-category"><option value="">All</option>${optionsHtml(CATEGORIES)}</select>
        </label><br><br>
        <label>Significance<br>
          <select id="filter-significance"><option value="">All</option>${optionsHtml(SIGNIFICANCES)}</select>
        </label><br><br>
        <label>Event type<br>
          <select id="filter-event-type"><option value="">All</option>${optionsHtml(EVENT_TYPES)}</select>
        </label>
      </aside>
      <section class="event-list"></section>
    </div>
  `;

  const toggleBtn = container.querySelector("#filter-toggle");
  const sidebar = container.querySelector("#filters-sidebar");
  toggleBtn.addEventListener("click", () => sidebar.classList.toggle("open"));

  container.querySelectorAll(".filters-sidebar select").forEach((sel) => {
    sel.addEventListener("change", () => renderResults(container));
  });

  if (param && stations.includes(param)) {
    // Station-level deep link, e.g. #/incidents/FMARS. A mission-specific
    // deep link now lives under #/missions/<mission_id> instead (see
    // missions-view.js) — an unrecognized param here is ignored rather
    // than corrupting the select, same graceful-degradation rule as before.
    container.querySelector("#filter-station").value = param;
  }

  renderResults(container);
}
