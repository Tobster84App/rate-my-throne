-- Benutzernamen ändern: nur über diese Funktion (so bleibt is_admin für Nutzer unveränderbar).
-- Neue Benutzernamen dürfen kein @ enthalten, damit keine E-Mail-Adressen öffentlich werden.
alter table public.profiles drop constraint if exists profiles_username_no_at;
alter table public.profiles add constraint profiles_username_no_at check (position('@' in username) = 0) not valid;

create or replace function public.set_username(new_name text) returns text
language plpgsql security definer set search_path = '' as $$
declare clean text := btrim(new_name);
begin
  if auth.uid() is null then raise exception 'not signed in'; end if;
  if char_length(clean) < 3 or char_length(clean) > 30 then raise exception 'length'; end if;
  if position('@' in clean) > 0 then raise exception 'at_sign'; end if;
  if exists (select 1 from public.profiles where lower(username) = lower(clean) and id <> auth.uid()) then
    raise exception 'taken';
  end if;
  update public.profiles set username = clean where id = auth.uid();
  return clean;
end $$;

revoke execute on function public.set_username(text) from public, anon;
grant execute on function public.set_username(text) to authenticated;
