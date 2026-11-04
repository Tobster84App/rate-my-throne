-- Ranglisten mit Humor: Thron der Woche, Goldene Throne (Kartenausschnitt), Hofstaat des Monats, Ehrentitel.
-- Alles nur lesend und ohne neue Personendaten (Benutzernamen sind bei Bewertungen ohnehin öffentlich).

-- Name einer Toilette (OSM oder selbst eingetragen) samt Lage
create or replace function public.toilet_label(ref text)
returns table (name text, lat double precision, lon double precision)
language sql stable security definer set search_path = '' as $$
  select coalesce(o.name, o.operator), o.lat, o.lon from public.osm_toilets o where o.id = ref
  union all
  select t.name, t.lat, t.lon from public.toilets t where t.id::text = ref
  limit 1
$$;
revoke execute on function public.toilet_label(text) from public;

-- 👑 Thron der Woche: beste Durchschnittsnote aus den Bewertungen der laufenden Woche (Montag bis Sonntag, deutsche Zeit)
create or replace function public.throne_of_week()
returns table (toilet_ref text, name text, lat double precision, lon double precision, score numeric, reviews bigint, quote text, week int)
language sql stable security definer set search_path = '' as $$
  with w as (
    select r.toilet_ref, r.comment, r.created_at, (r.clean + r.equip + r.access) / 3.0 as s
    from public.reviews r
    where r.created_at >= date_trunc('week', now() at time zone 'Europe/Berlin') at time zone 'Europe/Berlin'
  ), best as (
    select w.toilet_ref, round(avg(w.s), 1) as score, count(*) as n, max(w.created_at) as last
    from w group by w.toilet_ref
    order by avg(w.s) desc, count(*) desc, max(w.created_at) desc
    limit 1
  )
  select b.toilet_ref, l.name, l.lat, l.lon, b.score, b.n,
         (select w.comment from w where w.toilet_ref = b.toilet_ref and coalesce(trim(w.comment), '') <> ''
          order by w.s desc, w.created_at desc limit 1),
         extract(week from now() at time zone 'Europe/Berlin')::int
  from best b left join lateral public.toilet_label(b.toilet_ref) l on true
$$;
revoke execute on function public.throne_of_week() from public;
grant execute on function public.throne_of_week() to anon, authenticated;

-- ✨ Goldene Throne: die besten Toiletten im Kartenausschnitt, nur mit mindestens 3 Bewertungen
create or replace function public.top_thrones(min_lat double precision, max_lat double precision,
                                              min_lon double precision, max_lon double precision, lim int default 3)
returns table (toilet_ref text, name text, lat double precision, lon double precision, score numeric, reviews bigint)
language plpgsql stable security definer set search_path = '' as $$
begin
  if max_lat - min_lat > 2 or max_lon - min_lon > 3 then
    raise exception 'area_too_large';
  end if;
  return query
    with places as (
      select o.id as ref, coalesce(o.name, o.operator) as name, o.lat, o.lon from public.osm_toilets o
      where o.lat between min_lat and max_lat and o.lon between min_lon and max_lon
      union all
      select t.id::text, t.name, t.lat, t.lon from public.toilets t
      where t.lat between min_lat and max_lat and t.lon between min_lon and max_lon
    )
    select p.ref, p.name, p.lat, p.lon, round(avg((r.clean + r.equip + r.access) / 3.0), 1), count(*)
    from places p join public.reviews r on r.toilet_ref = p.ref
    group by p.ref, p.name, p.lat, p.lon
    having count(*) >= 3
    order by avg((r.clean + r.equip + r.access) / 3.0) desc, count(*) desc
    limit least(greatest(lim, 1), 10);
end $$;
revoke execute on function public.top_thrones(double precision, double precision, double precision, double precision, int) from public;
grant execute on function public.top_thrones(double precision, double precision, double precision, double precision, int) to anon, authenticated;

-- 👑 Hofstaat des Monats: wer im laufenden Monat am meisten bewertet hat (nur Benutzername und Anzahl)
create or replace function public.court_of_month(lim int default 5)
returns table (username text, reviews bigint)
language sql stable security definer set search_path = '' as $$
  select p.username, count(*)
  from public.reviews r join public.profiles p on p.id = r.user_id
  where r.created_at >= date_trunc('month', now() at time zone 'Europe/Berlin') at time zone 'Europe/Berlin'
    and p.username is not null
  group by p.username
  order by count(*) desc, max(r.created_at) asc
  limit least(greatest(lim, 1), 10)
$$;
revoke execute on function public.court_of_month(int) from public;
grant execute on function public.court_of_month(int) to anon, authenticated;

-- Ehrentitel: Zahl aller Bewertungen je Person (für die Abzeichen neben dem Benutzernamen)
create or replace function public.review_counts(ids uuid[])
returns table (user_id uuid, reviews bigint)
language sql stable security definer set search_path = '' as $$
  select r.user_id, count(*) from public.reviews r
  where r.user_id = any(ids[1:200])
  group by r.user_id
$$;
revoke execute on function public.review_counts(uuid[]) from public;
grant execute on function public.review_counts(uuid[]) to anon, authenticated;
