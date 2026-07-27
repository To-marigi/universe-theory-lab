# J30 source audit

- Oracle A: `J30 = Disc_t D(t)`, Equations (2.40) and (2.44).
- Oracle B: form the maximal cubic of Equation (2.43), divide its cubic
  discriminant by `J6^16`, then compute `Disc_t d(t)`.
- Table 1 supplies the target fiber configurations, Mordell-Weil data, lattice
  polarizations, and discriminant groups.

The two polynomial routes are separately implemented. Table entries are not
used to decide whether `Disc(D)` or `Disc(d)` vanishes.

Visual PDF audit: Table 1 displays `(Z/2Z)^3` on every J30 row. The extracted
text alone was ambiguous and was not trusted for this typography-sensitive fact.
