-- Aktualität, Detail-Kriterien und Familienfreundlichkeit.
-- 1) Neue Häkchen in Bewertungen (leer bei älteren Bewertungen)
-- 2) Kurzmeldungen angemeldeter Nutzer („Wie ist es gerade?“), höchstens eine pro Person, Toilette und Stunde
-- 3) Daumen hoch/runter ohne Anmeldung, nur über die Funktion vote_toilet (mit Bremse gegen Massen-Klicks)

alter table public.reviews
  add column if not exists paper boolean,
  add column if not exists soap boolean,
  add column if not exists dryer boolean,
  add column if not exists smell_ok boolean,
  add column if not exists lock_ok boolean,
  add column if not exists stroller boolean,
  add column if not exists kids_seat boolean,
  add column if not exists family boolean;

-- Kurzmeldungen
create table if not exists public.toilet_reports (
  id bigint generated always as identity primary key,
  toilet_ref text not null,
  user_id uuid not null default auth.uid() references auth.users(id) on delete cascade,
  kind text not null check (kind in ('ok', 'no_paper', 'dirty', 'closed', 'broken')),
  created_at timestamptz not null default now()
);
create index if not exists toilet_reports_ref_time on public.toilet_reports (toilet_ref, created_at desc);
alter table public.toilet_reports enable row level security;

drop policy if exists "Kurzmeldungen lesen" on public.toilet_reports;
create policy "Kurzmeldungen lesen" on public.toilet_reports for select to anon, authenticated using (true);

drop policy if exists "Kurzmeldung abgeben (1 pro Stunde)" on public.toilet_reports;
create policy "Kurzmeldung abgeben (1 pro Stunde)" on public.toilet_reports for insert to authenticated
  with check (
    user_id = (select auth.uid())
    and not exists (select 1 from public.toilet_reports r
                    where r.toilet_ref = toilet_reports.toilet_ref and r.user_id = (select auth.uid())
                      and r.created_at > now() - interval '1 hour')
  );

drop policy if exists "Kurzmeldung löschen (eigene oder Admin)" on public.toilet_reports;
create policy "Kurzmeldung löschen (eigene oder Admin)" on public.toilet_reports for delete to authenticated
  using (user_id = (select auth.uid()) or (select public.is_admin()));

-- Daumen hoch/runter (ohne Konto; es wird nichts über die Person gespeichert)
create table if not exists public.toilet_votes (
  id bigint generated always as identity primary key,
  toilet_ref text not null,
  up boolean not null,
  created_at timestamptz not null default now()
);
create index if not exists toilet_votes_ref_time on public.toilet_votes (toilet_ref, created_at desc);
alter table public.toilet_votes enable row level security;

drop policy if exists "Daumen lesen" on public.toilet_votes;
create policy "Daumen lesen" on public.toilet_votes for select to anon, authenticated using (true);

create or replace function public.vote_toilet(ref text, is_up boolean) returns void
language plpgsql security definer set search_path = '' as $$
begin
  if ref is null or length(ref) > 64 then
    raise exception 'invalid_ref';
  end if;
  -- Bremse: höchstens 30 Daumen pro Toilette und Stunde
  if (select count(*) from public.toilet_votes v where v.toilet_ref = ref and v.created_at > now() - interval '1 hour') >= 30 then
    raise exception 'too_many';
  end if;
  insert into public.toilet_votes (toilet_ref, up) values (ref, is_up);
end $$;
revoke execute on function public.vote_toilet(text, boolean) from public;
grant execute on function public.vote_toilet(text, boolean) to anon, authenticated;

-- Wird eine eingetragene Toilette gelöscht, auch Kurzmeldungen und Daumen entfernen
create or replace function public.delete_reviews_of_toilet() returns trigger
language plpgsql security definer set search_path = '' as $$
begin
  delete from public.reviews where toilet_ref = old.id::text;
  delete from public.toilet_reports where toilet_ref = old.id::text;
  delete from public.toilet_votes where toilet_ref = old.id::text;
  return old;
end $$;
revoke execute on function public.delete_reviews_of_toilet() from public, anon, authenticated;
