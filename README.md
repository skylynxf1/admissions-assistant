# GPT-5.6 Academic Planning OS

## Build Specification for OpenAI Build Week

## 1. Product Summary

**Working name:** AcademicOS, Pathway, DegreePilot, or TransferOS

**Core idea:**

A GPT-5.6-powered academic planning platform that helps students understand their current academic standing, evaluate future education paths, simulate different decisions, and build an optimized course plan across colleges, majors, transfer destinations, graduate programs, study-abroad programs, and professional degrees such as an MBA.

The platform is not just a chatbot and not just a degree audit. It combines:

- A personalized AI academic advisor
- A transcript understanding system
- A university and program policy research engine
- A multi-path academic simulator
- A prerequisite and course-planning engine
- A transfer-credit and equivalency analyzer
- A source-backed recommendation system

The central experience is:

> Upload your transcript, describe what you are considering, and simulate every realistic academic path before committing time or money.

GPT-5.6 is the core reasoning layer. It interprets transcripts, university policies, transfer-equivalency guides, degree requirements, prerequisite chains, AP and IB policies, residency rules, and student goals to produce an explainable academic plan.

---

# 2. The Problem

Academic planning is fragmented across:

- University degree-audit systems
- Transfer-equivalency databases
- University catalogs
- Major admission pages
- General-education requirement pages
- AP and IB credit charts
- Residency and tuition pages
- Community college articulation agreements
- Study-abroad course databases
- Graduate school prerequisite pages
- Advisor emails
- PDFs
- Reddit and student forums

Students often do not know:

- Which credits will transfer
- Which transferred credits count only as electives
- Which courses satisfy general education requirements
- Which courses satisfy major prerequisites
- Whether AP or IB credit counts toward a requirement
- Whether a course can satisfy more than one requirement
- Which prerequisite must be completed before another course can be taken
- Whether they have enough credits to apply as a transfer student
- Whether a university prefers a certain number of completed credits
- Whether transferring from a community college differs from transferring from a four-year university
- Whether in-state residency changes admission pathways or tuition
- Which courses preserve the greatest number of future major or university options
- How switching majors or schools changes time to graduation
- Whether a course taken abroad will count toward their degree
- Which undergraduate courses are needed for an MBA, graduate program, medical school, law school, or another professional path

A single mistake can delay an application, add an extra quarter or year, invalidate a prerequisite, or cost thousands of dollars.

---

# 3. Product Vision

The long-term product is an **AI operating system for education planning**.

It supports students across the full academic journey:

1. First-year college planning
2. Community college planning
3. Transfer planning
4. Internal major planning
5. Double-major and double-degree planning
6. Degree planning through graduation
7. Graduate school prerequisite planning
8. MBA preparation
9. Study-abroad planning
10. Professional-school planning
11. School-switching and re-enrollment planning
12. Multi-institution transcript consolidation

The user should be able to model a decision before making it.

Examples:

- “What should I take next quarter if I want to keep UW Informatics, UW Statistics, and Berkeley Data Science open?”
- “What changes if I transfer from a Washington community college instead of a four-year university?”
- “Does my AP Calculus score satisfy this prerequisite?”
- “If I switch from Biology to Computer Science, how much longer will graduation take?”
- “Which courses should I take now to prepare for an MBA later?”
- “Will this study-abroad course count toward my major?”
- “What happens if I become an in-state resident?”
- “Which of my courses transfer as direct equivalents, general education, or electives?”

---

# 4. Core Product Modes

During onboarding, the user selects one or more goals.

## 4.1 First-Year Planning

For students entering college or beginning their first year.

The platform helps them:

- Explore majors
- Understand general education requirements
- Build a first-year schedule
- Avoid unnecessary courses
- Complete prerequisite chains early
- Preserve multiple major options
- Evaluate AP, IB, dual-enrollment, and Running Start credit
- Estimate time to graduation

## 4.2 Transfer Planning

For students transferring from:

- Community college to a four-year university
- One four-year university to another
- Multiple previous institutions
- An out-of-state school to an in-state school
- An international institution to a U.S. institution

The platform evaluates:

- Minimum transfer-credit requirements
- Preferred transfer-credit ranges
- Maximum transferable credits
- Residency rules
- Community-college-specific pathways
- Direct transfer agreements
- Major admission prerequisites
- General education requirements
- Course equivalencies
- AP and IB treatment
- Competitiveness and readiness

## 4.3 Current-School Degree Planning

For students staying at their current institution.

The platform helps them:

- Choose a major
- Change majors
- Add a minor
- Add a second major
- Add a second degree
- Plan through graduation
- Understand course sequencing
- Identify bottleneck courses
- Find alternatives when a course is unavailable
- Estimate graduation date

## 4.4 Graduate School Prerequisite Planning

For students preparing for:

- Master’s programs
- PhD programs
- MBA programs
- Medical school
- Law school
- Other professional programs

The platform identifies:

- Required undergraduate coursework
- Recommended coursework
- GPA expectations
- Work-experience expectations
- Test requirements
- Missing prerequisites
- Suggested timeline
- Programs the user is currently eligible for

## 4.5 Study-Abroad Planning

The platform helps determine:

- Whether overseas courses transfer
- Whether they count toward the major
- Whether they count toward general education
- Whether they count only as electives
- Which courses require pre-approval
- Whether course descriptions or syllabi should be submitted
- How study abroad affects graduation timing

---

# 5. Primary User Flow

## Step 1: Account Creation

The user creates an account and optionally selects:

- Current institution
- Current location
- State of residence
- Citizenship or international-student status
- Intended enrollment term

## Step 2: Goal Selection

The user answers:

**What are you trying to do?**

Options:

- Plan my first year
- Transfer to another college
- Plan courses at my current college
- Choose or change my major
- Add a second major or degree
- Plan through graduation
- Prepare for graduate school
- Prepare for an MBA
- Plan study abroad
- Explore multiple options

The user may choose multiple goals.

## Step 3: Academic Background

The platform asks:

- What school do you currently attend?
- Is it a community college or four-year institution?
- Have you attended more than one college?
- Are you considered an in-state resident?
- Are you transferring from an in-state community college?
- Are you an international student?
- What term are you targeting?
- Are you currently enrolled?
- Do you have AP, IB, CLEP, dual-enrollment, or other exam credit?

## Step 4: Transcript Input

The platform asks the user to upload a **PDF transcript**.

Supported input methods:

1. Upload an unofficial or official transcript PDF
2. Upload multiple transcript PDFs from different colleges
3. Upload AP or IB score reports
4. Manually enter courses and grades
5. Manually edit or confirm transcript data after extraction

The UI should clearly say:

> Upload a PDF of your transcript, or enter your courses manually.

The system should support students who attended multiple colleges.

## Step 5: GPT-5.6 Transcript Parsing

GPT-5.6 extracts:

- Institution name
- Course code
- Course title
- Term
- Credits attempted
- Credits earned
- Grade
- GPA points
- Cumulative GPA
- Term GPA
- Transfer credits
- Withdrawals
- Repeated courses
- Pass/fail courses
- In-progress courses
- Planned courses
- Degree or credential earned
- AP, IB, CLEP, or dual-enrollment credits when present

The user reviews the extracted information and confirms or corrects it.

## Step 6: Credit Summary

The system displays:

- Total college credits attempted
- Total college credits earned
- Estimated transferable credits
- Credits from two-year institutions
- Credits from four-year institutions
- Credits from AP or IB
- Credits currently in progress
- Credits likely to count only as electives
- Duplicate or overlapping credits

The system must separate:

- Credits earned
- Credits transferable
- Credits applicable to a degree
- Credits applicable to a specific major

These values are not always the same.

## Step 7: Destination and Program Selection

The user selects one or more:

- Universities
- Campuses
- Colleges within a university
- Majors
- Alternate majors
- Minors
- Double majors
- Double degrees
- Graduate programs
- MBA programs
- Study-abroad programs

The user should be able to add several options at once.

Example:

- University of Washington — Informatics
- University of Washington — Computer Science
- University of Washington — Statistics
- UC Berkeley — Data Science
- UCLA — Cognitive Science

## Step 8: Policy and Equivalency Research

For every selected school and program, the system retrieves and evaluates:

- Minimum credits required to apply
- Preferred number of credits
- Maximum transferable credits
- Major prerequisites
- General admission prerequisites
- General education requirements
- Writing requirements
- Quantitative requirements
- Arts and humanities requirements
- Social science requirements
- Natural science requirements
- Diversity requirements
- Foreign language requirements
- Residency rules
- Community college transfer pathways
- Four-year transfer rules
- AP and IB credit policies
- Course equivalency guides
- Articulation agreements
- Department-specific transfer rules
- Application deadlines
- Enrollment prerequisites
- Graduation residency requirements

## Step 9: Personalized Analysis

The platform produces a school-by-school and major-by-major analysis.

For each option, it shows:

- Eligible to apply now
- Eligible after current term
- Not yet eligible
- Missing requirements
- Recommended but not required courses
- Number of credits completed
- Number of credits required
- Preferred credit range
- Major prerequisite completion
- General education completion
- Estimated transferable credits
- Estimated degree-applicable credits
- Estimated time to graduation
- AP or IB credits accepted
- AP or IB credits not accepted
- Questions requiring confirmation

## Step 10: Course Recommendations

GPT-5.6 suggests courses based on:

- Required prerequisites
- Prerequisite chains
- Courses that satisfy multiple requirements
- Courses that keep multiple majors open
- Courses accepted by the greatest number of target universities
- Courses that reduce time to graduation
- Courses that satisfy general education and major requirements simultaneously
- Courses required before high-demand upper-division courses
- Courses available at the user’s current school
- Credit-load constraints
- Work or family constraints
- Online, hybrid, or in-person preferences

## Step 11: Simulator

The user enters the simulator and tests different scenarios.

## Step 12: AI Advisor Chat

The user asks follow-up questions using their complete academic context.

## Step 13: Save, Export, or Share

The user can:

- Save a scenario
- Compare scenarios
- Export a plan
- Download a requirement checklist
- Create an advisor meeting summary
- Generate a draft email for admissions
- Share a plan with a parent, counselor, or advisor

---

# 6. Transcript and Credit Intelligence

## 6.1 PDF Transcript Upload

The primary upload format should be PDF.

The system should:

- Accept official and unofficial transcripts
- Accept image-based or digitally generated PDFs
- Support multiple institutions
- Detect pages belonging to different schools
- Extract structured course data
- Identify unreadable or uncertain values
- Ask the user to verify low-confidence results

## 6.2 Manual Course Entry

Students without a PDF can manually add:

- Institution
- Course code
- Course title
- Credits
- Grade
- Term
- Course description
- Syllabus link or PDF

## 6.3 Multiple Colleges

The system must support users who attended multiple colleges.

It should:

- Merge transcripts
- Detect duplicate courses
- Detect repeated courses
- Track which institution awarded each credit
- Apply each destination school’s maximum-credit rules
- Determine whether credits from one school were already transferred to another
- Avoid double-counting transferred credits

## 6.4 Credit Categories

Each course should be assigned one or more possible classifications:

- Direct course equivalent
- Major prerequisite
- Major elective
- General education
- Arts and humanities
- Social science
- Natural science
- Quantitative reasoning
- Writing or composition
- Diversity
- Foreign language
- Upper-division credit
- Lower-division credit
- Free elective
- Non-transferable
- Requires manual review

## 6.5 Confidence and Verification

Every credit determination should include:

- Result
- Confidence level
- Source
- Reasoning
- Last verified date
- Whether direct confirmation is recommended

Example:

> Bellevue College MATH& 151 appears equivalent to UW MATH 124 according to the published transfer guide. Confidence: High.

Example:

> This course may satisfy a social science requirement, but the university does not publish a direct equivalency. Confirm with admissions or the department before relying on it. Confidence: Medium.

---

# 7. AP, IB, CLEP, and Exam Credit

The product must explicitly check whether exam credit counts.

For each AP, IB, CLEP, or similar score, the platform should show:

- Whether the destination school accepts it
- Minimum score required
- Course equivalent awarded
- Number of credits awarded
- Whether it satisfies general education
- Whether it satisfies a major prerequisite
- Whether the department accepts it for major admission
- Whether it counts only as elective credit
- Whether the credit expires or is limited
- Whether duplicate credit rules apply

The system must not assume that exam credit accepted by one university is accepted by another.

It must also distinguish between:

- Credit awarded by the university
- Credit accepted for transfer admission
- Credit accepted toward graduation
- Credit accepted toward a specific major

The user should see a clear note such as:

> Your AP Calculus BC score gives general university credit at this school, but the Computer Science department does not allow it to replace the required calculus course for major admission.

If a policy is unclear, the system should say so and recommend confirmation.

---

# 8. University and Major Policy Engine

## 8.1 Sources to Check

The system should prioritize official sources:

1. University admissions pages
2. University registrar pages
3. Department and major pages
4. Official degree-audit requirements
5. Official course catalogs
6. Transfer-equivalency databases
7. State articulation databases
8. AP and IB credit charts
9. Residency and tuition pages
10. Published advising PDFs

Unofficial sources may be used only as supplementary context and must be labeled as unofficial.

## 8.2 Transfer Credit Requirements

For each university, the system should identify:

- Minimum number of college credits required to be considered a transfer applicant
- Preferred number of credits
- Maximum number of transferable credits
- Minimum GPA
- Recommended GPA
- Whether high school records are still required
- Whether SAT or ACT scores are required
- Whether the institution treats students differently based on credit count
- Whether the institution gives preference to community college applicants
- Whether in-state community college pathways exist

## 8.3 Community College Versus Four-Year Transfer

The simulator must allow the user to change the source institution type:

- In-state community college
- Out-of-state community college
- In-state four-year university
- Out-of-state four-year university
- International university

The system should identify whether this changes:

- Admission preference
- Articulation guarantees
- Transfer pathways
- Credit evaluation
- General education completion
- Tuition
- Residency
- Scholarship eligibility
- Application requirements

## 8.4 Major Admission Rules

The platform should track whether a major is:

- Open admission
- Capacity constrained
- Direct admission
- Competitive admission
- Separate application required
- Available only after enrollment
- Available to transfer students
- Unavailable to transfer students

It should identify:

- Required prerequisites
- Minimum prerequisite grades
- Required prerequisite GPA
- Application windows
- Essay requirements
- Portfolio requirements
- Interview requirements
- Credit minimums
- Courses that must be completed at the destination institution

---

# 9. Prerequisite Chain Engine

The platform should not only show missing major prerequisites. It must show the prerequisite chain required to reach them.

Example:

To take Data Structures, the student may first need:

1. Introductory Programming
2. Programming II
3. Discrete Mathematics
4. A minimum grade in each course

The system should display:

- Immediate prerequisite
- Prerequisite of the prerequisite
- Co-requisites
- Minimum grade requirements
- Placement requirements
- Whether AP credit can replace a prerequisite
- Whether transfer credit can replace a prerequisite
- Earliest term the target course can be taken
- Bottlenecks that may delay graduation

Example output:

> You still need CSE 143 for the major application. Before taking it, you must complete the equivalent of CSE 142. Because CSE 142 is offered this fall and CSE 143 is offered in winter, the earliest you could complete this sequence is Winter 2027.

---

# 10. Course Recommendation Engine

The recommendation engine should optimize for the student’s goals rather than simply filling requirements.

## 10.1 Recommendation Priorities

The engine should prioritize courses that:

- Are required for the greatest number of selected majors
- Transfer to the greatest number of selected universities
- Satisfy both general education and major requirements
- Unlock future prerequisite chains
- Are difficult to schedule later
- Are required before application deadlines
- Reduce time to graduation
- Improve academic preparation
- Support the student’s intended career or graduate program

## 10.2 Option-Preserving Courses

The system should identify courses that preserve the most options.

Example:

> Taking Calculus II next term keeps six of your seven selected programs open. Taking Business Statistics keeps only three open.

## 10.3 Course Recommendation Explanations

Every recommendation should explain:

- Why the course is recommended
- Which schools accept it
- Which majors require it
- Which requirements it satisfies
- Which future courses it unlocks
- What happens if the student does not take it now

## 10.4 Constraints

The user can set:

- Maximum credits per term
- Minimum credits per term
- Part-time or full-time status
- Work schedule
- Preferred class times
- Online-only preference
- No-Friday preference
- Summer availability
- Maximum number of difficult STEM courses
- Budget constraints
- Target graduation date

---

# 11. Multi-Path Academic Simulator

The simulator is one of the product’s central features.

## 11.1 Scenario Settings

The user can change:

- Current school
- Destination school
- Source institution type
- In-state or out-of-state residency
- Community college or four-year transfer status
- Intended major
- Alternate major
- Multiple majors
- Double major
- Double degree
- Minor
- Target transfer term
- Target graduation term
- Credit load per term
- AP or IB credit usage
- Whether to retake a course
- Whether to stay another quarter or year
- Whether to attend summer term
- Whether to study abroad
- Whether to pursue graduate school or an MBA

## 11.2 Multiple Major Comparison

The user should be able to add several majors and compare:

- Shared prerequisites
- Unique prerequisites
- Admission competitiveness
- Time to graduation
- Additional credits required
- Earliest application term
- Career alignment
- Courses that keep all options open

## 11.3 School Switching

The user can switch between destination schools and instantly see:

- Which credits transfer
- Which credits change category
- Which requirements become incomplete
- Which AP credits no longer count
- Which major prerequisites change
- How graduation timing changes
- How tuition and residency assumptions change

## 11.4 What-If Scenarios

Examples:

- What if I take 12 credits instead of 15?
- What if I fail or withdraw from this course?
- What if I retake Calculus?
- What if I stay at community college for one more quarter?
- What if I switch from Informatics to Computer Science?
- What if I add a Business major?
- What if I become an in-state resident?
- What if I transfer from a four-year school instead of a community college?
- What if I use AP credit?
- What if the department does not accept my AP credit?
- What if I study abroad for one term?

## 11.5 Scenario Comparison

The user can compare scenarios side by side.

Each scenario should show:

- Eligibility
- Missing requirements
- Transferable credits
- Degree-applicable credits
- Time to graduation
- Estimated remaining credits
- Estimated tuition range
- Risk level
- Unverified assumptions
- Recommended next actions

---

# 12. AI Advisor Chat

The AI chat should be grounded in:

- The user’s transcript
- Current and prior institutions
- AP and IB scores
- Selected schools
- Selected majors
- Saved scenarios
- University policies
- Course equivalency guides
- Degree requirements
- Student constraints

The user should not need to repeatedly explain their academic history.

## Example Questions

- Can I transfer next fall?
- Which of my courses count toward the major?
- Does AP Calculus count?
- What should I take next quarter?
- Which major gives me the fastest graduation path?
- Can I apply to both Informatics and Statistics?
- What changes if I transfer as an in-state community college student?
- Should I stay one more quarter before transferring?
- Which requirement is my biggest bottleneck?
- Can I study abroad without delaying graduation?
- What undergraduate courses should I take for an MBA?

## AI Response Requirements

Every answer should:

- Use the student’s actual academic context
- Distinguish facts from estimates
- Cite official sources
- Show uncertainty
- Explain the reasoning
- Identify assumptions
- Recommend confirmation when necessary
- Avoid presenting uncertain policy interpretations as guaranteed outcomes

---

# 13. Admissions and Advisor Confirmation Workflow

Some equivalencies and department policies will remain unclear.

When the system is unsure, it should not guess.

It should:

1. Clearly flag the uncertainty
2. Explain what information is missing
3. Identify the correct office to contact
4. Generate a draft email
5. Include the exact course and policy question
6. Allow the user to copy or send the message

Example:

> The university accepts this course as general transfer credit, but the department does not publish whether it satisfies the major prerequisite. Confirm with the Computer Science department before relying on it.

Generated email:

> Hello, I am planning to apply as a transfer student to the Computer Science major. I completed MATH& 146 at Bellevue College. Could you confirm whether this course satisfies the statistics prerequisite for admission to the major, or whether it transfers only as general elective credit?

The system should direct the user to:

- Admissions
- Transfer credit office
- Registrar
- Department advisor
- Residency office
- Study-abroad office

Depending on the question.

---

# 14. Dashboard

## 14.1 Student Overview

Display:

- Current institution
- Current GPA
- Credits earned
- Estimated transferable credits
- Degree-applicable credits
- Current major
- Target schools
- Target majors
- Target transfer term
- Target graduation term

## 14.2 Requirement Progress

Progress categories may include:

- Overall degree
- Major prerequisites
- Major requirements
- General education
- Writing
- Quantitative reasoning
- Arts and humanities
- Social science
- Natural science
- Diversity
- Foreign language
- Residency credits
- Upper-division credits

## 14.3 Alerts

Examples:

- Missing application prerequisite
- AP credit does not count for selected major
- Course will transfer only as an elective
- Credit maximum may be exceeded
- Required course has an unmet prerequisite
- Application deadline approaching
- Requirement information needs confirmation
- Planned schedule delays graduation

---

# 15. Program Readiness Score

Instead of presenting a fake acceptance probability, the product should initially use a transparent readiness model.

For each program, show:

- Eligibility status
- Required prerequisites completed
- Recommended prerequisites completed
- GPA relative to published minimum
- Credit requirement status
- Application requirement status
- Major-specific preparation
- Unresolved transfer-credit questions

Possible labels:

- Ready to apply
- Nearly ready
- Additional preparation recommended
- Not yet eligible
- Requires manual confirmation

A future version may include admissions-likelihood modeling, but it should avoid unsupported claims.

---

# 16. GPT-5.6 Responsibilities

GPT-5.6 is the central intelligence layer.

It should handle:

## 16.1 Transcript Understanding

- Parse inconsistent transcript formats
- Normalize course records
- Detect repeated or transferred courses
- Recognize exam credit
- Explain extraction uncertainty

## 16.2 Policy Interpretation

- Read university catalogs and transfer guides
- Compare policies across schools
- Extract structured requirements
- Interpret exceptions and footnotes
- Detect conflicting policy pages

## 16.3 Academic Reasoning

- Determine which credits apply where
- Build prerequisite chains
- Recommend option-preserving courses
- Compare majors and schools
- Simulate changes
- Generate personalized explanations

## 16.4 Natural-Language Advising

- Answer student questions
- Explain complex rules simply
- Ask targeted follow-up questions
- Draft admissions emails
- Summarize advisor meetings

## 16.5 Uncertainty Handling

- Identify unclear equivalencies
- Avoid hallucinating course mappings
- Clearly separate official information from inference
- Recommend direct confirmation when needed

---

# 17. Data Model

## User

- User ID
- Name
- Residency status
- Citizenship status
- State
- Academic goals
- Scheduling constraints

## Institution

- Institution ID
- Name
- Type
- State
- Country
- Accreditation

## Transcript

- Transcript ID
- Institution
- Upload file
- Extraction status
- Verification status

## Course Record

- Course code
- Course title
- Credits
- Grade
- Term
- Institution
- Status
- Repeat indicator
- Transfer indicator

## Exam Credit

- Exam type
- Subject
- Score
- Date
- Credits awarded

## University Policy

- School
- Program
- Policy type
- Requirement
- Source URL
- Effective term
- Last verified date

## Course Equivalency

- Source institution
- Source course
- Destination institution
- Destination course
- Credit amount
- Requirement category
- Confidence
- Source

## Scenario

- Selected schools
- Selected majors
- Residency setting
- Institution type
- Planned terms
- Planned courses
- Target dates
- Results

---

# 18. Suggested Technical Architecture

## Frontend

- Next.js
- React
- TypeScript
- Tailwind CSS
- Interactive dashboard
- Scenario comparison UI
- Transcript review UI

## Backend

- Python with FastAPI or TypeScript server routes
- PostgreSQL or Supabase
- Background document processing
- Structured course and policy database

## AI Layer

- GPT-5.6 for reasoning, extraction, policy interpretation, planning, and chat
- Structured outputs for transcript and requirement extraction
- Tool calling for university-policy retrieval
- Retrieval-augmented generation over official sources

## Document Processing

- PDF upload
- Native text extraction when possible
- OCR fallback for scanned transcripts
- Page-level confidence checks
- Human verification interface

## Search and Retrieval

- Official university site search
- University catalog ingestion
- Transfer guide ingestion
- Course-equivalency lookup
- Policy freshness tracking
- Source citation storage

## Planning Engine

Use a hybrid system:

- Deterministic rules for credit totals, prerequisite logic, and requirement completion
- GPT-5.6 for interpretation, ambiguous policy reasoning, recommendations, explanations, and natural-language interaction

The LLM should not be the sole source of truth for arithmetic or confirmed degree requirements.

---

# 19. MVP for Build Week

The full vision is large. The hackathon MVP should demonstrate the core magic clearly.

## MVP Scope

1. User selects “Transfer Planning” or “Degree Planning”
2. User uploads a transcript PDF or manually enters courses
3. GPT-5.6 extracts and structures the transcript
4. User selects two universities and up to three majors
5. System retrieves official transfer and major requirements
6. System maps completed courses to:
   - Direct equivalents
   - General education categories
   - Major prerequisites
   - Electives
   - Unclear or non-transferable credits
7. System checks AP credit
8. System shows missing requirements
9. System recommends the next three to five courses that preserve the most options
10. User changes a simulator setting such as:
   - Major
   - School
   - Residency
   - Community college versus four-year transfer
11. Results update
12. User asks GPT-5.6 a personalized question
13. System cites sources and flags uncertain items
14. System generates an admissions email for one uncertain equivalency

## Ideal Demo Story

A student uploads transcripts from two colleges and enters an AP Calculus score.

They are considering:

- UW Informatics
- UW Computer Science
- UC Berkeley Data Science

The system:

- Extracts all courses
- Calculates earned and estimated transferable credits
- Notes the transfer-credit requirements for each school
- Shows which courses satisfy arts and humanities, diversity, writing, and quantitative requirements
- Maps courses to major prerequisites
- Identifies that one AP score counts at one school but not toward the major at another
- Finds a missing prerequisite chain
- Recommends a course schedule that keeps all three programs open
- Lets the student switch from “four-year transfer” to “in-state community college transfer”
- Updates the pathway and admissions notes
- Flags one ambiguous course equivalency
- Drafts an email to admissions asking for confirmation

This demonstrates GPT-5.6 performing document understanding, multi-source reasoning, structured planning, simulation, and personalized conversation.

---

# 20. Post-Hackathon Expansion

## Phase 1

- Transfer planning
- Transcript parsing
- Course equivalency
- Major prerequisites
- AP and IB credit
- Multi-school simulator

## Phase 2

- First-year planning
- Full degree planning through graduation
- Double majors and double degrees
- Course availability integration
- Graduation timeline optimization

## Phase 3

- Graduate school planning
- MBA preparation
- Medical and law school prerequisites
- Study-abroad equivalency
- Scholarship and financial planning

## Phase 4

- Advisor collaboration
- University partnerships
- Student information system integrations
- Verified equivalency submissions
- Institutional analytics

---

# 21. Safety, Trust, and Accuracy Requirements

Because academic decisions can be costly, the platform must be transparent.

It should always:

- Cite official sources
- Display the effective policy term
- Show when information was last checked
- Separate confirmed equivalencies from predictions
- Show confidence levels
- Ask the student to verify extracted transcript data
- Warn users that final transfer decisions belong to the institution
- Recommend contacting admissions or a department when necessary
- Avoid guaranteeing admission
- Avoid guaranteeing that a course will transfer without official support

Recommended disclaimer:

> This plan is based on published university policies and the information you provided. Final admission, transfer-credit, residency, and degree decisions are made by the institution. Confirm any item marked uncertain before enrolling in or withdrawing from a course.

---

# 22. Product Differentiation

The product is not merely:

- A generic college chatbot
- A static degree audit
- A transfer-credit lookup page
- A course scheduler
- An admissions probability calculator

Its differentiation is the combination of:

- Transcript understanding
- Multi-institution policy reasoning
- Multi-major and multi-school simulation
- Prerequisite-chain planning
- AP and IB policy analysis
- Option-preserving course recommendations
- Personalized AI advising
- Explainable, source-backed decisions
- Direct escalation to admissions when uncertain

The strongest product promise is:

> See how every course, credit, major, school, and policy affects your future before you make the decision.

