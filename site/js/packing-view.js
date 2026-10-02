// packing-view.js — the packing checklist: Equipment Item records
// (what crews wished they'd brought, found essential, need spares of, or
// shouldn't bring), filterable by station/area/advice and printable.
// Grouping and filter sanitizing are pure helpers in util.js; this module
// is only DOM wiring.
import { runQuery, buildEquipmentQuery, getDistinctStations } from "./db.js";
import { escapeHtml, groupEquipmentItems, pickKnownFilters } from "./util.js";
import { linkHtmlFor } from "./event-list.js";
import { routeToHash } from "./router.js";

// Same order as schema/equipment_item.schema.json's area enum — headings
// render in this order.
export const AREAS = [
  "Food & Cooking", "Water & Drinking", "Personal Hygiene & Sanitation",
  "Clothing & Thermal", "Sleep & Personal Comfort", "Medical & First Aid",
  "Safety & Environmental Monitoring", "Tools & Spare Parts",
  "Power & Electronics", "EVA Suits & Comms", "Vehicles", "Science & Lab",
  "Morale & Recreation",
];
export const ADVICE_TYPES = ["Wished Brought", "Essential", "Bring Spare", "Don't Bring"];

function currentFilters(container) {
  const get = (sel) => container.querySelector(sel)?.value || undefined;
  return {
    station: get("#packing-station"),
    area: get("#packing-area"),
    advice_type: get("#packing-advice"),
  };
}

// history.replaceState, not location.hash — see incidents-view.js's syncUrl.
function syncUrl(container) {
  history.replaceState(null, "", routeToHash("packing", null, currentFilters(container)));
}

function optionsHtml(values) {
  return values.map((v) => `<option value="${escapeHtml(v)}">${escapeHtml(v)}</option>`).join("");
}

function recordDetailHtml(r) {
  const related = JSON.parse(r.related_events || "[]");
  const incidentLink = related.length
    ? ` · <a href="#/missions/${escapeHtml(r.mission_id)}">related incident on the mission page</a>`
    : "";
  return `
    <div class="packing-record">
      <p><strong>${escapeHtml(r.mission_id)}</strong> (${escapeHtml(r.advice_type)})${incidentLink}</p>
      <p>${escapeHtml(r.rationale)}</p>
      <button class="packing-source-toggle" data-item-id="${escapeHtml(r.item_id)}">See source</button>
      <div class="source-panel" style="display:none;"></div>
    </div>
  `;
}

function groupRowHtml(group) {
  const crews = group.crewCount > 1
    ? `<span class="crew-count">flagged by ${group.crewCount} crews</span>`
    : "";
  return `
    <li class="packing-item">
      <div class="packing-summary">
        <span class="packing-box" aria-hidden="true"></span>
        <span class="packing-name">${escapeHtml(group.item)}</span>
        <span class="advice-badge">${escapeHtml(group.advice_type)}</span>
        ${crews}
      </div>
      <div class="packing-detail" style="display:none;">
        ${group.records.map(recordDetailHtml).join("")}
      </div>
    </li>
  `;
}

function checklistHtml(groups, hasAnyRecords) {
  if (!groups.length) {
    return hasAnyRecords
      ? "<p>No packing advice matches these filters.</p>"
      : "<p>No packing advice has been recorded yet.</p>";
  }
  return AREAS.map((area) => {
    const inArea = groups.filter((g) => g.area === area);
    if (!inArea.length) return "";
    const pack = inArea.filter((g) => g.advice_type !== "Don't Bring");
    const skip = inArea.filter((g) => g.advice_type === "Don't Bring");
    return `
      <section class="packing-area">
        <h3>${escapeHtml(area)}</h3>
        ${pack.length ? `<ul class="packing-items">${pack.map(groupRowHtml).join("")}</ul>` : ""}
        ${skip.length ? `<h4>Don't bring</h4><ul class="packing-items packing-dont">${skip.map(groupRowHtml).join("")}</ul>` : ""}
      </section>
    `;
  }).join("");
}

function sourcePanelHtml(itemId) {
  const rows = runQuery(
    `SELECT q.source_citation, s.url_or_reference
     FROM equipment_item q LEFT JOIN source s ON q.source_id = s.source_id
     WHERE q.item_id = ?`,
    [itemId]
  );
  if (!rows.length) return "<p>No linked source on record.</p>";
  return `<p>${escapeHtml(rows[0].source_citation)}</p>` + linkHtmlFor(rows[0].url_or_reference);
}

// Delegated click handler, bound once per list element — the list is
// re-rendered in place on every filter change, and re-binding would stack
// handlers that cancel each other's toggle (see commit b854ab6).
function attachListeners(listEl) {
  if (listEl.dataset.listenersAttached) return;
  listEl.dataset.listenersAttached = "true";
  listEl.addEventListener("click", (e) => {
    const sourceBtn = e.target.closest(".packing-source-toggle");
    if (sourceBtn) {
      const panel = sourceBtn.nextElementSibling;
      if (panel.style.display === "none") {
        panel.innerHTML = sourcePanelHtml(sourceBtn.dataset.itemId);
        panel.style.display = "block";
      } else {
        panel.style.display = "none";
      }
      return;
    }
    if (e.target.closest(".packing-detail")) return;
    const row = e.target.closest(".packing-item");
    if (row) {
      const detail = row.querySelector(".packing-detail");
      detail.style.display = detail.style.display === "none" ? "block" : "none";
    }
  });
}

function renderResults(container) {
  const listEl = container.querySelector(".packing-list");
  const filters = currentFilters(container);
  const { sql, params } = buildEquipmentQuery(filters);
  const groups = groupEquipmentItems(runQuery(sql, params));
  const hasAnyRecords = runQuery("SELECT COUNT(*) AS n FROM equipment_item")[0].n > 0;
  const heading = `Packing checklist — Station: ${filters.station || "All"} · Area: ${filters.area || "All"} · Advice: ${filters.advice_type || "All"}`;
  listEl.innerHTML =
    `<p class="packing-print-heading">${escapeHtml(heading)}</p>` +
    checklistHtml(groups, hasAnyRecords);
  attachListeners(listEl);
}

export function renderPacking(container, param, query = {}) {
  const stations = getDistinctStations();
  container.innerHTML = `
    <div class="incidents-layout">
      <button class="mock-button" id="filter-toggle">Filters</button>
      <aside class="filters-sidebar" id="filters-sidebar">
        <label>Station<br>
          <select id="packing-station"><option value="">All</option>${optionsHtml(stations)}</select>
        </label><br><br>
        <label>Area<br>
          <select id="packing-area"><option value="">All</option>${optionsHtml(AREAS)}</select>
        </label><br><br>
        <label>Advice<br>
          <select id="packing-advice"><option value="">All</option>${optionsHtml(ADVICE_TYPES)}</select>
        </label><br><br>
        <button class="mock-button" id="print-checklist">Print checklist</button>
      </aside>
      <section class="packing-list"></section>
    </div>
  `;

  const sidebar = container.querySelector("#filters-sidebar");
  container.querySelector("#filter-toggle").addEventListener("click", () => sidebar.classList.toggle("open"));
  container.querySelector("#print-checklist").addEventListener("click", () => window.print());

  const initial = pickKnownFilters(query, { station: stations, area: AREAS, advice_type: ADVICE_TYPES });
  if (initial.station) container.querySelector("#packing-station").value = initial.station;
  if (initial.area) container.querySelector("#packing-area").value = initial.area;
  if (initial.advice_type) container.querySelector("#packing-advice").value = initial.advice_type;

  container.querySelectorAll(".filters-sidebar select").forEach((sel) => {
    sel.addEventListener("change", () => {
      renderResults(container);
      syncUrl(container);
    });
  });

  renderResults(container);
  syncUrl(container);
}
