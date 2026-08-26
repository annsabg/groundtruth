// missions-view.js — sidebar filters + event results list.
// Event detail expand-in-place and the "see source" affordance are
// added in Task 9, on top of this file's renderEventList.
import { runQuery, buildEventsQuery } from "./db.js";

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

function getStations() {
  const rows = runQuery("SELECT DISTINCT stations FROM mission");
  const set = new Set();
  rows.forEach((r) => JSON.parse(r.stations).forEach((s) => set.add(s)));
  return Array.from(set).sort();
}

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
  listEl.innerHTML = events.length
    ? events.map(eventCardHtml).join("")
    : "<p>No events match these filters.</p>";
}

function eventCardHtml(ev) {
  return `
    <div class="event-card" data-event-id="${ev.event_id}">
      <div class="event-summary">
        <span>${ev.mission_id} · Sol ${ev.sol} · ${ev.system_category}</span>
        <span class="sig-${ev.significance}">${ev.significance}</span>
      </div>
      <div>${ev.description}</div>
    </div>
  `;
}

function optionsHtml(values) {
  return values.map((v) => `<option value="${v}">${v}</option>`).join("");
}

export function renderMissions(container, param) {
  const stations = getStations();
  container.innerHTML = `
    <div class="missions-layout">
      <button class="mock-button" id="filter-toggle" style="display:none;">Filters</button>
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
  if (window.matchMedia("(max-width: 700px)").matches) {
    toggleBtn.style.display = "inline-block";
  }
  toggleBtn.addEventListener("click", () => sidebar.classList.toggle("open"));

  container.querySelectorAll(".filters-sidebar select").forEach((sel) => {
    sel.addEventListener("change", () => renderResults(container));
  });

  if (param) {
    container.querySelector("#filter-station").value = param;
  }

  renderResults(container);
}
