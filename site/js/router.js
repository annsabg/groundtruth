// router.js — hash-based routing. Pure parsing functions are exported
// separately from the DOM-wiring function so they're unit-testable
// with node:test, no browser or bundler required.

export function parseHash(hash) {
  const clean = (hash || "").replace(/^#\/?/, "");
  if (!clean) return { view: "landing", param: null };
  const parts = clean.split("/").filter(Boolean);
  return { view: parts[0], param: parts[1] || null };
}

export function routeToHash(view, param) {
  return param ? `#/${view}/${param}` : `#/${view}`;
}

export function onRouteChange(callback) {
  const handler = () => callback(parseHash(window.location.hash));
  window.addEventListener("hashchange", handler);
  handler(); // fire once immediately for the initial page load
}
