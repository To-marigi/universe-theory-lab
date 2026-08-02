# Handoff -- CPOBC v0.4/v0.4.1 research track

Written 2026-08-01; continued 2026-08-02. This is the live handoff for work
after the public v0.3.9 release. The historical `HANDOFF.md` remains the frozen
v0.3.9 record and is not superseded as release provenance.

## 1. Governing roadmap

Start with `KNOWLEDGE_BASE_v0.4.md` for current scientific facts and reusable
proof rules. `CURRENT_RESEARCH_STATE.json` is the compact mutable index for
tools and future agents. Use `reports/cpobc_publication_roadmap_v0.4-v0.7.md`
as the ordering authority, read
`reports/v0.4.2_post_literature_strategy_review.md` for the post-audit refocus,
`reports/v0.4.2_sr2v_principal_open_and_state_native_progress.md` for the
current SR2-V exact branch state, and use this handoff for exact operational
continuation:

```text
v0.3.9 strong/strong theorem        PUBLIC
v0.4 weak/weak rational witness     ON RESULT COMPLETE; OFF TRANSFER PENDING
v0.4-V observability strengthening  BOTTOM CSG CLASSIFIED; FIXED SLICES CLOSED;
                                    EQUAL-Q LOCUS WITNESS-FREE; S PARTLY CLASSIFIED; OPEN
SR3b-M minimal recovery lemmas       REQUIRED PAPER I MODULE; NOT A SHORT REPORT
v0.4.1 one-sided ON profiles        PROOF INTERPRETATION WITHDRAWN; BOTH OPEN
v0.4.2 profile-native repair        PURE-LOWER NO-GO CERTIFIED; MIXED OPEN
prior-art/related-work audit         COMPLETE; XU OVERLAP SCOPED
OFF 406-occurrence classification   OPEN SEPARATE COMPILER TRACK
Paper I assembly                    STATEWISE OBSERVABILITY/RECOVERY + SR3b-A
v0.5 genuine source-stage n=5       INDEPENDENT EXTENSION TRACK
```

### 2026-08-02 exact-gate continuation

This section controls older SR2-V “next step” wording later in the handoff.

- Bottom scalar MSR is complete: the 24 Laurent equations on `G_m^29` are
  globally the normalized finite-CSG principal open in four couplings times
  external `G_m(Q5)`. Verdict
  `SR2V_BOTTOM_MSR_GLOBAL_CSG_PARAMETERISATION_CERTIFIED_NONTERMINAL`, digest
  `d7978cac841bf725baa03df99aa661183a5c96367a2979b245b978f7d5dd08a4`.
- The former fixed harmonic alpha/beta chart is empty by the constant raw
  generator `2/117`. The D12 Q5/budget preflight remains valid provenance, but
  no solver may run on this slice.
- The corrected CSG-compatible selected fixed-`(h,k)` slice is nonsingularly
  empty by the exact two-row beta-localized unit identity. Verdict
  `SR2V_CORRECTED_CSG_FIXED_HK_NONSINGULAR_CPOBC_UNIT_IDEAL_OBSTRUCTION_CERTIFIED_NO_SOLVER_RUN`,
  digest `2b6c8483598cf73bbf9dd2365dd2c7828c10bc0aedb72c58a84c47142c215b7f`.
- That two-row mechanism is not generic in the variable harmonic family. The
  exact audit constructs another rank-two root-zero `k`, with all betas one,
  that solves the same two rows, and a rational section on the nonempty open
  where its coefficient determinant is nonzero. Its predecessor verdict is
  `SR2V_FIXED_K_TWO_ROW_OBSTRUCTION_ZARISKI_SPECIAL_CERTIFIED_NONTERMINAL`,
  digest `64a79807b4a19169517c5a9864b005c38a44593118987ed88e95dd2edb9cb84e`.
- The follow-up checks all 3,132 raw CPOBC entries at that escape and finds 911
  nonzero residuals. On the entire beta-one, two-alpha `Delta!=0` section, two
  extra rows force both alphas to zero and a `62 by 62` minor with determinant
  `2^192*3^9*977` forces the root-zero harmonic coordinate to zero. Hence this
  sparse section is a localized unit ideal. Verdict
  `SR2V_VARIABLE_HARMONIC_TWO_ALPHA_PRINCIPAL_OPEN_CPOBC_UNIT_IDEAL_CERTIFIED_NONTERMINAL`,
  digest `4c8a71689c69d4845344eb44e459b3a5256075188b1f2d71dabc5a7428235efe`.
- The transverse reducible cocycle fibre is split on four separate nonempty
  principal opens: derived/literal Eq. (113), each with strict/completed
  Eq. (139). The `1156 by 132` and `1162 by 132` branch matrices have exact
  ranks 131 on derived branches and 132 on literal branches. All 131 actual
  cocycles vanish, so `Q1,...,Q4` commute. The joint 1,187-row matrix is never
  used for branch inference. Verdict
  `SR2V_TRANSVERSE_ALL_FOUR_SEMANTIC_BRANCHES_Q1_Q4_SPLITTING_PRINCIPAL_OPENS_CERTIFIED_NONTERMINAL`,
  digest `07e60a4d6b029d3cf08efd3ef3aae14598a1614090d3809d764973065b35eaf0`.
- The transverse determinant-zero gate is now open from the inside. Determinant
  vanishing is not the witness condition: the six commutator coefficients are
  universally `x_j*(a_i-b_i)-x_i*(a_j-b_j)`, so a witness needs
  `rank[M;C]>rank M`, not `Delta=0`. The commuting subspace is
  `K_delta=ker C(delta_Q)`: it is `span(delta_Q)` only for nonzero `delta_Q` and
  all of `QQ^4` at zero. Thus the entire equal-`Q`-spectrum locus is witness-free;
  `beta=a-b` is a global
  conjugation coboundary that lies in the kernel wherever the upper character is
  itself a bottom character and never produces a witness. Four nonzero-`delta_Q`
  two-scalar points have rank 130 and kernel `span(beta,e_Q5)`, while a Q5-only
  point outside the full diagonal has `delta_Q=0`, rank 127 and a five-dimensional
  tangent kernel. Verdict
  `SR2V_TRANSVERSE_COMMUTATOR_KERNEL_COBOUNDARY_AND_NESTED_DEGENERACY_LOCI_CERTIFIED_NONTERMINAL`,
  v3 digest `da062443965d679dc936dd4263f150c6d413deea7f5425790d039e099c89ac30`.
  Do not restore the uncommitted v1 draft digest `37bcbb5b...`: it omitted the
  `delta_Q=0` exception and the Q5-only subfamily and was superseded before commit.
  The committed v2 digest `a61eaeec...` had correct point data but overstated
  four sampled scalars as whole punctured-line rank constancy; v3 corrects the
  wording without changing those data.
- The successor scalar-base/cover/ablation certificate proves that CPOBC alone
  has saturated scalar rank 83 and defines the common `G_m^49`; both Eq. (113)
  scalar readings are redundant and Eq. (139) scalar rows vanish. Source-native
  Eq. (120) reduces the six commutators globally to the minimal star
  `c12,c13,c14`, and locally to one row on each of `D(rk-r1)`, with a three-row
  equal-ratio nonunit remainder. Strict Eq. (139) controls completed by literal
  row inclusion, leaving two Eq. (113) readings crossed with four loci: eight
  obligations. Exact direct ablations show that fixed-vector GC and
  reachable-state MSR are each individually necessary for a universal
  transverse commutativity statement. The GC-ablation witness passes all 50
  source-reaching path-state MSR checks. Verdict
  `SR2V_TRANSVERSE_BASE_FOUR_CHART_REDUCTION_AND_GC_MSR_BLOCK_INDEPENDENCE_CERTIFIED_NONTERMINAL`,
  digest `005d9a5492bd379f5ac51d1d17b7d31df4acaa175fc9089ef4a138b761f23f6e`.
  A separate 960-evaluation exact scout found no full-profile escape; its input
  ledger is preserved in `reports/v0.4.2_sr2v_transverse_exact_scout_ledger.md`,
  but it remains bounded scout evidence, not a theorem.
- The proposed branch-independent elimination has now passed globally.  A
  fixed 127-by-127 minor of the non-`Q` columns uses 83 raw CPOBC rows, 20
  fixed-vector-GC rows, and all 24 reachable-state-MSR rows.  After five
  bottom-CSG zero edges are removed symbolically, its 554-edge safe support
  supergraph has a unique perfect matching.  The determinant is a single
  Laurent monomial in the upper `G_m^49` coordinates and already-localized
  bottom `lambda` factors, hence a unit on the full 54-dimensional transverse
  base.  No Eq. (113), Eq. (139), Eq. (120), or new principal open is used.
  Verdict `SR2V_TRANSVERSE_COMMON_CORE_GLOBAL_UNIT_MINOR_CERTIFIED_NONTERMINAL`,
  digest `59c73ef93bfc67fafb643223152ca49a6b4eb9b4a958fd8d0894c394aacf5f97`.
  The exact consequence is `rank(M0)>=127` everywhere and a lossless reduction
  to the five `Q` columns.  This is not yet a commutativity terminal.

The common-core Schur problem now has an exact fail-closed chart contract.
After the 127 non-`Q` columns are eliminated, source-native Eq. (120) splits
the base into `U2=D(g2)`, `U3=D(g3)`, `U4=D(g4)`, the aligned locus
`V(g2,g3,g4) intersect D(r1-1)`, and the automatically safe remainder
`r1=r2=r3=r4=1`. On each `Uk`, every Eq. (120) solution has
`x=delta*h+(b/b1)*w`; the target commutator is a unit times `gk*w`. Thus the
exact obligation is `e_w` membership in the localized Schur row module. On the
aligned locus the three targets `e_w2,e_w3,e_w4` must lie in the five-column
restriction module. The certificate retains `Q5`, proves that changing the
visible reference only rescales minors by units, and explicitly rejects both
an `AB` minor that ignores `Q5` and the inference `multivariate gcd 1 => unit
ideal`. Verdict `SR2V_TRANSVERSE_EQ120_SCHUR_CHART_OBLIGATIONS_CERTIFIED_NONTERMINAL`,
digest `56bc0f94aff5a87e109d3fd54e343ebe36076c889279c5740ed3e92c539048c8`.

Three four-row Schur scouts are rejected:
`{83,147,154,688}` fails five mixed/direction points, while
`{23,147,154,688}` passes that 81-point ledger but fails on the exact
hypersurface point `u13*u45-u44=0` with ranks `3/3/4`. At the latter point full
`M0` and all four branches remain `131/131` after all commutators, so it is not
a witness. The replacement `{23,31,147,688}` also passes the preceding 82
points but fails at the positive rational torus point
`(u12,u13,u15,u44,u45)=(1/2,1,1,1,2)`; its exact escape is `e_Q2`, while full
`M0` and every branch again remain `131/131`. None of these fixed-four sets may
be reused. Two proposed Eq. (120) repair pairs, `(32,120)` on `U2` and
`(424,544)` on `U3`, also have exact positive-rational chart-internal failures.
The alternative `(8,14)` repairs those two points, but all three pair minors
vanish simultaneously at `u=(1,1/2,1,2,2)`, where
`(g2,g3,g4)=(1/96,1/256,0)` and each restricted rank is `1/1/2`. Full `M0`
still remains `131/131`. Therefore only this three-minor subcover is rejected;
the Eq. (120) charts and the full common core remain open. Verdict
`SR2V_TRANSVERSE_EQ120_THREE_PAIR_MINOR_SUBCOVER_EXACTLY_REJECTED_FULL_M0_SURVIVES_NONTERMINAL`,
digest `dea028466f41a6a186fbcb09f7b5ba8a74d12834dc7f348d0a1f5f04abf4bcf7`.

The next exact operation is full-module saturation, not another fixed-pair
scout. Lazily Schur-reduce all `M0` rows through the certified matching DAG;
on `Uk`, form `(A_r,B_r,C_r)` and prove `e_w` membership directly, or compute
the syzygy image ideal `J=B(ker[A,C])` and certify `(J:gk^infinity)=R`. If a
syntactic audit proves the common-core `Q5` column zero, this simplifies to
`J=B(ker A)`. Use exponent-lattice HNF/SNF to remove spectator torus variables
before rational saturation. The aligned quotient is handled separately.
Only if common-core membership fails should work split into the eight
derived/literal strict obligations. On every route the
exact criterion remains `rank[M;C]=rank M`; `span(beta,e_Q5)` is not the invariant.
Run charts sequentially with one CAS worker. Checkpoint and leave the current
leaf explicitly open at aggregate RSS 7.5 GiB (worker 7.0 GiB), five million
live sparse terms, 60 minutes per non-aligned leaf, 90 minutes for aligned, or
split depth 6 / 64 leaves. A cap yields `WEAK_D2_OPEN_RESOURCE_LIMIT`, never a
noncommutative conclusion; preserve the unresolved ideal, monomial order, and
row-selection digest.
Alongside that, enlarge the state-native support beyond beta one and the two
retained alphas. The next genuine state cover remains the rank-two open in
`Gr(2,63)` (dimension 122), not another isolated `k`.

Focused reproduction:

```powershell
uv run pytest -q tests/final_theory/test_sr2v_additive_msr_laurent_v042.py
uv run pytest -q tests/final_theory/test_sr2v_bottom_msr_global_csg_v042.py
uv run pytest -q tests/final_theory/test_weak_d2_state_native_fixed_harmonic_cpobc_obstruction_v042.py
uv run pytest -q tests/final_theory/test_weak_d2_state_native_corrected_csg_rank2_v042.py
uv run pytest -q tests/final_theory/test_sr2v_variable_harmonic_two_row_audit_v042.py
uv run pytest -q tests/final_theory/test_sr2v_variable_harmonic_sparse_section_cpobc_v042.py
uv run pytest -q tests/final_theory/test_sr2v_transverse_cocycle_principal_open_v042.py
uv run pytest -q tests/final_theory/test_sr2v_transverse_determinant_zero_locus_v042.py
uv run pytest -q tests/final_theory/test_sr2v_transverse_base_cover_ablation_v042.py
uv run pytest -q tests/final_theory/test_sr2v_transverse_common_core_unit_minor_v042.py
uv run pytest -q tests/final_theory/test_sr2v_transverse_common_core_schur_scout_v042.py
uv run pytest -q tests/final_theory/test_sr2v_transverse_eq120_schur_chart_obligations_v042.py
uv run pytest -q tests/final_theory/test_sr2v_transverse_eq120_repair_pair_scout_v042.py
```

Do not begin `d=3` or an infinite lifting theorem in a way that bypasses the
SR2-V/SR3b-M and scoped Paper I gates. A scoped Paper I draft may begin without
full 955/721 closure or `n=5`; it must not claim complete classification.

## 2. Scientific state

### Closed

- Strong GC plus strong MSR, occurrence identification ON: finite nonsingular
  `d=2`, `n<=4` commutativity is proved by the public v0.3.9 baseline.
- Fixed-vector GC plus reachable-state MSR, occurrence identification ON: v0.4
  supplies a nonsingular exact rational noncommutative witness. Its reachable
  span is rank one and every Q commutator kills that ray, so it certifies
  algebraic separation but not reachable-visible noncommutativity.
- Strong GC plus reachable-state MSR on the proper reconstruction slice
  `P intersect image(Phi_U)`: `PROVED_PARTIAL_SLICE`; this is not closure of
  the general one-sided profile.
- This proper-slice theorem is the independent short report **SR3b-A**, with
  locked state `THEOREM_CERTIFIED / SHORT_REPORT_SLOT_CONFIRMED /
  PRIOR_ART_AUDIT_COMPLETE / DISTINCT_TECHNICAL_CONTRIBUTION_IDENTIFIED /
  DRAFT_RECOMMENDED / DEPOSIT_NOT_AUTHORIZED`; see
  `reports/v0.4.2_partial_slice_short_report_plan.md`.
- The targeted prior-art audit is complete through 2026-08-01. No same claim
  was found for the weak/weak exact rational witness or the SR3b-A
  reconstruction-slice theorem. This is a bounded-search result, not an
  absolute absence claim.
- Within the mixed 262-variable ansatz, the `x=0` pure-lower family has the
  bounded global no-go `V042_955_PURE_LOWER_TRIANGULAR_GLOBAL_NO_GO_PROVED`,
  independently certified by `V042_955_PURE_LOWER_ORACLE_CERTIFIED`. This is
  an SR3b auxiliary theorem, not closure of the general profile or a new short
  report.
- Within SR2-V, the aligned branch is nonlinearly closed on the nonempty
  principal open `Delta_align!=0`, and the two-character transitive-percolation
  transverse family splits on a second nonempty principal open. Their
  determinant-zero boundaries and other components remain open.
- The six nonzero Q-commutator pivots now give a complete four-way structural
  cover of Q-noncommutativity: pair-irreducible, triple-irreducible,
  transverse globally reducible, and aligned globally reducible. This is a
  branch cover, not a solution of the CPOBC equations.
- One exact harmonic state slice has a complete 262-parameter state-native
  edge-action chart, but its raw CPOBC ideal contains the constant `2/117`.
  The fixed-state relation variety is empty before any localization.
- Its D12 shear manifest and Q5/budget preflight are preserved as exact
  ambient/provenance artifacts. No solver has run or may now run on that empty
  fixed state slice.
- The two scalar monomial relation lattices are globally parameterized: the
  843-by-132 operator block is a split `G_m^49`, and the 1,163-by-132
  observed-bottom plus fixed-GC block is a split `G_m^29`. The 24 additive
  bottom-MSR equations are globally normalized finite CSG times external Q5.
  The upper character and cocycle fibres are not globally classified by that
  result; the separate four-branch theorem covers nonempty transverse opens.
- A corrected CSG-compatible selected fixed-`(h,k)` chart is also empty after
  beta localization, but the responsible two-row mechanism is Zariski-special
  in variable `k`. An exact rank-two escape and nonempty-open rational section
  solve those rows. The follow-up proves that escape fails 911 raw entries and
  that its full beta-one, two-alpha `Delta!=0` section is empty by an exact
  localized unit ideal. Variable betas and the other 129 alphas remain open.
- On four separately compiled transverse semantic branches, nonzero 131- or
  132-column minors force every actual upper-right cocycle to vanish. Thus
  `Q1,...,Q4` commute on each open.
- Nested loci inside and around those determinant-zero boundaries are now
  partially classified. The whole equal-`Q`-spectrum locus `delta_Q=0` is
  witness-free. Its full diagonal sublocus `a_e=b_e` (dimension 5) is therefore
  witness-free at every point; at three
  exact points its branch rank is 127 with kernel equal to the tangent space of
  the bottom scalar locus. The two-scalar locus, where the upper character is
  itself a bottom scalar locus point (dimension 10), always contains `beta=a-b`
  in its kernel; at four exact points with `delta_Q!=0` its branch rank is 130 and
  the kernel is exactly `span(beta,e_Q5)`, so those points carry no witness.
  Its six-dimensional same-couplings independent-Q5 subfamily has `delta_Q=0`
  and is witness-free throughout; one exact off-diagonal Q5-only point has rank
  127 and a five-dimensional tangent kernel. Rank constancy on these loci and
  witness freedom on the remaining nonzero-`delta_Q` part are not claimed.
  Splitting principal opens
  are also certified over non-normalized bottom characters for the first time.

### Open

- all naturally labelled 406-occurrence OFF profiles;
- direct OFF verification of the v0.4 orbit-constant witness transfer;
- both one-sided ON profiles in general nonsingular `GL_2`;
- a rank-two, stage/source-compatible reachable-visible weak/weak witness or a
  full-profile exact obstruction (`SR2-V`);
- globally minimal relation-ID forcing groups;
- `n>=5`, `d>=3`, singular systems, and finite-to-infinite lifting.

### Prior-art boundary now fixed

- Xu, arXiv:2607.26672v1 (submitted 2026-07-29), is the closest public CPOBC
  result. Its Theorem 29.12 is more general on the finite-dimensional
  self-adjoint slice and contains several two-dimensional triangular/extension
  rigidity statements. It leaves non-self-adjoint nonsingular transitions and
  state-only covariance open. Treat it as
  `STRICTLY_MORE_GENERAL_ON_SELF_ADJOINT_SLICE / ADJACENT_OVERALL`, never as a
  same weak-semantics claim.
- Surya's March 2024 Chengdu slides already display strong operator MSR and
  operator path/color independence. Novelty is exact classification and
  certification, not introduction of the strong semantics.
- The public v0.3.9 Zenodo record is dated 2026-07-31, two days after Xu v1.
  Do not make broad public-priority claims over self-adjoint/triangular CPOBC
  rigidity.
- The authority is
  `reports/v0.4.2_prior_art_and_related_work_audit.md`; detailed theorem/page
  notes are in
  `references/notes/v0.4.2_prior_art_related_work_2026-08-01.md`.
- Paper preservation is complete: 87 source records, 66 local PDFs, 14 new
  PDFs, regenerated text/hash manifest, and 66/66 SHA-256 matches at
  `Y:\universe-theory-lab-backup\references\papers\`.
- Backup policy: tracked programs and research documents rely on Git commit
  plus push and are not copied as an unpacked NAS worktree. The 512 expensive
  Git-ignored research artifacts are preserved as one immutable compressed
  snapshot; see `reports/cpobc_backup_policy_2026-08-01.md`. Never execute or
  extract it on the NAS; restore to local storage first.

### Mathematical commutativity tools to reuse

The recovery items below are registered in the roadmap as auxiliary module
**SR3b-M**; the commutator-pivot items are reusable SR2-V structure. This is
theorem/lemma material for Paper I, not another short report.

1. Split exact searches into common-invariant-line/simultaneously
   triangularizable and irreducible branches before heavy elimination.
2. For a residual space `R`, the minimal state-to-operator condition is
   injectivity of `D -> D Omega` on `R`; cyclicity alone is insufficient.
3. At a source in `d=2`, two linearly independent probe vectors killed by the
   same MSR residual force that residual to vanish, recovering strong MSR.
   Single-`Omega` GC gives only one state per source; global reachable rank two
   is not this multi-probe condition and does not automatically promote all
   source residuals.
4. The centralizer of one non-scalar `2 by 2` matrix is `F[I,A]`; proving all
   `Q_i` commute with one such `Q_k` is enough for full pairwise commutativity.
5. `det[A,B]=0` or simultaneous triangularizability does not imply
   commutativity; keep the nonzero square-zero commutator branch explicit.
6. A nonzero Q commutator has four exact branches under the invariants
   `det C`, `tr(C A_e)`, and `det(C Omega,Omega)`. Pair-irreducible no-go alone
   never closes the triple-irreducible branch; Q5 remains supplemental.
7. Reachable rank two is a separate state condition; do not infer it from an
   invariant-line normalization or from operator noncommutativity.

The independently reimplemented v0.4.1 triangular scout forces all six
commutators to zero in both one-sided cores inside its declared 132-variable
two-character family. It remains bounded evidence only.

The later 42-chart campaign is exact for its input ideals but does not supply
the intended arbitrary-`GL_2` one-sided theorems. Its direct/Q coordinates
were built under `PAPER_STRONG_OPERATOR_PROFILE`: Eq. (108) retains hidden
strong-MSR consequences and Eq. (112) retains hidden strong-GC consequences
before relation-family filtering. See
`reports/v0.4.1_scope_break_decision_packet.md` and
`reports/v0.4.1_reachable_msr_soundness_audit.md` (SHA-256
`48f2ef5e235ab1e6d4134474eea49ef14981cbd9ac118e7d8067bd9ed267a117`).

## 3. v0.4.1 inventory now frozen locally

The static compiler is
`src/universe_lab/final_theory/one_sided_d2_v041.py`. It binds ten source
artifacts and emits `results/v0.4.1_one_sided_inventory.json`.

Current exact inventory:

| object | count |
|---|---:|
| v0.3.7 Q5-free strong shared core | 976 |
| CPOBC + strong MSR sufficient core | 721 |
| CPOBC + strong GC sufficient core | 955 |
| ON quotient transition variables | 131 |
| OFF naturally labelled transition occurrences | 406 |

The 721/955 relation lists were intended as conservative sufficient no-go
cores, but the scope audit rejects that interpretation: their ambient
coordinates retain both strong-profile reductions. They are exact
restricted-locus ablations only. A surviving point would still not be a
profile counterexample until all source-level weak vector equalities and
supplemental gates were checked.

Static verdict:

```text
V041_INVENTORY_READY_ELIMINATION_NOT_RUN
semantic digest 5b09ebcb7be60fecc027e93e4277007c94d98573937038cd03a3a399a46af3c6
```

## 3a. v0.4.1 restricted-locus computation

The exact QQ campaign completed all 42 requests:

| profile | exact closed charts | core |
|---|---:|---:|
| fixed-vector GC + strong MSR | 21/21 | 721 relations |
| strong GC + reachable-state MSR | 21/21 | 955 relations |

There are 24 exact empty charts and 18 charts in which all noncommutativity
components generate unit ideals after complete localisation. There are no
survivors or unresolved charts. The campaign used 406.452 seconds, with a
maximum worker time of 47.281 seconds and maximum peak RSS of 349,569,024
bytes.

```text
WEAK_D2_ON_ONE_SIDED_COMMUTATIVITY_PROVED
campaign digest 6b4300485c23c485177584d8dd9afd8c77463e64ca55cf812eae9898b430382c
V041_ON_ONE_SIDED_QQ_INDEPENDENT_ORACLE_PASSED
oracle digest   48e3eea12ed6f7f8497260922d088e2efdeb6a14548451157517d307f1c1b4a3
```

See `reports/v0.4.1_on_semantics_lattice.md`.

The displayed machine verdict is retained as historical artifact content,
but its semantic interpretation is superseded. All 42 certificates declare
`semantic_profile=PAPER_STRONG_OPERATOR_PROFILE`; their emptiness proves only
commutativity on the corresponding strong-profile-derived restricted loci.

The live driver and oracle are now scope-corrected. Future manifest, campaign,
oracle, and certificate writes use separate `restricted_locus` paths and can
emit only restricted-locus verdicts. The old three JSON artifacts and all 42
certificate bytes are accepted only as explicitly withdrawn historical
arithmetic inputs and are pinned read-only by regression hashes. No Sage run
was needed for this correction.

The 955 source pullback audit independently matches 783 CPOBC equations to 83
identities plus 700 direct residuals, and the 320 strong-GC basis to 65
identities plus 255 direct residuals. It also binds all 165 transition
predicates and the four Q plus 22 B inverse sites to source nonsingularity.
The formerly missing chart-attachment gate is now closed source-natively:
six raw antichain CPOBC Eq. (103) instances plus source nonsingularity derive
the three `k=1` Eq. (120) identities without MSR, GC, Eq. (108), Eq. (112), or
stored B reductions. The independent audit then applies the `R_2`--`R_4`
partition and 21 exact QQ certificates, yielding `PROVED_PARTIAL_SLICE` with
semantic digest
`2d65ddeefdec9606b6680dce6a6a790fb30ff50dd8d552a01043b022a6c99839`.
The result covers only `P intersect image(Phi_U)`; the full 955 profile remains
open on `P minus image(Phi_U)`.

The mixed source-native ansatz `A_e=[[p_e,x_[e]],[y_[e],1]]` is now expanded
as a 262-variable sparse QQ manifest. Its verdict is
`V042_955_MIXED_SOURCE_NATIVE_SCALAR_MANIFEST_READY_NO_SOLVER_RUN`, semantic
digest `13dc6cc8ec89395ba86bc66c5d96e25f79ed8cc5bbf9c6cc2b6925d1256430f2`.
It contains 783 CPOBC, 320 strong-GC-basis, and 24 reachable-state-MSR vector
equations, plus all 165 determinant predicates. The `p1-0` operator residual
has a constant lower-right entry one, so the ansatz is uniformly in `N!=0`.
No solver ran and none of the old 21 chart ideals was reused.

The associated exact tangent scout has verdict
`V042_955_MIXED_XY_SCOUT_NO_WITNESS_OPEN`, semantic digest
`d7a4f6dba63d17cd1107ce173fb829a60af0bbf044bb02b7ccca262c70b029d5`
under schema v2.
At the diagonal point the upper block has rank 114/nullity 17, while the lower
CPOBC+reachable-MSR block has rank 131. Its full-rank QQ certificate selects
108 CPOBC rows and 23 reachable-MSR rows. Because the lower Jacobian is
independent of the upper-family `x` coordinates, the same obstruction holds
at every point of that family: its unique local branch has `y=0` and is
commuting.

Schema v2 also upgrades the `x=0` pure lower-triangular family from a tangent
observation to a bounded global theorem. Direct specialization checks all 783
CPOBC, 320 strong-GC, and 24 reachable-MSR equations are exactly linear in
the 131 `y` variables. The 108 CPOBC + 23 reachable-MSR QQ certificate has
rank 131, so the unique solution is `y=0`; all Q matrices are diagonal and
commute, while `D_p1=diag(0,1)` keeps the point in `N!=0`. The bounded verdict
is `V042_955_PURE_LOWER_TRIANGULAR_GLOBAL_NO_GO_PROVED`.

The independent module
`src/universe_lab/final_theory/source_native_955_pure_lower_oracle_v042.py`
re-extracts these equations from the nonlinear manifest without importing the
tangent rank implementation. It emits
`results/v0.4.2_955_pure_lower_oracle.json` with verdict
`V042_955_PURE_LOWER_ORACLE_CERTIFIED` and semantic digest
`809f1931c2274b0b57a3bdedf73ca1997a3115030af11437f6c1f1793c20f5ba`;
see `reports/v0.4.2_955_pure_lower_oracle.md`. This is an SR3b auxiliary
theorem, not a new short report, and the SR3b-A scope remains unchanged.

This is still not full mixed closure. Remote/disconnected `x!=0,y!=0`
components and the full 955 profile remain open.

## 4. Critical occurrence-semantics correction

Never describe the 165 entries of the v0.3.2 reduction map as 165 independent
OFF variables. They are Bell-pair-selected occurrence/alias records over 131
quotient orbits and do not cover the naturally labelled GC domain.

The coherent OFF universe is the v0.3.3 naturally labelled growth DAG:

- 50 labelled source nodes through source stage four;
- 406 labelled transition occurrences;
- labelled operator words, not quotient signatures.

OFF requires new labelled CPOBC, MSR, Eq. (113), and Eq. (139) lifts. The
current ON Q-level chart campaign cannot be used as an OFF classification.

## 5. Equation-family guards

- Eq. (113) derived `Q_n`: 25 relations.
- Eq. (113) literal `Q_(n+1)`: 25 relations.
- Eq. (139) printed-strict: 4 instances.
- Eq. (139) Eq. (145)-completed: 10 instances.

Keep all four inventories separate. Within the frozen strong profile, the
v0.3.7 Q5-free core omits the 25 Eq. (112)/(113) path relations; this is safe
for that strong-profile forward no-go proof but is not a one-sided result or a
redundancy theorem. A witness must pass the full supplemental gates.

## 6. Resource state

The owner approved `config/v0.4.1_budget.json` on 2026-08-01:

- 3,600 seconds per chart;
- 43,200 seconds total wall time;
- 8 GiB memory.

The inventory therefore reports
`HUMAN_BUDGET_PRESENT_ELIMINATION_NOT_RUN`. The same limits are the approved
default for later project campaigns; each campaign must still materialise and
bind its own versioned budget file. A deviation requires fresh approval. The
v0.4.1 Sage/Singular campaign has now completed under this budget. No finite
field run occurred.

## 7. Next work

The structured source-native inventory now covers 165 occurrences in 131 ON
orbits, all 24 timid slack recurrences, 783 CPOBC word equations, the 320-edge
strong-GC basis, and 48 principal-open `N!=0` patches. Its semantic digest is
`5baf2a4a0273c8f5d9c08d2436b2df1ef77eafad97a4532d444dc9a8e522e042`.
It recomputes 407 paths/87 endpoint trees/1,529 path pairs, and keeps Eq. (113)
25/25 and Eq. (139) 4/10 as separated fail-closed validation ledgers. It is not
an expanded scalar-polynomial solver manifest.

1. **Complete:** SR2-V now has a stage/source-compatible visibility domain,
   exact metrics, and a separate nonterminal baseline verdict.
2. **Complete:** the independent observability verifier rebuilt 407 paths and
   87 endpoint states without importing the original witness compiler. Its
   verdict is `SR2V_BASELINE_OBSERVABILITY_AUDIT_CERTIFIED`, semantic digest
   `73508f8ad94d97a3147cbd913d687f0b779c740b80a84a4836854053f6f01c62`;
   reachable rank is one and all six operator-nonzero commutators are invisible.
3. **Complete:** SR3b-M has verdict
   `SR3B_M_CONDITIONAL_RECOVERY_LEMMAS_CERTIFIED`, semantic digest
   `a742976ab7d955a66beb07f6efd06170cd3b2f320638b6a64c3292f6fcf5d735`.
   It certifies evaluation injectivity, same-residual two-probe recovery,
   global-span and cyclicity counterexamples, and the non-scalar centralizer
   endpoint. It closes neither one-sided profile.
4. **Bounded exact scouts complete; SR2-V remains open:** the 49-dimensional
   scalar exponent torus has rank 83 in 132 variables. A deterministic
   180-point rational campaign left no Q commutator free; verdict
   `SR2V_VISIBLE_TORUS_SCOUT_NO_WITNESS_OPEN`, digest
   `7ed0d5f8c3d67528bd6cb2853e8b8887479488453799a43b6645d87437ad028f`.
   The invariant-line-breaking subsystem has 1,187 rows, rank 131, and kernel
   only cutoff-external Q5. The full 528-variable Jacobian has rank 455/nullity
   73 but no in-scope lower-left or first-order visibility direction; verdict
   `SR2V_BASELINE_LOWER_TANGENT_VISIBILITY_OBSTRUCTED`, digest
   `d83afca2c460bad9e8d420e75ad60e1974f3419f0dd655bfc51821d6a02b5a92`.
   These are not SR2-V terminals; see
   `reports/v0.4.2_sr2v_visible_search.md`.
5. **Nonlinear aligned open complete:** the selected residuals factor exactly
   as `F=H y`; the stored determinant is nonzero, so `Delta_align!=0` forces
   `y=0`. This supersedes the phrase "first-order only" on that open, but not
   on `Delta_align=0` or disconnected components. Verdict
   `SR2V_ALIGNED_PRINCIPAL_OPEN_VISIBILITY_OBSTRUCTED`, digest
   `66ed68773f8023c0e84f18c48719dc5517cb3c43f8d5f87e25b3f9ddf01d6fa5`.
6. **Generic transverse splitting complete:** for two transitive-percolation
   diagonal characters, the same-character line commutes and the distinct
   character family has only the split coboundary extension on the nonempty
   open `Delta(r,s)!=0`, within `r*s*(1+r)*(1+s)!=0`. This is a
   `Q_1,...,Q_4` result; supplemental Q5 has its upper-right coordinate fixed
   to zero outside the 131-variable kernel. Verdict
   `SR2V_TRANSITIVE_EXTENSION_PRINCIPAL_OPEN_SPLITTING_CERTIFIED`, digest
   `5b3cf83ae5cd6338cfa07c1894bf5eab2f6cf8fe5870fd8fdc6911682b06d000`.
7. **Q-noncommutative branch cover complete:** six Q pairs and four exact
   branches per nonzero commutator cover the target. Verdict
   `SR2V_COMMUTATOR_PIVOT_BRANCH_COVER_CERTIFIED`, digest
   `100fefe528012254edcd66c7237ae5706dcb3bba6badbe75da170f68403b4032`.
8. **Original state-native chart classified:** one exact harmonic boundary slice
   gives 87 states, 131 actual edge actions, 262 affine parameters, and exact
   rank two while building in GC/MSR and reducing actual-edge
   nonsingularity to `beta_e!=0` (automatic only on the shear slice). Verdict
   `SR2V_STATE_NATIVE_RANK2_CHART_CERTIFIED`, digest
   `3bf3b56c97ef73fcce3ff089f5229191b9d1ade04e217706ac51abe11eaebe6c`.
   The later full alpha/beta audit proves this fixed-state relation variety
   empty by the constant `2/117`.
9. **First pair-irreducible manifest retained, solver cancelled:** the state-native
   shear D12 patch has 136 saturated coordinates, 9,345 scalar entries, and
   29,994 terms. The ambient open is exact and nonempty, but its fixed-state
   relation intersection is empty. Verdict
   `SR2V_STATE_NATIVE_SHEAR_D12_MANIFEST_CERTIFIED_NO_SOLVER_RUN`, digest
   `82cd51ddd29e5923b003c8cf8f75a5a26cf5a36edf68728ad58d298d3f573090`.
10. **Scalar lattice and bottom MSR complete:** the exact operator and observed-bottom
   monomial lattices have ranks 83 and 103, all nonzero Smith factors one, and
   primitive kernel ranks 49 and 29. Verdict
   `SR2V_SCALAR_LATTICE_SNF_CERTIFIED_NONTERMINAL`, digest
   `155ddfd5ec1b90765acbb0eccfaa66991fc2d98a44432055b5481b09a0de5eb9`.
   The 24 additive equations then give the global finite-CSG classification,
   digest `d7978cac841bf725baa03df99aa661183a5c96367a2979b245b978f7d5dd08a4`.
11. **State-native sparse section closed:** the original chart is empty before
    localization; the corrected selected fixed-`(h,k)` chart is empty after a
    two-row beta localization; the variable-`k` audit proves that mechanism
    Zariski-special; and its exact escape fails the full raw ledger. Two alpha
    killers plus a rank-62 minor prove the entire beta-one, two-alpha
    `Delta!=0` section empty.
12. **Four transverse semantic opens complete:** derived/literal Eq. (113) and
    strict/completed Eq. (139) are compiled as four different matrices. Each
    has a nonzero actual-transition splitting minor, so `Q1,...,Q4` commute on
    its own nonempty principal open. The old 1,187-row joint matrix is auxiliary
    only and cannot support a branch conclusion.
13. **Transverse commutator kernel and nested loci classified:** the witness
    condition is `rank[M;C]>rank M`, not `Delta=0`, and the commuting subspace is
    `K_delta=ker C(delta_Q)`. The entire `delta_Q=0` locus is witness-free. At
    three full-diagonal points the rank is 127 with bottom-tangent kernel; four
    nonzero-`delta_Q` two-scalar points have rank 130 and kernel
    `span(beta,e_Q5)`; and one Q5-only point has rank 127 and a larger tangent
    kernel. Verdict
    `SR2V_TRANSVERSE_COMMUTATOR_KERNEL_COBOUNDARY_AND_NESTED_DEGENERACY_LOCI_CERTIFIED_NONTERMINAL`,
    v3 digest `da062443965d679dc936dd4263f150c6d413deea7f5425790d039e099c89ac30`.
14. **Transverse base and minimal targets certified:** CPOBC alone defines the
    saturated `G_m^49` scalar base; strict Eq. (139) controls completed; and raw
    CPOBC Eq. (120) reduces six commutators to the globally minimal star of three.
    The nontrivial base is covered by three one-row opens plus one three-row
    equal-ratio locus. Both weak semantic blocks have exact ablation witnesses,
    and restoring the omitted block closes the rank escape at the same point.
    Verdict
    `SR2V_TRANSVERSE_BASE_FOUR_CHART_REDUCTION_AND_GC_MSR_BLOCK_INDEPENDENCE_CERTIFIED_NONTERMINAL`,
    digest `005d9a5492bd379f5ac51d1d17b7d31df4acaa175fc9089ef4a138b761f23f6e`.
15. **Current:** try the branch-independent common core first. Prove the frozen
    127-column matched minor is a Laurent unit, reduce to the Q Schur complement,
    and solve the four Eq. (120) loci. If this fails, retain derived/literal
    strict as eight separate obligations. Also enlarge the state-native search
    to variable betas or wider alpha support, then target `Delta_align=0` and
    triple-irreducible pivots. Numerical and finite-field points remain scouts
    until exact rational direct certification.
16. Only after the bounded SR2-V campaign reaches an allowed terminal, return
   to the remote/disconnected `x!=0,y!=0` 955 components. The first upper
   family, mixed tangent branch,
   and global `x=0` pure-lower family are already closed in their declared
   scopes; do not rerun them or report them as a full-profile no-go.
17. For 955, do **not** brute-force all 131 principal patches. First split the
   common-invariant-line and irreducible branches, construct a symmetry/orbit
   reduction, and exact-scout a small natural principal-open set. Permit a
   solver campaign only after its source coverage certificate and versioned
   budget artifact are available.
18. Restore the 20 Eq. (112)-eliminated generators for 721 after 955 reaches a
   terminal state, or use 721 as the fallback if 955 exhausts its budget. Keep
   the certified diagonal 721 escape point as a regression fixture.
19. Keep OFF, relation minimality, `n=5`, and `d=3` as separate downstream
   tracks. SR3b-A drafting may proceed in parallel under its existing scope and
   owner-gated deposit rule.

The initial v0.4.2 fail-closed namespace audit is reproducible via
`REPRODUCING_v0.4.2.md` and has semantic digest
`8718c6d9266486ec6df775bdd8027b5e64658451a0b3fd09b35498bb5faf5237`.
The subsequent exact lift audit supersedes its “mapping absent” diagnosis:
all three candidate source constraints have unique zero Q residuals. They are
not selectable nonzero direct relations, and no 701-relation campaign ran.

Unexpected stronger results may open a new roadmap branch when they have an
exact certificate, an independently checked scope statement, and a clearly
stated relation to SR3. If a foundational definition, source-stage lift, chart
cover, or exact solver pipeline fails in a way that threatens the project,
stop the affected campaign and prepare an owner decision packet: failing
artifact/command, smallest reproducer, affected claims, recoverable results,
alternatives, estimated repair cost, and a recommended decision.

## 8. Reproduction and validation

See `REPRODUCING_v0.4.1.md` and `REPRODUCING_v0.4.2.md`. The current mixed
milestone is guarded by:

CI now separates the mutable v0.4 tree from the byte-frozen public v0.3.9
release. The current lane runs `scripts/reproduce_v04.py` and excludes only
four release-relative wrappers; a separate lane checks out exact public commit
`cba86eae795e1e985c4ba1bcd3dabe4eb2773fab` with `fetch-depth: 0` and runs all
four there. The v0.3.8 bridge and v0.3.9 release manifest remain unchanged and
are hash-pinned by `test_ci_version_boundary_v04.py`. See
`reports/v0.4_ci_release_boundary_repair_2026-08-02.md`.

```powershell
uv run pytest -q tests/final_theory/test_source_native_955_mixed_manifest_v042.py
uv run pytest -q tests/final_theory/test_v042_955_mixed_xy_tangent_scout.py
uv run python -m universe_lab.final_theory.source_native_955_pure_lower_oracle_v042
uv run pytest -q tests/final_theory/test_source_native_955_pure_lower_oracle_v042.py
uv run python -m universe_lab.final_theory.weak_d2_observability_v042
uv run python -m universe_lab.final_theory.semantic_recovery_v042
uv run python -m universe_lab.final_theory.weak_d2_visible_torus_scout_v042
uv run python -m universe_lab.final_theory.weak_d2_visible_tangent_v042
uv run python -m universe_lab.final_theory.weak_d2_aligned_principal_open_v042
uv run python -m universe_lab.final_theory.weak_d2_transitive_extension_v042
uv run python -m universe_lab.final_theory.weak_d2_commutator_branching_v042
uv run python -m universe_lab.final_theory.weak_d2_state_native_rank2_v042
uv run python -m universe_lab.final_theory.weak_d2_state_native_shear_pair_open_v042
uv run python -m universe_lab.final_theory.sr2v_scalar_lattice_v042
uv run pytest -q tests/final_theory/test_weak_d2_observability_v042.py
uv run pytest -q tests/final_theory/test_semantic_recovery_v042.py
uv run pytest -q tests/final_theory/test_weak_d2_visible_torus_scout_v042.py
uv run pytest -q tests/final_theory/test_weak_d2_visible_tangent_v042.py
uv run pytest -q tests/final_theory/test_weak_d2_aligned_principal_open_v042.py
uv run pytest -q tests/final_theory/test_weak_d2_transitive_extension_v042.py
uv run pytest -q tests/final_theory/test_weak_d2_commutator_branching_v042.py
uv run pytest -q tests/final_theory/test_weak_d2_state_native_rank2_v042.py
uv run pytest -q tests/final_theory/test_weak_d2_state_native_shear_pair_open_v042.py
uv run pytest -q tests/final_theory/test_sr2v_scalar_lattice_v042.py
uv run pytest -q tests/final_theory/test_sr2v_transverse_determinant_zero_locus_v042.py
uv run pytest -q tests/final_theory/test_sr2v_transverse_base_cover_ablation_v042.py
uv run pytest -q tests/final_theory/test_sr2v_transverse_common_core_unit_minor_v042.py
uv run pytest -q tests/final_theory/test_sr2v_transverse_common_core_schur_scout_v042.py
uv run pytest -q tests/final_theory/test_sr2v_transverse_eq120_schur_chart_obligations_v042.py
uv run pytest -q tests/final_theory/test_sr2v_transverse_eq120_repair_pair_scout_v042.py
```

Expected focused results are manifest `5 passed`, 955 tangent schema v2
`8 passed`, independent pure-lower oracle `4 passed`, SR2-V baseline `6 passed`,
SR3b-M `14 passed`, the two original visible-search suites `9 passed`, and the
twelve latest exact-gate SR2-V suites `105 passed`. The tests
regenerate the stored exact payloads and preserve the `NO_SOLVER_RUN`,
bounded-family `GLOBAL_NO_GO`, and general mixed `NO_WITNESS_OPEN` boundaries.

The 2026-08-02 mutable-index resume suite, including the latest SR2-V
suites, the CI boundary guard, and all semantic escape guards reports
`196 passed` at its recorded checkpoint. The determinant/base-cover/unit-minor/
Schur-scout/chart-contract/repair-scout six-suite chain reports `54 passed`,
with Ruff and targeted mypy clean. An unfiltered local run
reports `598 passed`; its only 13 nonpasses are in the four historical wrappers
that the current CI lane intentionally excludes. The exact public-v0.3.9
checkout reports `25 passed` for its four release-boundary files, in addition
to a successful `scripts/reproduce_v039.py` replay.

The earlier broader validation snapshot (before the mixed-manifest/tangent
milestone above) was:

```text
v0.4--v0.4.2 targeted tests                     80 passed
upstream dependency regression tests            96 passed
ruff                                             passed
mypy                                             passed
```

The current-tree regression intentionally excludes four historical
reproduction wrappers whose frozen raw-byte bridges correctly reject the
post-v0.3.9 reference-manifest changes. This is not a mathematical or compiler
failure, and those bridges must not be rewritten. Their separate exact-public-
commit lane is now mandatory and verified. A future public v0.4 release needs
its own new bridge for intentional post-v0.3.9 files.

## 9. Invariants

- Exact characteristic-zero certificates carry proofs; floats and finite
  fields do not.
- A bounded ansatz is never promoted to arbitrary `GL_2`.
- No timed-out chart is called empty.
- Existing public/frozen artifacts are not overwritten.
- Source claims, independent derivations, and unresolved components remain
  separate.
- The NAS is cold backup only. Do not create an unpacked repository mirror or
  run/extract programs, solvers, tests, notebooks, builds, or archives there.
  Tracked code is protected by Git push; only versioned papers and expensive
  non-Git artifacts receive NAS backup.
- Before any SR3b-A/Paper I wording or deposit decision, follow the completed
  claim boundaries in `reports/v0.4.2_prior_art_and_related_work_audit.md`.
  Preserve later sources under `references/`, run a delta search from the
  2026-08-01 cutoff, and mirror validated PDFs by SHA-256 to
  `Y:\universe-theory-lab-backup\references\papers\`.
- No publication, deposit, tag, push, or correspondence occurs without fresh
  explicit approval.

## 10. Resume checklist

Before continuing this track:

1. read `KNOWLEDGE_BASE_v0.4.md`, `CURRENT_RESEARCH_STATE.json`, the current
   roadmap, and `reports/v0.4.2_post_literature_strategy_review.md`;
2. retain the recorded owner approval; the slice inclusion gate has passed,
   but keep Sage frozen until the global source-native assumption-ledger and
   coverage gates pass;
3. run the two focused semantic guards:
   `test_v041_reachable_msr_soundness.py` and
   `test_v042_source_to_q_lift.py`;
4. require an assumption ledger, source-profile coverage certificate, and
   versioned budget artifact before any solver campaign is accepted;
5. preserve the v0.4.1 certificates as restricted-locus evidence rather than
   rewriting their historical verdict strings.
6. run both semantic escape guards:
   `test_v041_reachable_msr_soundness.py` and
   `test_fixed_vector_gc_strong_msr_escape_v042.py`.
7. run `test_eq120_source_provenance_v042.py` and
   `test_v041_partial_slice_audit.py`; require `PROVED_PARTIAL_SLICE`, while
   preserving the explicit `P minus image(Phi_U)` boundary.
8. run `test_source_native_955_slack_compiler_v042.py`; accept its inventory
   verdict only as structured provenance, never as a solver or commutativity
   verdict.
9. run `test_source_native_955_n_nonzero_scout_v042.py`; its `OPEN` verdict
   excludes only the declared exact upper-triangular family.
10. run `test_source_native_955_mixed_manifest_v042.py`; require the exact
    262-variable 783/320/24 manifest and 165 determinant predicates, while
    preserving `NO_SOLVER_RUN` and the prohibition on old 21-ideal reuse.
11. run `test_v042_955_mixed_xy_tangent_scout.py`; require schema v2, upper
    rank/nullity 114/17, the lower 108+23 QQ rank-131 certificate, and bounded
    verdict `V042_955_PURE_LOWER_TRIANGULAR_GLOBAL_NO_GO_PROVED`. Preserve the
    OPEN boundary for remote/disconnected `x!=0,y!=0` components and full 955.
12. run `test_source_native_955_pure_lower_oracle_v042.py`; require independent
    exact re-extraction, verdict `V042_955_PURE_LOWER_ORACLE_CERTIFIED`, and
    semantic digest
    `809f1931c2274b0b57a3bdedf73ca1997a3115030af11437f6c1f1793c20f5ba`.
13. run the SR2-V/SR3b-M suites named in §8, including the principal-open,
    chart/lattice, global bottom-MSR, fixed-state obstruction, variable-`k`,
    sparse-section, four-branch transverse cocycle, and transverse
    determinant-zero stratum suites. Require the baseline
    rank-one audit, the conditional SR3b-M lemma boundary, the finite-torus
    `OPEN` boundary, and the rank-131 invariant-line-breaking tangent scope.
    Do not call either bounded negative result a reachable-visibility
    obstruction for arbitrary `GL_2`.
14. before drafting novelty, priority, or related-work claims, read
    `reports/v0.4.2_prior_art_and_related_work_audit.md` and its detailed
    reference note. Run only a delta search from 2026-08-01, preserving every
    material new source with exact version, retrieval date, lawful local copy,
    claim boundary, and NAS hash check.

Items 2--12 preserve the 955 regression boundary and are required when 955 is
resumed. They are not the immediate implementation order. The immediate order
is now: retain the completed baseline and SR3b-M; use the certified sparse-
section unit ideal, the four branch-separated transverse splitting opens and the
commutator-kernel/nested-locus certificate as regressions; decide whether the
`Q`-projection of `ker M` always lies in `K_delta=ker C(delta_Q)`; and widen the state-native
alpha/beta support before the aligned and triple-irreducible work.
Never run the old fixed-state D12/shear solver. Only after an SR2-V terminal
resume the 955 mixed locus. The frozen upper-family tangent search and generic
points in certified principal opens must not be repeated.
