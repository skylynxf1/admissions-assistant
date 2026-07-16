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
2. Complete the short student profile.
3. Upload a PDF for sample extraction or choose manual entry, then review and edit every course field.
4. Search for destination schools, check multiple options, and choose one priority school.
5. Pick one or more priority-school majors and read the short requirement outline.
6. Open the planning playground and drag recommended courses into editable quarter templates.
7. Add more majors, adjust scenario settings, and show or hide movable workspace panels.
8. Review plain-language requirements, prerequisite chains, and sample source records.
9. Ask the grounded advisor a question or export the visible plan as a readable PDF.
