# CPOBC research knowledge base — v0.4 track

Updated: 2026-08-02

This is the live scientific index after the public v0.3.9 release. Use the
publication roadmap for ordering, this file for current facts and reusable
methodology, and `HANDOFF_v0.4.1.md` for operational continuation. Historical
release files and content-addressed artifacts remain unchanged even when a
later scope audit supersedes their interpretation.

## 1. Reading order and authority

1. `reports/cpobc_publication_roadmap_v0.4-v0.7.md` — research and publication
   order.
2. `reports/v0.4.2_post_literature_strategy_review.md` — post-audit scientific
   focus, Paper I theorem stack, observability track, and revised gates.
3. `reports/v0.4.2_sr2v_principal_open_and_state_native_progress.md` — current
   exact SR2-V branch reductions, bottom-MSR classification, fixed-state
   obstructions, chart/manifests, and nonterminal boundaries.
4. This knowledge base — current scientific state, terminology, and proof
   rules.
5. `CURRENT_RESEARCH_STATE.json` — compact mutable index for tools and future
   agents; it is not a proof certificate.
6. `HANDOFF_v0.4.1.md` — exact operational state, commands, hashes, and next
   gates.
7. `reports/v0.4.1_scope_break_decision_packet.md` — scope-break owner decision.
8. `reports/v0.4.2_prior_art_and_related_work_audit.md` — current novelty,
   priority, related-work, and mathematical-commutativity claim boundaries.
9. `reports/cpobc_backup_policy_2026-08-01.md` — Git/NAS responsibility split,
   cold-backup rule, and the current non-Git artifact snapshot checksum.
10. Versioned reports and machine artifacts — evidence within their declared
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

The weak/weak witness is algebraically noncommutative but has reachable-span
rank one, and every certified `Q` commutator kills that reachable ray. It is an
exact logical separation, not yet reachable-visible noncommutativity. The new
SR2-V track records operator noncommutativity, reachable rank, and action on a
stage/source-compatible reachable-state domain as separate predicates.

That observability statement is now independently machine-certified, rather
than inferred from the original witness compiler. The follow-up exact search
has not reached an SR2-V terminal. A 180-point rational-torus campaign found no
transverse reducible witness. The aligned selected residuals factor as
`F(y,z)=H(y,z)y`, and on the explicit nonempty principal open `det H != 0`
every exact solution has `y=0`. A two-character transitive-percolation
extension also splits generically. The broader transverse cocycle fibre is now
split on four separately compiled nonempty principal opens: derived/literal
Eq. (113), each crossed with strict/completed Eq. (139). The branch matrices
have shapes `1156 by 132` or `1162 by 132` and force all 131 actual cocycles to
zero, hence `Q1,...,Q4` commute. The 1,187-row all-readings matrix is auxiliary
only.

Those four determinant-zero boundaries are now partly classified, and the
analysis changed the question. The six commutator coefficients are
universally `x_j*(a_i-b_i)-x_i*(a_j-b_j)`, so a reachable-visible witness needs
`rank[M;C]>rank M`, not merely `Delta=0`: a determinant-zero point is where the
principal-open argument stops, not where a witness appears. Substituting
`x_e=beta_e:=a_e-b_e` gives `[[a,a-b],[0,b]]=C*diag(a,b)*C^-1` with
`C=[[1,-1],[0,1]]`, so `beta` is a global conjugation coboundary: it satisfies
every operator relation row at every base point, and every commutator form
annihilates it. The commuting subspace is `K_delta=ker C(delta_Q)`: for nonzero
`delta_Q` it is `span(delta_Q)`, while for zero `delta_Q` it is all of `QQ^4`.
Hence the entire equal-`Q`-spectrum locus is witness-free. On its
five-dimensional full diagonal sublocus `E={a_e=b_e}`, rank 127 and the
bottom-tangent kernel are certified at three exact points, not locus-wide. On
the ten-dimensional two-scalar locus, `beta` always lies in the kernel; at four
certified nonzero-`delta_Q` points the branch rank is 130 with kernel exactly
`span(beta,e_Q5)`. The same locus also contains a six-dimensional
same-couplings independent-Q5 subfamily `T` with `delta_Q=0`, witness-free
throughout; at one exact point of `T\E`, rank is 127 with a five-dimensional
tangent kernel. Rank constancy and witness freedom on the remaining
nonzero-`delta_Q` part are not claimed. Splitting principal
opens are now also certified over non-normalized bottom characters. The
remaining reducible components and irreducible branches stay open.

The next exact gates sharpen this further. On the observed-bottom primitive
`G_m^29`, all 24 additive reachable-MSR equations are globally triangular and
their complete nonzero locus is the smooth irreducible rational normalized
finite-CSG principal open in four couplings times external `G_m(Q5)`. The
separate upper operator character remains `G_m^49`; reachable-state MSR must
not be promoted to strong MSR on that character.

The former fixed-harmonic state-native chart is not a viable solver input. Its
full 262-parameter raw-CPOBC ideal contains the constant `2/117`, so every
localization, including D12 and Q5, is empty. A corrected CSG-compatible first
harmonic removes all pure constants. For the selected independent harmonic
`k`, however, two alpha-free raw equations
`f=beta_u+1/8` and `g=8 beta_v(1-8 beta_u)`, together with the required inverse
`rho beta_v-1`, satisfy

```text
1 = (rho/16) g + 4 rho beta_v f - (rho beta_v - 1).
```

Thus that corrected fixed-`(h,k)` nonsingular slice is also empty. These two
results close only their declared state assignments, not all rank-two state
assignments and not SR2-V. Varying `k` in the 62-dimensional root-zero
harmonic space shows that this two-row mechanism is Zariski-special: an exact
rank-two escape `k` solves both rows with every beta nonzero, and a coefficient
determinant `-393/2` produces a rational section on a nonempty principal open.
The follow-up substitutes that escape into all 3,132 raw scalar entries and
finds 911 nonzero residuals. On the full beta-one, two-alpha `Delta!=0`
section, two further raw entries force the alphas to zero, and an exact rank-62
harmonic minor with determinant `2^192*3^9*977` then forces `k=0`, contradicting
`Delta!=0`. That sparse section therefore has a localized unit ideal. Variable
betas, the other 129 alphas, and a complete open subset of `Gr(2,63)` remain
unclassified. The old fixed-state D12/shear solver must not be run.

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
| `reports/v0.4.2_post_literature_strategy_review.md` | current research-direction authority after the audit | refocuses Paper I on statewise observability, exact separation, and minimal recovery; adds SR2-V; makes full one-sided closure and `n=5` upgrades rather than scoped-manuscript gates |
| `results/v0.4.2_sr2v_baseline_observability.json` | independent exact `Fraction` reconstruction; digest `73508f8ad94d97a3147cbd913d687f0b779c740b80a84a4836854053f6f01c62` | certifies 407 paths/87 states, reachable rank one, six operator-nonzero commutators, and zero action on every declared reachable domain; baseline audit only |
| `results/v0.4.2_sr3b_m_semantic_recovery.json` | exact QQ/symbolic lemma certificate; digest `a742976ab7d955a66beb07f6efd06170cd3b2f320638b6a64c3292f6fcf5d735` | residual-family evaluation injectivity, same-residual two-probe recovery, global-span and cyclicity counterexamples, and the non-scalar `2x2` centralizer endpoint; closes neither one-sided profile |
| `results/v0.4.2_sr2v_visible_torus_scout.json` | exact finite rational scout; digest `7ed0d5f8c3d67528bd6cb2853e8b8887479488453799a43b6645d87437ad028f` | 49-dimensional scalar torus, 180 rational points, no free Q commutator; `OPEN` bounded evidence, not a torus cover or general no-go |
| `results/v0.4.2_sr2v_baseline_lower_tangent.json` and `reports/v0.4.2_sr2v_visible_search.md` | exact dual-number QQ tangent certificate; digest `d83afca2c460bad9e8d420e75ad60e1974f3419f0dd655bfc51821d6a02b5a92` | base-upper-right-independent 1,187-row invariant-line-breaking subsystem has rank 131/kernel external Q5; full Jacobian rank 455/nullity 73 but no in-scope lower direction or first-order visibility escape; not a global obstruction |
| `results/v0.4.2_sr2v_aligned_principal_open.json` | exact determinant-localized polynomial factorization; digest `66ed68773f8023c0e84f18c48719dc5517cb3c43f8d5f87e25b3f9ddf01d6fa5` | upgrades the aligned tangent result to `F=H y`; on the nonempty open `det H!=0`, all exact solutions have `y=0`; Eq. (113) 25/25 and Eq. (139) 4/10 provenance remain separately serialized; the degeneracy hypersurface and other components remain open |
| `results/v0.4.2_sr2v_transitive_extension_principal_open.json` | exact symbolic identities plus a nonzero 130-minor; digest `5b3cf83ae5cd6338cfa07c1894bf5eab2f6cf8fe5870fd8fdc6911682b06d000` | on `r*s*(1+r)*(1+s)!=0`, the same-character line and a generic distinct-character principal open force `Q_1,...,Q_4` commutativity through split extensions; Q5 upper-right coordinate is fixed outside the kernel and the exceptional determinant-zero locus remains open |
| `results/v0.4.2_sr2v_commutator_pivot_branch_cover.json` | exact `2 by 2` polynomial identities; digest `100fefe528012254edcd66c7237ae5706dcb3bba6badbe75da170f68403b4032` | six Q pairs completely cover Q-noncommutativity and split it into pair-irreducible, triple-irreducible, transverse-reducible, and aligned-reducible branches; structural cover only |
| `results/v0.4.2_sr2v_state_native_rank2_chart.json` | exact harmonic-state and local-frame certificate; digest `3bf3b56c97ef73fcce3ff089f5229191b9d1ade04e217706ac51abe11eaebe6c` | 87 states, 131 orbit actions, exact reachable rank two; fixed-vector GC/reachable MSR are built into a 262-parameter fixed-state chart and nonsingularity reduces to `beta_e!=0` (automatic on the shear slice), while CPOBC/Eq. (113)/Eq. (139) remain unsolved |
| `results/v0.4.2_sr2v_state_native_shear_D12_manifest.json` | exact sparse QQ substitution manifest; digest `82cd51ddd29e5923b003c8cf8f75a5a26cf5a36edf68728ad58d298d3f573090` | 131-edge shear plus separate Q5; `D12=det[Q1,Q2]` is a nonzero seven-term cubic and all ledgers are compiled; the original artifact made no intersection claim, while the later fixed-harmonic unit certificate proves this fixed-state intersection empty |
| `results/v0.4.2_sr2v_scalar_lattice.json` | exact ZZ/QQ Smith-normal-form and primitive-kernel certificate; digest `155ddfd5ec1b90765acbb0eccfaa66991fc2d98a44432055b5481b09a0de5eb9` | operator scalar block is a split `G_m^49`; observed-bottom plus fixed-GC block is a split `G_m^29`; additive MSR, cocycle, commutator, and chart-cover claims are excluded |
| `results/v0.4.2_sr2v_additive_msr_laurent.json` | exact local Laurent/Jacobian certificate | normalized CSG point has logarithmic rank 24 and local dimension five; retained as an independent regression after the global classification |
| `results/v0.4.2_sr2v_bottom_msr_global_csg.json` and `reports/v0.4.2_sr2v_bottom_msr_global_csg.md` | exact global triangular/CSG isomorphism certificate; digest `d7978cac841bf725baa03df99aa661183a5c96367a2979b245b978f7d5dd08a4` | globally classifies the nonzero bottom-MSR locus as normalized finite CSG times `G_m(Q5)`; does not solve upper `G_m^49`, the cocycle fibre, or SR2-V |
| `results/v0.4.2_sr2v_state_native_shear_D12_preflight.json` | exact Q5-localization and approved-budget provenance; fail-closed digest `58b77ba00838a1051364c2c7feebbbe99bf3104b957c15d4e356fe2fdd8aa524` | live rebuild binds the later fixed-harmonic unit-ideal certificate and returns `EXECUTION_CANCELLED_BY_LATER_UNIT_IDEAL`; it cannot re-authorise the solver |
| `results/v0.4.2_sr2v_fixed_harmonic_cpobc_obstruction.json` | exact raw-CPOBC unit generator; digest `d5514f31bf6caef5ca102ef8ce78f0bcf137e72922c0f230c716386f22cffc7d` | the complete 262-parameter chart for the former fixed harmonic state assignment is empty before localization; not a global state cover |
| `results/v0.4.2_sr2v_corrected_csg_fixed_hk_obstruction.json` | exact full-chart census, beta-lattice SNF, and localized two-row unit identity; digest `2b6c8483598cf73bbf9dd2365dd2c7828c10bc0aedb72c58a84c47142c215b7f` | the corrected CSG-compatible selected fixed-`(h,k)` nonsingular slice is empty; other `k` and other harmonic two-planes remain open |
| `results/v0.4.2_sr2v_variable_harmonic_two_row_audit.json` and `reports/v0.4.2_sr2v_variable_harmonic_two_row_audit.md` | exact harmonic-space/gauge audit and two-row escape certificate; digest `64a79807b4a19169517c5a9864b005c38a44593118987ed88e95dd2edb9cb84e` | predecessor result proving the fixed-`k` two-row obstruction Zariski-special and constructing an open rational section; it did not solve the other entries, which the following sparse-section certificate then audits and obstructs |
| `results/v0.4.2_sr2v_variable_harmonic_sparse_section_cpobc.json` and `reports/v0.4.2_sr2v_variable_harmonic_sparse_section_cpobc.md` | exact 3,132-entry substitution, sparse polynomial identities, and rank-62 minor; digest `4c8a71689c69d4845344eb44e459b3a5256075188b1f2d71dabc5a7428235efe` | the predecessor escape has 911 raw residuals; two alpha-killing rows plus determinant `2^192*3^9*977` make the beta-one, two-alpha `Delta!=0` section a localized unit ideal; wider alpha/beta support is open |
| `results/v0.4.2_sr2v_transverse_cocycle_principal_open.json` and `reports/v0.4.2_sr2v_transverse_cocycle_principal_open.md` | exact four-matrix branch-separated rational linear algebra; digest `07e60a4d6b029d3cf08efd3ef3aae14598a1614090d3809d764973065b35eaf0` | separate nonzero minors on derived/literal Eq. (113) crossed with strict/completed Eq. (139) force all actual cocycles to zero and `Q1,...,Q4` to commute on four nonempty opens; the joint 1,187-row matrix is auxiliary and all four determinant-zero loci remain open |
| `results/v0.4.2_sr2v_transverse_determinant_zero_locus.json` and `reports/v0.4.2_sr2v_transverse_determinant_zero_locus.md` | exact universal `2 by 2` identities plus exact rational rank/kernel data at eight nested-locus points, two off-normalized opens, and a 60-point deterministic scan; digest `a61eaeec40499a0d756699fcaa8ff71ee1e54da2adb5e95b985f6a488503773f` | the witness condition is `rank[M;C]>rank M`, not `Delta=0`, and the commuting subspace is `K_delta=ker C(delta_Q)`; the whole `delta_Q=0` locus is witness-free; three full-diagonal samples have rank 127 and bottom-tangent kernel, four nonzero-`delta_Q` two-scalar samples have rank 130 and kernel `span(beta,e_Q5)`, and one Q5-only two-scalar sample has rank 127 with a larger tangent kernel; rank constancy and the remaining nonzero-`delta_Q` locus are open, as are the four unexpanded hypersurfaces |
| `references/notes/v0.4.2_sr2v_bottom_msr_csg_interpretation_2026-08-02.md` | source/derivation boundary | finite CSG is prior classical work; the new project claim is the exact weak/weak `G_m^29` coordinate classification and its certified scope, not broad CSG priority |
| `reports/v0.4.2_sr2v_principal_open_and_state_native_progress.md` | current SR2-V exact progress authority | consolidates the exact certificates through the sparse-section unit ideal and four branch-separated cocycle opens, discarded numerical-scout boundary, revised exact search order, and nonterminal publication scope |
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
- For a chosen nonzero Q commutator `C`, the exact complete split uses
  `det C`, all transition traces `tr(C A_e)`, and
  `det(C Omega,Omega)`. The resulting branches are pair-irreducible,
  triple-irreducible, transverse globally reducible, and aligned globally
  reducible. `det C=0` alone does not prove reducibility of the whole generator
  family. The 131 actual transitions and supplemental Q5 remain distinct.
- The minimal promotion from `D Omega=0` is separation by `Omega` on the
  profile-specific residual space, i.e. injectivity of `D -> D Omega`; cyclicity
  alone is insufficient. Two independent probe vectors killed by the same
  `2 by 2` MSR residual recover strong MSR sourcewise. Ordinary single-`Omega`
  GC supplies only one state at each source, so a global rank-two reachable set
  does not by itself provide this sourcewise multi-probe condition.
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

### 3.2 Post-literature strategic facts

- Paper I is now organized around statewise-versus-operator observability,
  exact semantic separation, and minimal recovery—not a broad historical
  `d=2` rigidity claim.
- SR2-V is the first new research track. Its three terminal states are
  `REACHABLE_VISIBLE_NONCOMMUTATIVE_WITNESS_CERTIFIED`,
  `REACHABLE_VISIBLE_NONCOMMUTATIVITY_OBSTRUCTED`, and
  `REACHABLE_VISIBILITY_OPEN_RESOURCE_LIMIT`.
- The strong SR2-V quality target requires both exact reachable-span rank two
  and nonzero commutator action on a declared stage/source-compatible reachable
  state. These are separate conditions; neither is silently inferred from
  operator noncommutativity.
- The SR2-V baseline verifier is complete: 407 paths, 87 endpoint states,
  exact reachable rank one, and all six nonzero commutators invisible on the
  full declared cylinder-state domain. The aligned branch now has a nonlinear
  obstruction on `det H!=0`; a transverse two-character family splits on a
  second nonempty principal open. Neither covers its determinant-zero boundary,
  so SR2-V remains open.
- Q-noncommutativity is now covered structurally by six nonzero commutator
  pivots. Each pivot has four exact branches: pair-irreducible,
  triple-irreducible, transverse globally reducible, and aligned globally
  reducible. In the transverse upper chart the commutator determinant is
  identically zero, so noncommutativity must be saturated by the normalized
  upper-right commutator coefficient instead.
- The original state-native rank-two chart fixes one harmonic terminal
  boundary slice, uses 262 affine edge parameters, and builds fixed-vector GC
  and reachable-state MSR into the coordinates. The later raw-CPOBC audit
  proves that complete fixed-state chart empty by the constant `2/117`.
- Its pair-irreducible shear/D12 manifest and later Q5/budget preflight remain
  valid ambient/provenance artifacts, but the relation intersection is empty
  on that fixed state assignment. No elimination may be launched there.
- The scalar monomial relation lattices are now global rather than sampled:
  the 843-by-132 operator block has rank 83 and Smith factors `1^83`, while the
  1,163-by-132 observed-bottom plus fixed-GC block has rank 103 and factors
  `1^103`. Their primitive kernels give split tori `G_m^49` and `G_m^29`.
  The 24 additive bottom-MSR equations are now imposed and globally classified
  on `G_m^29`; the upper `G_m^49` character and extension fibre remain open.
- SR3b-M must distinguish ordinary reachability from multiple preparations or
  probes applied to the same residual. The latter is a conditional recovery
  theorem, not an automatic consequence of the base single-state semantics.
- SR3b-M is now exact and machine-certified. Its same-residual two-probe and
  residual-evaluation injectivity lemmas may be used in Paper I, but they do
  not settle either one-sided profile or the reachable-visible search.
- The next heavy profile is 955 because it lies in the non-self-adjoint,
  state-only boundary left open by Xu and already has the strongest native
  compiler/certificate assets. The 721 compiler follows 955 or becomes the
  fallback if 955 reaches its budget terminal.
- SR3b-A remains a confirmed scoped short report, but SR2-V and SR3b-M have
  higher conceptual priority. Full 955/721 closure and `n=5` are upgrades, not
  mandatory gates for drafting a carefully scoped Paper I.

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

The post-literature lightweight gates preceding further 955 work are also now
materialized: SR2-V baseline observability and SR3b-M are complete; the aligned
tangent obstruction has been upgraded to a nonlinear principal-open theorem;
a two-character transverse family splits generically; the six Q-commutator
pivots give a complete structural branch cover; and an exact state-native
rank-two chart is ready. Smith-normal-form certificates also replace finite
scalar-torus sampling by primitive `G_m^49` and `G_m^29` Laurent coordinates.
Bottom MSR is now globally classified, both isolated fixed-state charts have
exact unit-ideal obstructions, and the selected two-row mechanism has an exact
variable-`k` escape. The escape fails 911 raw entries, while its entire beta-
one, two-alpha principal-open section is empty by a rank-62 unit certificate.
Separately, four transverse semantic branches have their own nonempty
splitting opens, and their universal commutator kernel plus nested degeneracy
loci are now partly classified. The immediate targets are whether the
`Q`-projection of `ker M` always lies in `K_delta=ker C(delta_Q)`, wider state-native
alpha/beta support, the aligned degeneracy locus,
and the triple-irreducible branches. Generic points inside certified opens
should not be resampled. The equal-`Q` locus needs no witness rescan, but the
nonzero-`delta_Q` part of the two-scalar locus remains open away from four points.

For SR2-V specifically:

1. **aligned open closed:** `F=H y` and a nonzero exact determinant certify
   `y=0` on `Delta_align!=0`; only `Delta_align=0` and other components remain;
2. **transverse family generically closed:** the same-character line commutes,
   and on `r!=s, Delta(r,s)!=0` the only extension is the split coboundary;
3. **branch cover complete:** six Q pairs and four branches per nonzero pivot
   cover every Q-noncommutative model, with supplemental Q5 tracked separately;
4. **original rank-two chart closed:** one exact harmonic boundary slice has
   262 affine edge parameters, but its raw CPOBC ideal contains `2/117` and is
   empty before localization;
5. **D12 execution cancelled:** the 136-coordinate ambient input, Q5
   localization, and approved budget are certified, but the fixed-state
   relation intersection is empty and no solver may run;
6. **scalar lattices globalized:** the two declared monomial loci are split
   connected tori of dimensions 49 and 29; all 24 additive bottom-MSR equations
   reduce the latter globally to normalized finite CSG times external Q5;
7. **corrected selected state closed:** a CSG-compatible `h` removes all pure
   constants, but for one fixed harmonic `k`, two raw rows plus beta
   nonsingularity generate one exactly;
8. **fixed-`k` mechanism escaped then sparse section closed:** the harmonic space has dimension 63 and
    the fixed-`h` family is `P^61`; an exact alternative `k` and a nonempty-open
    rational section solve the selected two rows, but direct substitution has
    911 residuals and a rank-62 localized certificate closes the beta-one,
    two-alpha section;
9. **four transverse opens closed:** four separately compiled Eq. (113)/Eq.
    (139) semantic branches have nonzero 131- or 132-column minors, forcing all
    actual cocycles to zero and `Q1,...,Q4` to commute on each open;
10. **commutator kernel and nested loci classified:** the witness condition is
    `rank[M;C]>rank M`, not `Delta=0`, and the commuting subspace is
    `K_delta=ker C(delta_Q)`; the whole `delta_Q=0` locus is witness-free. Three
    full-diagonal samples have rank 127 with bottom-tangent kernel; four
    nonzero-`delta_Q` two-scalar samples have rank 130 with kernel
    `span(beta,e_Q5)`; one Q5-only sample has rank 127 with a larger tangent
    kernel. The residual question is whether the `Q`-projection of `ker M`
    always lies in `K_delta`;
11. **terminal unchanged:** none of these scoped certificates is a witness or
    full-profile obstruction, so SR2-V remains `OPEN`.

For the one-sided repair track, current progress remains:

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
9. **955 resumption gate:** the pure-lower theorem is an SR3b auxiliary result,
   not a new short report, and does not change SR3b-A. After the bounded SR2-V
   campaign reaches an allowed terminal, the remaining 955 targets are
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

Paper I is now scoped as a statewise-versus-operator observability and recovery
paper. Its established asymmetric core is strong/strong commutativity versus
the weak/weak exact noncommutative witness, together with the
dimension-independent source-native Eq. (120) lemma and the certified 955
reconstruction-slice proposition. SR2-V must disclose that the current witness
has reachable rank one and off-reachable-sector commutators, while SR3b-M must
state the exact residual-separation and multi-probe recovery conditions. Both
general one-sided corners remain explicitly open unless later closed, and the
slice must not be advertised as their solution. Do not use “sharp semantic
threshold” or “complete finite ON classification” in a title, abstract, or
conclusion.

A bounded SR2-V campaign must reach witness, obstruction, or resource-limit
terminal before manuscript freeze, but neither full one-sided closure nor
`n=5` is an absolute gate for a scoped draft. If only the present rank-one
witness survives, the target-journal decision is reassessed from the completed
manuscript rather than strengthened by wording.

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
- Current-tree CI and public-release replay are separate verification domains.
  The current lane runs `scripts/reproduce_v04.py`; the historical lane checks
  out public v0.3.9 commit
  `cba86eae795e1e985c4ba1bcd3dabe4eb2773fab` with full history and runs its
  frozen reproducer and four release-relative test files. Never regenerate the
  v0.3.8 bridge or v0.3.9 release manifest against v0.4. The fail-closed hashes,
  LF normalization boundary, and regression test are recorded in
  `reports/v0.4_ci_release_boundary_repair_2026-08-02.md`.
- v0.4 followed the counterexample-first rule and closed the weak/weak ON
  corner with an exact rational witness; no elimination was needed.
- The independent SR2-V audit fixes that witness at reachable rank one and
  proves all six nonzero commutators annihilate all 87 compiled cylinder
  states. Do not describe it as reachable-visible.
- The transverse rational-torus scout tested 180 exact rational points in a
  49-dimensional scalar torus and found no free Q commutator. Do not rerun the
  same points or promote the finite census to a torus cover. The relevant
  monomial loci now have primitive global Laurent maps `G_m^49` and `G_m^29`;
  use those maps for additive-MSR and cocycle work instead.
- The weak/weak invariant-line-breaking subsystem has 1,187 exact rows,
  rank 131 on 132 lower coordinates, and kernel equal to cutoff-external Q5.
  The full 528-coordinate Jacobian has rank 455/nullity 73, but no actual
  `n<=4` lower-left tangent direction. The nonlinear `F=H y` certificate now
  closes `Delta_align!=0`; do not search that open again. Target
  `Delta_align=0`, the still-unclassified part of the transverse degeneracy
  locus, or the pair/triple irreducible pivots. The 1,187-row all-readings inventory is not a
  semantic branch and must never support an Eq. (113)/Eq. (139) conclusion.
  This is not a full SR2-V obstruction.
- The original state-native rank-two chart fixes one harmonic boundary slice
  and is complete only for edge actions over those states. Its full raw-CPOBC
  relation variety is now proved empty by `2/117`. Do not call it a cover or
  treat its exact validation sample as a CPOBC point.
- The old state-native D12 shear manifest, Q5 localization, and budget binding
  are provenance-only. Their fixed-state relation intersection is empty, so
  never cite the ambient point as a model and never run the planned solver.
- The corrected CSG-compatible fixed-`(h,k)` chart is also empty after beta
  localization, but its two-row mechanism is Zariski-special in variable `k`.
  Its escape/open rational section has now been tested against the full raw
  ledger: the point has 911 residuals and the beta-one, two-alpha section is a
  localized unit ideal. Do not call its two-row assignment a full CPOBC point,
  and do not rescan that sparse section. Enlarge beta or alpha support.
- The four transverse cocycle matrices must remain separate. Derived Eq. (113)
  has a universally zero external-Q5 column and a nonzero actual 131-column
  minor; literal Eq. (113) has a nonzero full 132-column minor. Both statements
  hold separately for strict and completed Eq. (139), giving four nonempty
  splitting opens.
- Do not equate the transverse determinant-zero loci with a witness locus. The
  correct condition is `rank[M;C]>rank M` for the six commutator rows `C`. The
  commuting subspace is `K_delta=ker C(delta_Q)`: it is `span(delta_Q)` only for
  nonzero `delta_Q`, and is all `QQ^4` at zero. Therefore do not rescan the
  equal-`Q`-spectrum locus for witnesses. The nonzero-`delta_Q` part of the
  two-scalar locus remains open away from four certified points; do not mark the
  whole locus closed. Rank constancy is not proved.
- Do not cite or regenerate the uncommitted draft digest `37bcbb5b...`. Its
  criterion incorrectly used `span(delta_Q)` at `delta_Q=0` and missed the
  Q5-only part of the two-scalar locus. Schema v2 digest `a61eaeec...` supersedes
  it before any commit or release.
- Larger exploratory counts reported during that session (~490 line points and
  ~900 points overall) have no frozen complete input ledger in this artifact.
  Treat them as scouts only; the formal evidence is the 60-point deterministic
  scan and eight explicit nested-locus samples.
- Do not adopt "the kernel stays inside `span(beta,e_Q5)`" as the invariant to
  defend. One recorded degenerate point has `beta` outside the kernel entirely,
  a kernel not contained in that span, and still-vanishing commutator forms. The
  decidable invariant is containment of the `Q`-projection of `ker M` in
  `K_delta=ker C(delta_Q)`. `beta=a-b` is a global conjugation coboundary, satisfies
  every operator relation row at every base point, and is annihilated by every
  commutator form, so a kernel direction equal to `beta` never yields a witness.
- `transverse._eq139_row` hardcodes the normalized `torus._csg` bottom
  character. Use `sr2v_transverse_determinant_zero_locus_v042.eq139_row` and
  `branch_matrix` for any evaluation away from `t=(1,1,1,1)`; mixing the two
  silently produces meaningless strict-branch ranks.
- A source/target frame cocycle `A_(c->d)=p_(c->d)S_dS_c^-1` was rejected as
  a construction route. It gives strong GC, exact reachable-state MSR,
  reachable rank two, and visible noncommuting Q for nonconstant harmonic
  frame columns, but the tested exact point fails all 783 raw CPOBC equations
  and every completed Eq. (139) instance. Preserve the lesson: CPOBC, not the
  statewise semantic equations, is the barrier for this natural gauge ansatz.
- SR3b-M is complete as a conditional lemma module. Global reachable rank two
  across different sources is still not sourcewise residual recovery; two
  independent probes must act on the same residual, or evaluation must be
  injective on its declared residual space.
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
- The earlier repair order—code scope fix, certified `P intersect image(Phi)`
  partial slice, +48-variable slack extension, then the 131-orbit coverage
  verifier—completed its first three milestones. The current next-work order is
  superseded by `reports/v0.4.2_post_literature_strategy_review.md`: SR2-V and
  SR3b-M first, then symmetry-reduced 955 work, then 721. Heavy solving remains
  frozen until profile coverage and versioned budget gates pass.

Before repeating external research, search `references/sources.json`,
`references/manifest.json`, `references/text/`, and `references/notes/`.
