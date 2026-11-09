-- Seitenaufrufe auch für die Städte-Seiten zählen (wie bisher: nur eine Zahl pro Seite und Tag, keine Personendaten).
-- Städte-Seiten melden sich als "city:<stadt>", z. B. "city:heilbronn" (deutsche und englische Fassung zusammen).

alter table public.page_views drop constraint if exists page_views_page_check;
alter table public.page_views add constraint page_views_page_check
  check (page in ('home', 'map') or page ~ '^city:[a-z0-9-]{1,40}$');

create or replace function public.count_view(p text) returns void
language plpgsql security definer set search_path = '' as $$
begin
  if not (p in ('home', 'map') or p ~ '^city:[a-z0-9-]{1,40}$') then
    raise exception 'invalid_page';
  end if;
  insert into public.page_views (day, page, views) values (current_date, p, 1)
  on conflict (day, page) do update set views = public.page_views.views + 1;
end $$;
revoke execute on function public.count_view(text) from public;
grant execute on function public.count_view(text) to anon, authenticated;
