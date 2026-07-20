# Andrew Branch Handoff

The active work is on `andrew`. `main` must remain unchanged.

Start here:

1. Read `docs/superpowers/specs/2026-07-18-bellevue-to-uw-transfer-backend-design.md`.
2. Follow `docs/superpowers/plans/2026-07-18-bellevue-to-uw-transfer-backend.md` task by task.
3. Re-run the baseline before editing.
4. Work test-first and review each vertical slice independently.

At this checkpoint, the approved design and implementation plan are present, but production implementation has not started. The last verified baseline was 122 passing Python tests and 4 passing frontend tests.

The chosen ownership boundary is intentional:

- Python/FastAPI/Alembic: public academic facts, evidence, equivalencies, evaluation, and planning.
- Supabase: authenticated private student documents and immutable confirmed transcript revisions.
- Next.js: typed UI/client; demo/sample results remain explicitly unverified.

Clone and continue:

```powershell
git clone https://github.com/skylynxf1/admissions-assistant.git
cd admissions-assistant
git fetch origin
git switch andrew
npm install
```

Use Python 3.12. On Windows with a OneDrive checkout, prefer a virtual environment outside the repository if `.venv` files are locked or unexpectedly hard-linked.

Before changing code:

```powershell
python -m pytest
npm test
git status --short --branch
```

The first safe implementation slice is publication integrity and append-only version selection. Do not begin multi-major analysis or planning until stable program/requirement identities, exact evidence relationships, equivalency mappings, and immutable confirmed transcript revisions exist.
