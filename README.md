# Pathwise — Academic Planning OS prototype

Pathwise is a demo-ready academic transfer planning and simulation experience built from the original [GPT-5.6 Academic Planning OS specification](docs/product-spec.md). The prototype covers the full Transfer Planning journey with editable transcript extraction, multi-school and multi-major planning, reactive scenario simulation, requirement analysis, uncertainty escalation, and a context-aware advisor chat.

> **Demo data only:** analysis, policy summaries, equivalencies, citations, and advisor answers in this prototype are realistic sample data. They are not verified official academic guidance. Final decisions belong to the institution.

## Quick start

Requirements: Node.js 20+ and pnpm 9+ (npm also works).

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
- `supabase/schema.sql` — suggested persistence schema with row-level security notes
- `docs/product-spec.md` — original product specification
- `docs/GPT56_TODO.md` — concise production integration plan

The frontend calls the same strict TypeScript models used by the mock service layer. Server route placeholders expose transcript extraction, academic analysis, scenario simulation, and advisor chat boundaries that can be replaced with structured GPT-5.6 responses later.

## Optional environment setup

Copy `.env.example` to `.env.local` and add OpenAI/Supabase credentials when connecting production services. The current route implementations intentionally continue using sample services even when keys are present, so a key cannot accidentally make the demo claim unverified policy results.

## Primary demo path

1. Select Transfer Planning.
2. Complete the student profile and scenario settings.
3. Upload a PDF for sample extraction or enter courses manually.
4. Review and edit every extracted course field.
5. Select multiple schools and majors.
6. Review credits, equivalencies, requirements, prerequisite chains, and recommended courses.
7. Change residency, source-school type, transfer term, credit load, or AP credit and see the plan update.
8. Ask the advisor a question and draft an email for an uncertain equivalency.
