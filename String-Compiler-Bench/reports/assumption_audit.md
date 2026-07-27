# Constructor assumption audit

## Encoded assumptions

1. Calculations take place over characteristic zero.
2. The quartic parameters satisfy `(gamma,delta) != (0,0)` and
   `(epsilon,zeta) != (0,0)` so that the minimal resolution belongs to the
   stated K3 family.
3. Generic singular-fiber lists exclude the enhancement and confluence loci
   tabulated in the source.
4. Symbolic expressions use the source's coordinates and normalization.
5. Lattice signatures are reported as `(positive, negative, zero)`.
6. The `E8 + E8` heterotic root frontend receives Wilson lines in the standard
   16-dimensional orthonormal root realization.
7. A heterotic root survives a pair of Wilson holonomies when its inner
   product with each supplied Wilson vector is integral.
8. Equality of raw `tau`, `rho`, or Wilson coordinates is not treated as a
   duality invariant because the Narain quotient mixes them.

## Explicitly rejected assumptions

- Four algebraically inequivalent fibrations are not assumed to define one
  coordinate-identical heterotic background.
- A Kodaira fiber type is not automatically equated with a unique gauge group.
- Trivial Mordell-Weil rank does not by itself prove a global gauge-group form.
- Mordell-Weil torsion is retained and is never discarded as irrelevant
  metadata.
- Numerical agreement is not described as an analytic proof.
- The source's branch labels are not used as an oracle inside discriminant,
  lattice, root-survival, or modular-invariant calculations.
- A formal type-safe `DualityLinkCertificate` is not evidence that physical
  duality has been established.
- The source's statement about quantum-exact effective interactions is not
  generalized beyond its stated moduli subspace.

## Open or blocked assumptions

| Item | Status | Reason |
| --- | --- | --- |
| Explicit period map for arbitrary input coefficients | BLOCKED | Requires period integration and marking data |
| Fibration branch to explicit Wilson vectors | BLOCKED | No compiler-ready vector table in the primary source |
| `Spin(32)/Z2` root frontend | BLOCKED | Not implemented in v0.1 constructor |
| Dynkin decomposition from surviving roots | PARTIAL | Root set is computed; classification is not |
| Split/non-split monodromy | PARTIAL | Must be supplied or computed from additional local data |
| Global gauge-group reconstruction | PARTIAL | Requires more than local ADE data |
| Full physical round trip | BLOCKED | Depends on the preceding maps and branch data |

## Failure behavior

Inputs outside the quartic validity exclusions return `BLOCKED`. Unsupported
Kodaira order triples return `BLOCKED`; cases whose fiber is fixed but algebra
depends on monodromy return `PARTIAL`. Cross-frame `UniverseTagged` values
cannot be compared without a certificate identifier allowed by both values.
