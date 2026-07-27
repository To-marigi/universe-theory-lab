# Period oracle validation

The upstream Shioda K3 example was executed at 128 and 256 bits. Both runs
recovered:

- H2 rank 22;
- intersection signature `(3,19)` and determinant `-1`;
- a 1x22 certified period matrix;
- vanishing period pairings on the known trivial lattice;
- `omega.omega = 0` and `omega.conjugate(omega) > 0`.

All validation gates: `True`.
Numerical Neron-Severi recovery was not used as exact evidence.
