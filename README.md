# Pathwise — Academic Planning OS prototype

Pathwise is a demo-ready academic transfer planning and simulation experience built from the original [GPT-5.6 Academic Planning OS specification](docs/product-spec.md). The prototype covers the full Transfer Planning journey with editable transcript extraction, multi-school and multi-major planning, reactive scenario simulation, requirement analysis, uncertainty escalation, and a context-aware advisor chat.

> **Demo data only:** analysis, policy summaries, equivalencies, citations, and advisor answers in this prototype are realistic sample data. They are not verified official academic guidance. Final decisions belong to the institution.

## Quick start

Requirements: Node.js 22+ and pnpm 9+ (npm also works).

```bash
pnpm install
pnpm dev
```

Open [http://localhost:3000](http://localhost:3000) and choose **Transfer planning**. No API key or Supabase project is required for the complete demo flow.

## Quality checks

```bash
pnpm typecheck
pnpm lint
pnpm build
```

## Architecture

- `app/` — Next.js App Router pages and API route placeholders
- `components/` — reusable flow, dashboard, and UI components
- `lib/services/` — typed academic-planning service contracts and isolated mock implementations
- `data/` — sample transcript and university/major policies
- `supabase/migrations/` — executable domain-separated Supabase schema, indexes, storage, and RLS
- `supabase/seed.sql` — labeled local sample catalog data
- `docs/BACKEND.md` — Supabase setup, security model, routes, and ingestion contract
- `docs/product-spec.md` — original product specification
- `docs/GPT56_TODO.md` — concise production integration plan

The frontend calls the same strict TypeScript models used by the mock service layer. Server route placeholders expose transcript extraction, academic analysis, scenario simulation, and advisor chat boundaries that can be replaced with structured GPT-5.6 responses later.

The private transcript ingestion architecture—including Docling worker setup, strict extraction, validation, review APIs, and Supabase tables—is documented in [docs/TRANSCRIPT_PIPELINE.md](docs/TRANSCRIPT_PIPELINE.md).

## Optional environment setup

Copy `.env.example` to `.env.local` and add OpenAI/Supabase credentials when connecting production services. Live transcript extraction additionally needs the private Docling worker. Academic-policy analysis remains sample-only and never claims its results are official.

For the database, run the checked-in Supabase migrations and follow [docs/BACKEND.md](docs/BACKEND.md). With a signed-in Supabase session, **Save draft** persists the transcript and scenario; without Supabase or authentication it safely remains a local-browser save.

## Primary demo path

1. Select Transfer Planning.
2. Complete the short student profile.
3. Upload a PDF for sample extraction or choose manual entry, then review and edit every course field.
4. Search for destination schools, check multiple options, and choose one priority school.
5. Pick one or more priority-school majors and read the short requirement outline.
6. Open the planning playground and drag recommended courses into editable quarter templates.
7. Use the simulator to add or remove schools, majors, transcript courses, grades, AP/IB credit, and planned courses.
8. Change current school/type, residency, enrollment term, maximum quarterly load, summer attendance, and graduation target.
9. Watch transfer and major eligibility, missing prerequisites, general education, credits, timeline, and open options recalculate.
10. Save multiple scenarios in the Compare tab, restore any version, or export the visible plan as a readable PDF.
11. Open Verification to distinguish confirmed, likely, unclear, manual-evaluation, and conflicting results; inspect every checked source and draft an exact-context email for unresolved items.
12. Ask the grounded advisor a question or review the sample source records behind the plan.

## Verification safeguards

The typed verification layer stores the status, source course, institution, term, destination school, exact question, responsible office, and the outcome of each checked source. A destination course is only displayed when a saved source explicitly contains that mapping. Unresolved results never infer an equivalency; they explain the gap and can generate a reviewable email draft without sending it.

## Simulator coverage

The playground keeps all editable inputs in the typed scenario, transcript, and target-school models. The mock simulation service—not the UI—calculates transfer eligibility, major readiness, prerequisite gaps, general-education progress, projected transferable credit, estimated remaining credit, graduation timing, term overloads, GPA, and the academic options that remain open. Saved comparison plans capture the complete scenario and can be restored during the session.
