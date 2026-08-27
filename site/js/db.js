// db.js — sql.js initialization and query helpers.
// initDatabase/runQuery touch the real sql.js runtime and a fetched
// database file — verified manually in a browser (Task 13), not unit
// tested. The query-builder functions below are pure and unit-tested
// via node:test (site-tests/db.test.js).

let db = null;

export async function initDatabase(wasmPath, sqlitePath) {
  const SQL = await initSqlJs({ locateFile: () => wasmPath });
  const response = await fetch(sqlitePath);
  if (!response.ok) {
    throw new Error(`Failed to load database file (${sqlitePath}): HTTP ${response.status}`);
  }
  const buffer = await response.arrayBuffer();
  db = new SQL.Database(new Uint8Array(buffer));
}

export function runQuery(sql, params = []) {
  if (!db) throw new Error("Database not initialized — call initDatabase() first");
  const results = db.exec(sql, params);
  if (results.length === 0) return [];
  const { columns, values } = results[0];
  return values.map((row) => Object.fromEntries(columns.map((col, i) => [col, row[i]])));
}

// mission.stations is stored as a JSON-encoded array (a mission can list
// more than one, e.g. MARS160-2017: [FMARS, MDRS]) — this flattens and
// dedupes across every mission. Shared by incidents-view.js's station
// filter dropdown and landing-view.js's stats snapshot.
export function getDistinctStations() {
  const rows = runQuery("SELECT DISTINCT stations FROM mission");
  const set = new Set();
  rows.forEach((r) => JSON.parse(r.stations).forEach((s) => set.add(s)));
  return Array.from(set).sort();
}

export function buildEventsQuery(filters) {
  const clauses = [];
  const params = [];
  if (filters.mission_id) {
    clauses.push("mission_id = ?");
    params.push(filters.mission_id);
  }
  if (filters.station) {
    // Filters on the event's own station, not the mission's full stations
    // list — a multi-leg mission (e.g. MARS160-2017: FMARS then MDRS) must
    // not have every one of its events match every station it ever visited.
    // See schema/event.schema.json's "station" field.
    clauses.push("station = ?");
    params.push(filters.station);
  }
  if (filters.system_category) {
    clauses.push("system_category = ?");
    params.push(filters.system_category);
  }
  if (filters.significance) {
    clauses.push("significance = ?");
    params.push(filters.significance);
  }
  if (filters.event_type) {
    clauses.push("event_type = ?");
    params.push(filters.event_type);
  }
  const where = clauses.length ? `WHERE ${clauses.join(" AND ")}` : "";
  const sql = where
    ? `SELECT * FROM event ${where} ORDER BY mission_id, sol`
    : "SELECT * FROM event ORDER BY mission_id, sol";
  return { sql, params };
}
