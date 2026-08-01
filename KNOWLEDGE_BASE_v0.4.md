# CPOBC research knowledge base — v0.4 track

Updated: 2026-08-01

This is the live scientific index after the public v0.3.9 release. Use the
publication roadmap for ordering, this file for current facts and reusable
methodology, and `HANDOFF_v0.4.1.md` for operational continuation. Historical
release files and content-addressed artifacts remain unchanged even when a
later scope audit supersedes their interpretation.

## 1. Reading order and authority

1. `reports/cpobc_publication_roadmap_v0.4-v0.7.md` — research and publication
   order.
2. This knowledge base — current scientific state, terminology, and proof
   rules.
3. `CURRENT_RESEARCH_STATE.json` — compact mutable index for tools and future
   agents; it is not a proof certificate.
4. `HANDOFF_v0.4.1.md` — exact operational state, commands, hashes, and next
   gates.
5. `reports/v0.4.1_scope_break_decision_packet.md` — current owner decision.
6. `reports/v0.4.2_prior_art_and_related_work_audit.md` — current novelty,
   priority, related-work, and mathematical-commutativity claim boundaries.
7. `reports/cpobc_backup_policy_2026-08-01.md` — Git/NAS responsibility split,
   cold-backup rule, and the current non-Git artifact snapshot checksum.
8. Versioned reports and machine artifacts — evidence within their declared
   scope. A later scope addendum controls interpretation but does not rewrite
   old bytes.

The public Zenodo v0.3.9 record remains the baseline for the strong/strong
theorem. Unreleased v0.4 work must not be described as part of that deposit.

## 2. Current theorem table

All entries below are finite, nonsingular, `d=2`, source stages `n<=4`, and
occurrence identification `ON_QUOTIENT` unless stated otherwise.

| GC semantics | MSR semantics | current status |
|---|---|---|
| strong operator | strong operator | commutativity proved; public v0.3.9 baseline |
| fixed initial vector | strong operator | `OPEN`; v0.4.1 proof interpretation invalid |
| strong operator | reachable state | `OPEN`; v0.4.1 proof interpretation invalid |
| fixed initial vector | reachable state | exact rational noncommutative witness certified in v0.4 |

The sharp “at least one strong side” threshold is not a theorem. Both
one-sided truth values are unresolved. `FINAL_THEORY_OPEN` remains the global
status.

A proper sublocus of the strong-GC/reachable-state-MSR corner is nevertheless
closed: on the nonsingular source reconstruction slice
`P_sGC+rMSR intersect image(Phi_U)`, the four `Q` matrices commute. This is the
machine-certified `PROVED_PARTIAL_SLICE` result, not a full-profile theorem.

A second bounded subresult is also closed inside the 262-variable mixed
ansatz: on the pure-lower slice `x=0`, exact `y`-linearity and the 108+23 QQ
rank-131 certificate force `y=0`, hence diagonal commuting Q while
`D_p1=diag(0,1)` keeps `N!=0`. This is an SR3b auxiliary theorem, not a new
semantic-profile row and not a change to SR3b-A.

## 3. Artifact interpretation ledger

| artifact/result | arithmetic status | allowed scientific use |
|---|---|---|
| Zenodo v0.3.9 | public and retained | strong-GC/strong-MSR ON commutativity only |
| `results/v0.4_weak_d2_classification.json` | exact source-coordinate witness | weak/weak ON noncommutativity; OFF only an orbit-constant transfer candidate |
| `results/v0.4.1_one_sided_scout.json` | exact QQ linear algebra | bounded two-character upper-triangular evidence only |
| v0.4.1 42 QQ certificates | exact; 42/42 closed on input ideals | restricted loci inside the strong-profile Q reconstruction |
| v0.4.1 independent oracle | exact certificate verification | arithmetic, binding, relation selection, and resource checks; not semantic coverage |
| scope-corrected v0.4.1 driver/oracle | fail-closed implementation guard | future artifacts use `restricted_locus` paths/verdicts; historical bytes are read-only |
| `reports/v0.4.1_reachable_msr_soundness_audit.md` | exact source-native coverage counterexample | authoritative reason the one-sided proof lift is invalid |
| `results/v0.4.2_fixed_vector_gc_strong_msr_escape.json` | exact source-native coverage counterexample | symmetric proof that the 721 source profile is not covered by the Eq. (112) reconstruction |
| `reports/v0.4.2_955_minimal_deelimination_design.md` | exact local parameterisation plus provenance audit | `N_c=u_c(Jv_c)^T` is exhaustive and adds 48 scalars; a global source-native compiler is still required |
| `results/v0.4.2_eq120_source_provenance.json` | exact source-native free-word certificate | six raw CPOBC relations plus source nonsingularity prove the three `k=1` Eq. (120) identities; no MSR, GC, Eq. (108), or Eq. (112) is used |
| `results/v0.4.1_partial_slice_audit.json` | independently rebound source-to-chart proof | certifies Q commutativity on `P_sGC+rMSR intersect image(Phi_U)` using 21 of the 42 historical QQ certificates |
| `reports/v0.4.2_partial_slice_short_report_plan.md` | SR3b-A scope/publication lock | `THEOREM_CERTIFIED / SHORT_REPORT_SLOT_CONFIRMED / PRIOR_ART_AUDIT_COMPLETE / DISTINCT_TECHNICAL_CONTRIBUTION_IDENTIFIED / DRAFT_RECOMMENDED / DEPOSIT_NOT_AUTHORIZED`; the proper-slice theorem is draftable independently but is not the full 955 theorem |
| `reports/v0.4.2_prior_art_and_related_work_audit.md` | completed novelty/priority and related-work audit | no same claim found for SR2 or SR3b-A in the bounded search; Xu arXiv:2607.26672v1 is more general on the self-adjoint slice and forbids broad rigidity/priority wording; full one-sided profiles remain open |
| `references/notes/v0.4.2_prior_art_related_work_2026-08-01.md` | theorem/page-level literature and mathematical-tool ledger | records direct-source semantics, Xu overlap, triangularisation/common-eigenvector/Burnside/cyclic-separating/LLD tools, 66-PDF local/NAS preservation, and exact claim boundaries |
| `results/v0.4.2_955_source_native_slack_compiler.json` | structured source word/matrix-block inventory | covers 165 occurrences/131 orbits, 48 slack coordinates, and independently proves the 320-edge strong-GC basis spans all 1,529 path pairs; no scalar solver manifest or chart theorem yet |
| `results/v0.4.2_955_n_nonzero_scout.json` | exact QQ-linear source-native scout | the entire nonsingular `A_e=[[p_e,x_e],[0,1]]` family lies in `N!=0`, but all six Q commutators are forced zero; general mixed nonlinear patches remain open |
| `results/v0.4.2_955_mixed_source_native_manifest.json` | exact sparse QQ scalar manifest, no solver run | `V042_955_MIXED_SOURCE_NATIVE_SCALAR_MANIFEST_READY_NO_SOLVER_RUN`; 262 variables, 783 CPOBC + 320 strong-GC + 24 reachable-MSR vector equations, 165 determinant predicates, uniform `N!=0`; old 21 chart ideals are unused |
| `results/v0.4.2_955_mixed_xy_tangent_scout.json` | exact QQ tangent/pivot certificate, schema v2; digest `d7a4f6dba63d17cd1107ce173fb829a60af0bbf044bb02b7ccca262c70b029d5` | `V042_955_MIXED_XY_SCOUT_NO_WITNESS_OPEN`; upper rank 114/nullity 17, lower CPOBC+reachable-MSR rank 131, and the `x=0` pure-lower family has the bounded global verdict `V042_955_PURE_LOWER_TRIANGULAR_GLOBAL_NO_GO_PROVED`; general mixed components remain open |
| `results/v0.4.2_955_pure_lower_oracle.json` and `reports/v0.4.2_955_pure_lower_oracle.md` | independent fail-closed nonlinear-manifest oracle; digest `809f1931c2274b0b57a3bdedf73ca1997a3115030af11437f6c1f1793c20f5ba` | `V042_955_PURE_LOWER_ORACLE_CERTIFIED`; re-extracts all 783/320/24 equations at `x=0`, proves exact `y`-linearity, and independently verifies the 108+23 QQ rank-131 system; not a full-profile theorem |
| `results/v0.4.2_source_to_direct_audit.json` | valid initial namespace audit | records that three source IDs are not direct relation IDs; superseded on the reason by the zero-lift audit |
| `reports/v0.4.2_source_to_q_lift_design.md` | exact word-algebra audit | the three candidates have unique zero Q residuals; no 701-relation campaign exists |

The string `WEAK_D2_ON_ONE_SIDED_COMMUTATIVITY_PROVED` may appear in stored
v0.4.1 artifacts. It is historical machine output, not an active theorem
verdict.

### 3.1 Prior-art and mathematical-commutativity facts

- The direct source arXiv:2603.25503v1 writes MSR first on a reachable state
  in Eqs. (31)--(32), promotes it to an operator identity in Eq. (33), and
  states GC on the fixed initial vector. This is the semantic seam classified
  by v0.4; do not attribute the project's weak-profile theorem to the source.
- Surya's March 2024 Chengdu slides already display strong operator MSR and
  operator path/color independence. The strong formulation is prior source
  work; exact finite classification/certification is the project contribution.
- Xu arXiv:2607.26672v1, submitted 2026-07-29, contains the closest public
  CPOBC rigidity result. It is more general for finite-dimensional
  self-adjoint nonsingular systems and has several exact `2 by 2`
  triangular/extension results. It leaves non-self-adjoint nonsingular and
  state-only covariance directions open. Never claim broad priority over this
  territory; the public project Zenodo v0.3.9 date is 2026-07-31.
- No `SAME_CLAIM` was found through 2026-08-01 for the weak/weak exact rational
  witness or SR3b-A. This is a bounded-search finding, not a proof of absence.
- For `2 by 2` searches, split common-invariant-line/simultaneously
  triangularizable and irreducible branches early. `det[A,B]=0` detects the
  former for pairs over the appropriate field but does not imply commutativity.
- The minimal promotion from `D Omega=0` is separation by `Omega` on the
  profile-specific residual space, i.e. injectivity of `D -> D Omega`; cyclicity
  alone is insufficient. Two independent reachable vectors killed by the same
  `2 by 2` MSR residual recover strong MSR sourcewise.
- The centralizer of a non-scalar `A in M_2(F)` is `F[I,A]`. Showing all
  `Q_i` commute with one certified non-scalar `Q_k` is a valid compact endpoint
  for pairwise commutativity.
- Local archive state: 87 source records, 66 PDFs, 14 newly acquired PDFs,
  searchable text and SHA-256 manifest regenerated, and all 66 PDFs matched at
  `Y:\universe-theory-lab-backup\references\papers\`.
- Tracked code, tests, reports, and result JSON use Git commit plus push and do
  not need an unpacked NAS mirror. The NAS is cold backup only: never execute
  or extract there. Expensive Git-ignored outputs are stored as immutable
  compressed snapshots, currently the 512-entry archive recorded in
  `reports/cpobc_backup_policy_2026-08-01.md`.

## 4. The central methodological lesson

Relation-family ablation is not semantic ablation.

The v0.4.1 driver removed explicit `STRONG_OPERATOR_MSR` or
`LOCAL_OPERATOR_GC` records only after loading a Q presentation compiled under
`PAPER_STRONG_OPERATOR_PROFILE`. That coordinate layer had already used:

- Eq. (108), derived through operator MSR, for all 24 timid and 117 non-timid
  occurrence reconstructions;
- Eq. (112), derived under strong operator GC, for 20 non-antichain
  gregarious generators and their inverse nodes.

Therefore a proof profile must carry an **assumption ledger** through every
coordinate definition, elimination, substitution, localisation, and final
relation. Deleting a final relation is valid only when the deleted assumption
is absent from the entire dependency closure.

## 5. Mandatory soundness gates for future compilers

Before any counterexample or no-go result is promoted, record and verify all
of the following.

1. **Source semantics:** exact source variables, occurrence mode, vector
   semantics, field, stage bound, and nonsingularity domain.
2. **Assumption closure:** every derived coordinate and relation lists its GC,
   MSR, CPOBC, Eq. (113), and Eq. (139) dependencies.
3. **No-go coverage direction:** every target source-profile point maps into
   the compiled search space. A restricted slice is insufficient.
4. **Witness lifting direction:** every proposed compiled witness lifts back
   to source operators and passes every full-profile gate by direct exact
   substitution.
5. **Identity/relation separation:** a source constraint with zero reduced
   residual is an identity of that parameterisation, not an independently
   selectable direct relation.
6. **Independent semantic oracle:** certificate arithmetic and semantic
   coverage must be checked by separate tests or implementations.
7. **Branch separation:** never merge Eq. (113) literal/derived branches or
   Eq. (139) printed-strict/Eq. (145)-completed domains.
8. **Occurrence separation:** never treat 165 reduction/alias records as 165
   independent OFF variables.

For a no-go campaign, the inclusion certificate is a prerequisite to solver
execution, not a post-processing check.

## 6. Occurrence and equation census

| object | count / distinction |
|---|---|
| ON quotient transition matrices | 131 |
| v0.3.2 reduction/alias records | 165 |
| naturally labelled OFF source nodes | 50 |
| naturally labelled OFF transitions | 406 |
| raw CPOBC word equations | 783 |
| inverse-containing CPOBC rewrites | 712 |
| source MSR constraints | 24 |
| strong-GC spanning basis | 320 |
| all same-endpoint GC path pairs | 1,529 |
| Eq. (113) derived / literal | 25 / 25, kept separate |
| Eq. (139) printed / completed | 4 / 10, kept separate |

OFF requires its own labelled CPOBC, MSR, Eq. (113), and Eq. (139) compiler.
No current ON chart proof transfers automatically.

## 7. Exact escape fixture for regression testing

For each transition occurrence `t`, let

```text
A_t = diag(p_t, 1),  Omega = (1,0)^T,
```

where `p_t` is the frozen CSG character. This exact assignment is consistent
on 131 ON orbits, nonsingular at 165/165 occurrences, and passes CPOBC
783/783, inverse CPOBC 712/712, strong GC 1,529/1,529, and reachable-state MSR
24/24. All 24 strong-MSR operator identities fail; the first residual is
`diag(0,1)` and annihilates `Omega`.

Every future reachable-MSR compiler must accept this point. Rejecting it is a
minimal signal that strong MSR has leaked into the parameterisation. The
fixture is tested in
`tests/final_theory/test_v041_reachable_msr_soundness.py`.

There is now a symmetric fixed-vector-GC/strong-MSR escape fixture. Put
`Omega=e_1` and use exact diagonal transitions `diag(p_e,r_e)`, with `p_e`
the `t_j=1` CSG character and `r_e` obtained from the Eq. (107)/(108)
reduction at `Q_n=3^-n`, `G_c=3^-stage(c)`, except `G_p2-2=2/9`.
Direct substitution gives CPOBC 783/783, inverse forms 712/712, strong MSR
24/24, fixed-vector GC 1,529/1,529, and 165/165 nonzero determinants. Strong
GC fails on 510 path pairs; the first residual is `diag(0,-2/27)`. Eq. (112)
also fails directly at `p2-2` by `diag(0,1/9)`. This proves that the 721
source profile is not contained in the old Eq. (112) image, but the diagonal
fixture is not a noncommutative witness. It is tested in
`tests/final_theory/test_fixed_vector_gc_strong_msr_escape_v042.py`.

## 8. Next decision-gated research stage

The owner approved repair work after independently checking the primary
source, implementation, escape point, and 35-test regression. Sage/Singular
remains frozen until the semantic gates below pass. Current progress is:

1. **complete:** the v0.4.1 driver/oracle can no longer reissue the withdrawn
   theorem; new outputs and certificate writes use separate restricted-locus
   paths, while the old three JSON artifacts and 42 certificates are pinned
   read-only;
2. **complete partial theorem:** the source-to-955 pullback, localisation,
   source-native Eq. (120), `R_2`--`R_4` cover, and the relevant 21 exact QQ
   certificates have been rebound. The verdict is `PROVED_PARTIAL_SLICE` on
   `P_sGC+rMSR intersect image(Phi_U)`; no conclusion holds yet on its
   complement;
3. **local result complete:** `N_c = u_c (J v_c)^T` exhausts the missing
   reachable-MSR slack with two parameters per source, hence 48 scalars;
4. **structured inventory complete:** the source-native 131-orbit/165-alias
   compiler declares 783 CPOBC + 320 strong-GC + 24 timid-definition matrix
   blocks, 48 slack coordinates, 131 determinant localisations, and 48
   principal-open `N != 0` patches. It independently checks 407 paths in 87
   connected endpoint trees, hence all 1,529 strong-GC path pairs;
5. **first `N != 0` scout complete:** in the exact 131-variable upper-triangular
   family, CPOBC has rank 108 and CPOBC+strong GC rank 114/nullity 17; the
   `p1-0` operator-MSR residual has permanent lower-right entry one, yet all
   six Q commutators are forced zero;
6. **mixed scalar manifest complete, no solver:** the 131-orbit ansatz
   `A_e=[[p_e,x_e],[y_e,1]]` has 262 variables and expands 783 CPOBC, 320
   strong-GC basis, and 24 reachable-MSR vector equations with all 165
   determinant predicates. Its verdict is
   `V042_955_MIXED_SOURCE_NATIVE_SCALAR_MANIFEST_READY_NO_SOLVER_RUN`; it is
   uniformly in `N!=0`, does not reuse the old 21 ideals, and is not a chart
   cover, witness, or commutativity proof;
7. **exact mixed tangent scout complete:** upper rank is
   114/nullity 17. The lower CPOBC+reachable-MSR block has rank 131, certified
   over QQ by 108 selected CPOBC rows plus 23 selected reachable-MSR rows. The
   same lower obstruction holds at every upper-family point, so the unique
   local branch there is `y=0` and is commuting. The verdict remains
   `V042_955_MIXED_XY_SCOUT_NO_WITNESS_OPEN` for the general mixed problem;
8. **pure-lower bounded global no-go certified:** after `x=0`, all 783 CPOBC,
   320 strong-GC, and 24 reachable-MSR equations are exactly `y`-linear. The
   same 108+23 QQ rank-131 certificate forces the unique solution `y=0`; all
   four Q matrices are diagonal and commute, while `D_p1=diag(0,1)` certifies
   `N!=0`. The bounded verdict is
   `V042_955_PURE_LOWER_TRIANGULAR_GLOBAL_NO_GO_PROVED`, independently checked
   by `V042_955_PURE_LOWER_ORACLE_CERTIFIED` with semantic digest
   `809f1931c2274b0b57a3bdedf73ca1997a3115030af11437f6c1f1793c20f5ba`;
9. **next gate:** the pure-lower theorem is an SR3b auxiliary result, not a new
   short report, and does not change SR3b-A. The remaining targets are
   remote/disconnected `x!=0,y!=0` mixed components and the full 955 profile.
   Do not brute-force all 131 patches: first derive a symmetry/orbit reduction
   and exact-scout a small natural principal-open set. A solver campaign is
   permitted only after source coverage and versioned budget artifacts exist;
10. restore the 20 Eq. (112)-eliminated gregarious generators separately for
   the fixed-vector-GC side; the new exact escape fixture is its regression
   guard.

Relation-level minimality is deferred until this compiler exists. The
406-occurrence OFF compiler and genuine source-stage `n=5` remain separate
tracks.

## 9. Resource, evidence, and stopping policy

The approved default campaign budget is:

- 3,600 seconds per chart;
- 43,200 seconds total wall time;
- 8 GiB memory.

Each campaign must bind a versioned budget artifact. Exact characteristic-zero
arithmetic carries proofs; floats and finite fields are scouts only. Timeouts
remain unresolved. Existing public or content-addressed artifacts are never
overwritten.

If a definition, lift, chart cover, or verifier fails at project scope, stop
the affected campaign and prepare: the smallest reproducer, affected claims,
recoverable results, alternatives, estimated repair cost, and a recommended
owner decision.

## 10. Publication posture

Until both one-sided profiles are repaired, Paper I may use the asymmetric
main result—strong/strong commutativity versus the weak/weak exact
noncommutative witness—together with the dimension-independent source-native
Eq. (120) lemma and the certified 955 reconstruction-slice proposition. Both
general one-sided corners must remain explicitly open, and the slice must not
be advertised as their solution. Do not use “sharp semantic threshold” or
“complete finite ON classification” in a title, abstract, or conclusion.

The reconstruction-slice proposition is now the independent short report
**SR3b-A**. Its locked state is
`THEOREM_CERTIFIED / SHORT_REPORT_SLOT_CONFIRMED / PRIOR_ART_AUDIT_COMPLETE /
DISTINCT_TECHNICAL_CONTRIBUTION_IDENTIFIED / DRAFT_RECOMMENDED /
DEPOSIT_NOT_AUTHORIZED`; see
`reports/v0.4.2_partial_slice_short_report_plan.md`. Drafting is recommended,
but manuscript/reproduction gates and fresh owner approval precede any deposit
or submission.

The novelty/priority audit is complete through 2026-08-01; follow
`reports/v0.4.2_prior_art_and_related_work_audit.md`. Paper I and SR3b-A must
cite Xu arXiv:2607.26672v1, distinguish its self-adjoint/triangular rigidity
from the project's non-self-adjoint weak-semantics results, and avoid broad
“first” or priority language. Before manuscript freeze, run a delta search from
the recorded cutoff. A bounded search with no match never justifies an absolute
absence claim.

The pure-lower bounded global no-go and its independent oracle remain an SR3b
auxiliary theorem. They do not create another short report and do not alter
the SR3b-A theorem, title, or deposit status.

## 11. Decision log and work not to repeat

- v0.3.9 is the immutable public strong/strong baseline.
- v0.4 followed the counterexample-first rule and closed the weak/weak ON
  corner with an exact rational witness; no elimination was needed.
- v0.4.1 completed 42 exact QQ runs and an independent arithmetic oracle, then
  failed the later semantic-coverage audit. Do not rerun those 42 charts to
  repair the problem; new coordinates are required.
- v0.4.2 proved that `msr:p1-0`, `msr:p2-0`, and `msr:p2-2` have zero Q
  residuals. Do not schedule the proposed 63-run/701-relation campaign.
- The 955-side formula `N_c=u_c(Jv_c)^T` is an exact local lemma, not yet a
  solver-ready global 48-variable presentation. Do not append slack variables
  to the frozen Eq. (108)-expanded Q system.
- Six source-native antichain CPOBC instances and nonsingularity prove all
  three `k=1` Eq. (120) identities. This closes the ratio-commutation premise
  on source points, including future reachable-MSR slack points, but does not
  prove ideal membership on arbitrary points of the 700-relation direct locus.
  The free-word lemma is dimension-independent; only its present chart use is
  restricted to `d=2`, so preserve it for the future `d=3` track.
- The 955 historical arithmetic now proves the certified proper-slice theorem
  `P_sGC+rMSR intersect image(Phi_U) => [Q_i,Q_j]=0`. The unsolved region is
  exactly the source-profile complement outside that reconstruction image.
- The first global source-native slack inventory is complete, but its equations
  are structured words/matrix blocks rather than expanded scalar polynomials.
  Eq. (113) 25/25 and Eq. (139) 4/10 remain separated, fail-closed downstream
  validation gates; they are not silently imported through Eq. (112).
- The exact `N!=0` upper-triangular scout has no noncommutative survivor. This
  is a useful obstruction inside a 17-dimensional solution family, not a
  general no-go theorem. Three mixed local-`SL_2` numerical attempts retained
  CPOBC residuals near `10^-1` and are invalid scouts, so do not seed exact
  certification from those points.
- The exact 262-variable mixed source-native manifest is now available with
  783/320/24 profile blocks and 165 determinant predicates. It guarantees
  `N!=0`, invokes no solver, and deliberately does not reuse the historical 21
  chart ideals.
- The exact mixed tangent scout closes only the formal/local neighbourhood of
  the 17-dimensional upper family: the upper rank/nullity is 114/17 and the
  lower CPOBC+reachable-MSR rank is 131, with a 108+23 exact QQ row
  certificate. Schema v2 additionally proves a global no-go on the bounded
  `x=0` pure-lower family because its equations are exactly linear, not merely
  tangent equations.
- The pure-lower no-go is independently certified by an oracle that reads the
  nonlinear manifest without importing the tangent rank implementation. It
  forces `y=0`, diagonal commuting Q, and `D_p1=diag(0,1)`. Treat this as an
  SR3b auxiliary theorem, not a new short report; the SR3b-A scope is unchanged.
- Do not promote either result to a global mixed or full-profile no-go. The
  remaining mathematical target is remote/disconnected `x!=0,y!=0` mixed
  components and the full 955 profile.
- Do not launch a 131-patch exhaustive campaign next. First quotient patches
  by symmetry/orbits and run exact scouts on a small natural principal-open
  set inside the remaining mixed locus. Heavy solving remains frozen until
  coverage and versioned budget artifacts exist.
- The 721-side source profile now has an exact Eq. (112)-image escape point.
  It validates the scope withdrawal but does not decide commutativity because
  its four Q matrices are diagonal.
- Relation-level minimality is downstream of semantic compiler soundness.
- The standard 3,600 s/chart, 43,200 s total, 8 GiB budget is approved for
  future versioned campaigns. Broader research expansion is authorised when
  exact evidence reveals a stronger result or natural extension.
- The owner approved the revised repair order: code scope fix, certified
  `P intersect image(Phi)` partial slice, +48-variable slack extension, then
  the 131-orbit coverage verifier. Sage remains frozen during these gates.

Before repeating external research, search `references/sources.json`,
`references/manifest.json`, `references/text/`, and `references/notes/`.
