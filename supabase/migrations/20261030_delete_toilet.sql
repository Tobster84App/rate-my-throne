-- Eingetragene Toiletten löschen.
-- Wer eine Toilette eingetragen hat, darf sie löschen, solange niemand anderes sie bewertet hat.
-- Admins dürfen jede eingetragene Toilette löschen. Bewertungen dazu werden mitgelöscht.

drop policy if exists "Toilette löschen (eigene oder Admin)" on public.toilets;
create policy "Toilette löschen (eigene ohne fremde Bewertungen, oder Admin)" on public.toilets for delete to authenticated
  using (
    (select public.is_admin())
    or (created_by = (select auth.uid())
        and not exists (select 1 from public.reviews r
                        where r.toilet_ref = toilets.id::text and r.user_id <> (select auth.uid())))
  );

-- Bewertungen gehören über toilet_ref (Text) zur Toilette, daher kein Fremdschlüssel: per Trigger aufräumen
create or replace function public.delete_reviews_of_toilet() returns trigger
language plpgsql security definer set search_path = '' as $$
begin
  delete from public.reviews where toilet_ref = old.id::text;
  return old;
end $$;
revoke execute on function public.delete_reviews_of_toilet() from public, anon, authenticated;

drop trigger if exists toilets_delete_reviews on public.toilets;
create trigger toilets_delete_reviews after delete on public.toilets
  for each row execute function public.delete_reviews_of_toilet();
