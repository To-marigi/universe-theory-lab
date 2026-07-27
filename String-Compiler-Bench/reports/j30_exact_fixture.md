# J30 exact fixtures

| role | J2 | J3 | J4 | J5 | J6 | double root |
| --- | --- | --- | --- | --- | --- | --- |
| training | 1 | 2 | 3 | 6 | 12 | 1 |
| validation | 1 | -1 | 4 | -2 | -16 | 2 |
| held_out | 3 | 1 | 2 | -20 | 48 | -2 |

For every point, exact arithmetic proves `Disc(D)=Disc(d)=0`, both gcds have
degree one, the residual quartic/sextic is square-free, and `a`, `J4`, `J6`,
`Res(D,E)`, and the other named resultants are nonzero.

Training example:

- `D(t) = (t - 1)**2*(t**4 + 2*t**3 - 3*t**2 - 16*t - 32)`
- `d(t) = -108*(t - 12)**2*(t + 36)*(t**5 + 72*t**4 + 1188*t**3 - 27216*t**2 - 419904*t + 17356032)`

Status: `J30_EXACT_LOCUS_PASS`.
