# Final-Theory v0.4 weak-semantics research note — 2026-07-31

## Sources checked before new research

- Public project baseline: Zenodo record 21720863, v0.3.9, DOI
  `10.5281/zenodo.21720863`, published 2026-07-31 and linked to source
  commit `cba86eae795e1e985c4ba1bcd3dabe4eb2773fab`. The public API reports
  `final-theory-bench-v0.3.9.tar.gz`, 7,210,462 bytes, with checksum
  `md5:9d35096cea4b904190551d8034f5bbd0`.
- Primary external source: Srivastava and Surya,
  *Implementing Bell causality in Quantum Sequential Growth*,
  arXiv:2603.25503v1. The archived PDF SHA-256 remains
  `545c2c1a6a0ad046bcb41612a0d108030601992ccc9e3c9d472dec3d92cc89aa`.
- Existing local notes and frozen v0.3.1--v0.3.9 artifacts were searched
  before online verification.

`scripts/archive_references.py` was run after the catalog update. The plain
shell environment did not provide `pypdf`, so the required fallback
`--skip-text` mode refreshed hashes and metadata without re-extracting PDF
text. The existing extracted text was used only for search; equations and
page layout were checked against rendered PDF pages.

## Source claims and source ambiguities

The paper defines general covariance on the distinguished initial vector
and states MSR first on reachable states. Later manipulations use operator
equalities. The repository's earlier uniform strong-operator profile is
therefore a project strengthening, as already recorded by v0.3.3/v0.3.7.

Eq. (113) has two preserved source-index readings: the formula derived from
Eq. (112) uses `Q_n`, while printed Eq. (113) uses `Q_(n+1)`. They remain
separate in v0.4.

Eq. (139) has a second, independent source inconsistency. Page 30 prints
`m,k<n`, but page 31's Eq. (145) specialises Eq. (139) at `n=2` using
`A_2^(1)` and `A_2^(2)`. v0.4 therefore preserves a printed-strict domain
and an Eq. (145)-completed domain.

## Independent project derivation

For transition source stage `n`, precursor cardinality `w`, and maximal
precursor count `m`, define over `QQ`

`A_e=[[2^(w-m)/2^n, 4/2^n if w=0 else 0],[0,1]]`

and choose `omega=(1,0)^T`. The first diagonal entry is the normalized CSG
transition character with all couplings `t_j=1`. Direct exact enumeration
shows that fixed-vector GC and reachable-state MSR hold throughout the
frozen finite inventory. The gregarious matrices are

`Q_n=[[2^-n,4*2^-n],[0,1]]`,

so all six commutators among `Q_1,...,Q_4` are nonzero. The construction
also satisfies every frozen CPOBC equation and both Eq. (113) branches and
Eq. (139) domains as operator identities. All transition determinants are
nonzero.

This is a new project construction; it is not attributed to the source
paper or to the Zenodo v0.3.9 release.

## Scientific judgment and claim boundary

The construction settles the doubly weak profile negatively, with
occurrence identification both ON and OFF. It does not settle the two
one-sided profiles. Exact upper-triangular scouts found no counterexample
when exactly one of GC or MSR was promoted to an operator identity, but
those ranks are not a complete arbitrary-`GL_2` elimination.

Spanning/separating test-state conditions are recorded as sufficient
semantic recovery criteria. Whether strong GC alone or strong MSR alone is
necessary, and the globally smallest relation family forcing
commutativity, remain unresolved.

Inside the explicitly declared two-character upper-triangular scout, the
commutator quotient modulo CPOBC is one-dimensional. Any one of the strong
MSR constraints `msr:p1-0`, `msr:p2-0`, or `msr:p2-2` kills it, as do 168
individual strong-GC basis relations. This exact ansatz-local
cardinality-one result is useful for targeting later elimination, but it is
not evidence that one of those relations suffices for arbitrary invertible
2 by 2 matrices.

No elimination campaign was appropriate after an exact rational witness
passed the counterexample-first gate.
