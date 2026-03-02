-- Run this in Supabase SQL Editor to create all tables

create table stories (
  id uuid primary key default gen_random_uuid(),
  title text not null,
  summary text not null,
  category text not null,
  current_status text not null,
  source text not null,
  created_at timestamptz default now(),
  last_updated timestamptz default now(),
  is_active boolean default true
);

create table users (
  id uuid primary key default gen_random_uuid(),
  email text unique not null,
  lang text default 'en',
  token text unique not null,
  verified boolean default false,
  verification_token text unique,
  created_at timestamptz default now()
);

create table watches (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references users(id) on delete cascade,
  story_id uuid references stories(id) on delete cascade,
  created_at timestamptz default now(),
  unique(user_id, story_id)
);

create table updates (
  id uuid primary key default gen_random_uuid(),
  story_id uuid references stories(id) on delete cascade,
  level text not null check (level in ('big_move', 'small_move')),
  summary text not null,
  new_status text not null,
  created_at timestamptz default now()
);

create index idx_stories_active on stories(is_active);
create index idx_watches_user on watches(user_id);
create index idx_watches_story on watches(story_id);
create index idx_updates_story on updates(story_id);
create index idx_updates_created on updates(created_at);
create index idx_users_token on users(token);
create index idx_users_verification on users(verification_token);
