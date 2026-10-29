-- Bewertungsverlauf: Jede Person darf dieselbe Toilette erneut bewerten, frühestens 30 Tage nach ihrer letzten Bewertung.
-- Alte Bewertungen bleiben mit Datum erhalten, so wird sichtbar, ob es besser oder schlechter wird.
alter table public.reviews drop constraint if exists reviews_toilet_ref_user_id_key;
create index if not exists reviews_toilet_user_created on public.reviews (toilet_ref, user_id, created_at desc);

create or replace function public.can_review(ref text) returns boolean
language sql stable security definer set search_path = '' as $$
  select not exists (
    select 1 from public.reviews
    where toilet_ref = ref and user_id = auth.uid() and created_at > now() - interval '30 days');
$$;
revoke execute on function public.can_review(text) from public;
grant execute on function public.can_review(text) to authenticated;

drop policy if exists "Bewertung anlegen" on public.reviews;
create policy "Bewertung anlegen (höchstens alle 30 Tage je Toilette)" on public.reviews for insert to authenticated
  with check (user_id = (select auth.uid()) and public.can_review(toilet_ref));
