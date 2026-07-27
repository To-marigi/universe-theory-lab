# Source audit

## Audited primary sources

The constructor used the TeX source of:

- Adrian Clingher, Thomas Hill, and Andreas Malmendier, *The duality between
  F-theory and the Heterotic String in D=8 with two Wilson lines*,
  [arXiv:2205.08100v1](https://arxiv.org/abs/2205.08100v1).
- Adrian Clingher, Thomas Hill, and Andreas Malmendier, *Jacobian elliptic
  fibrations on the generalized Inose quartic of Picard rank sixteen*,
  [arXiv:1908.09578](https://arxiv.org/abs/1908.09578). This is the mathematical
  classification source cited as CHM19 by the main paper. Its abstract and
  current version record independently confirm the “exactly four” result.

The main paper's arXiv source was inspected directly rather than relying on its
abstract. The following transcription map is used in the implementation:

| Implemented object | Primary locator | Evidence state |
| --- | --- | --- |
| Quartic validity exclusions | paragraph after Eq. (2) | FORMALLY_DERIVED |
| Four-fibration classification | Section 2.1; CHM19 Prop. 2.3 and Thm. 3.6 | PROVEN |
| Standard `f`, `g`, discriminant convention | Eqs. (4)-(7) | EXACT_SYMBOLIC |
| Alternate `A`, `B`, discriminant | Eqs. (8)-(11) | EXACT_SYMBOLIC |
| Base-fiber-dual `F`, `G`, discriminant | Eqs. (12)-(15) | EXACT_SYMBOLIC |
| Maximal `a`, `b`, `c`, discriminant | Eqs. (16)-(18) | EXACT_SYMBOLIC |
| Generic Kodaira fibers and Mordell-Weil groups | paragraphs after Eqs. (7), (11), (15), (18) | FORMALLY_DERIVED |
| Modular combinations `J2,...,J6` | Theorem 2.1 and Eq. (25) | FORMALLY_DERIVED |
| Open moduli domain in `WP(2,3,4,5,6)` | Eqs. (26)-(27) | PROVEN |
| Narain lattice and quotient | Eqs. (37)-(42) | FORMALLY_DERIVED |
| F-theory/heterotic branch statements | Propositions 4.1-4.4 | FORMALLY_DERIVED |

## Convention audit

The paper writes

`Delta = 4 f^3 + 27 g^2`

for a short Weierstrass equation. The conventional polynomial discriminant is
`-16` times this expression. The implementation names the paper convention
explicitly and documents that the zero locus and vanishing orders are
unchanged.

The `J_k` subscripts and their modular weights differ by a factor of two:
`J2,...,J6` have weights `4,6,8,10,12`, while the coarse moduli space is written
as `WP(2,3,4,5,6)`. Both are stored; they are not conflated.

The Kodaira classifier does not infer a gauge algebra from `I_n`, `I_n*`, `IV`,
or `IV*` without split/monodromy information. ADE labels quoted for the four
generic fibrations remain source-backed atlas data, separate from order-only
inference.

## What was not promoted to an exact compiler claim

- The paper describes the duality via period points and modular forms, but it
  does not give a table of explicit Wilson vectors in the frontend's
  `E8 + E8` basis for every one of the four branches.
- The `Spin(32)/Z2` gauge lattice is not implemented as a root-basis frontend.
- A general algorithm for period integration and reduction modulo
  `O(2,18;Z)` is not implemented.
- Global gauge-group form is not reconstructed automatically from local
  Kodaira and Mordell-Weil data.
- Enhancement-locus tables in the source are curated as evidence, not used as
  hidden production-code answers.

Consequently, the constructor supports exact symbolic F-theory models and an
independent heterotic lattice/root primitive for caller-supplied `E8 + E8`
Wilson vectors. It does **not** certify a physical F-theory/heterotic round trip
by itself.
