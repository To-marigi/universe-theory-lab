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
and builds GC/MSR into 262 affine edge parameters. The later raw-CPOBC audit
proves that fixed-state relation variety empty by the constant `2/117`; no
solver has run or may run on it. None of these verdicts is an SR2-V terminal.
The shear D12 artifact still certifies only ambient pair-irreducible
nonemptiness. The Smith-normal-form
artifact additionally certifies primitive
Laurent parameterizations `G_m^49` and `G_m^29` for the two declared scalar
monomial loci; the later section below globally imposes bottom MSR. See
`reports/v0.4.2_sr2v_principal_open_and_state_native_progress.md`.

## SR2-V bottom-MSR, state-slice, and transverse-cocycle certificates

```powershell
uv run python -m universe_lab.final_theory.sr2v_additive_msr_laurent_v042
uv run python -m universe_lab.final_theory.sr2v_bottom_msr_global_csg_v042
uv run python -m universe_lab.final_theory.weak_d2_state_native_shear_d12_preflight_v042
uv run python -m universe_lab.final_theory.weak_d2_state_native_fixed_harmonic_cpobc_obstruction_v042
uv run python -m universe_lab.final_theory.weak_d2_state_native_corrected_csg_rank2_v042
uv run python -m universe_lab.final_theory.sr2v_variable_harmonic_two_row_audit_v042
uv run python -m universe_lab.final_theory.sr2v_variable_harmonic_sparse_section_cpobc_v042
uv run python -m universe_lab.final_theory.sr2v_transverse_cocycle_principal_open_v042
uv run python -m universe_lab.final_theory.sr2v_transverse_determinant_zero_locus_v042
uv run python -m universe_lab.final_theory.sr2v_transverse_base_cover_ablation_v042
uv run python -m universe_lab.final_theory.sr2v_transverse_common_core_unit_minor_v042
uv run python -m universe_lab.final_theory.sr2v_transverse_common_core_schur_scout_v042
uv run python -m universe_lab.final_theory.sr2v_transverse_eq120_schur_chart_obligations_v042
uv run python -m universe_lab.final_theory.sr2v_transverse_eq120_repair_pair_scout_v042
uv run python -m universe_lab.final_theory.sr2v_transverse_common_core_q5_free_v042
uv run python -m universe_lab.final_theory.sr2v_q5_free_auxiliary_ideal_manifest_v042
uv run pytest -q tests/final_theory/test_sr2v_additive_msr_laurent_v042.py tests/final_theory/test_sr2v_bottom_msr_global_csg_v042.py tests/final_theory/test_weak_d2_state_native_shear_d12_preflight_v042.py tests/final_theory/test_weak_d2_state_native_fixed_harmonic_cpobc_obstruction_v042.py tests/final_theory/test_weak_d2_state_native_corrected_csg_rank2_v042.py tests/final_theory/test_sr2v_variable_harmonic_two_row_audit_v042.py tests/final_theory/test_sr2v_variable_harmonic_sparse_section_cpobc_v042.py tests/final_theory/test_sr2v_transverse_cocycle_principal_open_v042.py tests/final_theory/test_sr2v_transverse_determinant_zero_locus_v042.py tests/final_theory/test_sr2v_transverse_base_cover_ablation_v042.py
uv run pytest -q tests/final_theory/test_sr2v_transverse_common_core_unit_minor_v042.py
uv run pytest -q tests/final_theory/test_sr2v_transverse_common_core_schur_scout_v042.py
uv run pytest -q tests/final_theory/test_sr2v_transverse_eq120_schur_chart_obligations_v042.py
uv run pytest -q tests/final_theory/test_sr2v_transverse_eq120_repair_pair_scout_v042.py
uv run pytest -q tests/final_theory/test_sr2v_transverse_common_core_q5_free_v042.py
uv run pytest -q tests/final_theory/test_sr2v_q5_free_auxiliary_ideal_manifest_v042.py
uv run pytest -q tests/final_theory/test_sr2v_q5_free_auxiliary_ideal_bundle_v042.py
```

Expected verdicts and semantic digests:

```text
SR2V_ADDITIVE_MSR_LAURENT_SMOOTH_CSG_POINT_CERTIFIED_NONTERMINAL
53241bd2973c41153d145d6e2fee2f082c4631f7aeba76e30f0e89cca7df3b8b
SR2V_BOTTOM_MSR_GLOBAL_CSG_PARAMETERISATION_CERTIFIED_NONTERMINAL
d7978cac841bf725baa03df99aa661183a5c96367a2979b245b978f7d5dd08a4
SR2V_STATE_NATIVE_SHEAR_D12_PREFLIGHT_SUPERSEDED_EXECUTION_CANCELLED
58b77ba00838a1051364c2c7feebbbe99bf3104b957c15d4e356fe2fdd8aa524
SR2V_FIXED_HARMONIC_FULL_ALPHA_BETA_CPOBC_UNIT_IDEAL_OBSTRUCTION_CERTIFIED_NO_SOLVER_RUN
d5514f31bf6caef5ca102ef8ce78f0bcf137e72922c0f230c716386f22cffc7d
SR2V_CORRECTED_CSG_FIXED_HK_NONSINGULAR_CPOBC_UNIT_IDEAL_OBSTRUCTION_CERTIFIED_NO_SOLVER_RUN
2b6c8483598cf73bbf9dd2365dd2c7828c10bc0aedb72c58a84c47142c215b7f
SR2V_FIXED_K_TWO_ROW_OBSTRUCTION_ZARISKI_SPECIAL_CERTIFIED_NONTERMINAL
64a79807b4a19169517c5a9864b005c38a44593118987ed88e95dd2edb9cb84e
SR2V_VARIABLE_HARMONIC_TWO_ALPHA_PRINCIPAL_OPEN_CPOBC_UNIT_IDEAL_CERTIFIED_NONTERMINAL
4c8a71689c69d4845344eb44e459b3a5256075188b1f2d71dabc5a7428235efe
SR2V_TRANSVERSE_ALL_FOUR_SEMANTIC_BRANCHES_Q1_Q4_SPLITTING_PRINCIPAL_OPENS_CERTIFIED_NONTERMINAL
07e60a4d6b029d3cf08efd3ef3aae14598a1614090d3809d764973065b35eaf0
SR2V_TRANSVERSE_COMMUTATOR_KERNEL_COBOUNDARY_AND_NESTED_DEGENERACY_LOCI_CERTIFIED_NONTERMINAL
da062443965d679dc936dd4263f150c6d413deea7f5425790d039e099c89ac30
SR2V_TRANSVERSE_BASE_FOUR_CHART_REDUCTION_AND_GC_MSR_BLOCK_INDEPENDENCE_CERTIFIED_NONTERMINAL
005d9a5492bd379f5ac51d1d17b7d31df4acaa175fc9089ef4a138b761f23f6e
SR2V_TRANSVERSE_COMMON_CORE_GLOBAL_UNIT_MINOR_CERTIFIED_NONTERMINAL
286b2c8e0329dd585c33dee13c66e3a923a270d04822f3489186aad4ee1e45ac
SR2V_TRANSVERSE_COMMON_CORE_FIXED4_REJECTED_FULL_M0_NO_ESCAPE_AT_ADVERSARIAL_POINT_OPEN
5d1dae52b6f268b52e0deedccca405d49c92f8a01527f62b07c02bd239d1a875
SR2V_TRANSVERSE_EQ120_SCHUR_CHART_STRONG_CERTIFICATE_CONTRACTS_CERTIFIED_NONTERMINAL
c040fa5f4a1542becf5ba4579a2cefb5b0f224b910da1ec2da42bb77df44d644
SR2V_TRANSVERSE_EQ120_THREE_PAIR_MINOR_SUBCOVER_EXACTLY_REJECTED_FULL_M0_SURVIVES_NONTERMINAL
4efc456ac29986380f985aa7299b38fd17351f57ae87648b034aea6ae088208a
SR2V_TRANSVERSE_COMMON_CORE_Q5_FREE_SCHUR_REDUCTION_CERTIFIED_NONTERMINAL
d19b01460604c647dc290143bf3a5aba2986bc9e6be235fd1ebae3a7702c25a3
SR2V_Q5_FREE_AUXILIARY_IDEAL_MANIFEST_OPEN_RESOURCE_LIMIT_NONTERMINAL
357d739091d2bf36740895f35c9227ba912e69f8d455f9e91dd8a6ea7ce6c605
SR2V_Q5_FREE_AUXILIARY_IDEAL_FULL_MANIFEST_DIGEST_AND_SOLVER_INPUTS_FROZEN_NO_SOLVER_RUN
aa246d3856a5f12e67a326222d906ce5b7239d83053fd5b902d2e5e5b6d54e7c
```

The common-core unit schema and its four successor schemas use canonical JSON
semantic-digest predecessor bindings. Raw-byte SHA bindings are intentionally
absent, so CRLF/LF checkout normalization does not change their reconstructed
payloads.

The local Laurent certificate is retained as a Jacobian regression; the
global certificate supersedes only its former global-open boundary. The Q5
and budget preflight is also retained, but the old fixed-state D12 execution
is cancelled because its full alpha/beta CPOBC ideal already contains one.
The corrected fixed-`(h,k)` slice has a different two-row obstruction only
after beta localization. Varying `k` proves that mechanism is Zariski-special
and supplies a nonempty open rational section for those two rows. The follow-up
checks all raw entries: the escape has 911 residuals, and two alpha-killing
rows plus a nonzero rank-62 minor prove the entire beta-one, two-alpha
`Delta!=0` section empty. The separate transverse certificate builds four
Eq. (113)/Eq. (139) semantic matrices and proves `Q1,...,Q4` splitting on four
nonempty principal opens. It never uses the 1,187-row joint inventory for a
branch conclusion. The determinant-zero certificate then classifies the
universal commuting subspace and analyses nested loci. The witness condition is
`rank[M;C]>rank M`, not `Delta=0`, and
`K_delta=ker C(delta_Q)` equals `span(delta_Q)` only when `delta_Q!=0`; at zero
it is all `QQ^4`. Thus the whole equal-`Q`-spectrum locus is witness-free.
`beta=a-b` is a global conjugation coboundary annihilated by every commutator
form. At three full-diagonal points rank is 127 with bottom-tangent kernel. On
the ten-dimensional two-scalar locus `beta` is always in the kernel; four exact
nonzero-`delta_Q` points have rank 130 and kernel `span(beta,e_Q5)`. Its
six-dimensional Q5-only subfamily has `delta_Q=0` and is witness-free; one exact
point there has rank 127 and a five-dimensional tangent kernel. The corrected
v3 wording asserts only agreement of the four recorded scalar samples in each
scan direction; whole-line rank constancy remains open.

The successor certificate proves that CPOBC alone defines the saturated common
`G_m^49`, reduces the six commutators through source-native Eq. (120) to the
minimal star `c12,c13,c14`, and uses strict-to-completed row inclusion to leave
eight localized obligations. It also directly certifies two noncommutative
semantic-block ablations. The fixed-GC ablation still satisfies reachable-state
MSR on all 50 source-reaching path states; restoring either omitted block closes
the escape at the same scalar point. These are individual-necessity results,
not a full-profile witness.

The common-core unit-minor successor then uses only raw CPOBC, fixed-vector GC,
and reachable-state MSR to invert a fixed 127-by-127 non-`Q` block over the
entire 54-dimensional transverse base. Its 554-edge safe symbolic supergraph
has a unique perfect matching and its determinant is a Laurent unit. This is a
lossless five-`Q`-column reduction, not yet a commutativity theorem.

The five-`Q` scout freezes the original 81-point candidate ledger and targeted
82nd and 83rd exact points. Three tested four-row candidates are rejected. The
third fails at the positive rational torus point
`(u12,u13,u15,u44,u45)=(1/2,1,1,1,2)` with exact escape `e_Q2`. At both targeted
candidate escapes the complete common core and all four semantic branches
remain `131 -> 131` after all commutators, so no full-profile witness is found.

The Eq. (120) chart-obligation successor derives the exact remaining pointwise
rank problem. On each `D(gk)`, Eq. (120) gives
`x=delta*h+(b/b1)*w` and `c1k=-b_k*g_k*w`; adjoining the coordinate row `e_w`
must preserve rank over every residue field. Localized row-module membership of
`e_w` is a stronger sufficient certificate. On the aligned remainder the same
distinction applies simultaneously to `e_w2,e_w3,e_w4`; the `r1=1` sublocus is
automatically safe. The certificate retains the external `Q5` coefficient,
proves that the same corresponding minors under visible-reference changes are
unit rescalings while alternate anchors may refine the cover, and records why a finite rank ledger,
a pointwise nonzero minor, an `AB` minor with hidden `Q5`, or multivariate gcd
one is not a global proof.

The repair-pair scout then rejects `(32,120)` on `D(g2)` and `(424,544)` on
`D(g3)` by exact positive-rational points. Pair `(8,14)` repairs those two
points, but all three pair minors vanish at
`u=(1,1/2,1,2,2)`, where the normalized ratio values are
`(g2,g3,g4)=(-1/2,-1/2,0)` and the determinant-form values are
`(d2,d3,d4)=(1/96,1/256,0)`, with `d_i=-b1*b_i*g_i`. Each restricted rank is
`1/1/2`, while full `M0` remains `131 -> 131`. This rejects only the proposed
three-minor subcover, not either chart or the common-core theorem target.

The source-native Q5 audit then checks all 1,127 common-core rows independently:
none of 4,756 source references resolves to external `Q5`, the independent
symbolic compiler finds no nonzero Q5 coefficient, and the 127 pivot rows are
also Q5-free. The global Schur block identity therefore removes Q5 exactly.
The non-aligned target is `T=[A B]`; the aligned target is
`T=[A B2 B3 B4]`. Every semantic branch contains `M0` once and in order, so a
common-core pointwise theorem propagates to all four branches by row inclusion.
This does not assert Q5-freeness of appended Eq. (113) or Eq. (139) rows.

The Phase-A checkpoint then machine-rebuilds the four predecessor bindings,
the 14-factor bottom-CSG localization, and the lightweight spectator reduction
to
`R52=QQ[t1,...,t4,s0,...,s47][(F_lambda*product(s_j))^-1]`. The complete
1,127-row manifest attempt did not emit a result before its manually observed
request boundary. Its elapsed time, CPU/RSS, and stop event are manual local
observations because no attempt-time source snapshot or raw monitor transcript
was preserved; no partial row count is certified. Running the module command
above reproduces the fail-closed checkpoint only and does **not** repeat the
long attempt. No Sage, Gröbner basis, saturation, unit ideal, or witness is
claimed.

## Phase-A bundle: two-tier freeze

The full Phase-A payload is about 20.9 GiB as pretty JSON and is never tracked
in Git. It is frozen in two tiers: a 3.33 MiB root manifest under Git, and both
coefficient arenas outside Git as compact canonical JSONL split into
deterministic gzip chunks (level 6, `mtime=0`, no embedded filename). Nine
chunks total 2,025.6 MiB uncompressed and 128.0 MiB compressed. The
uncompressed canonical byte stream is the mathematical authority; each chunk's
gzip digest is a transport check only.

Both commands below are expensive: each recompiles all 1,127 rows and takes
roughly fifty minutes on one core.

```bash
uv run python -m universe_lab.final_theory.sr2v_q5_free_auxiliary_ideal_bundle_v042
uv run python -m universe_lab.final_theory.sr2v_q5_free_auxiliary_ideal_bundle_v042 --verify
```

The first command writes the chunks and a root carrying
`FULL_BUILD_DIGEST_OBSERVED_UNFROZEN_NONTERMINAL`: storing the bundle is a
digest commitment and nothing more. The second streams every chunk against the
ledger and independently recompiles Phase A -- source and pivot rebuild, the
Schur identities, Q5 and spectator vanishing, denominator clearing with its
inverse reconstruction, the six chart generator manifests, and the six frozen
rational cross-check points -- and also checks that the compiler module, the
bundle module and `uv.lock` still hash to the values the root was produced
from. Only when every entry of `REQUIRED_RECOMPILATION_CHECKS` is present and
true does the verdict rise to
`SR2V_Q5_FREE_AUXILIARY_IDEAL_FULL_MANIFEST_DIGEST_AND_SOLVER_INPUTS_FROZEN_NO_SOLVER_RUN`.
A check that reports failure, a missing chunk, or any digest mismatch yields
`OPEN_ARTIFACT_INCOMPLETE`; a check that is simply absent leaves the verdict
unfrozen rather than being read as a pass.

The verdict deliberately says *digest and solver inputs*, not *full manifest*:
the bundle retains both arenas and commits to everything else by digest, and it
does not store every byte of the roughly 20.9 GiB logical payload. Editing the
compiler or the bundle module invalidates an existing root under this contract,
which is intended -- a root must be regenerated and re-verified after any
change to the code that produced it.

The full logical payload digest is
`2a79c1d0b9fd464ba9c80e970cad948b21920f8d25e7403256ccbc27017a5a8a`. The v0.4.2
resource checkpoint `357d7390...c605` is a separate, earlier artifact and is not
superseded or overwritten by the bundle.

The chunk directory is Git-ignored. It is backed up as an immutable NAS
snapshot under the CPOBC backup policy and is intended for a Zenodo
supplemental dataset at publication; it is never expanded or executed on the
NAS.

## Next exact gate

For state-native SR2-V, enlarge the exact section beyond beta one and the two
retained alpha coordinates; do not rerun the now-empty sparse section or either
old fixed-state D12/shear campaign. In the transverse reducible branch, use the
certified global unit minor in the branch-independent common core
`M0=CPOBC+fixed-vector GC+reachable-state MSR` and use its Q5-free Schur
complement. The Phase-A input gate is now closed: the compiler carries
deterministic row checkpoints and a cached fraction-field representation, and
all 1,127 Schur rows and six chart generator manifests are frozen and verified
in the bundle above. Proceeding from that input gate,
on each `S_k=R_base[g_k^-1]` certify the auxiliary ideal
`J_k=<A_i*h+B_i>=S_k[h]`, equivalently the `g_k`-saturated unit ideal over the
original base. The determinantal alternative is `I1(T_k)=S_k` and
`<A_i> subset sqrt(I2(T_k))`. On the equal-ratio quotient localized at
`f=r1-1`, certify `I3(B)=R` and `<A_i> subset sqrt(I4(T))`, or exclude each of
the three normalized obstruction charts `w2=1`, `w3=1`, `w4=1`. Full Schur
row-module membership is a stronger accepted route, not a necessity. Use
exponent-lattice HNF/SNF to remove spectator torus variables. If the common-core
ideal certificates succeed, all four branches follow and the old eight
branch/locus obligations are bypassed. If a bad point is found, lift it by
Eq. (120) and the 127-pivot backsolve, verify `M0` and commutators directly, and
then test the four branch-specific additions; completed Eq. (139) follows from
strict, while derived and literal Eq. (113) are never combined.
Then treat
`Delta_align=0` and the triple-irreducible pivots. Keep supplemental Q5
separate. Do not launch an exhaustive 131-patch campaign.
When the 955 mixed components resume, first construct a symmetry/orbit
reduction and exact-scout a small set of natural principal-open patches. Any
solver campaign requires a source-profile coverage certificate and a
versioned budget artifact.
