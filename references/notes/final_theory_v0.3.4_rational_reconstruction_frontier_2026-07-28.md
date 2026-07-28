# Final-Theory v0.3.4 rational-reconstruction frontier (2026-07-28)

## Primary-source record

- The official record for arXiv:2603.25503 remained v1, submitted
  2026-03-26, when checked on 2026-07-28.  The arXiv record listed no
  journal reference or journal DOI.  Searches of the official arXiv author
  records, INSPIRE, and Crossref found no correction, erratum, or follow-up
  that resolves the finite-dimensional CPOBC representation problem.  This
  is a bounded search result, not proof that no such work exists anywhere.
- The target paper assumes nonsingular transition operators in the
  inverse-based CPOBC analysis.  Its displayed d=2 calculation starts from
  the Pauli-proportional family in Eq. (165), so its inconsistency result is
  not a classification of arbitrary invertible 2 by 2 matrices.
- PDF pages 26--27 contain Eqs. (103)--(114).  Eq. (112) compares
  atomisation paths through `Q_n`, while the literal Eq. (113) prints
  `[S_alpha^{-1} S_beta, Q_(n+1)] = 0`.  Appendix Eq. (163), on PDF page
  35, uses `Q_4` in the concrete `G_4` calculation.  The evidence therefore
  supports retaining two source-index branches and the verdict
  `SOURCE_INDEXING_DISCREPANCY_CANDIDATE`; it does not license silently
  correcting the paper.
- Lemma 3.10 on PDF page 31 assumes that one `Q_k` commutes with every
  `Q_n` in the full family.  Its commutative-collapse conclusion cannot be
  imported automatically from a calculation involving only
  `Q_1,...,Q_4`.
- PDF page 19 contains a sentence saying that transition operators “may
  not themselves be invertible”, although the immediately surrounding
  construction requires invertible transition operators and later formulas
  explicitly use their inverses.  This is recorded as a prose inconsistency,
  not as permission to include singular transitions in the audited profile.

## Literature-locked tools

- Cayley--Hamilton and the adjugate identity give, for a fixed 2 by 2 matrix
  over a commutative coefficient ring,
  `X^{-1} = adj(X)/det(X) = (tr(X) I - X)/det(X)` on the locus where
  `det(X)` is invertible.
- Florentino's 2 by 2 matrix-tuple results supply known simultaneous
  triangularisation, similarity, trace-invariant, and generic
  reconstruction tools.  They do not impose GC, MSR, or CPOBC and do not
  solve the project's polynomial systems.
- Volčič and Porat--Vinnikov supply general noncommutative rational
  realization theory.  Their objects and domains are not the same as the
  v0.3.4 fixed-d=2 rational matrix DAG over a commutative coordinate ring.
- The localisation and saturation references justify exact algebraic
  techniques, but not any project-specific nonzero denominator,
  saturation, unit-ideal, or completeness claim.

## Independent project boundary

The open target is the finite `n<=4`, fixed-d=2 reconstruction problem under
`PAPER_STRONG_OPERATOR_PROFILE`: determine which of the 22 inverse
auxiliaries are rationally definitional; prove the forward and reverse
equivalence of the reconstructed system; keep the `Q_n` and literal
`Q_(n+1)` source branches separate; and eliminate all S1/S2/S3 charts with
exact denominator predicates and certificates.

General matrix theory and general rational-realization theory are
`LITERATURE_LOCKED` or `FORMULATION_MISMATCH`, not new project results.
No audited external result supersedes the v0.3.4 task.  Until the finite
systems and their completeness gates are discharged, the only licensed
overall conclusion is `FINAL_THEORY_OPEN`.
