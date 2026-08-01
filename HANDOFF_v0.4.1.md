# Handoff -- CPOBC v0.4/v0.4.1 research track

Written 2026-08-01. This is the live handoff for work after the public v0.3.9
release. The historical `HANDOFF.md` remains the frozen v0.3.9 record and is not
superseded as release provenance.

## 1. Governing roadmap

Start with `KNOWLEDGE_BASE_v0.4.md` for current scientific facts and reusable
proof rules. `CURRENT_RESEARCH_STATE.json` is the compact mutable index for
tools and future agents. Use `reports/cpobc_publication_roadmap_v0.4-v0.7.md`
as the ordering authority, read
`reports/v0.4.2_post_literature_strategy_review.md` for the post-audit refocus,
and use this handoff for exact operational continuation:

```text
v0.3.9 strong/strong theorem        PUBLIC
v0.4 weak/weak rational witness     ON RESULT COMPLETE; OFF TRANSFER PENDING
v0.4-V observability strengthening  NEW FIRST RESEARCH PRIORITY
SR3b-M minimal recovery lemmas       REQUIRED PAPER I MODULE; NOT A SHORT REPORT
v0.4.1 one-sided ON profiles        PROOF INTERPRETATION WITHDRAWN; BOTH OPEN
v0.4.2 profile-native repair        PURE-LOWER NO-GO CERTIFIED; MIXED OPEN
prior-art/related-work audit         COMPLETE; XU OVERLAP SCOPED
OFF 406-occurrence classification   OPEN SEPARATE COMPILER TRACK
Paper I assembly                    STATEWISE OBSERVABILITY/RECOVERY + SR3b-A
v0.5 genuine source-stage n=5       INDEPENDENT EXTENSION TRACK
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

These four items are registered in the roadmap as auxiliary module **SR3b-M**.
It is a theorem/lemma module for Paper I, not another short report.

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
5. **Current:** search disconnected transverse-reducible and irreducible
   weak/weak components. Do not repeat first-order perturbations of the frozen
   upper family. Require direct separated validation of both Eq. (113)
   branches and both Eq. (139) domains. Numerical and finite-field points are
   scouts until exact rational direct certification.
6. Only after the bounded SR2-V campaign reaches an allowed terminal, return
   to the remote/disconnected `x!=0,y!=0` 955 components. The first upper
   family, mixed tangent branch,
   and global `x=0` pure-lower family are already closed in their declared
   scopes; do not rerun them or report them as a full-profile no-go.
7. For 955, do **not** brute-force all 131 principal patches. First split the
   common-invariant-line and irreducible branches, construct a symmetry/orbit
   reduction, and exact-scout a small natural principal-open set. Permit a
   solver campaign only after its source coverage certificate and versioned
   budget artifact are available.
8. Restore the 20 Eq. (112)-eliminated generators for 721 after 955 reaches a
   terminal state, or use 721 as the fallback if 955 exhausts its budget. Keep
   the certified diagonal 721 escape point as a regression fixture.
9. Keep OFF, relation minimality, `n=5`, and `d=3` as separate downstream
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

```powershell
uv run pytest -q tests/final_theory/test_source_native_955_mixed_manifest_v042.py
uv run pytest -q tests/final_theory/test_v042_955_mixed_xy_tangent_scout.py
uv run python -m universe_lab.final_theory.source_native_955_pure_lower_oracle_v042
uv run pytest -q tests/final_theory/test_source_native_955_pure_lower_oracle_v042.py
uv run python -m universe_lab.final_theory.weak_d2_observability_v042
uv run python -m universe_lab.final_theory.semantic_recovery_v042
uv run python -m universe_lab.final_theory.weak_d2_visible_torus_scout_v042
uv run python -m universe_lab.final_theory.weak_d2_visible_tangent_v042
uv run pytest -q tests/final_theory/test_weak_d2_observability_v042.py
uv run pytest -q tests/final_theory/test_semantic_recovery_v042.py
uv run pytest -q tests/final_theory/test_weak_d2_visible_torus_scout_v042.py
uv run pytest -q tests/final_theory/test_weak_d2_visible_tangent_v042.py
```

Expected focused results are manifest `5 passed`, 955 tangent schema v2
`8 passed`, independent pure-lower oracle `4 passed`, SR2-V baseline `6 passed`,
SR3b-M `14 passed`, and the two visible-search suites `9 passed`. The tests
regenerate the stored exact payloads and preserve the `NO_SOLVER_RUN`,
bounded-family `GLOBAL_NO_GO`, and general mixed `NO_WITNESS_OPEN` boundaries.

The earlier broader validation snapshot (before the mixed-manifest/tangent
milestone above) was:

```text
v0.4--v0.4.2 targeted tests                     80 passed
upstream dependency regression tests            96 passed
ruff                                             passed
mypy                                             passed
```

The dependency regression intentionally excludes historical reproduction
wrappers whose frozen raw-byte bridges correctly reject the post-v0.3.9
reference-manifest changes. This is not a mathematical or compiler failure,
and those bridges must not be rewritten. No full historical suite is claimed
for v0.4.1; a later release needs its own bridge for intentional post-v0.3.9
files.

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
13. run the four SR2-V/SR3b-M focused suites named in §8. Require the baseline
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
is now: retain the completed SR2-V baseline, SR3b-M, torus, and tangent
artifacts; split the remaining weak/weak search into disconnected transverse
reducible and irreducible components; exact-scout a symmetry-reduced
commutator-determinant principal open; and only after an SR2-V terminal resume
the 955 mixed locus. The frozen upper-family tangent search must not be
repeated.
