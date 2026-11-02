-- Nutzer-Übersicht für Admins: Benutzername, Registrierung, letzte Anmeldung, Zahl der Bewertungen und eingetragenen Toiletten.
-- E-Mail-Adressen werden bewusst nicht ausgegeben. Nicht-Admins bekommen einen Fehler.

create or replace function public.admin_users()
returns table (id uuid, username text, is_admin boolean, created_at timestamptz, last_sign_in_at timestamptz,
               confirmed boolean, reviews bigint, toilets bigint)
language plpgsql security definer set search_path = '' as $$
begin
  if not public.is_admin() then
    raise exception 'not_admin';
  end if;
  return query
    select u.id, p.username, coalesce(p.is_admin, false), u.created_at, u.last_sign_in_at,
           u.email_confirmed_at is not null,
           (select count(*) from public.reviews r where r.user_id = u.id),
           (select count(*) from public.toilets t where t.created_by = u.id)
    from auth.users u
    left join public.profiles p on p.id = u.id
    order by u.created_at desc;
end $$;

revoke execute on function public.admin_users() from public, anon;
grant execute on function public.admin_users() to authenticated;
