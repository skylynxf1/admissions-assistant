# University of Washington Seattle Source Map

Inspected: 2026-07-16 UTC. This is a bounded source inspection, not a policy crawl. It records access and page-structure observations only; no policy claim is verified merely because its page was reachable.

## Access policy

| Host | Robots result | Sitemap result | Decision |
|---|---|---|---|
| `www.washington.edu` | `200`; disallows search-query and search paths, not the specified catalog or schedule paths | `/sitemap.xml` returned `404` | Configured seed and discovered catalog subject paths are allowed. Do not use site-search paths. |
| `admit.washington.edu` | `200`; disallows `/wp-admin/` and allows `admin-ajax.php` | `/sitemap.xml` is a current index for `sitemap-misc.xml` and `page-sitemap.xml` | Configured public pages are allowed. Never fetch WordPress administration paths. |

Both hosts served the requested pages over HTTPS without authentication. The framework still evaluates robots for every live job and treats a later denial or failed robots retrieval conservatively.

## Source inventory

| Source | Policy family | Authority | Campus | Structure and adapter | Effective-date signals | Limitations |
|---|---|---|---|---|---|---|
| [Seattle course index](https://www.washington.edu/students/crscat/) | Course | Official registrar catalog | Seattle | Static subject-link index; `uw.course_catalog_index` | Says descriptions update during the academic year | No canonical tag or explicit catalog year; announcements can change |
| [Course glossary](https://www.washington.edu/students/crscat/glossary.html) | Course terminology | Official registrar catalog | Seattle | Static prose sections; `uw.course_glossary` | No explicit version date | Must be snapshotted and versioned, not hard-coded as timeless |
| [CSE catalog](https://www.washington.edu/students/crscat/cse.html) | Course | Official registrar catalog | Seattle | Static course heading followed by description/evidence siblings; `uw.course_catalog` | Current page plus terms-offered abbreviations | No canonical tag or catalog year; NetID links are out of scope |
| [INFO catalog](https://www.washington.edu/students/crscat/info.html) | Course | Official registrar catalog | Seattle | Same subject-page pattern; `uw.course_catalog` | Same as CSE | Same limitations as CSE |
| [MATH catalog](https://www.washington.edu/students/crscat/math.html) | Course | Official registrar catalog | Seattle | Same subject-page pattern; selected-course filter | Same as CSE | Ingest only requested sample courses in fixture mode |
| [STAT catalog](https://www.washington.edu/students/crscat/stat.html) | Course | Official registrar catalog | Seattle | Same subject-page pattern; selected-course filter | Same as CSE | Ingest STAT 311 for the bounded sample |
| [ENGL catalog](https://www.washington.edu/students/crscat/engl.html) | Course | Official registrar catalog | Seattle | Same subject-page pattern; selected-course filter | Same as CSE | Ingest ENGL 131 for the bounded sample |
| [Time Schedule index](https://www.washington.edu/students/timeschd/) | Course offering | Official registrar schedule | Seattle | Static term index; conditional `uw.time_schedule` | Explicit quarter links | Public observations only; never follow NetID-only links or infer future offerings |
| [Transfer overview](https://admit.washington.edu/apply/transfer/) | Admissions | Official admissions | Seattle | Static prose plus two tables; `uw.transfer_admissions` | Application terms and date rows | Multiple scopes must become separate records |
| [Transfer application process](https://admit.washington.edu/apply/transfer/how-to-apply/) | Admissions | Official admissions | Seattle | Static sections; `uw.transfer_admissions` | Term-specific opening and deadline language | Page freshness is not an effective term by itself |
| [Transfer-credit policies](https://admit.washington.edu/apply/transfer/policies/) | Transfer policy | Official admissions | Seattle | Static sections plus one table; `uw.transfer_policies` | Some rules state ranges or historical conditions | Table headers, notes, and footnotes are mandatory evidence context |
| [Admission to majors](https://admit.washington.edu/apply/admission-to-majors/) | Major admission | Official admissions | Seattle | Static definitions; `uw.major_detail` | No explicit effective date observed | University definitions cannot be applied as program-specific rules without evidence |
| [Majors index](https://admit.washington.edu/academics/majors/) | Program | Official admissions | Seattle | Server-rendered major cards and detail links; `uw.majors_index` | No explicit effective date observed | Cards repeat type definitions; selected details must be compared to department/catalog sources |
| [Computer Science detail](https://admit.washington.edu/majors/computer-science/) | Program and major admission | Official admissions | Seattle | Static applicant-type, required-course, and outcome sections; `uw.major_detail` | Application-quarter prose | Outcome statistics stay separate from requirements |
| [Computer Engineering detail](https://admit.washington.edu/majors/computer-engineering/) | Program and major admission | Official admissions | Seattle | Same detail-page pattern; `uw.major_detail` | Application and prerequisite timing prose | Separate UW and department applications must remain distinct |
| [Informatics detail](https://admit.washington.edu/majors/informatics/) | Program and major admission | Official admissions | Seattle | Required-course lists plus numbered notes; `uw.major_detail` | No explicit catalog year observed | Footnote changes INFO 200 treatment and must travel with the requirement |
| [Statistics detail](https://admit.washington.edu/majors/statistics/) | Program and major admission | Official admissions | Seattle | Same detail-page pattern; `uw.major_detail` | Page-specific application language | Compare with department and catalog rather than blending disagreements |
| [Mathematics detail](https://admit.washington.edu/majors/mathematics/) | Program and major admission | Official admissions | Seattle | Same detail-page pattern; `uw.major_detail` | No explicit catalog year observed | Mathematics is listed as minimum requirements on the inspected index |
| [AP credit](https://admit.washington.edu/apply/transfer/exams-for-credit/ap/) | Exam credit | Official admissions | Seattle | 26 static tables with subject headings and nearby notes; `uw.ap_credit` | Current page, historical markers within rows when present | Preserve headers, rowspans, subject notes, score notes, and restrictions |
| [Exams-for-credit index](https://admit.washington.edu/apply/first-year/exams-for-credit/) | Exam credit | Official admissions | Seattle | Static link index; `generic_html` | No explicit effective date observed | Index is discovery evidence, not an exam award |
| [Application-type definitions](https://admit.washington.edu/apply/whats-my-application-type/) | Admissions | Official admissions | Seattle | Static conditional definitions; `uw.transfer_admissions` | Conditions depend on prior enrollment/credit | Do not collapse applicant categories |
| [WA CC Equivalency Guide](https://admit.washington.edu/apply/transfer/equivalency-guide/) | Transfer equivalency | Official admissions | Seattle receiving institution | Public institution index and very large static institution pages; `uw.equivalency_guide` | Row-level effective dates, including historical ranges | This iteration implements discovery and snapshots only; no broad equivalency parser |

## Structural findings

- The registrar catalog is directly parseable static HTML. Subject URLs are discoverable from the Seattle index; Bothell and Tacoma are separately linked and must be rejected for Seattle publication.
- Course descriptions have stable textual blocks containing heading, credits, designators, description, prerequisite/recommendation/restriction phrases, equivalence/overlap phrases, and offered-language. Catalog prose is not an actual term observation.
- Admissions uses self-referencing canonical tags and server-rendered HTML. No JSON-LD, CSV, public policy API, or embedded structured export was exposed on the inspected seeds.
- The majors index contains cards with official names, one of three type labels, summaries, and official detail links. Detail pages use predictable applicant-type, department-information, required-course, notes, and outcome-statistics sections.
- Transfer and AP pages contain semantic HTML tables. A table row without its heading, headers, nearby notes, and footnotes is insufficient evidence.
- The public Equivalency Guide redirects mixed-case institution paths to lowercase canonical paths. Its records include sending institution, source course, UW outcome, requirement designators, and effective ranges, but the pages are sufficiently large and historically complex that snapshot-only support is safer for this iteration.

## Discovered dependencies and exclusions

- Official department and catalog links from major pages are conflict-comparison inputs, not automatic replacements for Admissions claims.
- MyPlan, MyUW, and NetID-required Time Schedule links are excluded.
- `www.uwb.edu`, `tacoma.uw.edu`, Bothell course links, and Tacoma course links are outside Seattle publication scope.
- Live inspection uses a bounded identifiable user agent. Production crawling additionally requires the configured contact email and conservative per-host limits.
