# Course recommendation and prerequisite graph service

This Python 3.12/FastAPI service produces deterministic course eligibility and ranked recommendations for a saved planning scenario. Supabase is the production source of truth; NetworkX is an in-memory traversal layer only. The service runs with conspicuously labeled fictional sample data when Supabase credentials are absent.

GPT does not calculate eligibility, requirement completion, graph reachability, risk, or scores. The API exposes a `RecommendationExplanationContext` so a language model can later explain already-calculated facts without changing them.

## Run locally

```powershell
cd services/course-recommendation
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install -e ".[test]"
.venv\Scripts\uvicorn.exe app.main:app --reload --port 8002
```

Without environment variables, use the fictional scenario ID `90000000-0000-0000-0000-000000000001`.

For Supabase-backed mode, set server-only values before starting the service:

```dotenv
SUPABASE_URL=http://127.0.0.1:54321
SUPABASE_SERVICE_ROLE_KEY=<service-role-key>
```

Never expose the service-role key to the browser. The repository reads the normalized `catalog`, `policy`, `equivalency`, `student`, and `planning` schemas created by the Supabase migrations.

## Endpoint

```http
POST /api/v1/scenarios/{scenario_id}/recommendations
Content-Type: application/json

{
  "target_term": "autumn-2026",
  "max_results": 10,
  "include_uncertain": true
}
```

See [examples/request.json](examples/request.json) and [examples/response.json](examples/response.json). The response contains eligible recommendations, excluded courses and reasons, full feature values, signed score components, source IDs, warnings, and a deterministic scenario fingerprint.

## Processing pipeline

1. `SupabaseRecommendationRepository` loads one scenario and its academic-data bundle.
2. `build_prerequisite_graph` creates a directed `prerequisite -> target` NetworkX graph and rejects cycles.
3. `PrerequisiteEligibilityEvaluator` evaluates relational ALL, ANY, and MIN_COUNT groups. The graph is never used as a substitute for group semantics.
4. Candidate generation filters completed, unavailable, duplicate-credit, ineligible, irrelevant, and insufficient-confidence options.
5. Feature calculation measures program/institution coverage, general-education overlap, direct and transitive unlock value, conservative delay avoidance, portability, and risk.
6. `WeightedRecommendationScorer` ranks candidates with the active database configuration and returns every component.
7. Reasons and warnings are rendered directly from feature values.
8. The complete response is cached by a SHA-256 fingerprint of scenario inputs, weight version, and academic-data version.

The repository, graph, evaluator, feature calculator, and scorer are isolated behind interfaces so an OR-Tools schedule optimizer can be added later without replacing the eligibility or evidence layers.

## Scoring model

Positive weights are major coverage 30, university coverage 20, unlock value 18, dual-requirement value 12, graduation acceleration 10, and infrequent offering 8. Penalties are uncertain equivalency 15, dead-end risk 8, and duplicate-credit risk 25.

Each feature is normalized to a 0–1 signal. Signed components are scaled against the positive capacity and the final score is clamped to 0–100. Program contribution uses `1 / priority`, so priority 1 contributes more than priority 3. Unlock value uses diminishing returns:

```text
direct unlocks * 3 + sqrt(required descendant count) * 5
```

Unknown equivalencies never count as accepted. Direct equivalency, general education, prerequisite applicability, departmental elective, and general elective outcomes remain separate in `university_coverage`.

## Data and safety boundaries

- Course equivalency is loaded from approved equivalency records; it is never inferred from similar names.
- General-education application and program requirement application are independent mappings.
- Prerequisite eligibility uses prerequisite-group records and student grades/statuses.
- Recommendation scoring consumes those facts but cannot change them.
- GPT may explain the result but cannot add sources, offerings, equivalencies, prerequisites, or score components.
- Missing, OTHER, permission, and unknown conditions are not treated as satisfied.
- Graduation acceleration is a conservative term-delay estimate, never an exact graduation promise.
- Sample course, offering, and equivalency records are fictional and not verified official information.

## Tests

```powershell
.venv\Scripts\python.exe -m pytest
```

The suite covers the linear and branching graphs, AND/OR/MIN_COUNT groups, grades, concurrency, placement, permissions, cycles, multi-program and multi-university coverage, dual requirements, infrequent offerings, unknown equivalencies, duplicate credit, portability, priorities, exclusions, deterministic scores, stable ordering, caching, and the FastAPI contract.
