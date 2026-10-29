-- Konto löschen: Profil und Bewertungen werden mitgelöscht,
-- selbst eingetragene Toiletten bleiben für die Community erhalten (ohne Verweis auf die Person).
alter table public.toilets alter column created_by drop not null;
alter table public.toilets drop constraint toilets_created_by_fkey;
alter table public.toilets add constraint toilets_created_by_fkey
  foreign key (created_by) references public.profiles(id) on delete set null;

create or replace function public.delete_my_account() returns void
language plpgsql security definer set search_path = '' as $$
begin
  if auth.uid() is null then raise exception 'not signed in'; end if;
  delete from auth.users where id = auth.uid();
end $$;

revoke execute on function public.delete_my_account() from public, anon;
grant execute on function public.delete_my_account() to authenticated;
