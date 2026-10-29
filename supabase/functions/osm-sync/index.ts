// Importiert öffentliche Toiletten aus OpenStreetMap (Overpass) in die Tabelle osm_toilets.
// Aufruf durch den Zeitplan ({cron:true}) oder durch die App ({tiles:["13_52"]}) für noch fehlende Gegenden.
// Daten: © OpenStreetMap-Mitwirkende, Lizenz ODbL.
import { createClient } from "npm:@supabase/supabase-js@2.45.4";

const OVERPASS = ["https://overpass-api.de/api/interpreter", "https://overpass.private.coffee/api/interpreter"];
const FRESH_MS = 7 * 24 * 3600e3;     // Kachel gilt 7 Tage als aktuell
const STUCK_MS = 5 * 60e3;            // "loading" länger als 5 Min. gilt als hängengeblieben
const RETRY_MS = 10 * 60e3;           // fehlgeschlagene Kacheln frühestens nach 10 Min. erneut
const MAX_TILES = 2;                  // Kacheln pro Aufruf
const MAX_STARTS_PER_MIN = 6;         // Schonung der Overpass-Server
const UA = "RateMyThrone/0.1 (+https://tobster84app.github.io/rate-my-throne/)";

const cors = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};
const json = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), { status, headers: { ...cors, "Content-Type": "application/json" } });

const db = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!, {
  auth: { persistSession: false },
});

function validKey(k: unknown): k is string {
  if (typeof k !== "string" || !/^-?\d{1,3}_-?\d{1,2}$/.test(k)) return false;
  const [x, y] = k.split("_").map(Number);
  return x >= -180 && x < 180 && y >= -90 && y < 90;
}

async function overpass(query: string) {
  const errors: string[] = [];
  for (const url of OVERPASS) {
    try {
      const res = await fetch(url + "?data=" + encodeURIComponent(query), {
        headers: { "Accept": "application/json", "User-Agent": UA },
        signal: AbortSignal.timeout(60000),
      });
      if (!res.ok) throw new Error("HTTP " + res.status);
      return await res.json();
    } catch (err) { errors.push(new URL(url).host + ": " + ((err as Error)?.message ?? err)); }
  }
  throw new Error(errors.join("; "));
}

async function importTile(key: string) {
  const [x, y] = key.split("_").map(Number);
  const started = new Date().toISOString();
  await db.from("osm_tiles").upsert({ key, status: "loading", started_at: started });
  try {
    const data = await overpass(`[out:json][timeout:55];nwr["amenity"="toilets"](${y},${x},${y + 1},${x + 1});out center tags qt;`);
    const rows = [];
    for (const e of data.elements ?? []) {
      const lat = e.lat ?? e.center?.lat, lon = e.lon ?? e.center?.lon;
      if (lat == null || lon == null) continue;
      const tg = e.tags ?? {};
      rows.push({
        id: "osm-" + e.type + e.id, tile: key, lat, lon,
        name: tg.name ?? null, operator: tg.operator ?? null, fee: tg.fee ?? null,
        wheelchair: tg.wheelchair ?? null, changing_table: tg.changing_table ?? null,
        opening_hours: tg.opening_hours ?? null, updated_at: started,
      });
    }
    for (let i = 0; i < rows.length; i += 1000) {
      const { error } = await db.from("osm_toilets").upsert(rows.slice(i, i + 1000));
      if (error) throw new Error(error.message);
    }
    // In OSM gelöschte Toiletten entfernen
    await db.from("osm_toilets").delete().eq("tile", key).lt("updated_at", started);
    await db.from("osm_tiles").update({ status: "ok", fetched_at: new Date().toISOString(), count: rows.length, error: null }).eq("key", key);
    return { key, count: rows.length };
  } catch (err) {
    const msg = String((err as Error)?.message ?? err).slice(0, 300);
    await db.from("osm_tiles").update({ status: "error", error: msg }).eq("key", key);
    return { key, error: msg };
  }
}

function needsImport(row: { status: string; fetched_at: string | null; started_at: string | null } | undefined, now: number) {
  if (!row) return true;
  const started = row.started_at ? Date.parse(row.started_at) : 0;
  if (row.status === "loading") return now - started > STUCK_MS;
  if (row.status === "error") return now - started > RETRY_MS;
  if (row.status === "ok") return !row.fetched_at || now - Date.parse(row.fetched_at) > FRESH_MS;
  return true; // queued
}

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: cors });
  if (req.method !== "POST") return json({ error: "POST only" }, 405);
  let body: { cron?: boolean; tiles?: unknown[] } = {};
  try { body = await req.json(); } catch { /* leerer Body */ }
  const now = Date.now();

  // Kandidaten bestimmen
  let candidates: string[];
  if (body.cron) {
    const { data, error } = await db.from("osm_tiles").select("key,status,fetched_at,started_at")
      .order("priority", { ascending: false }).order("fetched_at", { ascending: true, nullsFirst: true }).limit(1000);
    if (error) return json({ error: error.message }, 500);
    candidates = data.filter((r) => needsImport(r, now)).map((r) => r.key);
  } else {
    const keys = [...new Set((body.tiles ?? []).filter(validKey))].slice(0, MAX_TILES);
    if (!keys.length) return json({ error: "no valid tiles" }, 400);
    const { data, error } = await db.from("osm_tiles").select("key,status,fetched_at,started_at").in("key", keys);
    if (error) return json({ error: error.message }, 500);
    const byKey = new Map(data.map((r) => [r.key, r]));
    candidates = keys.filter((k) => needsImport(byKey.get(k), now));
  }
  if (!candidates.length) return json({ done: [], skipped: true });

  // Drosselung: nicht mehr als MAX_STARTS_PER_MIN Importe pro Minute insgesamt
  const { count } = await db.from("osm_tiles").select("key", { count: "exact", head: true })
    .gte("started_at", new Date(now - 60000).toISOString());
  const allowed = Math.max(0, Math.min(MAX_TILES, MAX_STARTS_PER_MIN - (count ?? 0)));
  if (!allowed) return json({ busy: true, pending: candidates.slice(0, MAX_TILES) }, 429);

  const done = await Promise.all(candidates.slice(0, allowed).map(importTile));
  return json({ done });
});
