-- Import der OSM-Toiletten direkt aus der Datenbank (pg_net), weil Overpass Anfragen aus Edge Functions ablehnt (HTTP 406).
-- Ablauf: osm_start_requests() schickt Anfragen für fällige Kacheln los, osm_process_responses() speichert die Antworten.

create table if not exists public.osm_requests (
  request_id bigint primary key,
  tile text not null,
  started_at timestamptz not null default now()
);
alter table public.osm_requests enable row level security;  -- keine Policies: nur intern

-- Fällige Kacheln anfragen (höchstens 2 gleichzeitig)
create or replace function public.osm_start_requests() returns void
language plpgsql security definer set search_path = '' as $$
declare r record; x int; y int; q text;
begin
  for r in
    select t.key from public.osm_tiles t
    where not exists (select 1 from public.osm_requests o where o.tile = t.key)
      and (t.status = 'queued'
        or (t.status = 'error' and t.started_at < now() - interval '10 minutes')
        or (t.status = 'ok' and t.fetched_at < now() - interval '7 days')
        or (t.status = 'loading' and t.started_at < now() - interval '5 minutes'))
    order by t.priority desc, t.fetched_at nulls first
    limit greatest(0, 2 - (select count(*) from public.osm_requests))
  loop
    x := split_part(r.key, '_', 1)::int;
    y := split_part(r.key, '_', 2)::int;
    q := format('[out:json][timeout:55];nwr["amenity"="toilets"](%s,%s,%s,%s);out center tags qt;', y, x, y + 1, x + 1);
    insert into public.osm_requests (request_id, tile) values (
      net.http_get(
        url := 'https://overpass-api.de/api/interpreter',
        params := jsonb_build_object('data', q),
        headers := jsonb_build_object('User-Agent', 'RateMyThrone/0.1 (+https://tobster84app.github.io/rate-my-throne/)'),
        timeout_milliseconds := 60000),
      r.key);
    update public.osm_tiles set status = 'loading', started_at = now() where key = r.key;
  end loop;
end $$;

-- Eingetroffene Antworten in osm_toilets übernehmen
create or replace function public.osm_process_responses() returns void
language plpgsql security definer set search_path = '' as $$
declare r record; resp record; n int;
begin
  for r in select * from public.osm_requests loop
    select status_code, content, error_msg into resp from net._http_response where id = r.request_id;
    if not found then
      if r.started_at < now() - interval '5 minutes' then
        update public.osm_tiles set status = 'error', error = 'keine Antwort' where key = r.tile;
        delete from public.osm_requests where request_id = r.request_id;
      end if;
      continue;
    end if;
    if resp.status_code = 200 then
      begin
        insert into public.osm_toilets (id, tile, lat, lon, name, operator, fee, wheelchair, changing_table, opening_hours, updated_at)
        select 'osm-' || (e->>'type') || (e->>'id'), r.tile,
               coalesce((e->>'lat')::float8, (e->'center'->>'lat')::float8),
               coalesce((e->>'lon')::float8, (e->'center'->>'lon')::float8),
               e->'tags'->>'name', e->'tags'->>'operator', e->'tags'->>'fee', e->'tags'->>'wheelchair',
               e->'tags'->>'changing_table', e->'tags'->>'opening_hours', r.started_at
        from jsonb_array_elements(resp.content::jsonb -> 'elements') e
        where coalesce(e->>'lat', e->'center'->>'lat') is not null
        on conflict (id) do update set tile = excluded.tile, lat = excluded.lat, lon = excluded.lon, name = excluded.name,
          operator = excluded.operator, fee = excluded.fee, wheelchair = excluded.wheelchair,
          changing_table = excluded.changing_table, opening_hours = excluded.opening_hours, updated_at = excluded.updated_at;
        get diagnostics n = row_count;
        -- In OSM gelöschte Toiletten entfernen
        delete from public.osm_toilets where tile = r.tile and updated_at < r.started_at;
        update public.osm_tiles set status = 'ok', fetched_at = now(), count = n, error = null where key = r.tile;
      exception when others then
        update public.osm_tiles set status = 'error', error = left(sqlerrm, 300) where key = r.tile;
      end;
    else
      update public.osm_tiles set status = 'error',
        error = left(coalesce('HTTP ' || resp.status_code || ': ' || left(resp.content, 120), resp.error_msg, 'Fehler'), 300)
      where key = r.tile;
    end if;
    delete from public.osm_requests where request_id = r.request_id;
  end loop;
end $$;

create or replace function public.osm_sync_tick() returns void
language plpgsql security definer set search_path = '' as $$
begin
  perform public.osm_process_responses();
  perform public.osm_start_requests();
end $$;

-- Aufruf durch die App: neue Gegend nach vorn in die Warteschlange stellen und sofort anfragen
create or replace function public.request_osm_tiles(keys text[]) returns void
language plpgsql security definer set search_path = '' as $$
begin
  if coalesce(array_length(keys, 1), 0) > 4 then raise exception 'too many tiles'; end if;
  if (select count(*) from public.osm_tiles where status = 'queued' and priority >= 20) > 50 then return; end if;
  insert into public.osm_tiles (key, priority)
  select k, 20 from unnest(keys) k
  where k ~ '^-?[0-9]{1,3}_-?[0-9]{1,2}$'
    and split_part(k, '_', 1)::int between -180 and 179
    and split_part(k, '_', 2)::int between -90 and 89
  on conflict (key) do update set priority = 20 where public.osm_tiles.status <> 'ok';
  perform public.osm_start_requests();
end $$;

revoke execute on function public.osm_start_requests(), public.osm_process_responses(), public.osm_sync_tick() from public, anon, authenticated;
revoke execute on function public.request_osm_tiles(text[]) from public;
grant execute on function public.request_osm_tiles(text[]) to anon, authenticated;

-- Zeitplan: alle 20 Sekunden, ersetzt den bisherigen Aufruf der Edge Function
select cron.schedule('osm-sync', '20 seconds', 'select public.osm_sync_tick()');

-- Bisher fehlgeschlagene Kacheln neu einreihen
update public.osm_tiles set status = 'queued', started_at = null, error = null where status in ('error', 'loading');
