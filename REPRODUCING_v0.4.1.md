# Reproducing the v0.4.1 ON restricted-locus computation

Scope correction: the commands reproduce the stored arithmetic, but the
campaign does not prove either intended one-sided source profile. The frozen
Q/direct coordinates were compiled under `PAPER_STRONG_OPERATOR_PROFILE` and
retain Eq. (108)/strong-MSR and Eq. (112)/strong-GC dependencies before
relation-family filtering. See
`reports/v0.4.1_scope_break_decision_packet.md`.

The first command below reproduces only the static inventory. Later sections
reproduce the bounded scout, exact Sage/Singular campaign, and independent
certificate oracle. No finite-field run is used anywhere in v0.4.1.

## Regenerate without writing

From the repository root:

```powershell
uv run python scripts/reproduce_v041_inventory.py
```

Expected status:

```text
verdict                  V041_INVENTORY_READY_ELIMINATION_NOT_RUN
budget_status            HUMAN_BUDGET_PRESENT_ELIMINATION_NOT_RUN
Q5-free relation count   976
fixed-GC/strong-MSR core 721
strong-GC/reachable core 955
semantic digest          5b09ebcb7be60fecc027e93e4277007c94d98573937038cd03a3a399a46af3c6
```

## Rewrite the machine-readable artifact

```powershell
uv run python scripts/reproduce_v041_inventory.py --write
```

This writes `results/v0.4.1_one_sided_inventory.json` with LF line endings.
The compiler rejects any change to its ten pinned source artifacts.

## Verification

```powershell
uv run pytest -q tests/final_theory/test_one_sided_d2_v041.py
uv run ruff check src/universe_lab/final_theory/one_sided_d2_v041.py `
  scripts/reproduce_v041_inventory.py `
  tests/final_theory/test_one_sided_d2_v041.py
uv run mypy src/universe_lab/final_theory/one_sided_d2_v041.py `
  scripts/reproduce_v041_inventory.py
```

The inventory-only expected result is `5 passed`.

## Exact bounded counterexample scout

```powershell
uv run python scripts/reproduce_v041_scout.py
uv run pytest -q tests/final_theory/test_one_sided_d2_v041_scout.py
```

Expected scout verdict:

```text
ONE_SIDED_TRIANGULAR_SCOUT_NO_NONCOMMUTATIVE_SURVIVOR
semantic digest b3981798a5a2c06b9a7f79329b50fefa88d53b533715bc6bcb3cc2ba9f28420a
```

This is exact `QQ` linear algebra inside the declared triangular
two-character ansatz. It is not the arbitrary-`GL_2` proof.

## Exact QQ chart campaign

Compile the solver-free 42-request manifest:

```powershell
uv run python scripts/reproduce_v041_one_sided_elimination.py --write-manifest
```

Expected current scope-corrected manifest output:

```text
path     results/v0.4.1_one_sided_restricted_locus_manifest.json
verdict  V041_RESTRICTED_LOCUS_QQ_MANIFEST_READY_SOLVER_NOT_RUN
digest   56515b2c8076a164640f9d56a47d194b18566fb23e92310c4f4fd4d2bc68deb6
```

With the repository Sage 10.9 container running, explicitly execute or resume
the budget-bound campaign:

```powershell
uv run python scripts/reproduce_v041_one_sided_elimination.py --run-qq
```

Existing historical certificates with the same budget and request digests are
verified and reused read-only rather than silently retried. Any future
certificate write goes to the separate
`certificates/d2_saturation/one_sided_v041_restricted_locus` root. The
historical run completed all 42 requests with:

```text
WEAK_D2_ON_ONE_SIDED_COMMUTATIVITY_PROVED
24 EXACT_EMPTY_CHART
18 EXACT_NO_NONCOMMUTATIVE_SOLUTION_IN_CHART
0 unresolved
campaign semantic digest 6b4300485c23c485177584d8dd9afd8c77463e64ca55cf812eae9898b430382c
```

## Independent oracle

```powershell
uv run python scripts/reproduce_v041_one_sided_oracle.py
uv run pytest -q tests/final_theory/test_one_sided_elimination_oracle_v041.py
```

Expected result:

```text
V041_RESTRICTED_LOCUS_QQ_INDEPENDENT_ORACLE_PASSED
terminal verdict V041_ON_Q_RECONSTRUCTION_RESTRICTED_LOCUS_COMMUTATIVITY_PROVED
source mode HISTORICAL_WITHDRAWN_FULL_PROFILE_CLAIM
verified certificates 42
semantic digest cc3347215cdb160ef37d455200b701fb1c2a042ee7775bdd8cdc34c606fd4535
```

The oracle does not import the v0.4.1 campaign driver. It reconstructs the
721/955 relation sets from the raw direct-operator artifact and verifies every
stored certificate. It accepts the old full-profile verdict only as withdrawn
historical arithmetic input and cannot emit it as a current or terminal
verdict. Regression tests pin the bytes of all three historical JSON artifacts
and the aggregate hash of all 42 certificates.

## Certified 955 source-reconstruction slice

The scope-corrected source pullback and the source-native Eq. (120)
certificate can be rebound to the 21 strong-GC/reachable-MSR certificates
without invoking Sage:

```powershell
uv run python scripts/reproduce_v041_partial_slice_audit.py --write-audit
uv run pytest -q tests/final_theory/test_eq120_source_provenance_v042.py `
  tests/final_theory/test_v041_partial_slice_audit.py
```

Expected result:

```text
V042_EQ120_SOURCE_NATIVE_PROVENANCE_PROVED
PROVED_PARTIAL_SLICE
partial-slice semantic digest 2d65ddeefdec9606b6680dce6a6a790fb30ff50dd8d552a01043b022a6c99839
14 passed
```

This proves commutativity only on the nonsingular source slice
`P_sGC+rMSR intersect image(Phi_U)`. It does not prove Eq. (120) on arbitrary
points of the selected-700 direct locus and does not cover
`P_sGC+rMSR minus image(Phi_U)`.

## Resource gate

The static compiler reads the explicitly authorised
`config/v0.4.1_budget.json`, which contains exactly:

```json
{
  "timeout_seconds_per_chart": 3600,
  "total_wall_time_seconds": 43200,
  "memory_limit_gib": 8
}
```

The per-chart timeout may not exceed the total wall time. The user approved
these values on 2026-08-01 as the default for later project campaigns as well;
each campaign must still bind an explicit versioned budget file. The historical
`config/v0.3.7_budget.json` is not used as a fallback.

## Claim boundary

Neither the static inventory nor the exact campaign plus oracle proves a
one-sided source profile. They certify commutativity only on two selected
relation loci inside the frozen strong-profile reconstruction. Both general
one-sided `ON_QUOTIENT` statements and `OFF_NATURALLY_LABELLED` remain open.

Reproduce the semantic soundness failure separately with:

```powershell
uv run pytest -q tests/final_theory/test_v041_reachable_msr_soundness.py
```

Expected result: `4 passed`.
