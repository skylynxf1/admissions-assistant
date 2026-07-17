-- Pathwise Supabase foundation
-- Public evidence describes what official sources say; policy normalizes those facts;
-- planning records how the rules apply to one student's scenario.

create extension if not exists "pgcrypto";

create schema if not exists source;
create schema if not exists catalog;
create schema if not exists policy;
create schema if not exists equivalency;
create schema if not exists student;
create schema if not exists planning;
create schema if not exists operations;

create type public.confidence_level as enum ('high', 'medium', 'low');
create type source.source_type as enum ('web_page', 'catalog', 'policy', 'articulation', 'pdf', 'json', 'csv', 'api');
create type source.review_status as enum ('pending', 'approved', 'rejected', 'needs_review');
create type policy.requirement_kind as enum (
  'university', 'general_education', 'college', 'degree', 'major', 'major_admission',
  'minor', 'graduation', 'residency', 'enrollment_prerequisite', 'recommended_preparation'
);
create type policy.requirement_scope as enum (
  'institution', 'campus', 'college', 'department', 'program', 'major', 'applicant_type', 'catalog_year'
);
create type policy.expression_type as enum (
  'course', 'all_of', 'any_of', 'choose_n', 'sequence', 'minimum_grade', 'minimum_gpa',
  'minimum_credits', 'concurrent', 'placement', 'permission', 'class_standing',
  'program_restriction', 'campus_restriction', 'conditional', 'raw_unresolved'
);
create type equivalency.mapping_type as enum (
  'direct_equivalent', 'departmental_elective', 'general_elective', 'general_education',
  'major_requirement', 'sequence_equivalent', 'partial_equivalent', 'no_credit',
  'not_found', 'manual_review'
);
create type student.transcript_status as enum ('pending', 'extracting', 'complete', 'error');
create type student.verification_state as enum ('unreviewed', 'reviewing', 'confirmed');
create type planning.verification_status as enum ('confirmed', 'likely', 'unclear', 'manual_evaluation', 'conflicting');
create type planning.requirement_evaluation_status as enum (
  'satisfied', 'partially_satisfied', 'not_satisfied', 'in_progress', 'planned', 'unresolved', 'not_applicable'
);
create type operations.job_status as enum ('queued', 'running', 'succeeded', 'failed', 'cancelled');

create or replace function public.set_updated_at()
returns trigger
language plpgsql
set search_path = ''
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

-- CATALOG -------------------------------------------------------------------

create table catalog.institutions (
  id uuid primary key default gen_random_uuid(),
  slug text not null unique,
  name text not null,
  short_name text,
  institution_type text not null,
  system_name text,
  campus text,
  city text,
  state text,
  country text not null default 'US',
  timezone text,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table source.official_domains (
  id uuid primary key default gen_random_uuid(),
  institution_id uuid not null references catalog.institutions(id) on delete cascade,
  domain text not null,
  campus text,
  verified_at timestamptz,
  active boolean not null default true,
  created_at timestamptz not null default now(),
  unique (institution_id, domain)
);

create table catalog.catalog_versions (
  id uuid primary key default gen_random_uuid(),
  institution_id uuid not null references catalog.institutions(id) on delete cascade,
  label text not null,
  academic_year text,
  effective_from date,
  effective_to date,
  is_current boolean not null default false,
  source_page_id uuid,
  created_at timestamptz not null default now(),
  unique (institution_id, label)
);

create table catalog.colleges (
  id uuid primary key default gen_random_uuid(),
  institution_id uuid not null references catalog.institutions(id) on delete cascade,
  name text not null,
  code text,
  campus text,
  metadata jsonb not null default '{}'::jsonb,
  unique (institution_id, name, campus)
);

create table catalog.departments (
  id uuid primary key default gen_random_uuid(),
  institution_id uuid not null references catalog.institutions(id) on delete cascade,
  college_id uuid references catalog.colleges(id) on delete set null,
  name text not null,
  code text,
  campus text,
  metadata jsonb not null default '{}'::jsonb,
  unique (institution_id, name, campus)
);

create table catalog.courses (
  id uuid primary key default gen_random_uuid(),
  institution_id uuid not null references catalog.institutions(id) on delete cascade,
  department_id uuid references catalog.departments(id) on delete set null,
  campus text,
  subject text not null,
  number text not null,
  canonical_code text generated always as (trim(subject) || ' ' || trim(number)) stored,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (institution_id, campus, subject, number)
);

create table catalog.course_versions (
  id uuid primary key default gen_random_uuid(),
  course_id uuid not null references catalog.courses(id) on delete cascade,
  catalog_version_id uuid references catalog.catalog_versions(id) on delete set null,
  title text not null,
  description text,
  credits_min numeric(5,2),
  credits_max numeric(5,2),
  course_level text,
  prerequisite_expression jsonb,
  corequisite_expression jsonb,
  restrictions jsonb not null default '[]'::jsonb,
  repeatability jsonb not null default '{}'::jsonb,
  equivalent_course_ids uuid[] not null default '{}',
  cross_listed_course_ids uuid[] not null default '{}',
  general_education_designators text[] not null default '{}',
  effective_from date,
  effective_to date,
  created_at timestamptz not null default now(),
  unique (course_id, catalog_version_id)
);

create table catalog.course_offerings (
  id uuid primary key default gen_random_uuid(),
  course_id uuid not null references catalog.courses(id) on delete cascade,
  term text not null,
  campus text,
  delivery_modes text[] not null default '{}',
  status text,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  unique (course_id, term, campus)
);

create table catalog.programs (
  id uuid primary key default gen_random_uuid(),
  institution_id uuid not null references catalog.institutions(id) on delete cascade,
  college_id uuid references catalog.colleges(id) on delete set null,
  department_id uuid references catalog.departments(id) on delete set null,
  catalog_version_id uuid references catalog.catalog_versions(id) on delete set null,
  slug text not null,
  campus text,
  name text not null,
  degree_type text,
  program_type text not null,
  admission_type text,
  capacity_status text,
  application_required boolean not null default false,
  application_terms text[] not null default '{}',
  application_deadlines jsonb not null default '{}'::jsonb,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (institution_id, slug, catalog_version_id)
);

create table catalog.concentrations (
  id uuid primary key default gen_random_uuid(),
  program_id uuid not null references catalog.programs(id) on delete cascade,
  name text not null,
  concentration_type text not null default 'concentration',
  metadata jsonb not null default '{}'::jsonb,
  unique (program_id, name)
);

-- SOURCE AND INGESTION -------------------------------------------------------

create table source.pages (
  id uuid primary key default gen_random_uuid(),
  institution_id uuid not null references catalog.institutions(id) on delete cascade,
  original_url text not null,
  canonical_url text not null,
  page_title text,
  source_type source.source_type not null,
  official boolean not null default false,
  active boolean not null default true,
  first_seen_at timestamptz not null default now(),
  last_seen_at timestamptz not null default now(),
  metadata jsonb not null default '{}'::jsonb,
  unique (institution_id, canonical_url)
);

alter table catalog.catalog_versions
  add constraint catalog_versions_source_page_fk
  foreign key (source_page_id) references source.pages(id) on delete set null;

create table operations.crawl_jobs (
  id uuid primary key default gen_random_uuid(),
  institution_id uuid references catalog.institutions(id) on delete set null,
  status operations.job_status not null default 'queued',
  requested_by uuid references auth.users(id) on delete set null,
  seed_urls text[] not null default '{}',
  configuration jsonb not null default '{}'::jsonb,
  started_at timestamptz,
  finished_at timestamptz,
  error_message text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table source.snapshots (
  id uuid primary key default gen_random_uuid(),
  page_id uuid not null references source.pages(id) on delete cascade,
  crawl_job_id uuid references operations.crawl_jobs(id) on delete set null,
  retrieved_at timestamptz not null,
  content_hash text not null,
  mime_type text,
  storage_bucket text,
  storage_path text,
  http_status integer,
  etag text,
  catalog_year text,
  effective_term text,
  raw_text text,
  response_metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  unique (page_id, content_hash)
);

create table operations.parser_runs (
  id uuid primary key default gen_random_uuid(),
  snapshot_id uuid not null references source.snapshots(id) on delete cascade,
  status operations.job_status not null default 'queued',
  parser_name text not null,
  parser_version text not null,
  prompt_version text,
  model text,
  input_hash text,
  output jsonb,
  started_at timestamptz,
  finished_at timestamptz,
  error_message text,
  created_at timestamptz not null default now()
);

create table source.evidence_records (
  id uuid primary key default gen_random_uuid(),
  snapshot_id uuid not null references source.snapshots(id) on delete cascade,
  parser_run_id uuid references operations.parser_runs(id) on delete set null,
  claim_key text not null,
  claim_type text not null,
  exact_quote text not null,
  locator jsonb not null default '{}'::jsonb,
  table_headers jsonb,
  table_row jsonb,
  footnotes text[] not null default '{}',
  normalized_value jsonb,
  effective_from date,
  effective_to date,
  confidence public.confidence_level not null,
  review_status source.review_status not null default 'pending',
  reviewed_by uuid references auth.users(id) on delete set null,
  reviewed_at timestamptz,
  created_at timestamptz not null default now()
);

create table source.evidence_links (
  evidence_id uuid not null references source.evidence_records(id) on delete cascade,
  entity_schema text not null,
  entity_table text not null,
  entity_id uuid not null,
  relationship text not null default 'supports',
  created_at timestamptz not null default now(),
  primary key (evidence_id, entity_schema, entity_table, entity_id)
);

-- POLICY --------------------------------------------------------------------

create table policy.requirements (
  id uuid primary key default gen_random_uuid(),
  institution_id uuid not null references catalog.institutions(id) on delete cascade,
  program_id uuid references catalog.programs(id) on delete cascade,
  catalog_version_id uuid references catalog.catalog_versions(id) on delete set null,
  requirement_type policy.requirement_kind not null,
  scope policy.requirement_scope not null,
  scope_key text,
  name text not null,
  description text,
  expression jsonb not null,
  minimum_credits numeric(7,2),
  minimum_courses integer,
  minimum_grade text,
  exclusions jsonb not null default '[]'::jsonb,
  double_counting_rule jsonb,
  residency_rule jsonb,
  mandatory boolean not null default true,
  recommended boolean not null default false,
  effective_from date,
  effective_to date,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  check (not (mandatory and recommended))
);

create table policy.requirement_expressions (
  id uuid primary key default gen_random_uuid(),
  requirement_id uuid not null references policy.requirements(id) on delete cascade,
  parent_id uuid references policy.requirement_expressions(id) on delete cascade,
  expression_type policy.expression_type not null,
  position integer not null default 0,
  course_id uuid references catalog.courses(id) on delete set null,
  value jsonb not null default '{}'::jsonb,
  constraints jsonb not null default '[]'::jsonb,
  raw_text text,
  created_at timestamptz not null default now(),
  unique (requirement_id, parent_id, position)
);

create table policy.requirement_courses (
  requirement_id uuid not null references policy.requirements(id) on delete cascade,
  course_id uuid not null references catalog.courses(id) on delete cascade,
  role text not null default 'allowed',
  conditions jsonb not null default '{}'::jsonb,
  primary key (requirement_id, course_id, role)
);

create table policy.transfer_policies (
  id uuid primary key default gen_random_uuid(),
  institution_id uuid not null references catalog.institutions(id) on delete cascade,
  program_id uuid references catalog.programs(id) on delete cascade,
  applicant_type text,
  sending_institution_type text,
  minimum_transfer_credits numeric(7,2),
  preferred_credit_min numeric(7,2),
  preferred_credit_max numeric(7,2),
  maximum_transfer_credits numeric(7,2),
  lower_division_limit numeric(7,2),
  minimum_grade text,
  credit_conversion_rule jsonb,
  class_standing_effect jsonb,
  admission_eligibility_effect jsonb,
  degree_applicability jsonb,
  effective_from date,
  effective_to date,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table policy.exam_credit_rules (
  id uuid primary key default gen_random_uuid(),
  institution_id uuid not null references catalog.institutions(id) on delete cascade,
  program_id uuid references catalog.programs(id) on delete cascade,
  exam_type text not null,
  exam_name text not null,
  score_min numeric(6,2),
  score_max numeric(6,2),
  awarded_course_ids uuid[] not null default '{}',
  awarded_credits numeric(7,2),
  placement_effect jsonb,
  general_education_effect jsonb,
  major_prerequisite_effect jsonb,
  duplicate_credit_rule jsonb,
  program_exception jsonb,
  effective_from date,
  effective_to date,
  created_at timestamptz not null default now()
);

-- EQUIVALENCY ---------------------------------------------------------------

create table equivalency.course_equivalencies (
  id uuid primary key default gen_random_uuid(),
  source_institution_id uuid not null references catalog.institutions(id) on delete cascade,
  source_campus text,
  destination_institution_id uuid not null references catalog.institutions(id) on delete cascade,
  destination_campus text,
  mapping_type equivalency.mapping_type not null,
  credits_awarded numeric(7,2),
  minimum_grade text,
  conditions jsonb not null default '{}'::jsonb,
  effective_from date,
  effective_to date,
  confidence public.confidence_level not null,
  review_status source.review_status not null default 'pending',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  check (mapping_type <> 'not_found' or credits_awarded is null),
  check (mapping_type <> 'no_credit' or coalesce(credits_awarded, 0) = 0)
);

create table equivalency.equivalency_components (
  id uuid primary key default gen_random_uuid(),
  equivalency_id uuid not null references equivalency.course_equivalencies(id) on delete cascade,
  component_role text not null check (component_role in ('source', 'destination', 'category')),
  course_id uuid references catalog.courses(id) on delete cascade,
  category text,
  position integer not null default 0,
  required boolean not null default true,
  metadata jsonb not null default '{}'::jsonb,
  check ((component_role = 'category' and category is not null) or (component_role <> 'category' and course_id is not null)),
  unique (equivalency_id, component_role, position)
);

-- STUDENT -------------------------------------------------------------------

create table student.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  display_name text,
  current_institution_id uuid references catalog.institutions(id) on delete set null,
  current_institution_name text,
  institution_type text,
  residency_status text,
  citizenship_status text,
  home_state text,
  intended_term text,
  current_major text,
  onboarding_state jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create or replace function student.handle_new_user()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
begin
  insert into student.profiles (id, display_name)
  values (new.id, coalesce(new.raw_user_meta_data ->> 'name', new.email))
  on conflict (id) do nothing;
  return new;
end;
$$;

create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function student.handle_new_user();

create table student.uploaded_documents (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references student.profiles(id) on delete cascade,
  document_type text not null,
  original_filename text not null,
  storage_bucket text not null default 'transcript-uploads',
  storage_path text not null,
  mime_type text,
  size_bytes bigint,
  content_hash text,
  created_at timestamptz not null default now(),
  unique (user_id, storage_path)
);

create table student.transcripts (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references student.profiles(id) on delete cascade,
  client_id text,
  source_document_id uuid references student.uploaded_documents(id) on delete set null,
  original_filename text,
  extraction_status student.transcript_status not null default 'pending',
  verification_status student.verification_state not null default 'unreviewed',
  cumulative_gpa numeric(5,3),
  extraction_metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (user_id, client_id)
);

create table student.transcript_institutions (
  id uuid primary key default gen_random_uuid(),
  transcript_id uuid not null references student.transcripts(id) on delete cascade,
  institution_id uuid references catalog.institutions(id) on delete set null,
  institution_name text not null,
  attended_from date,
  attended_to date,
  is_primary boolean not null default false,
  created_at timestamptz not null default now(),
  unique (transcript_id, institution_name)
);

create table student.course_records (
  id uuid primary key default gen_random_uuid(),
  transcript_id uuid not null references student.transcripts(id) on delete cascade,
  transcript_institution_id uuid references student.transcript_institutions(id) on delete set null,
  institution_id uuid references catalog.institutions(id) on delete set null,
  client_id text,
  institution_name text not null,
  subject text,
  number text,
  course_code text not null,
  course_title text not null,
  term text not null,
  credits_attempted numeric(7,2) not null default 0,
  credits_earned numeric(7,2) not null default 0,
  grade text,
  course_status text not null,
  repeat_indicator boolean not null default false,
  transfer_indicator boolean not null default false,
  in_progress boolean not null default false,
  extraction_confidence public.confidence_level not null,
  user_verified boolean not null default false,
  extraction_evidence jsonb not null default '{}'::jsonb,
  notes text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (transcript_id, client_id)
);

create table student.exam_scores (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references student.profiles(id) on delete cascade,
  transcript_id uuid references student.transcripts(id) on delete cascade,
  client_id text,
  exam_type text not null,
  subject text not null,
  score text not null,
  exam_date date,
  reported_institution_id uuid references catalog.institutions(id) on delete set null,
  credits_awarded numeric(7,2),
  enabled boolean not null default true,
  user_verified boolean not null default false,
  created_at timestamptz not null default now(),
  unique (user_id, client_id)
);

create table student.academic_goals (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references student.profiles(id) on delete cascade,
  goal_type text not null,
  target_term text,
  target_program_id uuid references catalog.programs(id) on delete set null,
  priority integer not null default 0,
  details jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table student.constraints (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references student.profiles(id) on delete cascade,
  constraint_type text not null,
  value jsonb not null,
  active boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table student.verification_corrections (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references student.profiles(id) on delete cascade,
  transcript_id uuid not null references student.transcripts(id) on delete cascade,
  course_record_id uuid references student.course_records(id) on delete cascade,
  field_name text not null,
  extracted_value jsonb,
  corrected_value jsonb not null,
  reason text,
  created_at timestamptz not null default now()
);

-- PLANNING AND DERIVED RESULTS ----------------------------------------------

create table planning.scenarios (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references student.profiles(id) on delete cascade,
  client_id text not null,
  name text not null,
  planning_mode text not null,
  priority_institution_id uuid references catalog.institutions(id) on delete set null,
  transcript_id uuid references student.transcripts(id) on delete set null,
  profile_snapshot jsonb not null,
  settings jsonb not null,
  assumptions jsonb not null default '[]'::jsonb,
  is_archived boolean not null default false,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (user_id, client_id)
);

create table planning.scenario_targets (
  id uuid primary key default gen_random_uuid(),
  scenario_id uuid not null references planning.scenarios(id) on delete cascade,
  institution_id uuid references catalog.institutions(id) on delete set null,
  institution_key text not null,
  program_id uuid references catalog.programs(id) on delete set null,
  program_key text,
  is_priority boolean not null default false,
  created_at timestamptz not null default now(),
  unique (scenario_id, institution_key, program_key)
);

create table planning.planned_courses (
  id uuid primary key default gen_random_uuid(),
  scenario_id uuid not null references planning.scenarios(id) on delete cascade,
  client_id text not null,
  course_id uuid references catalog.courses(id) on delete set null,
  course_code text not null,
  title text not null,
  credits numeric(7,2) not null,
  term_id text not null,
  term_label text not null,
  satisfies text[] not null default '{}',
  source text not null,
  created_at timestamptz not null default now(),
  unique (scenario_id, client_id)
);

create table planning.scenario_results (
  id uuid primary key default gen_random_uuid(),
  scenario_id uuid not null references planning.scenarios(id) on delete cascade,
  analysis_version text not null,
  source_bundle_hash text,
  generated_at timestamptz not null,
  input_snapshot jsonb not null,
  eligibility jsonb not null default '{}'::jsonb,
  transferable_credits numeric(7,2),
  degree_applicable_credits numeric(7,2),
  estimated_remaining_credits numeric(7,2),
  estimated_graduation_term text,
  warnings jsonb not null default '[]'::jsonb,
  unresolved_assumptions jsonb not null default '[]'::jsonb,
  recommended_actions jsonb not null default '[]'::jsonb,
  full_result jsonb not null,
  created_at timestamptz not null default now()
);

create table planning.course_evaluations (
  id uuid primary key default gen_random_uuid(),
  scenario_result_id uuid not null references planning.scenario_results(id) on delete cascade,
  course_record_id uuid references student.course_records(id) on delete set null,
  destination_institution_id uuid references catalog.institutions(id) on delete cascade,
  transferable boolean,
  transferred_credits numeric(7,2),
  direct_equivalent_course_id uuid references catalog.courses(id) on delete set null,
  degree_applicable boolean,
  major_applicable boolean,
  general_education_categories text[] not null default '{}',
  admission_eligibility_effect jsonb,
  enrollment_prerequisite_effect jsonb,
  duplicate_credit_effect jsonb,
  verification_status planning.verification_status not null,
  confidence public.confidence_level not null,
  supporting_rule_ids uuid[] not null default '{}',
  evidence_ids uuid[] not null default '{}',
  explanation text,
  created_at timestamptz not null default now(),
  check (direct_equivalent_course_id is null or verification_status = 'confirmed')
);

create table planning.requirement_evaluations (
  id uuid primary key default gen_random_uuid(),
  scenario_result_id uuid not null references planning.scenario_results(id) on delete cascade,
  requirement_id uuid not null references policy.requirements(id) on delete cascade,
  status planning.requirement_evaluation_status not null,
  satisfied_by jsonb not null default '[]'::jsonb,
  missing_items jsonb not null default '[]'::jsonb,
  progress_credits numeric(7,2) not null default 0,
  required_credits numeric(7,2),
  blocking_conditions jsonb not null default '[]'::jsonb,
  assumptions jsonb not null default '[]'::jsonb,
  confidence public.confidence_level not null,
  explanation text,
  created_at timestamptz not null default now()
);

create table planning.program_readiness (
  id uuid primary key default gen_random_uuid(),
  scenario_result_id uuid not null references planning.scenario_results(id) on delete cascade,
  program_id uuid references catalog.programs(id) on delete cascade,
  program_key text not null,
  eligibility_status text not null,
  completed_requirements integer not null default 0,
  missing_requirements integer not null default 0,
  gpa_status jsonb not null default '{}'::jsonb,
  credit_status jsonb not null default '{}'::jsonb,
  earliest_application_term text,
  unresolved_question_ids uuid[] not null default '{}',
  readiness_label text not null,
  score numeric(5,2),
  created_at timestamptz not null default now(),
  unique (scenario_result_id, program_key)
);

create table planning.recommendations (
  id uuid primary key default gen_random_uuid(),
  scenario_result_id uuid not null references planning.scenario_results(id) on delete cascade,
  course_id uuid references catalog.courses(id) on delete set null,
  course_code text not null,
  title text not null,
  priority integer not null,
  option_count integer not null default 0,
  accepted_by text[] not null default '{}',
  supports_programs text[] not null default '{}',
  satisfies text[] not null default '{}',
  unlocks text[] not null default '{}',
  why_now text not null,
  impact_if_skipped text,
  confidence public.confidence_level not null,
  evidence_ids uuid[] not null default '{}',
  created_at timestamptz not null default now()
);

create table planning.unresolved_questions (
  id uuid primary key default gen_random_uuid(),
  scenario_result_id uuid not null references planning.scenario_results(id) on delete cascade,
  verification_status planning.verification_status not null,
  course_record_id uuid references student.course_records(id) on delete set null,
  institution_id uuid references catalog.institutions(id) on delete set null,
  exact_course text,
  exact_institution text,
  exact_term text,
  exact_question text not null,
  explanation text not null,
  office text not null,
  source_checks jsonb not null default '[]'::jsonb,
  draft_email jsonb,
  resolved_at timestamptz,
  resolution jsonb,
  created_at timestamptz not null default now()
);

create table planning.advisor_messages (
  id uuid primary key default gen_random_uuid(),
  scenario_id uuid not null references planning.scenarios(id) on delete cascade,
  user_id uuid not null references student.profiles(id) on delete cascade,
  role text not null check (role in ('user', 'assistant')),
  content text not null,
  confidence public.confidence_level,
  citation_ids uuid[] not null default '{}',
  assumptions jsonb not null default '[]'::jsonb,
  created_at timestamptz not null default now()
);

-- OPERATIONS ----------------------------------------------------------------

create table operations.conflicts (
  id uuid primary key default gen_random_uuid(),
  institution_id uuid references catalog.institutions(id) on delete cascade,
  entity_schema text not null,
  entity_table text not null,
  entity_id uuid,
  conflict_type text not null,
  left_evidence_id uuid references source.evidence_records(id) on delete set null,
  right_evidence_id uuid references source.evidence_records(id) on delete set null,
  description text not null,
  status source.review_status not null default 'needs_review',
  resolution jsonb,
  resolved_by uuid references auth.users(id) on delete set null,
  resolved_at timestamptz,
  created_at timestamptz not null default now()
);

create table operations.review_tasks (
  id uuid primary key default gen_random_uuid(),
  task_type text not null,
  entity_schema text not null,
  entity_table text not null,
  entity_id uuid not null,
  priority integer not null default 0,
  status source.review_status not null default 'pending',
  assigned_to uuid references auth.users(id) on delete set null,
  context jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table operations.change_events (
  id uuid primary key default gen_random_uuid(),
  entity_schema text not null,
  entity_table text not null,
  entity_id uuid not null,
  change_type text not null,
  previous_value jsonb,
  current_value jsonb,
  evidence_ids uuid[] not null default '{}',
  created_at timestamptz not null default now()
);

-- INDEXES -------------------------------------------------------------------

create index institutions_name_idx on catalog.institutions using gin (to_tsvector('simple', name));
create index courses_lookup_idx on catalog.courses (institution_id, subject, number);
create index programs_lookup_idx on catalog.programs (institution_id, campus, name);
create index source_pages_institution_idx on source.pages (institution_id, source_type, active);
create index source_snapshots_retrieved_idx on source.snapshots (page_id, retrieved_at desc);
create index source_evidence_claim_idx on source.evidence_records (claim_key, review_status);
create index source_evidence_value_idx on source.evidence_records using gin (normalized_value);
create index requirements_scope_idx on policy.requirements (institution_id, program_id, requirement_type, scope);
create index requirements_expression_idx on policy.requirements using gin (expression);
create index requirement_expression_tree_idx on policy.requirement_expressions (requirement_id, parent_id, position);
create index equivalencies_route_idx on equivalency.course_equivalencies (source_institution_id, destination_institution_id, effective_from, effective_to);
create index equivalency_components_course_idx on equivalency.equivalency_components (course_id, component_role);
create index transcripts_user_idx on student.transcripts (user_id, updated_at desc);
create index course_records_transcript_idx on student.course_records (transcript_id, term, course_code);
create index scenarios_user_idx on planning.scenarios (user_id, updated_at desc) where not is_archived;
create index scenario_results_latest_idx on planning.scenario_results (scenario_id, generated_at desc);
create index unresolved_questions_status_idx on planning.unresolved_questions (scenario_result_id, verification_status) where resolved_at is null;
create index crawl_jobs_status_idx on operations.crawl_jobs (status, created_at);
create index review_tasks_queue_idx on operations.review_tasks (status, priority desc, created_at);

-- UPDATED-AT TRIGGERS -------------------------------------------------------

create trigger institutions_set_updated_at before update on catalog.institutions for each row execute function public.set_updated_at();
create trigger courses_set_updated_at before update on catalog.courses for each row execute function public.set_updated_at();
create trigger programs_set_updated_at before update on catalog.programs for each row execute function public.set_updated_at();
create trigger requirements_set_updated_at before update on policy.requirements for each row execute function public.set_updated_at();
create trigger transfer_policies_set_updated_at before update on policy.transfer_policies for each row execute function public.set_updated_at();
create trigger equivalencies_set_updated_at before update on equivalency.course_equivalencies for each row execute function public.set_updated_at();
create trigger profiles_set_updated_at before update on student.profiles for each row execute function public.set_updated_at();
create trigger transcripts_set_updated_at before update on student.transcripts for each row execute function public.set_updated_at();
create trigger course_records_set_updated_at before update on student.course_records for each row execute function public.set_updated_at();
create trigger goals_set_updated_at before update on student.academic_goals for each row execute function public.set_updated_at();
create trigger constraints_set_updated_at before update on student.constraints for each row execute function public.set_updated_at();
create trigger scenarios_set_updated_at before update on planning.scenarios for each row execute function public.set_updated_at();
create trigger crawl_jobs_set_updated_at before update on operations.crawl_jobs for each row execute function public.set_updated_at();
create trigger review_tasks_set_updated_at before update on operations.review_tasks for each row execute function public.set_updated_at();

-- ROW LEVEL SECURITY --------------------------------------------------------

alter table catalog.institutions enable row level security;
alter table catalog.catalog_versions enable row level security;
alter table catalog.colleges enable row level security;
alter table catalog.departments enable row level security;
alter table catalog.courses enable row level security;
alter table catalog.course_versions enable row level security;
alter table catalog.course_offerings enable row level security;
alter table catalog.programs enable row level security;
alter table catalog.concentrations enable row level security;
alter table source.official_domains enable row level security;
alter table source.pages enable row level security;
alter table source.snapshots enable row level security;
alter table source.evidence_records enable row level security;
alter table source.evidence_links enable row level security;
alter table policy.requirements enable row level security;
alter table policy.requirement_expressions enable row level security;
alter table policy.requirement_courses enable row level security;
alter table policy.transfer_policies enable row level security;
alter table policy.exam_credit_rules enable row level security;
alter table equivalency.course_equivalencies enable row level security;
alter table equivalency.equivalency_components enable row level security;
alter table student.profiles enable row level security;
alter table student.uploaded_documents enable row level security;
alter table student.transcripts enable row level security;
alter table student.transcript_institutions enable row level security;
alter table student.course_records enable row level security;
alter table student.exam_scores enable row level security;
alter table student.academic_goals enable row level security;
alter table student.constraints enable row level security;
alter table student.verification_corrections enable row level security;
alter table planning.scenarios enable row level security;
alter table planning.scenario_targets enable row level security;
alter table planning.planned_courses enable row level security;
alter table planning.scenario_results enable row level security;
alter table planning.course_evaluations enable row level security;
alter table planning.requirement_evaluations enable row level security;
alter table planning.program_readiness enable row level security;
alter table planning.recommendations enable row level security;
alter table planning.unresolved_questions enable row level security;
alter table planning.advisor_messages enable row level security;
alter table operations.crawl_jobs enable row level security;
alter table operations.parser_runs enable row level security;
alter table operations.conflicts enable row level security;
alter table operations.review_tasks enable row level security;
alter table operations.change_events enable row level security;

-- Evidence and normalized public policy are readable; only service_role may write.
create policy "public reads institutions" on catalog.institutions for select to anon, authenticated using (true);
create policy "public reads catalog versions" on catalog.catalog_versions for select to anon, authenticated using (true);
create policy "public reads colleges" on catalog.colleges for select to anon, authenticated using (true);
create policy "public reads departments" on catalog.departments for select to anon, authenticated using (true);
create policy "public reads courses" on catalog.courses for select to anon, authenticated using (true);
create policy "public reads course versions" on catalog.course_versions for select to anon, authenticated using (true);
create policy "public reads course offerings" on catalog.course_offerings for select to anon, authenticated using (true);
create policy "public reads programs" on catalog.programs for select to anon, authenticated using (true);
create policy "public reads concentrations" on catalog.concentrations for select to anon, authenticated using (true);
create policy "public reads official domains" on source.official_domains for select to anon, authenticated using (true);
create policy "public reads source pages" on source.pages for select to anon, authenticated using (true);
-- Raw snapshots remain service-role-only; public clients receive reviewed evidence excerpts instead.
create policy "public reads approved evidence" on source.evidence_records for select to anon, authenticated using (review_status = 'approved');
create policy "public reads approved evidence links" on source.evidence_links for select to anon, authenticated using (
  exists (select 1 from source.evidence_records e where e.id = evidence_id and e.review_status = 'approved')
);
create policy "public reads requirements" on policy.requirements for select to anon, authenticated using (true);
create policy "public reads requirement expressions" on policy.requirement_expressions for select to anon, authenticated using (true);
create policy "public reads requirement courses" on policy.requirement_courses for select to anon, authenticated using (true);
create policy "public reads transfer policies" on policy.transfer_policies for select to anon, authenticated using (true);
create policy "public reads exam credit rules" on policy.exam_credit_rules for select to anon, authenticated using (true);
create policy "public reads approved equivalencies" on equivalency.course_equivalencies for select to anon, authenticated using (review_status = 'approved');
create policy "public reads approved equivalency components" on equivalency.equivalency_components for select to anon, authenticated using (
  exists (select 1 from equivalency.course_equivalencies e where e.id = equivalency_id and e.review_status = 'approved')
);

create or replace function student.owns_transcript(target_transcript_id uuid)
returns boolean
language sql
stable
security definer
set search_path = ''
as $$
  select exists (
    select 1 from student.transcripts t
    where t.id = target_transcript_id and t.user_id = auth.uid()
  );
$$;

create or replace function planning.owns_scenario(target_scenario_id uuid)
returns boolean
language sql
stable
security definer
set search_path = ''
as $$
  select exists (
    select 1 from planning.scenarios s
    where s.id = target_scenario_id and s.user_id = auth.uid()
  );
$$;

create or replace function planning.owns_result(target_result_id uuid)
returns boolean
language sql
stable
security definer
set search_path = ''
as $$
  select exists (
    select 1
    from planning.scenario_results r
    join planning.scenarios s on s.id = r.scenario_id
    where r.id = target_result_id and s.user_id = auth.uid()
  );
$$;

create policy "users manage own profile" on student.profiles for all to authenticated using ((select auth.uid()) = id) with check ((select auth.uid()) = id);
create policy "users manage own documents" on student.uploaded_documents for all to authenticated using ((select auth.uid()) = user_id) with check ((select auth.uid()) = user_id);
create policy "users manage own transcripts" on student.transcripts for all to authenticated using ((select auth.uid()) = user_id) with check ((select auth.uid()) = user_id);
create policy "users manage own transcript institutions" on student.transcript_institutions for all to authenticated using (student.owns_transcript(transcript_id)) with check (student.owns_transcript(transcript_id));
create policy "users manage own course records" on student.course_records for all to authenticated using (student.owns_transcript(transcript_id)) with check (student.owns_transcript(transcript_id));
create policy "users manage own exam scores" on student.exam_scores for all to authenticated using ((select auth.uid()) = user_id) with check ((select auth.uid()) = user_id);
create policy "users manage own goals" on student.academic_goals for all to authenticated using ((select auth.uid()) = user_id) with check ((select auth.uid()) = user_id);
create policy "users manage own constraints" on student.constraints for all to authenticated using ((select auth.uid()) = user_id) with check ((select auth.uid()) = user_id);
create policy "users manage own corrections" on student.verification_corrections for all to authenticated using ((select auth.uid()) = user_id) with check ((select auth.uid()) = user_id);

create policy "users manage own scenarios" on planning.scenarios for all to authenticated using ((select auth.uid()) = user_id) with check ((select auth.uid()) = user_id);
create policy "users manage own targets" on planning.scenario_targets for all to authenticated using (planning.owns_scenario(scenario_id)) with check (planning.owns_scenario(scenario_id));
create policy "users manage own planned courses" on planning.planned_courses for all to authenticated using (planning.owns_scenario(scenario_id)) with check (planning.owns_scenario(scenario_id));
create policy "users read own scenario results" on planning.scenario_results for select to authenticated using (planning.owns_scenario(scenario_id));
create policy "users read own course evaluations" on planning.course_evaluations for select to authenticated using (planning.owns_result(scenario_result_id));
create policy "users read own requirement evaluations" on planning.requirement_evaluations for select to authenticated using (planning.owns_result(scenario_result_id));
create policy "users read own readiness" on planning.program_readiness for select to authenticated using (planning.owns_result(scenario_result_id));
create policy "users read own recommendations" on planning.recommendations for select to authenticated using (planning.owns_result(scenario_result_id));
create policy "users read own unresolved questions" on planning.unresolved_questions for select to authenticated using (planning.owns_result(scenario_result_id));
create policy "users manage own advisor messages" on planning.advisor_messages for all to authenticated using ((select auth.uid()) = user_id and planning.owns_scenario(scenario_id)) with check ((select auth.uid()) = user_id and planning.owns_scenario(scenario_id));

-- SCHEMA AND TABLE GRANTS ---------------------------------------------------

grant usage on schema catalog, source, policy, equivalency to anon, authenticated;
grant usage on schema student, planning to authenticated;
grant usage on schema catalog, source, policy, equivalency, student, planning, operations to service_role;
grant select on all tables in schema catalog, source, policy, equivalency to anon, authenticated;
grant select, insert, update, delete on all tables in schema student to authenticated;
grant select, insert, update, delete on planning.scenarios, planning.scenario_targets, planning.planned_courses, planning.advisor_messages to authenticated;
grant select on planning.scenario_results, planning.course_evaluations, planning.requirement_evaluations, planning.program_readiness, planning.recommendations, planning.unresolved_questions to authenticated;
grant all on all tables in schema catalog, source, policy, equivalency, student, planning, operations to service_role;
grant execute on function student.owns_transcript(uuid), planning.owns_scenario(uuid), planning.owns_result(uuid) to authenticated;

alter default privileges in schema catalog grant select on tables to anon, authenticated;
alter default privileges in schema source grant select on tables to anon, authenticated;
alter default privileges in schema policy grant select on tables to anon, authenticated;
alter default privileges in schema equivalency grant select on tables to anon, authenticated;

-- PRIVATE TRANSCRIPT STORAGE ------------------------------------------------

insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values ('transcript-uploads', 'transcript-uploads', false, 15728640, array['application/pdf'])
on conflict (id) do update set
  public = excluded.public,
  file_size_limit = excluded.file_size_limit,
  allowed_mime_types = excluded.allowed_mime_types;

create policy "users upload transcript documents"
on storage.objects for insert to authenticated
with check (bucket_id = 'transcript-uploads' and (storage.foldername(name))[1] = auth.uid()::text);

create policy "users read transcript documents"
on storage.objects for select to authenticated
using (bucket_id = 'transcript-uploads' and (storage.foldername(name))[1] = auth.uid()::text);

create policy "users update transcript documents"
on storage.objects for update to authenticated
using (bucket_id = 'transcript-uploads' and (storage.foldername(name))[1] = auth.uid()::text)
with check (bucket_id = 'transcript-uploads' and (storage.foldername(name))[1] = auth.uid()::text);

create policy "users delete transcript documents"
on storage.objects for delete to authenticated
using (bucket_id = 'transcript-uploads' and (storage.foldername(name))[1] = auth.uid()::text);
