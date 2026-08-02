# Reproducing the v0.4.2 profile-native audits and exact scouts

## CI and public-release boundary

The mutable v0.4 tree is reproduced with:

```powershell
uv run python scripts/reproduce_v04.py
uv run pytest -q tests/final_theory/test_ci_version_boundary_v04.py
```

The public v0.3.9 raw-byte contracts are intentionally not replayed against
this tree. CI checks them in a separate full-history checkout of exact public
commit `cba86eae795e1e985c4ba1bcd3dabe4eb2773fab`. Do not regenerate
`results/v0.3.8_line_ending_bridge.json` or
`results/v0.3.9_release_manifest.json`; see
`reports/v0.4_ci_release_boundary_repair_2026-08-02.md`.

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
`6c8b230fc4c4a8c2a0d4f352da846b633639ecf59f0ef67537a53b5dedb229a6`.
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

## SR3b-A partial-slice short report

The certified proper-slice theorem is now tracked as independent short report
**SR3b-A**. Its locked state is:

```text
THEOREM_CERTIFIED / DRAFT_RECOMMENDED / NOVELTY_PRIORITY_AUDIT_PENDING / DEPOSIT_NOT_AUTHORIZED
```

See `reports/v0.4.2_partial_slice_short_report_plan.md` for the theorem scope,
paper structure, evidence map, novelty/priority gate, and explicit nonclaims.
The theorem remains only
`P_sGC+rMSR intersect image(Phi_U) => [Q_i,Q_j]=0`; neither the full 955
profile nor `P minus image(Phi_U)` is closed.

## Mixed source-native 955 scalar manifest

The checked-in sparse QQ manifest is regenerated in memory and compared byte
for semantic content by:

```powershell
uv run python -m universe_lab.final_theory.source_native_955_mixed_manifest_v042
uv run pytest -q tests/final_theory/test_source_native_955_mixed_manifest_v042.py
```

Expected result:

```text
V042_955_MIXED_SOURCE_NATIVE_SCALAR_MANIFEST_READY_NO_SOLVER_RUN
semantic digest 13dc6cc8ec89395ba86bc66c5d96e25f79ed8cc5bbf9c6cc2b6925d1256430f2
5 passed
```

The ansatz `A_e=[[p_e,x_[e]],[y_[e],1]]` has 262 variables over 131 ON
orbits. The manifest expands 783 CPOBC, 320 strong-GC-basis, and 24
reachable-state-MSR vector residuals, and records all 165 occurrence
determinants `p_e-x_[e]y_[e]` (131 distinct factors). Its observed term census
is 23,166. A constant lower-right entry at source `p1-0` proves `N!=0`
throughout the ansatz. The old 21 chart ideals are not reused. This is a
manifest only: no solver or Sage process ran, and it is not a witness, chart
cover, or commutativity proof.

## Exact mixed x/y tangent scout

```powershell
uv run python -m universe_lab.final_theory.mixed_xy_nonneutral_scout_v042
uv run pytest -q tests/final_theory/test_v042_955_mixed_xy_tangent_scout.py
```

Expected result:

```text
V042_955_MIXED_XY_SCOUT_NO_WITNESS_OPEN
schema final-theory-v042-955-mixed-xy-tangent-scout-v2
semantic digest d7a4f6dba63d17cd1107ce173fb829a60af0bbf044bb02b7ccca262c70b029d5
8 passed
```

At the diagonal point, the upper block has exact rank 114 and nullity 17. The
lower CPOBC plus reachable-MSR block has rank 131. The stored QQ pivot
certificate selects 108 CPOBC rows and 23 reachable-MSR rows and pivots all
131 `y` columns. The lower Jacobian is independent of the upper-family `x`
coordinates, so the same rank-131 obstruction holds at every point of that
family: the unique formal/local branch through it is `y=0`, and that branch is
the commuting upper family.

Schema v2 contains the stronger bounded-family result
`V042_955_PURE_LOWER_TRIANGULAR_GLOBAL_NO_GO_PROVED`. At `x=0`, all 783 CPOBC,
320 strong-GC, and 24 reachable-MSR equations are exactly linear in `y`, with
no discarded higher-order terms. The 108 CPOBC + 23 reachable-MSR QQ
certificate has rank 131 and forces the unique solution `y=0`. Consequently
all four Q matrices are diagonal and commute, while
`D_p1=diag(0,1)` proves `N!=0`. Here “global” means only global within this
declared pure-lower family.

## Independent pure-lower oracle

The new authoritative paths are:

- `src/universe_lab/final_theory/source_native_955_pure_lower_oracle_v042.py`;
- `results/v0.4.2_955_pure_lower_oracle.json`;
- `reports/v0.4.2_955_pure_lower_oracle.md`;
- `tests/final_theory/test_source_native_955_pure_lower_oracle_v042.py`.

Reproduce the independent check with:

```powershell
uv run python -m universe_lab.final_theory.source_native_955_pure_lower_oracle_v042
uv run pytest -q tests/final_theory/test_source_native_955_pure_lower_oracle_v042.py
```

Expected result:

```text
V042_955_PURE_LOWER_ORACLE_CERTIFIED
semantic digest 809f1931c2274b0b57a3bdedf73ca1997a3115030af11437f6c1f1793c20f5ba
4 passed
```

The oracle re-extracts the specialized nonlinear-manifest equations and forms
its own exact SymPy QQ rank-131 matrix; it does not import the tangent scout's
rank implementation. This is an SR3b auxiliary theorem, not a new short
report, and does not change the SR3b-A scope.

The general mixed verdict remains deliberately `OPEN`: neither certificate
excludes remote/disconnected solutions with `x!=0,y!=0`, and neither proves
commutativity for the full 955 profile. No finite-field, numerical, Sage,
Gröbner, or saturation run was performed.

## SR2-V observability and minimal recovery

```powershell
uv run python -m universe_lab.final_theory.weak_d2_observability_v042
uv run python -m universe_lab.final_theory.semantic_recovery_v042
uv run pytest -q tests/final_theory/test_weak_d2_observability_v042.py
uv run pytest -q tests/final_theory/test_semantic_recovery_v042.py
```

Expected results:

```text
SR2V_BASELINE_OBSERVABILITY_AUDIT_CERTIFIED
semantic digest 73508f8ad94d97a3147cbd913d687f0b779c740b80a84a4836854053f6f01c62
6 passed
SR3B_M_CONDITIONAL_RECOVERY_LEMMAS_CERTIFIED
semantic digest a742976ab7d955a66beb07f6efd06170cd3b2f320638b6a64c3292f6fcf5d735
14 passed
```

The observability verifier independently reconstructs 407 paths and 87
endpoint states, proves reachable rank one, and verifies that all six nonzero
Q commutators annihilate every declared cylinder state. SR3b-M certifies
conditional residual-evaluation and same-residual multi-probe lemmas. Neither
artifact closes the reachable-visible search or a one-sided profile.

## SR2-V bounded reachable-visible scouts

```powershell
uv run python -m universe_lab.final_theory.weak_d2_visible_torus_scout_v042
uv run python -m universe_lab.final_theory.weak_d2_visible_tangent_v042
uv run pytest -q tests/final_theory/test_weak_d2_visible_torus_scout_v042.py
uv run pytest -q tests/final_theory/test_weak_d2_visible_tangent_v042.py
```

Expected results:

```text
SR2V_VISIBLE_TORUS_SCOUT_NO_WITNESS_OPEN
semantic digest 7ed0d5f8c3d67528bd6cb2853e8b8887479488453799a43b6645d87437ad028f
SR2V_BASELINE_LOWER_TANGENT_VISIBILITY_OBSTRUCTED
semantic digest d83afca2c460bad9e8d420e75ad60e1974f3419f0dd655bfc51821d6a02b5a92
9 passed
```

The first command constructs the exact 49-dimensional scalar exponent torus
and tests 180 deterministic nonzero rational points. No Q commutator survives,
but the finite campaign is not a torus cover. The second command differentiates
the full weak/weak system over exact dual numbers. Its 1,187-row
invariant-line-breaking subsystem has rank 131 on 132 lower coordinates and
kernel only cutoff-external Q5; the full 528-variable Jacobian has rank 455 and
nullity 73 with no in-scope lower-left direction. This is a first-order bounded
obstruction, not a global SR2-V terminal. See
`reports/v0.4.2_sr2v_visible_search.md`.

## SR2-V principal-open reductions and state-native rank-two chart

```powershell
uv run python -m universe_lab.final_theory.weak_d2_aligned_principal_open_v042
uv run python -m universe_lab.final_theory.weak_d2_transitive_extension_v042
uv run python -m universe_lab.final_theory.weak_d2_commutator_branching_v042
uv run python -m universe_lab.final_theory.weak_d2_state_native_rank2_v042
uv run python -m universe_lab.final_theory.weak_d2_state_native_shear_pair_open_v042
uv run python -m universe_lab.final_theory.sr2v_scalar_lattice_v042
uv run pytest -q tests/final_theory/test_weak_d2_aligned_principal_open_v042.py
uv run pytest -q tests/final_theory/test_weak_d2_transitive_extension_v042.py
uv run pytest -q tests/final_theory/test_weak_d2_commutator_branching_v042.py
uv run pytest -q tests/final_theory/test_weak_d2_state_native_rank2_v042.py
uv run pytest -q tests/final_theory/test_weak_d2_state_native_shear_pair_open_v042.py
uv run pytest -q tests/final_theory/test_sr2v_scalar_lattice_v042.py
```

Expected results:

```text
SR2V_ALIGNED_PRINCIPAL_OPEN_VISIBILITY_OBSTRUCTED
semantic digest 66ed68773f8023c0e84f18c48719dc5517cb3c43f8d5f87e25b3f9ddf01d6fa5
SR2V_TRANSITIVE_EXTENSION_PRINCIPAL_OPEN_SPLITTING_CERTIFIED
semantic digest 5b3cf83ae5cd6338cfa07c1894bf5eab2f6cf8fe5870fd8fdc6911682b06d000
SR2V_COMMUTATOR_PIVOT_BRANCH_COVER_CERTIFIED
semantic digest 100fefe528012254edcd66c7237ae5706dcb3bba6badbe75da170f68403b4032
SR2V_STATE_NATIVE_RANK2_CHART_CERTIFIED
semantic digest 3bf3b56c97ef73fcce3ff089f5229191b9d1ade04e217706ac51abe11eaebe6c
SR2V_STATE_NATIVE_SHEAR_D12_MANIFEST_CERTIFIED_NO_SOLVER_RUN
semantic digest 82cd51ddd29e5923b003c8cf8f75a5a26cf5a36edf68728ad58d298d3f573090
SR2V_SCALAR_LATTICE_SNF_CERTIFIED_NONTERMINAL
semantic digest 155ddfd5ec1b90765acbb0eccfaa66991fc2d98a44432055b5481b09a0de5eb9
31 passed
```

The aligned certificate upgrades `F'(0)y=0` to the exact localized
factorization `F=H y`, so the nonempty open `det H!=0` contains no nonlinear
invariant-line-breaking branch. The transverse certificate proves generic
splitting only for its two-character transitive-percolation family. The
commutator artifact is a structural six-pair/four-branch cover, not a CPOBC
solution. The state-native chart fixes one harmonic rank-two boundary slice
and builds GC/MSR into 262 affine edge parameters; the 783 CPOBC and separate
Eq. (113)/(139) ledgers remain unsolved. None of these verdicts is an SR2-V
terminal. The shear D12 artifact compiles all ledgers into 29,994 sparse terms
and proves only that the ambient pair-irreducible open is nonempty; no solver
has run and no relation-variety point is certified. The Smith-normal-form
artifact additionally certifies primitive
Laurent parameterizations `G_m^49` and `G_m^29` for the two declared scalar
monomial loci, before additive MSR and cocycle equations. See
`reports/v0.4.2_sr2v_principal_open_and_state_native_progress.md`.

## Next exact gate

For SR2-V, use the primitive Laurent maps instead of finite torus sampling.
The state-native shear `det[Q_1,Q_2]!=0` manifest is compiled; bind a separate
Q5 determinant localization and versioned solver budget before determining
whether its relation variety meets the open. Then treat `Delta_align=0`, the exceptional transverse
`Delta(r,s)=0` locus, and the triple-irreducible pivots. Keep supplemental Q5
and the two Eq. (113) and Eq. (139) ledgers separate. Do not launch an
exhaustive 131-patch campaign. When the 955 mixed components resume, first
construct a symmetry/orbit reduction and exact-scout a small set of natural
principal-open patches. Any solver campaign requires a source-profile coverage
certificate and a versioned budget artifact.
