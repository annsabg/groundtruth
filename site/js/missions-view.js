// missions-view.js — real Mission records: a list of missions (station,
// dates, crew size, goal), and per-mission detail pages that drill into
// that mission's own incidents. For the cross-mission filterable incident
// list (pattern-hunting across missions), see incidents-view.js.
import { runQuery } from "./db.js";
import { escapeHtml } from "./util.js";
import { renderEventListInto } from "./event-list.js";

function getMissions() {
  return runQuery("SELECT * FROM mission ORDER BY start_date");
}

function getMission(missionId) {
  const rows = runQuery("SELECT * FROM mission WHERE mission_id = ?", [missionId]);
  return rows.length ? rows[0] : null;
}

function stationsOf(mission) {
  return JSON.parse(mission.stations).join(", ");
}

function missionCardHtml(m) {
  return `
    <div class="mission-card" data-mission-id="${escapeHtml(m.mission_id)}">
      <h3>${escapeHtml(m.crew_designation)}</h3>
      <p>${escapeHtml(stationsOf(m))} · ${escapeHtml(m.start_date)} – ${escapeHtml(m.end_date)} · ${escapeHtml(m.crew_size)} crew</p>
      ${m.mission_goal ? `<p>${escapeHtml(m.mission_goal)}</p>` : ""}
    </div>
  `;
}

function renderMissionList(container) {
  const missions = getMissions();
  container.innerHTML = `
    <h1>Missions</h1>
    <div class="mission-list">${missions.map(missionCardHtml).join("")}</div>
  `;
  container.querySelectorAll(".mission-card").forEach((el) => {
    el.addEventListener("click", () => window.navigateTo("missions", el.dataset.missionId));
  });
}

function renderMissionDetail(container, mission) {
  const incidents = runQuery(
    "SELECT * FROM event WHERE mission_id = ? ORDER BY sol",
    [mission.mission_id]
  );
  container.innerHTML = `
    <p><a href="#/missions">← All missions</a></p>
    <h1>${escapeHtml(mission.crew_designation)}</h1>
    <p>
      <strong>Station(s):</strong> ${escapeHtml(stationsOf(mission))}<br>
      <strong>Dates:</strong> ${escapeHtml(mission.start_date)} – ${escapeHtml(mission.end_date)}<br>
      <strong>Crew size:</strong> ${escapeHtml(mission.crew_size)}<br>
      <strong>Type:</strong> ${escapeHtml(mission.institutional_or_volunteer)}
      ${mission.location ? `<br><strong>Location:</strong> ${escapeHtml(mission.location)}` : ""}
    </p>
    ${mission.mission_goal ? `<p>${escapeHtml(mission.mission_goal)}</p>` : ""}
    <h2>Incidents (${incidents.length})</h2>
    <div class="event-list"></div>
  `;
  renderEventListInto(
    container.querySelector(".event-list"),
    incidents,
    "No incidents recorded for this mission."
  );
}

export function renderMissions(container, param) {
  // An unrecognized param (or none) degrades to the mission list rather
  // than an error — same graceful-degradation rule used throughout the
  // site (incidents-view.js's station param, patterns-view.js's tile key).
  const mission = param ? getMission(param) : null;
  if (mission) {
    renderMissionDetail(container, mission);
  } else {
    renderMissionList(container);
  }
}
