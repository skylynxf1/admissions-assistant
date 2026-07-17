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
