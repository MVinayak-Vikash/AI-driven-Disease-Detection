-- AI Early-Risk & Referral Navigator: Supabase is the sole production datastore.
create extension if not exists pgcrypto;

create table public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  name text, date_of_birth date, age integer check (age between 0 and 130), gender text,
  medical_history jsonb not null default '[]'::jsonb,
  created_at timestamptz not null default now(), updated_at timestamptz not null default now()
);
create table public.devices (
  id uuid primary key default gen_random_uuid(), user_id uuid not null references auth.users(id) on delete cascade,
  device_uid text not null unique, device_name text, device_type text, device_token_hash text not null,
  status text not null default 'active' check (status in ('active','inactive','revoked')), last_seen timestamptz,
  created_at timestamptz not null default now()
);
create table public.measurement_sessions (
  id uuid primary key default gen_random_uuid(), user_id uuid not null references auth.users(id) on delete cascade,
  device_id uuid not null references public.devices(id) on delete restrict,
  started_at timestamptz not null default now(), ended_at timestamptz,
  status text not null default 'active' check (status in ('active','finished','cancelled'))
);
create table public.sensor_readings (
  id uuid primary key default gen_random_uuid(), session_id uuid not null references public.measurement_sessions(id) on delete cascade,
  timestamp timestamptz not null default now(), heart_rate double precision check (heart_rate between 20 and 250),
  spo2 double precision check (spo2 between 50 and 100), ppg_data jsonb,
  signal_quality double precision check (signal_quality between 0 and 1),
  check (heart_rate is not null or spo2 is not null or ppg_data is not null or signal_quality is not null)
);
create table public.physiological_features (
  id uuid primary key default gen_random_uuid(), session_id uuid not null unique references public.measurement_sessions(id) on delete cascade,
  heart_rate_mean double precision, heart_rate_min double precision, heart_rate_max double precision,
  hrv double precision, rmssd double precision, rhythm_irregularity double precision check (rhythm_irregularity between 0 and 1),
  signal_quality double precision check (signal_quality between 0 and 1), baseline_delta jsonb, trend_delta jsonb,
  created_at timestamptz not null default now()
);
create table public.ai_assessments (
  id uuid primary key default gen_random_uuid(), session_id uuid not null unique references public.measurement_sessions(id) on delete cascade,
  risk_level text not null check (risk_level in ('LOW','MODERATE','HIGH')), risk_score double precision not null check (risk_score between 0 and 1),
  confidence double precision not null check (confidence between 0 and 1), conditions_of_concern jsonb not null default '[]'::jsonb,
  evidence jsonb not null default '[]'::jsonb, trends jsonb not null default '[]'::jsonb,
  recommended_action text not null, specialist text, model_name text not null, model_version text not null,
  raw_response jsonb, created_at timestamptz not null default now()
);
create index devices_user_id_idx on public.devices(user_id);
create index sessions_user_started_idx on public.measurement_sessions(user_id, started_at desc);
create index sessions_device_id_idx on public.measurement_sessions(device_id);
create index readings_session_time_idx on public.sensor_readings(session_id, timestamp);
create index features_session_idx on public.physiological_features(session_id);
create index assessments_session_idx on public.ai_assessments(session_id);

alter table public.profiles enable row level security;
alter table public.devices enable row level security;
alter table public.measurement_sessions enable row level security;
alter table public.sensor_readings enable row level security;
alter table public.physiological_features enable row level security;
alter table public.ai_assessments enable row level security;

-- Explicit grants are needed for the authenticated Data API role; RLS remains
-- the authorization boundary. Do not grant the anon role access to PHI tables.
grant usage on schema public to authenticated;
grant select, insert, update, delete on all tables in schema public to authenticated;

create policy "own profile" on public.profiles for all to authenticated using ((select auth.uid()) = id) with check ((select auth.uid()) = id);
create policy "own devices" on public.devices for all to authenticated using ((select auth.uid()) = user_id) with check ((select auth.uid()) = user_id);
create policy "own sessions" on public.measurement_sessions for all to authenticated using ((select auth.uid()) = user_id) with check ((select auth.uid()) = user_id);
create policy "own readings through session" on public.sensor_readings for all to authenticated using (exists (select 1 from public.measurement_sessions s where s.id = session_id and s.user_id = (select auth.uid()))) with check (exists (select 1 from public.measurement_sessions s where s.id = session_id and s.user_id = (select auth.uid())));
create policy "own features through session" on public.physiological_features for all to authenticated using (exists (select 1 from public.measurement_sessions s where s.id = session_id and s.user_id = (select auth.uid()))) with check (exists (select 1 from public.measurement_sessions s where s.id = session_id and s.user_id = (select auth.uid())));
create policy "own assessments through session" on public.ai_assessments for all to authenticated using (exists (select 1 from public.measurement_sessions s where s.id = session_id and s.user_id = (select auth.uid()))) with check (exists (select 1 from public.measurement_sessions s where s.id = session_id and s.user_id = (select auth.uid())));
