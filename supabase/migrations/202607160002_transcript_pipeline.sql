-- Transcript ingestion pipeline: private document -> immutable parse evidence -> editable reviewed record.
-- This schema contains transcript facts only. It deliberately has no transfer-equivalency fields.

create type student.transcript_document_status as enum ('uploaded', 'processing', 'needs_review', 'completed', 'failed');
create type student.transcript_parse_status as enum ('queued', 'running', 'succeeded', 'failed');
create type student.transcript_warning_severity as enum ('info', 'warning', 'blocking');
create type student.transcript_warning_state as enum ('open', 'resolved', 'dismissed');

create table student.transcript_documents (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references student.profiles(id) on delete cascade,
  planner_transcript_id uuid references student.transcripts(id) on delete set null,
  original_filename text not null,
  storage_bucket text not null default 'transcript-uploads',
  storage_path text not null,
  mime_type text not null default 'application/pdf',
  size_bytes bigint not null check (size_bytes > 0 and size_bytes <= 15728640),
  content_hash_sha256 text not null,
  status student.transcript_document_status not null default 'uploaded',
  active_parse_run_id uuid,
  failure_code text,
  failure_message text,
  confirmed_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (user_id, content_hash_sha256),
  unique (user_id, storage_path)
);

create table student.transcript_parse_runs (
  id uuid primary key default gen_random_uuid(),
  document_id uuid not null references student.transcript_documents(id) on delete cascade,
  sequence_number integer not null check (sequence_number > 0),
  parser_name text not null,
  parser_version text not null,
  extraction_model text,
  extraction_schema_version text not null default '1.0',
  status student.transcript_parse_status not null default 'queued',
  raw_parser_output jsonb,
  raw_model_output jsonb,
  validation_output jsonb,
  error_code text,
  error_message text,
  started_at timestamptz,
  completed_at timestamptz,
  created_at timestamptz not null default now(),
  unique (document_id, sequence_number)
);

alter table student.transcript_documents
  add constraint transcript_documents_active_run_fk
  foreign key (active_parse_run_id) references student.transcript_parse_runs(id) on delete set null;

create table student.transcript_pages (
  id uuid primary key default gen_random_uuid(),
  parse_run_id uuid not null references student.transcript_parse_runs(id) on delete cascade,
  page_number integer not null check (page_number > 0),
  markdown text not null default '',
  plain_text text not null default '',
  parser_blocks jsonb not null default '[]'::jsonb,
  created_at timestamptz not null default now(),
  unique (parse_run_id, page_number)
);

create table student.student_institutions (
  id uuid primary key default gen_random_uuid(),
  document_id uuid not null references student.transcript_documents(id) on delete cascade,
  source_entity_id text not null,
  institution_name text not null,
  student_identifier text,
  attendance_start text,
  attendance_end text,
  degree_name text,
  degree_date text,
  extraction_confidence numeric(5,4) not null check (extraction_confidence between 0 and 1),
  source_page integer not null check (source_page > 0),
  source_block_ids jsonb not null default '[]'::jsonb,
  source_raw_text text,
  user_verified boolean not null default false,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (document_id, source_entity_id)
);

create table student.academic_terms (
  id uuid primary key default gen_random_uuid(),
  document_id uuid not null references student.transcript_documents(id) on delete cascade,
  student_institution_id uuid not null references student.student_institutions(id) on delete cascade,
  source_entity_id text not null,
  label text not null,
  start_date text,
  end_date text,
  academic_level text,
  credits_attempted numeric(7,2),
  credits_earned numeric(7,2),
  term_gpa numeric(5,3),
  extraction_confidence numeric(5,4) not null check (extraction_confidence between 0 and 1),
  source_page integer not null check (source_page > 0),
  source_block_ids jsonb not null default '[]'::jsonb,
  source_raw_text text,
  user_verified boolean not null default false,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (document_id, source_entity_id)
);

create table student.transcript_courses (
  id uuid primary key default gen_random_uuid(),
  document_id uuid not null references student.transcript_documents(id) on delete cascade,
  student_institution_id uuid not null references student.student_institutions(id) on delete cascade,
  academic_term_id uuid not null references student.academic_terms(id) on delete cascade,
  source_entity_id text not null,
  course_code text not null default '',
  course_title text not null default '',
  credits_attempted numeric(7,2),
  credits_earned numeric(7,2),
  grade text,
  course_status text not null,
  repeat_indicator boolean not null default false,
  transfer_indicator boolean not null default false,
  extraction_confidence numeric(5,4) not null check (extraction_confidence between 0 and 1),
  source_page integer not null check (source_page > 0),
  source_block_ids jsonb not null default '[]'::jsonb,
  source_raw_text text,
  user_verified boolean not null default false,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (document_id, source_entity_id)
);

create table student.exam_credits (
  id uuid primary key default gen_random_uuid(),
  document_id uuid not null references student.transcript_documents(id) on delete cascade,
  source_entity_id text not null,
  exam_type text not null,
  subject text not null,
  score text,
  credits_awarded numeric(7,2),
  extraction_confidence numeric(5,4) not null check (extraction_confidence between 0 and 1),
  source_page integer not null check (source_page > 0),
  source_block_ids jsonb not null default '[]'::jsonb,
  source_raw_text text,
  user_verified boolean not null default false,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (document_id, source_entity_id)
);

create table student.transcript_summaries (
  id uuid primary key default gen_random_uuid(),
  document_id uuid not null unique references student.transcript_documents(id) on delete cascade,
  cumulative_gpa numeric(5,3),
  total_credits_attempted numeric(9,2),
  total_credits_earned numeric(9,2),
  total_quality_points numeric(10,3),
  degree_name text,
  degree_date text,
  extraction_confidence numeric(5,4) not null check (extraction_confidence between 0 and 1),
  source_page integer not null check (source_page > 0),
  source_block_ids jsonb not null default '[]'::jsonb,
  source_raw_text text,
  user_verified boolean not null default false,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table student.transcript_warnings (
  id uuid primary key default gen_random_uuid(),
  document_id uuid not null references student.transcript_documents(id) on delete cascade,
  parse_run_id uuid references student.transcript_parse_runs(id) on delete set null,
  client_warning_id text not null,
  warning_code text not null,
  severity student.transcript_warning_severity not null,
  state student.transcript_warning_state not null default 'open',
  entity_type text not null,
  entity_source_id text,
  message text not null,
  details jsonb not null default '{}'::jsonb,
  source_page integer,
  source_block_ids jsonb not null default '[]'::jsonb,
  resolution_note text,
  resolved_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (document_id, client_warning_id)
);

create table student.transcript_review_actions (
  id uuid primary key default gen_random_uuid(),
  document_id uuid not null references student.transcript_documents(id) on delete cascade,
  user_id uuid not null references student.profiles(id) on delete cascade,
  action_type text not null,
  entity_type text not null,
  entity_id uuid,
  field_name text,
  previous_value jsonb,
  new_value jsonb,
  note text,
  created_at timestamptz not null default now()
);

create index transcript_documents_user_status_idx on student.transcript_documents (user_id, status, created_at desc);
create index transcript_parse_runs_document_idx on student.transcript_parse_runs (document_id, sequence_number desc);
create index transcript_pages_run_idx on student.transcript_pages (parse_run_id, page_number);
create index student_institutions_document_idx on student.student_institutions (document_id);
create index academic_terms_document_idx on student.academic_terms (document_id);
create index transcript_courses_document_idx on student.transcript_courses (document_id, academic_term_id);
create index exam_credits_document_idx on student.exam_credits (document_id);
create index transcript_warnings_open_idx on student.transcript_warnings (document_id, state, severity);
create index transcript_review_actions_document_idx on student.transcript_review_actions (document_id, created_at desc);

create trigger transcript_documents_set_updated_at before update on student.transcript_documents for each row execute function public.set_updated_at();
create trigger student_institutions_set_updated_at before update on student.student_institutions for each row execute function public.set_updated_at();
create trigger academic_terms_set_updated_at before update on student.academic_terms for each row execute function public.set_updated_at();
create trigger transcript_courses_set_updated_at before update on student.transcript_courses for each row execute function public.set_updated_at();
create trigger exam_credits_set_updated_at before update on student.exam_credits for each row execute function public.set_updated_at();
create trigger transcript_summaries_set_updated_at before update on student.transcript_summaries for each row execute function public.set_updated_at();
create trigger transcript_warnings_set_updated_at before update on student.transcript_warnings for each row execute function public.set_updated_at();

create or replace function student.owns_transcript_document(target_document_id uuid)
returns boolean language sql stable security definer set search_path = '' as $$
  select exists (select 1 from student.transcript_documents d where d.id = target_document_id and d.user_id = auth.uid());
$$;

create or replace function student.owns_transcript_parse_run(target_run_id uuid)
returns boolean language sql stable security definer set search_path = '' as $$
  select exists (
    select 1 from student.transcript_parse_runs r
    join student.transcript_documents d on d.id = r.document_id
    where r.id = target_run_id and d.user_id = auth.uid()
  );
$$;

alter table student.transcript_documents enable row level security;
alter table student.transcript_parse_runs enable row level security;
alter table student.transcript_pages enable row level security;
alter table student.student_institutions enable row level security;
alter table student.academic_terms enable row level security;
alter table student.transcript_courses enable row level security;
alter table student.exam_credits enable row level security;
alter table student.transcript_summaries enable row level security;
alter table student.transcript_warnings enable row level security;
alter table student.transcript_review_actions enable row level security;

create policy "users manage own transcript documents" on student.transcript_documents for all to authenticated
  using ((select auth.uid()) = user_id) with check ((select auth.uid()) = user_id);
create policy "users insert own parse runs" on student.transcript_parse_runs for insert to authenticated
  with check (student.owns_transcript_document(document_id));
create policy "users read own parse runs" on student.transcript_parse_runs for select to authenticated
  using (student.owns_transcript_document(document_id));
create policy "users insert own transcript pages" on student.transcript_pages for insert to authenticated
  with check (student.owns_transcript_parse_run(parse_run_id));
create policy "users read own transcript pages" on student.transcript_pages for select to authenticated
  using (student.owns_transcript_parse_run(parse_run_id));
create policy "users manage own student institutions" on student.student_institutions for all to authenticated
  using (student.owns_transcript_document(document_id)) with check (student.owns_transcript_document(document_id));
create policy "users manage own academic terms" on student.academic_terms for all to authenticated
  using (student.owns_transcript_document(document_id)) with check (student.owns_transcript_document(document_id));
create policy "users manage own transcript courses" on student.transcript_courses for all to authenticated
  using (student.owns_transcript_document(document_id)) with check (student.owns_transcript_document(document_id));
create policy "users manage own exam credits" on student.exam_credits for all to authenticated
  using (student.owns_transcript_document(document_id)) with check (student.owns_transcript_document(document_id));
create policy "users manage own transcript summaries" on student.transcript_summaries for all to authenticated
  using (student.owns_transcript_document(document_id)) with check (student.owns_transcript_document(document_id));
create policy "users manage own transcript warnings" on student.transcript_warnings for all to authenticated
  using (student.owns_transcript_document(document_id)) with check (student.owns_transcript_document(document_id));
create policy "users insert own review actions" on student.transcript_review_actions for insert to authenticated
  with check ((select auth.uid()) = user_id and student.owns_transcript_document(document_id));
create policy "users read own review actions" on student.transcript_review_actions for select to authenticated
  using ((select auth.uid()) = user_id and student.owns_transcript_document(document_id));

grant select, insert, update, delete on student.transcript_documents, student.student_institutions,
  student.academic_terms, student.transcript_courses, student.exam_credits, student.transcript_summaries,
  student.transcript_warnings to authenticated;
grant select, insert on student.transcript_parse_runs, student.transcript_pages, student.transcript_review_actions to authenticated;
grant all on student.transcript_documents, student.transcript_parse_runs, student.transcript_pages,
  student.student_institutions, student.academic_terms, student.transcript_courses, student.exam_credits,
  student.transcript_summaries, student.transcript_warnings, student.transcript_review_actions to service_role;
