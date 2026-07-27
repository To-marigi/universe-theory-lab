# String-Compiler Bench v0.3 research note

Date: 2026-07-28

## Source-backed statements

- arXiv:2205.08100v1 Equations (2.40), (2.43), and (2.44) identify the
  alternate residual polynomial `D(t)`, the maximal cubic, and the equality of
  the two discriminant loci called `J30`.
- Its Table 1 gives the four generic `J30=0` fiber confluences. The PDF page was
  rendered and visually inspected because text extraction reversed the apparent
  subscript/superscript order. The displayed discriminant group is
  `(Z/2Z)^3`, not `(Z/3Z)^2`.
- Equations (3.1)--(3.4) state the `J4=0` standard/base-fiber-dual birational
  relation and the alternate/maximal specialization.
- arXiv:2401.05131v2 describes the semi-numerical homology and certified-period
  algorithm implemented by `lefschetz-family`.

## Independently computed in this repository

- Three exact rational `J30=0` fixtures, including a held-out point, satisfy
  `Disc_t D = Disc_t d = 0` using separately implemented formulas.
- Each fixture has one generic double root, square-free residual factors, and
  excludes `a=0`, `J4=0`, `J6=0`, `Res(D,E)=0`, and the other named
  resultant confluences.
- Discriminant factorization of all four compiled Weierstrass presentations
  reproduces the source fiber configurations and Euler number 24.
- The external oracle reproduces rank-22 K3 homology, signature `(3,19)`,
  unimodular intersection form, certified period balls, and Hodge bilinear
  relations.
- On the `J4=0` slice, explicit rank-five integral marking matrices map the
  standard periods to the base-fiber-dual periods and the alternate periods to
  the maximal periods. Their Gram-form identities are checked exactly.

## Claim boundary

The numerical Neron-Severi recovery offered by the oracle is heuristic and is
not used as an exact source of fiber or Mordell-Weil data. The v0.3 computation
does not invert a generic period to `H_(2,2)`, construct a global Narain orbit,
or prove the full eight-dimensional duality. The strongest allowed scientific
status is `DUALITY_PARTIAL_STRONGER`.
