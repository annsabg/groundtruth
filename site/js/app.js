// app.js — wires router + db together, switches views on route change.
import { onRouteChange, routeToHash } from "./router.js";
import { initDatabase } from "./db.js";
import { renderLanding } from "./landing-view.js";
import { renderMissions } from "./missions-view.js";
import { renderPatterns } from "./patterns-view.js";
import { renderAbout } from "./about-view.js";

const appEl = document.getElementById("app");

const views = {
  landing: renderLanding,
  missions: renderMissions,
  patterns: renderPatterns,
  about: renderAbout,
};

function setActiveNav(view) {
  document.querySelectorAll("nav.main-nav a").forEach((a) => {
    a.classList.toggle("active", a.dataset.nav === view);
  });
}

async function main() {
  appEl.innerHTML = "<p>Loading database…</p>";
  await initDatabase("lib/sql-wasm.wasm", "data/groundtruth.sqlite");

  onRouteChange((route) => {
    setActiveNav(route.view);
    const renderer = views[route.view] || renderLanding;
    renderer(appEl, route.param);
  });
}

main();

// Exposed for view modules that need to navigate programmatically
// (e.g. clicking a mission card on the Missions page).
window.navigateTo = (view, param) => {
  window.location.hash = routeToHash(view, param);
};
