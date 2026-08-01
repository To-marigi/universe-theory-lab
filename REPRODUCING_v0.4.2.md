# Reproducing the v0.4.2 source-to-direct provenance audit

The v0.4.2 namespace artifact is a fail-closed static audit.  A subsequent
exact lift audit found the stronger explanation: all three source candidates
have unique zero Q residuals. Neither step invokes Sage/Singular, and the
proposed single-MSR relation campaign has not run.

From the repository root:

```powershell
uv run python scripts/reproduce_v042_single_strong_msr.py
uv run python scripts/reproduce_v042_single_strong_msr.py --write-audit
uv run pytest -q tests/final_theory/test_single_msr_elimination_v042.py
uv run pytest -q tests/final_theory/test_v042_source_to_q_lift.py
```

Expected result:

```text
V042_SOURCE_TO_DIRECT_PROVENANCE_REQUIRED
solver_invoked false
semantic digest 8718c6d9266486ec6df775bdd8027b5e64658451a0b3fd09b35498bb5faf5237
3 passed
V042_SOURCE_TO_Q_ZERO_LIFTS_VERIFIED
1 passed
```

The first audit binds the three triangular-ansatz candidate IDs to the v0.4
artifact and confirms that none is an ID in the frozen 21-relation direct
strong-MSR list. The focused lift test then follows the existing v0.3.1--v0.3.3
reduction path and proves that all three residuals cancel identically. Thus
there is no missing nonzero direct relation to map. The result neither proves
nor refutes sufficiency of a genuinely nonzero single MSR relation.

Any future direct single-relation campaign must choose among the 21 nonzero
Q-level MSR residuals. Source-level minimality instead requires a
profile-native source-coordinate compiler. Both are deferred behind the
v0.4.1 scope-break decision.

## Reachable-state MSR local slack audit

The sourcewise `d=2` formula

```text
N_c = u_c (J v_c)^T
```

is checked exactly with:

```powershell
uv run pytest -q tests/final_theory/test_strong_gc_reachable_msr_slack_v042.py
```

Expected result: `12 passed`. The audit proves that the 24 source slacks add
exactly 48 scalar parameters and exhaust `N_c v_c=0` for nonzero reachable
vectors. It also fails closed on global reuse: frozen Eq. (107), Eq. (108),
and Eq. (112) provenance requires a new source-native compiler before any
solver campaign.

## Fixed-vector GC / strong-MSR escape

Recompile the exact source fixture and run its focused checks with:

```powershell
uv run python -m universe_lab.final_theory.fixed_vector_gc_strong_msr_escape_v042
uv run pytest -q tests/final_theory/test_fixed_vector_gc_strong_msr_escape_v042.py
```

Expected verdict:

```text
FIXED_VECTOR_GC_STRONG_MSR_ESCAPE_CERTIFIED
```

The checked-in JSON has SHA-256
`7a51348850ea5d5c3c6048d8f9857b9b983c6945e36772c1e35f3c02da19d495`.
It verifies 165/165 nonsingular occurrences, CPOBC 783/783, inverse forms
712/712, strong MSR 24/24, and fixed-vector GC 1,529/1,529, while strong GC
fails on 510 path pairs and Eq. (112) fails at `p2-2`. The four Q matrices are
diagonal, so this is a coordinate-image escape, not a noncommutative witness.

## Source-native Eq. (120) certificate

The three `k=1` Eq. (120) identities are regenerated from six raw CPOBC
Eq. (103) records and source nonsingularity by the focused compiler test:

```powershell
uv run pytest -q tests/final_theory/test_eq120_source_provenance_v042.py
```

Expected result:

```text
V042_EQ120_SOURCE_NATIVE_PROVENANCE_PROVED
semantic digest 77d11eff7d14d84182abbf1eb30732fe2b94855507f1826747ba878fadb8d6ca
7 passed
```

MSR, GC, Eq. (108), Eq. (112), and stored B reductions are not used. The
certificate closes the ratio-commutation premise on the nonsingular source
locus, including future reachable-MSR slack points. It makes no direct-ideal
membership claim away from the source image. The final 955 partial-slice
binding is reproduced in `REPRODUCING_v0.4.1.md`.

## Structured 955 source-native slack inventory

```powershell
uv run pytest -q tests/final_theory/test_source_native_955_slack_compiler_v042.py
```

Expected result:

```text
V042_955_SOURCE_NATIVE_SLACK_INVENTORY_READY_NO_SOLVER_RUN
semantic digest 5baf2a4a0273c8f5d9c08d2436b2df1ef77eafad97a4532d444dc9a8e522e042
8 passed
```

The inventory records 165 occurrences/131 ON orbits, 48 slack coordinates,
783 CPOBC + 320 strong-GC + 24 timid-definition matrix blocks, 131 determinant
localisations, and 48 `N!=0` principal-open patches. It independently checks
that 320 basis edges connect 407 paths in 87 endpoint trees and hence span all
1,529 same-endpoint pairs. Eq. (113) 25/25 and Eq. (139) 4/10 remain separate
validation-only gates. No scalar-polynomial manifest, Sage run, global chart
cover, commutativity theorem, or witness is produced by this command.

## Exact `N!=0` upper-triangular scout

```powershell
uv run pytest -q tests/final_theory/test_source_native_955_n_nonzero_scout_v042.py
```

Expected result:

```text
V042_955_N_NONZERO_SCOUT_NO_WITNESS_OPEN
semantic digest 27935a8b7908f26179036b7732c5999f5ffe3b4b23363768ab714a83f90853d3
3 passed
```

The exact family `A_e=[[p_e,x_[e]],[0,1]]` has 131 orbit variables. All 165
determinants are nonzero; all 24 reachable-state MSR residuals annihilate
`Omega=e1`; and the operator residual at `p1-0` has lower-right entry one, so
the family is uniformly outside `N=0`. The 783 CPOBC rows have rank 108 and
adding the 320 strong-GC basis rows gives rank 114/nullity 17. Every Q
commutator has augmented rank 114 and is therefore forced zero in this family.
The verdict remains `OPEN` because mixed upper/lower nonlinear patches are not
classified.
