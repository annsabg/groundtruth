// landing-view.js — short intro + live stats snapshot.
import { runQuery, getDistinctStations } from "./db.js";

export function renderLanding(container) {
  const missionCount = runQuery("SELECT COUNT(*) as n FROM mission")[0].n;
  const eventCount = runQuery("SELECT COUNT(*) as n FROM event")[0].n;
  const crewCount = runQuery("SELECT COUNT(*) as n FROM crew_member")[0].n;
  const researchCount = runQuery("SELECT COUNT(*) as n FROM research_project")[0].n;
  const stationCount = getDistinctStations().length;

  container.innerHTML = `
    <h1>Groundtruth</h1>
    <p>
      Groundtruth consolidates operational and research knowledge from
      volunteer analog space missions — a useful tool for future missions,
      station managers, and researchers alike.
    </p>
    <div class="card-grid">
      <div class="tile"><strong>${stationCount}</strong><br>Stations</div>
      <div class="tile"><strong>${missionCount}</strong><br>Missions</div>
      <div class="tile"><strong>${eventCount}</strong><br>Events</div>
      <div class="tile"><strong>${crewCount}</strong><br>Crew Members</div>
      <div class="tile"><strong>${researchCount}</strong><br>Research Projects</div>
    </div>
    <p>
      <a href="#/missions">Browse missions →</a> &nbsp;|&nbsp;
      <a href="#/patterns">Explore patterns →</a>
    </p>
  `;
}
