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

export function buildEventsQuery(filters) {
  const clauses = [];
  const params = [];
  if (filters.mission_id) {
    clauses.push("mission_id = ?");
    params.push(filters.mission_id);
  }
  if (filters.station) {
    clauses.push("mission_id IN (SELECT mission_id FROM mission WHERE stations LIKE ?)");
    params.push(`%"${filters.station}"%`);
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
