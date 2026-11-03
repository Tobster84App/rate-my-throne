-- Seitenaufrufe zählen: nur eine Zahl je Seite und Tag, nichts über die Person (keine IP, kein Cookie).
-- Zählen über count_view(), lesen nur für Admins über admin_page_views().

create table if not exists public.page_views (
  day date not null default current_date,
  page text not null check (page in ('home', 'map')),
  views bigint not null default 0,
  primary key (day, page)
);
alter table public.page_views enable row level security;   -- keine Policies: direkter Zugriff gesperrt

create or replace function public.count_view(p text) returns void
language plpgsql security definer set search_path = '' as $$
begin
  if p not in ('home', 'map') then
    raise exception 'invalid_page';
  end if;
  insert into public.page_views (day, page, views) values (current_date, p, 1)
  on conflict (day, page) do update set views = public.page_views.views + 1;
end $$;
revoke execute on function public.count_view(text) from public;
grant execute on function public.count_view(text) to anon, authenticated;

create or replace function public.admin_page_views()
returns table (day date, page text, views bigint)
language plpgsql security definer set search_path = '' as $$
begin
  if not public.is_admin() then
    raise exception 'not_admin';
  end if;
  return query select v.day, v.page, v.views from public.page_views v order by v.day desc, v.page;
end $$;
revoke execute on function public.admin_page_views() from public, anon;
grant execute on function public.admin_page_views() to authenticated;
