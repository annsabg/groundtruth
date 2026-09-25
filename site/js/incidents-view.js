// incidents-view.js — sidebar filters + cross-mission incident list.
// This is for pattern-hunting across missions (all Power failures
// everywhere, all High-significance incidents at FMARS, etc). For actual
// mission records (dates, crew size, goal) and drilling into one
// mission's own incidents, see missions-view.js.
import { runQuery, buildEventsQuery, getDistinctStations } from "./db.js";
import { escapeHtml } from "./util.js";
import { renderEventListInto } from "./event-list.js";
import { routeToHash } from "./router.js";

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

// Keeps the address bar in sync with the current filter selections, via
// history.replaceState (not location.hash — setting location.hash would
// fire a hashchange and re-run the whole view, collapsing the sidebar and
// losing scroll position for no reason). This is what makes a filtered
// view a link a crew member can copy and share, instead of state that
// only exists in the DOM until the tab closes.
function syncUrl(container) {
  const hash = routeToHash("incidents", null, currentFilters(container));
  history.replaceState(null, "", hash);
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

async function copyCurrentLink(button) {
  const original = button.textContent;
  try {
    await navigator.clipboard.writeText(window.location.href);
    button.textContent = "Copied!";
  } catch {
    // Clipboard API unavailable (e.g. insecure context) — fall back to
    // showing the link so it can be selected and copied by hand.
    window.prompt("Copy this link:", window.location.href);
  }
  setTimeout(() => { button.textContent = original; }, 1500);
}

export function renderIncidents(container, param, query = {}) {
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
        </label><br><br>
        <button class="mock-button" id="copy-link">Copy link to this view</button>
      </aside>
      <section class="event-list"></section>
    </div>
  `;

  const toggleBtn = container.querySelector("#filter-toggle");
  const sidebar = container.querySelector("#filters-sidebar");
  toggleBtn.addEventListener("click", () => sidebar.classList.toggle("open"));

  container.querySelector("#copy-link").addEventListener("click", (e) => copyCurrentLink(e.target));

  container.querySelectorAll(".filters-sidebar select").forEach((sel) => {
    sel.addEventListener("change", () => {
      renderResults(container);
      syncUrl(container);
    });
  });

  // Query-string filters (?station=FMARS&system_category=Power&...) are the
  // shareable form of this view's state. The old path-based single-station
  // deep link (#/incidents/FMARS) still works as a fallback for station
  // only. Any value not found in its select's own option list — a stale or
  // hand-edited link — is silently ignored rather than corrupting the
  // select, same graceful-degradation rule used throughout this site.
  const initialStation = query.station && stations.includes(query.station)
    ? query.station
    : (param && stations.includes(param) ? param : null);
  if (initialStation) container.querySelector("#filter-station").value = initialStation;
  if (query.system_category && CATEGORIES.includes(query.system_category)) {
    container.querySelector("#filter-category").value = query.system_category;
  }
  if (query.significance && SIGNIFICANCES.includes(query.significance)) {
    container.querySelector("#filter-significance").value = query.significance;
  }
  if (query.event_type && EVENT_TYPES.includes(query.event_type)) {
    container.querySelector("#filter-event-type").value = query.event_type;
  }

  renderResults(container);
  syncUrl(container);
}
