-- Deterministic prerequisite graph and course recommendation foundation.
-- This extends the normalized catalog/policy/planning model instead of creating
-- duplicate public tables. GPT is intentionally not involved in these records.

alter table catalog.courses
  add column active boolean not null default true,
  add column credit_system text,
  add column source_id uuid references source.evidence_records(id) on delete set null;

alter table catalog.course_versions
  add column source_id uuid references source.evidence_records(id) on delete set null;

alter table catalog.course_offerings
  add column academic_year integer,
  add column offering_status text not null default 'UNKNOWN'
    check (offering_status in ('CONFIRMED', 'TYPICALLY_OFFERED', 'NOT_OFFERED', 'UNKNOWN')),
  add column delivery_mode text,
  add column source_id uuid references source.evidence_records(id) on delete set null;

alter table catalog.programs
  add column catalog_year text,
  add column active boolean not null default true;

alter table policy.requirements
  add column parent_requirement_id uuid references policy.requirements(id) on delete cascade,
  add column source_id uuid references source.evidence_records(id) on delete set null;

alter table policy.requirement_courses
  add column option_group text,
  add column priority integer not null default 0,
  add column source_id uuid references source.evidence_records(id) on delete set null;

alter table equivalency.course_equivalencies
  add column source_id uuid references source.evidence_records(id) on delete set null;

alter table student.course_records
  add column course_id uuid references catalog.courses(id) on delete set null,
  add column grade_points numeric(4,2);

alter table planning.scenarios
  add column current_institution_id uuid references catalog.institutions(id) on delete set null,
  add column target_term text,
  add column max_credits numeric(7,2),
  add column residency_status text,
  add column institution_type text,
  add column graduation_target text;

alter table planning.scenario_targets
  add column priority integer not null default 1 check (priority > 0);

create table policy.course_prerequisite_groups (
  id uuid primary key default gen_random_uuid(),
  target_course_id uuid not null references catalog.courses(id) on delete cascade,
  group_type text not null check (group_type in ('ALL', 'ANY', 'MIN_COUNT')),
  group_order integer not null default 0,
  required boolean not null default true,
  description text,
  minimum_conditions integer,
  source_id uuid references source.evidence_records(id) on delete set null,
  created_at timestamptz not null default now(),
  check (
    (group_type = 'MIN_COUNT' and minimum_conditions is not null and minimum_conditions > 0)
    or (group_type <> 'MIN_COUNT' and minimum_conditions is null)
  )
);

create table policy.course_prerequisite_conditions (
  id uuid primary key default gen_random_uuid(),
  prerequisite_group_id uuid not null references policy.course_prerequisite_groups(id) on delete cascade,
  condition_type text not null check (condition_type in (
    'COURSE', 'PLACEMENT', 'CREDIT_COUNT', 'INSTRUCTOR_PERMISSION',
    'PROGRAM_ADMISSION', 'OTHER'
  )),
  prerequisite_course_id uuid references catalog.courses(id) on delete cascade,
  admitted_program_id uuid references catalog.programs(id) on delete cascade,
  minimum_grade text,
  minimum_grade_points numeric(4,2),
  may_be_concurrent boolean not null default false,
  placement_test_code text,
  minimum_placement_score numeric(8,2),
  minimum_credits numeric(7,2),
  permission_required boolean not null default false,
  raw_requirement_text text,
  confidence public.confidence_level not null default 'medium',
  source_id uuid references source.evidence_records(id) on delete set null,
  created_at timestamptz not null default now(),
  check (condition_type <> 'COURSE' or prerequisite_course_id is not null),
  check (condition_type <> 'PLACEMENT' or placement_test_code is not null),
  check (condition_type <> 'CREDIT_COUNT' or minimum_credits is not null),
  check (condition_type <> 'PROGRAM_ADMISSION' or admitted_program_id is not null)
);

create table policy.general_education_mappings (
  id uuid primary key default gen_random_uuid(),
  course_id uuid not null references catalog.courses(id) on delete cascade,
  institution_id uuid not null references catalog.institutions(id) on delete cascade,
  category_code text not null,
  category_name text,
  status text not null check (status in ('CONFIRMED', 'LIKELY', 'UNCLEAR', 'REQUIRES_REVIEW')),
  confidence public.confidence_level not null,
  source_id uuid references source.evidence_records(id) on delete set null,
  created_at timestamptz not null default now(),
  unique (course_id, institution_id, category_code)
);

create table planning.recommendation_weight_configs (
  id uuid primary key default gen_random_uuid(),
  config_name text not null unique,
  version integer not null default 1,
  major_coverage_weight numeric(8,3) not null,
  university_coverage_weight numeric(8,3) not null,
  unlock_weight numeric(8,3) not null,
  dual_requirement_weight numeric(8,3) not null,
  graduation_acceleration_weight numeric(8,3) not null,
  infrequent_offering_weight numeric(8,3) not null,
  uncertain_equivalency_penalty numeric(8,3) not null,
  dead_end_penalty numeric(8,3) not null,
  duplicate_credit_penalty numeric(8,3) not null,
  active boolean not null default false,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create unique index one_active_recommendation_weight_config_idx
  on planning.recommendation_weight_configs (active) where active;

insert into planning.recommendation_weight_configs (
  config_name, version, major_coverage_weight, university_coverage_weight,
  unlock_weight, dual_requirement_weight, graduation_acceleration_weight,
  infrequent_offering_weight, uncertain_equivalency_penalty,
  dead_end_penalty, duplicate_credit_penalty, active
) values ('default-v1', 1, 30, 20, 18, 12, 10, 8, 15, 8, 25, true);

create table planning.recommendation_cache (
  id uuid primary key default gen_random_uuid(),
  scenario_id uuid not null references planning.scenarios(id) on delete cascade,
  target_term text not null,
  fingerprint text not null,
  weight_config_version text not null,
  academic_data_version text not null,
  response jsonb not null,
  created_at timestamptz not null default now(),
  expires_at timestamptz,
  unique (scenario_id, target_term, fingerprint)
);

create index prerequisite_groups_target_idx
  on policy.course_prerequisite_groups (target_course_id, group_order);
create index prerequisite_conditions_course_idx
  on policy.course_prerequisite_conditions (prerequisite_course_id)
  where prerequisite_course_id is not null;
create index offerings_recommendation_idx
  on catalog.course_offerings (course_id, term, offering_status);
create index general_education_course_idx
  on policy.general_education_mappings (course_id, institution_id);
create index recommendation_cache_lookup_idx
  on planning.recommendation_cache (scenario_id, target_term, fingerprint);

create trigger recommendation_weights_set_updated_at
  before update on planning.recommendation_weight_configs
  for each row execute function public.set_updated_at();

create view catalog.recommendation_courses
with (security_invoker = true)
as
select distinct on (c.id)
  c.id,
  c.institution_id,
  c.canonical_code as course_code,
  c.subject as subject_code,
  c.number as course_number,
  cv.title,
  cv.description,
  cv.credits_min,
  cv.credits_max,
  c.credit_system,
  c.active,
  array_remove(array[c.source_id, cv.source_id], null) as source_ids
from catalog.courses c
join catalog.course_versions cv on cv.course_id = c.id
order by c.id, cv.effective_from desc nulls last, cv.created_at desc;

create view equivalency.recommendation_course_equivalencies
with (security_invoker = true)
as
select
  e.id,
  source_component.course_id as source_course_id,
  e.destination_institution_id as target_institution_id,
  target_component.course_id as target_course_id,
  case e.mapping_type
    when 'direct_equivalent' then 'DIRECT'
    when 'departmental_elective' then 'DEPARTMENTAL_ELECTIVE'
    when 'general_elective' then 'GENERAL_ELECTIVE'
    when 'no_credit' then 'NO_CREDIT'
    when 'manual_review' then 'REQUIRES_REVIEW'
    else 'UNKNOWN'
  end as equivalency_type,
  e.credits_awarded,
  e.confidence,
  e.effective_from as effective_start_date,
  e.effective_to as effective_end_date,
  array_remove(array[e.source_id], null) as source_ids
from equivalency.course_equivalencies e
join equivalency.equivalency_components source_component
  on source_component.equivalency_id = e.id and source_component.component_role = 'source'
left join equivalency.equivalency_components target_component
  on target_component.equivalency_id = e.id and target_component.component_role = 'destination'
where e.review_status = 'approved';

create view planning.scenario_programs
with (security_invoker = true)
as
select id, scenario_id as planning_scenario_id, program_id, priority
from planning.scenario_targets
where program_id is not null;

create view student.student_courses
with (security_invoker = true)
as
select
  cr.id,
  t.user_id,
  cr.course_id,
  cr.institution_id,
  cr.course_code as course_code_raw,
  cr.credits_earned,
  cr.grade,
  cr.grade_points,
  case when cr.in_progress then 'IN_PROGRESS' else upper(cr.course_status) end as status,
  cr.term as term_completed
from student.course_records cr
join student.transcripts t on t.id = cr.transcript_id;

alter table policy.course_prerequisite_groups enable row level security;
alter table policy.course_prerequisite_conditions enable row level security;
alter table policy.general_education_mappings enable row level security;
alter table planning.recommendation_weight_configs enable row level security;
alter table planning.recommendation_cache enable row level security;

create policy "public reads prerequisite groups"
  on policy.course_prerequisite_groups for select to anon, authenticated using (true);
create policy "public reads prerequisite conditions"
  on policy.course_prerequisite_conditions for select to anon, authenticated using (true);
create policy "public reads general education mappings"
  on policy.general_education_mappings for select to anon, authenticated using (true);
create policy "public reads recommendation weights"
  on planning.recommendation_weight_configs for select to anon, authenticated using (true);
create policy "users read own recommendation cache"
  on planning.recommendation_cache for select to authenticated
  using (planning.owns_scenario(scenario_id));

grant select on policy.course_prerequisite_groups,
  policy.course_prerequisite_conditions,
  policy.general_education_mappings to anon, authenticated;
grant select on planning.recommendation_weight_configs to anon, authenticated;
grant select on catalog.recommendation_courses,
  equivalency.recommendation_course_equivalencies to anon, authenticated;
grant select on planning.scenario_programs, student.student_courses to authenticated;
grant select on planning.recommendation_cache to authenticated;
grant all on policy.course_prerequisite_groups,
  policy.course_prerequisite_conditions,
  policy.general_education_mappings,
  planning.recommendation_weight_configs,
  planning.recommendation_cache to service_role;
grant select on catalog.recommendation_courses,
  equivalency.recommendation_course_equivalencies,
  planning.scenario_programs,
  student.student_courses to service_role;
