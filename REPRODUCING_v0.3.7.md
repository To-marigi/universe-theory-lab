# Reproducing Final-Theory Bench v0.3.7

## Scope

The package verifies two finite, exact claims:

1. `LITERAL_Q1_Q4_COMMUTATIVITY_PROVED` for the frozen `n<=4`,
   strong-operator, `d=2` literal branch.
2. `LEMMA_GENERAL_SCALAR_CHAIN_FIBER_EXACT` on the recorded
   denominator-open scalar-chain locus.

Neither claim closes the unrestricted CPOBC theory. The expected global
verdict is `FINAL_THEORY_OPEN`.

## Prerequisites

- Python 3.12 and the locked project environment (`uv sync --dev`).
- Docker Desktop or another Docker Compose implementation.
- The repository's SageMath 10.9 service:

```powershell
.\scripts\sage.ps1 pull
.\scripts\sage.ps1 start
```

- A human-owned `config/v0.3.7_budget.json`. The checked-in file contains:

```json
{
  "timeout_seconds_per_chart": 3600,
  "total_wall_time_seconds": 43200,
  "memory_limit_gib": 8
}
```

The code accepts exactly those three positive keys. It has no runtime
defaults and will stop if the file is absent or malformed.

## Fast certificate verification

This checks the budget binding, frozen source hashes, all 63 Phase 1 backend
certificates, both Phase 2 exact certificates, compiler-provenance coverage,
and the scope addendum without rerunning Gröbner calculations:

```powershell
uv run python scripts/reproduce_v037.py --verify
```

Expected summary:

```text
LITERAL_Q1_Q4_COMMUTATIVITY_PROVED
LEMMA_GENERAL_SCALAR_CHAIN_FIBER_EXACT
V037_SCOPE_ADDENDUM_CERTIFIED
FINAL_THEORY_OPEN
```

## Exact reruns

Phase 1 runs 21 exact QQ charts and two 21-chart finite-field scout
campaigns. Phase 2 runs two exact QQ direct-relation evaluations.

```powershell
uv run python scripts/reproduce_v037.py --run-phase1
uv run python scripts/reproduce_v037.py --run-phase2
uv run python scripts/reproduce_v037.py --all
```

The supplied total wall-time authorisation is 12 hours, but actual runtime
depends on the host, Docker allocation, cache state, and Singular behaviour.
Same-budget terminal records are not retried automatically. A timeout,
backend failure, memory-gate failure, missing chart, or invalid binding
produces a partial/failing result; it is never rounded up to a theorem.

## Test suite

```powershell
uv run pytest tests/final_theory
uv run ruff check src/universe_lab/final_theory scripts/reproduce_v037.py
```

The final release inventory and SHA-256 hashes are in
`results/v0.3.7_release_manifest.json`.
