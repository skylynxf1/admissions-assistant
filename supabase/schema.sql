-- Suggested Supabase schema for Pathwise. Review and tailor RLS before production use.
create extension if not exists "pgcrypto";

create table public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  display_name text,
  residency_status text,
  citizenship_status text,
  home_state text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table public.institutions (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  institution_type text not null,
  state text,
  country text not null default 'US',
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table public.transcripts (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.profiles(id) on delete cascade,
  institution_id uuid references public.institutions(id),
  storage_path text,
  original_filename text,
  extraction_status text not null default 'pending',
  verification_status text not null default 'unreviewed',
  cumulative_gpa numeric(4,3),
  extraction_metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table public.course_records (
  id uuid primary key default gen_random_uuid(),
  transcript_id uuid not null references public.transcripts(id) on delete cascade,
  institution_id uuid references public.institutions(id),
  course_code text not null,
  course_title text not null,
  term text not null,
  credits_attempted numeric(5,2) not null,
  credits_earned numeric(5,2) not null,
  grade text,
  course_status text not null,
  confidence text not null,
  repeat_indicator boolean not null default false,
  transfer_indicator boolean not null default false,
  user_verified boolean not null default false,
  extraction_evidence jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table public.exam_credits (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.profiles(id) on delete cascade,
  exam_type text not null,
  subject text not null,
  score text not null,
  credits_awarded numeric(5,2),
  exam_date date,
  created_at timestamptz not null default now()
);

create table public.policy_sources (
  id uuid primary key default gen_random_uuid(),
  institution_id uuid not null references public.institutions(id),
  program_key text,
  policy_type text not null,
  title text not null,
  source_url text not null,
  effective_term text,
  retrieved_at timestamptz not null,
  content_hash text,
  official boolean not null default true,
  source_snapshot text,
  metadata jsonb not null default '{}'::jsonb,
  unique (source_url, effective_term, content_hash)
);

create table public.course_equivalencies (
  id uuid primary key default gen_random_uuid(),
  source_institution_id uuid not null references public.institutions(id),
  source_course_code text not null,
  destination_institution_id uuid not null references public.institutions(id),
  destination_course_code text,
  requirement_category text,
  credit_amount numeric(5,2),
  confidence text not null,
  reasoning text,
  confirmation_recommended boolean not null default false,
  policy_source_ids uuid[] not null default '{}',
  effective_term text,
  created_at timestamptz not null default now()
);

create table public.scenarios (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.profiles(id) on delete cascade,
  name text not null,
  planning_mode text not null,
  profile_snapshot jsonb not null,
  selected_targets jsonb not null,
  settings jsonb not null,
  analysis_result jsonb,
  analysis_version text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table public.advisor_messages (
  id uuid primary key default gen_random_uuid(),
  scenario_id uuid not null references public.scenarios(id) on delete cascade,
  user_id uuid not null references public.profiles(id) on delete cascade,
  role text not null check (role in ('user', 'assistant')),
  content text not null,
  confidence text,
  citation_ids uuid[] not null default '{}',
  created_at timestamptz not null default now()
);

alter table public.profiles enable row level security;
alter table public.transcripts enable row level security;
alter table public.course_records enable row level security;
alter table public.exam_credits enable row level security;
alter table public.scenarios enable row level security;
alter table public.advisor_messages enable row level security;

create policy "users manage own profile" on public.profiles for all using (auth.uid() = id) with check (auth.uid() = id);
create policy "users manage own transcripts" on public.transcripts for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy "users manage courses through own transcript" on public.course_records for all
  using (exists (select 1 from public.transcripts t where t.id = transcript_id and t.user_id = auth.uid()))
  with check (exists (select 1 from public.transcripts t where t.id = transcript_id and t.user_id = auth.uid()));
create policy "users manage own exam credits" on public.exam_credits for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy "users manage own scenarios" on public.scenarios for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy "users manage own advisor messages" on public.advisor_messages for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

-- institutions, policy_sources, and course_equivalencies should be readable by authenticated users
-- but writable only by a trusted ingestion service using the server-side service role.
