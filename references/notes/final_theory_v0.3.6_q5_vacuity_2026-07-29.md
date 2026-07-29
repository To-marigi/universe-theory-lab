# Final-Theory v0.3.6 Q5 vacuity and source-index audit (2026-07-29)

## Primary-source statements

- The archived arXiv:2603.25503v1 PDF was rendered and checked visually on
  pages 27--31. On page 27, Eq. (112) ends in
  `S_alpha Q_n S_alpha^{-1}`, while printed Eq. (113) is
  `[S_alpha^{-1} S_beta, Q_(n+1)] = 0`.
- Theorem 3.7 and Eq. (120), on PDF pages 27--28, give an all-stage
  CPOBC consequence
  `Q_n Q_k^{-1} Q_m = Q_m Q_k^{-1} Q_n` for the stated index conditions.
- Corollary 3.9 and Eq. (130), on PDF page 29, give the displayed
  `Q_1,Q_2` commutator relation.
- Eqs. (135) and (137), on PDF page 30, reconstruct the timid and
  precursor-cardinality-indexed antichain transition operators. Eq. (139) is
  a separate relation and genuinely contains `Q_(n+1)`.
- On PDF page 31, the paper substitutes `n=2` into Eq. (139); the resulting
  Eq. (145) explicitly contains `Q_3`. This confirms that the `n+1` in
  Eq. (139) is intentional.

## Independent project derivation

- Comparing two copies of Eq. (112) for paths alpha and beta gives
  `[S_alpha^{-1} S_beta,Q_n]=0` directly. There is no algebraic step from
  Eq. (112) to `Q_(n+1)`. This strongly suggests a typo in printed Eq. (113),
  but does not establish author intent.
- The frozen literal compiler has 1,001 matrix relations and 2,564 canonical
  scalar numerators. Its exact dependency census finds twelve numerators from
  three nonidentity Eq. (113) path records with Q5 dependency.
- Substituting the frozen witness values for Q1 through Q4 and retaining
  `Q5=[[a,b],[c,d]]` makes all twelve compiled canonical numerators the zero
  polynomial in `QQ[a,b,c,d]`. The other 2,552 numerators have no Q5
  dependency and remain zero at the fixed base point.
- In the direct operator DAG, the pre-Q5 word in each of the three relations
  reduces to `I` under the general scalar-chain hypotheses
  `Q2=lambda2 Q1`, `Q3=lambda3 Q1`, and `Q4=lambda4 Q1`. Thus each relation is
  `[I,Q5]=0`, conditionally giving the full `GL(2)` Q5 fiber over every frozen
  base solution on that locus.
- Exact symbolic substitution also makes every relevant Eq. (120), Eq. (130),
  and the three `n=4` Eq. (139) instances vanish for arbitrary Q5.
- After antichain transitions are reconstructed with Eqs. (135)/(137), the
  multiplicity-weighted MSR residual is the binomial identity
  `sum_{k=j}^n C(n,k)(-1)^(k-j)C(k,j)=delta_(j,n)`. A deliberately
  CPOBC-invalid invertible sample still has zero MSR residual for `n=1..5`;
  this reconstructed MSR is not an independent constraint.
- The rejected mechanical Q-index shifts remain invalid. No closure
  elimination, genuine stage-5 compiler, Sage run, Singular run, or budget
  file is needed for the vacuity proof.

## Implementation coverage and claim boundary

- The project's 25 `EQ112_PATH_CONSISTENCY` records implement Eq. (113)-shaped
  commutators. It preserves separate `Q_n` and literal `Q_(n+1)` branches and
  does not conflate them with Eq. (139).
- Eq. (139) is explicitly called only for the paper's `n=2` Eq. (145) inside
  a separate d=3 scaled-Heisenberg ansatz. General named n=3 and n=4 Eq. (139)
  records are not separately materialised in the frozen d=2 inventory. This is
  a coverage gap, even though the scalar-chain witness passes the n=4 forms.
- The polynomial Q5 ideal is zero after the frozen base substitution, but the
  ambient representation still requires `det(Q5) != 0`. The fiber is `GL(2)`,
  not all singular and nonsingular matrices indiscriminately.
- The result is finite (`d=2`, strong profile, frozen `n<=4`) and does not
  settle the weak profile or infinite QSG.

The licensed literal verdict is
`CPOBC_D2_LITERAL_BRANCH_VACUOUS_UNCONSTRAINED_GENERATOR`, with proof verdict
`LITERAL_Q5_UNCONSTRAINED`. The source classification stays
`SOURCE_AMBIGUITY`, and the global verdict remains `FINAL_THEORY_OPEN`.
