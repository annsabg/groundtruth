// event-list.js — shared incident/event card rendering: expand-in-place
// detail, opt-in "see source" affordance. Used by both incidents-view.js
// (the cross-mission filterable list) and missions-view.js (one mission's
// incidents on its detail page) so this rendering logic exists once.
import { runQuery } from "./db.js";
import { escapeHtml } from "./util.js";

export function eventCardHtml(ev) {
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

export function attachEventListListeners(listEl) {
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

// Renders a list of events into listEl (card HTML + expand-in-place +
// source-toggle wiring), or a plain empty-state message if there are none.
// listEl is expected to be freshly created each render (the view modules
// rebuild container.innerHTML wholesale), so re-attaching listeners here
// each call never double-binds.
export function renderEventListInto(listEl, events, emptyMessage = "No events match these filters.") {
  listEl.innerHTML = events.length
    ? events.map(eventCardHtml).join("")
    : `<p>${escapeHtml(emptyMessage)}</p>`;
  attachEventListListeners(listEl);
}
