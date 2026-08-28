create table if not exists public.workspaces (
  user_id uuid primary key references auth.users(id) on delete cascade,
  files jsonb not null default '{}'::jsonb,
  updated_at timestamptz not null default now()
);

alter table public.workspaces enable row level security;

create policy "Users can read their workspace"
  on public.workspaces for select
  using (auth.uid() = user_id);

create policy "Users can create their workspace"
  on public.workspaces for insert
  with check (auth.uid() = user_id);

create policy "Users can update their workspace"
  on public.workspaces for update
  using (auth.uid() = user_id)
  with check (auth.uid() = user_id);
