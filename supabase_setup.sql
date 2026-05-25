-- Run in Supabase SQL Editor (Dashboard → SQL → New query)

-- Profiles (display names for leaderboard)
create table if not exists public.profiles (
  id uuid primary key references auth.users (id) on delete cascade,
  display_name text not null,
  created_at timestamptz default now()
);

alter table public.profiles enable row level security;

create policy "Profiles are viewable by authenticated users"
  on public.profiles for select to authenticated using (true);

create policy "Users can insert own profile"
  on public.profiles for insert to authenticated
  with check (auth.uid() = id);

create policy "Users can update own profile"
  on public.profiles for update to authenticated
  using (auth.uid() = id);

-- Predictions (home / draw / away per match)
create table if not exists public.predictions (
  id bigint generated always as identity primary key,
  user_id uuid not null references auth.users (id) on delete cascade,
  match_id bigint not null references public.matches (id) on delete cascade,
  pick text not null check (pick in ('home', 'draw', 'away')),
  created_at timestamptz default now(),
  unique (user_id, match_id)
);

alter table public.predictions enable row level security;

create policy "Predictions viewable by authenticated users"
  on public.predictions for select to authenticated using (true);

create policy "Users can insert own predictions"
  on public.predictions for insert to authenticated
  with check (auth.uid() = user_id);

create policy "Users can update own predictions"
  on public.predictions for update to authenticated
  using (auth.uid() = user_id);

-- Matches: allow authenticated read (if not already)
alter table public.matches enable row level security;

drop policy if exists "Matches readable by authenticated" on public.matches;
create policy "Matches readable by authenticated"
  on public.matches for select to authenticated using (true);
