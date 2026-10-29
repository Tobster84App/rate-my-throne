-- Moderation: Kommentare melden; eigene Bewertungen löschen; Admins dürfen alles löschen.

-- 1) Admin-Kennzeichen (nur per SQL setzbar, Nutzer können ihr Profil nicht ändern)
alter table public.profiles add column if not exists is_admin boolean not null default false;

create or replace function public.is_admin() returns boolean
language sql stable security definer set search_path = '' as $$
  select coalesce((select is_admin from public.profiles where id = auth.uid()), false);
$$;
revoke execute on function public.is_admin() from public;
grant execute on function public.is_admin() to anon, authenticated;

-- 2) Löschen: eigene Bewertung oder als Admin jede
drop policy if exists "Eigene Bewertung löschen" on public.reviews;
create policy "Bewertung löschen (eigene oder Admin)" on public.reviews for delete to authenticated
  using (user_id = (select auth.uid()) or (select public.is_admin()));

drop policy if exists "Eigene Toilette löschen" on public.toilets;
create policy "Toilette löschen (eigene oder Admin)" on public.toilets for delete to authenticated
  using (created_by = (select auth.uid()) or (select public.is_admin()));

-- 3) Meldungen
create table if not exists public.review_reports (
  id bigint generated always as identity primary key,
  review_id bigint not null references public.reviews(id) on delete cascade,
  reporter uuid not null default auth.uid() references public.profiles(id) on delete cascade,
  reason text not null check (reason in ('offensive', 'spam', 'wrong', 'other')),
  note text check (char_length(note) <= 300),
  created_at timestamptz not null default now(),
  unique (review_id, reporter)                -- jede Person meldet eine Bewertung nur einmal
);
create index if not exists review_reports_review on public.review_reports (review_id);
create index if not exists review_reports_reporter on public.review_reports (reporter);
alter table public.review_reports enable row level security;

create policy "Melden" on public.review_reports for insert to authenticated
  with check (reporter = (select auth.uid()));
create policy "Eigene Meldungen sehen, Admin alle" on public.review_reports for select to authenticated
  using (reporter = (select auth.uid()) or (select public.is_admin()));
create policy "Meldungen erledigen (Admin)" on public.review_reports for delete to authenticated
  using ((select public.is_admin()));

-- 4) Dich selbst zum Admin machen: E-Mail-Adresse deines Kontos in Rate My Throne eintragen
update public.profiles set is_admin = true
where id = (select id from auth.users where email = 'kerntobias84@gmail.com');
