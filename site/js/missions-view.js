// missions-view.js — sidebar filters + event results list.
// Event detail expand-in-place and the "see source" affordance are
// added in Task 9, on top of this file's renderEventList.
import { runQuery, buildEventsQuery } from "./db.js";
import { escapeHtml } from "./util.js";

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

function getMissionIds() {
  return runQuery("SELECT mission_id FROM mission").map((r) => r.mission_id);
}

function currentFilters(container) {
  const get = (sel) => container.querySelector(sel)?.value || undefined;
  return {
    mission_id: container.dataset.missionId || undefined,
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
    <div class="event-card" data-event-id="${escapeHtml(ev.event_id)}">
      <div class="event-summary" data-toggle-detail>
        <span>${escapeHtml(ev.mission_id)} · Sol ${escapeHtml(ev.sol)} · ${escapeHtml(ev.system_category)}</span>
        <span class="sig-${ev.significance}">${escapeHtml(ev.significance)}</span>
      </div>
      <div>${escapeHtml(ev.description)}</div>
      <div class="event-detail" style="display:none;">
        <p><strong>Response:</strong> ${escapeHtml(ev.response) || "—"}</p>
        <p><strong>Lesson:</strong> ${escapeHtml(ev.lesson) || "—"}</p>
        <p><strong>Pattern:</strong> ${escapeHtml(ev.pattern_tag) || "—"} &nbsp; <strong>Outcome:</strong> ${escapeHtml(ev.outcome) || "—"}</p>
        <button class="source-toggle" data-event-id="${escapeHtml(ev.event_id)}">See source</button>
        <div class="source-panel" style="display:none;"></div>
      </div>
    </div>
  `;
}

function sourceInfoFor(eventId) {
  const rows = runQuery(
    `SELECT e.source_citation, s.url_or_reference
     FROM event e LEFT JOIN source s ON e.source_id = s.source_id
     WHERE e.event_id = ?`,
    [eventId]
  );
  if (rows.length === 0) return null;
  return rows[0];
}

function attachEventListListeners(listEl) {
  listEl.addEventListener("click", (e) => {
    const summary = e.target.closest("[data-toggle-detail]");
    if (summary) {
      const detail = summary.closest(".event-card").querySelector(".event-detail");
      detail.style.display = detail.style.display === "none" ? "block" : "none";
      return;
    }
    const sourceBtn = e.target.closest(".source-toggle");
    if (sourceBtn) {
      const panel = sourceBtn.nextElementSibling;
      if (panel.style.display === "none") {
        const info = sourceInfoFor(sourceBtn.dataset.eventId);
        panel.innerHTML = info
          ? `<p>${escapeHtml(info.source_citation)}</p>` + linkHtmlFor(info.url_or_reference)
          : "<p>No linked source on record.</p>";
        panel.style.display = "block";
      } else {
        panel.style.display = "none";
      }
    }
  });
}

// Only the two Source records with a genuine public URL should ever render
// a link. SRC-hypatia-iii-brief's url_or_reference is a local .docx
// filename ("Hypatia_III_Mission_Brief_v2.docx, produced May 2025 (local
// file, not in repo)") — it covers 46 of the 60 events, the majority, and
// naively linking to it would produce a broken href for most of the site.
// Only render a link when the value actually starts with a real URL scheme.
function linkHtmlFor(urlOrReference) {
  if (!urlOrReference) return "";
  const firstToken = urlOrReference.split(" ")[0];
  if (!/^https?:\/\//.test(firstToken)) return "";
  return `<p><a href="${escapeHtml(firstToken)}" target="_blank" rel="noopener">View source</a></p>`;
}

function optionsHtml(values) {
  return values.map((v) => `<option value="${escapeHtml(v)}">${escapeHtml(v)}</option>`).join("");
}

export function renderMissions(container, param) {
  const stations = getStations();
  container.innerHTML = `
    <div class="missions-layout">
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

  delete container.dataset.missionId;
  if (param) {
    const missionIds = getMissionIds();
    if (missionIds.includes(param)) {
      // Spec's literal example: #/missions/FMARS-C16-2024 — filter to just
      // that mission's events. No <select> exists for this; it's carried
      // on the container's dataset and read by currentFilters().
      container.dataset.missionId = param;
    } else if (stations.includes(param)) {
      // Backward-compatible with Task 8's original station-level deep
      // link (e.g. #/missions/FMARS).
      container.querySelector("#filter-station").value = param;
    }
    // Any other param value is ignored rather than corrupting the select
    // — an unrecognized param should degrade to "show everything", not
    // to a visibly broken blank dropdown.
  }

  attachEventListListeners(container.querySelector(".event-list"));
  renderResults(container);
}
