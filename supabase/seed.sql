-- SAMPLE DATA ONLY. These records support local development and are not verified policy facts.

insert into catalog.institutions (id, slug, name, short_name, institution_type, campus, city, state)
values
  ('10000000-0000-0000-0000-000000000001', 'uw-seattle', 'University of Washington', 'UW Seattle', 'public-four-year', 'Seattle', 'Seattle', 'WA'),
  ('10000000-0000-0000-0000-000000000002', 'uc-berkeley', 'University of California, Berkeley', 'UC Berkeley', 'public-four-year', 'Berkeley', 'Berkeley', 'CA'),
  ('10000000-0000-0000-0000-000000000003', 'ucla', 'University of California, Los Angeles', 'UCLA', 'public-four-year', 'Los Angeles', 'Los Angeles', 'CA'),
  ('10000000-0000-0000-0000-000000000004', 'bellevue-college', 'Bellevue College', 'Bellevue College', 'public-community-college', 'Main', 'Bellevue', 'WA'),
  ('10000000-0000-0000-0000-000000000005', 'seattle-university', 'Seattle University', 'Seattle University', 'private-four-year', 'Seattle', 'Seattle', 'WA')
on conflict (id) do update set name = excluded.name, short_name = excluded.short_name;

insert into source.official_domains (institution_id, domain, verified_at)
values
  ('10000000-0000-0000-0000-000000000001', 'washington.edu', now()),
  ('10000000-0000-0000-0000-000000000002', 'berkeley.edu', now()),
  ('10000000-0000-0000-0000-000000000003', 'ucla.edu', now()),
  ('10000000-0000-0000-0000-000000000004', 'bellevuecollege.edu', now()),
  ('10000000-0000-0000-0000-000000000005', 'seattleu.edu', now())
on conflict (institution_id, domain) do nothing;

insert into catalog.programs (id, institution_id, slug, name, degree_type, program_type, admission_type, capacity_status, application_required)
values
  ('20000000-0000-0000-0000-000000000001', '10000000-0000-0000-0000-000000000001', 'informatics', 'Informatics', 'BS', 'major', 'competitive', 'capacity-constrained', true),
  ('20000000-0000-0000-0000-000000000002', '10000000-0000-0000-0000-000000000001', 'computer-science', 'Computer Science', 'BS', 'major', 'competitive', 'capacity-constrained', true),
  ('20000000-0000-0000-0000-000000000003', '10000000-0000-0000-0000-000000000002', 'data-science', 'Data Science', 'BA', 'major', 'competitive', 'capacity-constrained', true)
on conflict (id) do update set name = excluded.name;

insert into policy.transfer_policies (
  id, institution_id, applicant_type, sending_institution_type,
  minimum_transfer_credits, preferred_credit_min, preferred_credit_max,
  maximum_transfer_credits, degree_applicability
)
values
  ('30000000-0000-0000-0000-000000000001', '10000000-0000-0000-0000-000000000001', 'transfer', 'community-college', 40, 60, 90, 90, '{"sample": true}'::jsonb),
  ('30000000-0000-0000-0000-000000000002', '10000000-0000-0000-0000-000000000002', 'transfer', 'community-college', 60, 60, 70, 70, '{"sample": true}'::jsonb),
  ('30000000-0000-0000-0000-000000000003', '10000000-0000-0000-0000-000000000003', 'transfer', 'community-college', 60, 60, 70, 70, '{"sample": true}'::jsonb)
on conflict (id) do nothing;

-- COURSE RECOMMENDATION SAMPLE DATA ONLY.
-- These fictional rows exercise graph/scoring code and are not verified official facts.

insert into catalog.courses (id, institution_id, campus, subject, number, credit_system, active)
values
  ('41000000-0000-0000-0000-000000000001', '10000000-0000-0000-0000-000000000004', 'Main', 'MATH&', '151', 'quarter', true),
  ('41000000-0000-0000-0000-000000000002', '10000000-0000-0000-0000-000000000004', 'Main', 'MATH&', '152', 'quarter', true),
  ('41000000-0000-0000-0000-000000000003', '10000000-0000-0000-0000-000000000004', 'Main', 'MATH', '208', 'quarter', true),
  ('41000000-0000-0000-0000-000000000004', '10000000-0000-0000-0000-000000000004', 'Main', 'PHYS&', '221', 'quarter', true),
  ('41000000-0000-0000-0000-000000000005', '10000000-0000-0000-0000-000000000004', 'Main', 'PHYS&', '222', 'quarter', true),
  ('41000000-0000-0000-0000-000000000006', '10000000-0000-0000-0000-000000000004', 'Main', 'CS', '141', 'quarter', true),
  ('41000000-0000-0000-0000-000000000007', '10000000-0000-0000-0000-000000000004', 'Main', 'CS', '210', 'quarter', true),
  ('41000000-0000-0000-0000-000000000008', '10000000-0000-0000-0000-000000000004', 'Main', 'ENGL&', '102', 'quarter', true),
  ('41000000-0000-0000-0000-000000000101', '10000000-0000-0000-0000-000000000001', 'Seattle', 'MATH', '125', 'quarter', true),
  ('41000000-0000-0000-0000-000000000102', '10000000-0000-0000-0000-000000000001', 'Seattle', 'MATH', '208', 'quarter', true),
  ('41000000-0000-0000-0000-000000000103', '10000000-0000-0000-0000-000000000001', 'Seattle', 'CSE', '143', 'quarter', true),
  ('41000000-0000-0000-0000-000000000201', '10000000-0000-0000-0000-000000000002', 'Berkeley', 'MATH', '1B', 'semester', true)
on conflict (id) do update set active = excluded.active, credit_system = excluded.credit_system;

insert into catalog.course_versions (id, course_id, title, credits_min, credits_max, description)
values
  ('42000000-0000-0000-0000-000000000001', '41000000-0000-0000-0000-000000000001', 'Calculus I', 5, 5, 'Fictional sample course.'),
  ('42000000-0000-0000-0000-000000000002', '41000000-0000-0000-0000-000000000002', 'Calculus II', 5, 5, 'Fictional sample course.'),
  ('42000000-0000-0000-0000-000000000003', '41000000-0000-0000-0000-000000000003', 'Linear Algebra', 5, 5, 'Fictional sample course.'),
  ('42000000-0000-0000-0000-000000000004', '41000000-0000-0000-0000-000000000004', 'Engineering Physics I', 5, 5, 'Fictional sample course.'),
  ('42000000-0000-0000-0000-000000000005', '41000000-0000-0000-0000-000000000005', 'Engineering Physics II', 5, 5, 'Fictional sample course.'),
  ('42000000-0000-0000-0000-000000000006', '41000000-0000-0000-0000-000000000006', 'Programming I', 5, 5, 'Fictional sample course.'),
  ('42000000-0000-0000-0000-000000000007', '41000000-0000-0000-0000-000000000007', 'Data Structures', 5, 5, 'Fictional sample course.'),
  ('42000000-0000-0000-0000-000000000008', '41000000-0000-0000-0000-000000000008', 'Composition II', 5, 5, 'Fictional sample course.'),
  ('42000000-0000-0000-0000-000000000101', '41000000-0000-0000-0000-000000000101', 'Calculus with Analytic Geometry II', 5, 5, 'Fictional sample target course.'),
  ('42000000-0000-0000-0000-000000000102', '41000000-0000-0000-0000-000000000102', 'Matrix Algebra', 3, 3, 'Fictional sample target course.'),
  ('42000000-0000-0000-0000-000000000103', '41000000-0000-0000-0000-000000000103', 'Computer Programming II', 5, 5, 'Fictional sample target course.'),
  ('42000000-0000-0000-0000-000000000201', '41000000-0000-0000-0000-000000000201', 'Calculus', 4, 4, 'Fictional sample target course.')
on conflict (id) do update set title = excluded.title;

insert into catalog.course_offerings (id, course_id, term, academic_year, offering_status, status)
values
  ('43000000-0000-0000-0000-000000000001', '41000000-0000-0000-0000-000000000002', 'autumn', 2026, 'TYPICALLY_OFFERED', 'sample'),
  ('43000000-0000-0000-0000-000000000002', '41000000-0000-0000-0000-000000000002', 'winter', 2026, 'TYPICALLY_OFFERED', 'sample'),
  ('43000000-0000-0000-0000-000000000003', '41000000-0000-0000-0000-000000000002', 'spring', 2026, 'TYPICALLY_OFFERED', 'sample'),
  ('43000000-0000-0000-0000-000000000004', '41000000-0000-0000-0000-000000000003', 'winter', 2026, 'TYPICALLY_OFFERED', 'sample'),
  ('43000000-0000-0000-0000-000000000005', '41000000-0000-0000-0000-000000000004', 'autumn', 2026, 'TYPICALLY_OFFERED', 'sample'),
  ('43000000-0000-0000-0000-000000000006', '41000000-0000-0000-0000-000000000005', 'winter', 2026, 'TYPICALLY_OFFERED', 'sample'),
  ('43000000-0000-0000-0000-000000000007', '41000000-0000-0000-0000-000000000007', 'autumn', 2026, 'TYPICALLY_OFFERED', 'sample'),
  ('43000000-0000-0000-0000-000000000008', '41000000-0000-0000-0000-000000000007', 'winter', 2026, 'TYPICALLY_OFFERED', 'sample'),
  ('43000000-0000-0000-0000-000000000009', '41000000-0000-0000-0000-000000000008', 'autumn', 2026, 'TYPICALLY_OFFERED', 'sample')
on conflict (id) do update set offering_status = excluded.offering_status;

insert into policy.course_prerequisite_groups (id, target_course_id, group_type, group_order, description)
values
  ('44000000-0000-0000-0000-000000000001', '41000000-0000-0000-0000-000000000002', 'ALL', 0, 'Complete Calculus I.'),
  ('44000000-0000-0000-0000-000000000002', '41000000-0000-0000-0000-000000000003', 'ALL', 0, 'Complete Calculus II.'),
  ('44000000-0000-0000-0000-000000000003', '41000000-0000-0000-0000-000000000004', 'ALL', 0, 'Complete Calculus I.'),
  ('44000000-0000-0000-0000-000000000004', '41000000-0000-0000-0000-000000000005', 'ALL', 0, 'Complete Physics I.'),
  ('44000000-0000-0000-0000-000000000005', '41000000-0000-0000-0000-000000000007', 'ANY', 0, 'Calculus I or approved placement.'),
  ('44000000-0000-0000-0000-000000000006', '41000000-0000-0000-0000-000000000007', 'ALL', 1, 'Programming I with a minimum 2.0 grade.')
on conflict (id) do update set description = excluded.description;

insert into policy.course_prerequisite_conditions (
  id, prerequisite_group_id, condition_type, prerequisite_course_id,
  minimum_grade_points, placement_test_code, minimum_placement_score,
  raw_requirement_text, confidence
)
values
  ('45000000-0000-0000-0000-000000000001', '44000000-0000-0000-0000-000000000001', 'COURSE', '41000000-0000-0000-0000-000000000001', null, null, null, 'Calculus I', 'high'),
  ('45000000-0000-0000-0000-000000000002', '44000000-0000-0000-0000-000000000002', 'COURSE', '41000000-0000-0000-0000-000000000002', null, null, null, 'Calculus II', 'high'),
  ('45000000-0000-0000-0000-000000000003', '44000000-0000-0000-0000-000000000003', 'COURSE', '41000000-0000-0000-0000-000000000001', null, null, null, 'Calculus I', 'high'),
  ('45000000-0000-0000-0000-000000000004', '44000000-0000-0000-0000-000000000004', 'COURSE', '41000000-0000-0000-0000-000000000004', null, null, null, 'Physics I', 'high'),
  ('45000000-0000-0000-0000-000000000005', '44000000-0000-0000-0000-000000000005', 'COURSE', '41000000-0000-0000-0000-000000000001', null, null, null, 'Calculus I', 'high'),
  ('45000000-0000-0000-0000-000000000006', '44000000-0000-0000-0000-000000000005', 'PLACEMENT', null, null, 'ALEKS', 75, 'ALEKS 75 or higher', 'high'),
  ('45000000-0000-0000-0000-000000000007', '44000000-0000-0000-0000-000000000006', 'COURSE', '41000000-0000-0000-0000-000000000006', 2.0, null, null, 'Programming I with 2.0 or higher', 'high')
on conflict (id) do update set raw_requirement_text = excluded.raw_requirement_text;

insert into policy.requirements (
  id, institution_id, program_id, requirement_type, scope, name,
  description, expression, mandatory
)
values
  ('46000000-0000-0000-0000-000000000001', '10000000-0000-0000-0000-000000000001', '20000000-0000-0000-0000-000000000002', 'major', 'program', 'Calculus II', 'Fictional recommendation seed requirement.', '{"sample":true}', true),
  ('46000000-0000-0000-0000-000000000002', '10000000-0000-0000-0000-000000000001', '20000000-0000-0000-0000-000000000002', 'major', 'program', 'Programming sequence', 'Fictional recommendation seed requirement.', '{"sample":true}', true),
  ('46000000-0000-0000-0000-000000000003', '10000000-0000-0000-0000-000000000001', '20000000-0000-0000-0000-000000000001', 'major', 'program', 'Quantitative preparation', 'Fictional recommendation seed requirement.', '{"sample":true}', true),
  ('46000000-0000-0000-0000-000000000004', '10000000-0000-0000-0000-000000000002', '20000000-0000-0000-0000-000000000003', 'major', 'program', 'Calculus II', 'Fictional recommendation seed requirement.', '{"sample":true}', true),
  ('46000000-0000-0000-0000-000000000005', '10000000-0000-0000-0000-000000000002', '20000000-0000-0000-0000-000000000003', 'major', 'program', 'Linear algebra', 'Fictional recommendation seed requirement.', '{"sample":true}', true)
on conflict (id) do update set name = excluded.name;

insert into policy.requirement_courses (requirement_id, course_id, role, priority)
values
  ('46000000-0000-0000-0000-000000000001', '41000000-0000-0000-0000-000000000101', 'required', 0),
  ('46000000-0000-0000-0000-000000000002', '41000000-0000-0000-0000-000000000103', 'required', 0),
  ('46000000-0000-0000-0000-000000000003', '41000000-0000-0000-0000-000000000101', 'required', 0),
  ('46000000-0000-0000-0000-000000000004', '41000000-0000-0000-0000-000000000201', 'required', 0),
  ('46000000-0000-0000-0000-000000000005', '41000000-0000-0000-0000-000000000102', 'required', 0)
on conflict (requirement_id, course_id, role) do update set priority = excluded.priority;

insert into policy.general_education_mappings (
  id, course_id, institution_id, category_code, category_name, status, confidence
)
values
  ('47000000-0000-0000-0000-000000000001', '41000000-0000-0000-0000-000000000002', '10000000-0000-0000-0000-000000000001', 'NSc', 'Natural Sciences', 'CONFIRMED', 'high'),
  ('47000000-0000-0000-0000-000000000002', '41000000-0000-0000-0000-000000000002', '10000000-0000-0000-0000-000000000002', 'QR', 'Quantitative Reasoning', 'CONFIRMED', 'high'),
  ('47000000-0000-0000-0000-000000000003', '41000000-0000-0000-0000-000000000008', '10000000-0000-0000-0000-000000000001', 'C', 'Composition', 'CONFIRMED', 'high'),
  ('47000000-0000-0000-0000-000000000004', '41000000-0000-0000-0000-000000000008', '10000000-0000-0000-0000-000000000002', 'R1B', 'Reading and Composition', 'CONFIRMED', 'high')
on conflict (id) do update set status = excluded.status;

insert into equivalency.course_equivalencies (
  id, source_institution_id, destination_institution_id, mapping_type,
  confidence, review_status, conditions
)
values
  ('48000000-0000-0000-0000-000000000001', '10000000-0000-0000-0000-000000000004', '10000000-0000-0000-0000-000000000001', 'direct_equivalent', 'high', 'approved', '{"sample":true}'),
  ('48000000-0000-0000-0000-000000000002', '10000000-0000-0000-0000-000000000004', '10000000-0000-0000-0000-000000000002', 'direct_equivalent', 'medium', 'approved', '{"sample":true}'),
  ('48000000-0000-0000-0000-000000000003', '10000000-0000-0000-0000-000000000004', '10000000-0000-0000-0000-000000000001', 'direct_equivalent', 'high', 'approved', '{"sample":true}'),
  ('48000000-0000-0000-0000-000000000004', '10000000-0000-0000-0000-000000000004', '10000000-0000-0000-0000-000000000001', 'direct_equivalent', 'high', 'approved', '{"sample":true}')
on conflict (id) do update set confidence = excluded.confidence;

insert into equivalency.equivalency_components (
  id, equivalency_id, component_role, course_id, position
)
values
  ('49000000-0000-0000-0000-000000000001', '48000000-0000-0000-0000-000000000001', 'source', '41000000-0000-0000-0000-000000000002', 0),
  ('49000000-0000-0000-0000-000000000002', '48000000-0000-0000-0000-000000000001', 'destination', '41000000-0000-0000-0000-000000000101', 0),
  ('49000000-0000-0000-0000-000000000003', '48000000-0000-0000-0000-000000000002', 'source', '41000000-0000-0000-0000-000000000002', 0),
  ('49000000-0000-0000-0000-000000000004', '48000000-0000-0000-0000-000000000002', 'destination', '41000000-0000-0000-0000-000000000201', 0),
  ('49000000-0000-0000-0000-000000000005', '48000000-0000-0000-0000-000000000003', 'source', '41000000-0000-0000-0000-000000000003', 0),
  ('49000000-0000-0000-0000-000000000006', '48000000-0000-0000-0000-000000000003', 'destination', '41000000-0000-0000-0000-000000000102', 0),
  ('49000000-0000-0000-0000-000000000007', '48000000-0000-0000-0000-000000000004', 'source', '41000000-0000-0000-0000-000000000007', 0),
  ('49000000-0000-0000-0000-000000000008', '48000000-0000-0000-0000-000000000004', 'destination', '41000000-0000-0000-0000-000000000103', 0)
on conflict (id) do nothing;
