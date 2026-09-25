// router.js — hash-based routing. Pure parsing functions are exported
// separately from the DOM-wiring function so they're unit-testable
// with node:test, no browser or bundler required.

export function parseHash(hash) {
  const clean = (hash || "").replace(/^#\/?/, "");
  if (!clean) return { view: "landing", param: null, query: {} };
  const [pathPart, queryPart] = clean.split("?");
  const parts = pathPart.split("/").filter(Boolean);
  const query = {};
  if (queryPart) {
    for (const [key, value] of new URLSearchParams(queryPart)) {
      if (value) query[key] = value;
    }
  }
  return { view: parts[0], param: parts[1] || null, query };
}

// query lets a view (e.g. incidents-view.js's filters) round-trip its
// current selections through the URL, so a filtered view is a shareable
// link rather than state that only exists in the DOM.
export function routeToHash(view, param, query) {
  let hash = param ? `#/${view}/${param}` : `#/${view}`;
  if (query) {
    const params = new URLSearchParams();
    for (const [key, value] of Object.entries(query)) {
      if (value) params.set(key, value);
    }
    const qs = params.toString();
    if (qs) hash += `?${qs}`;
  }
  return hash;
}

export function onRouteChange(callback) {
  const handler = () => callback(parseHash(window.location.hash));
  window.addEventListener("hashchange", handler);
  handler(); // fire once immediately for the initial page load
}
