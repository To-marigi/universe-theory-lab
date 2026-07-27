# J4 standard / base-fiber-dual period certificate

The exact map `(t,X,Y) -> (1/t,X/t^4,-Y/t^6)` sends Equation (3.2) to
Equation (3.1), is involutive, and preserves `dt wedge dX/Y`.

At 256 bits the independently obtained rank-five transcendental bases are
related by:

```text
M = [[0, 0, -1, 0, -1], [1, -1, 0, 0, -1], [0, -1, -1, 1, -1], [-1, 1, 0, -1, 0], [0, 0, 0, 0, -1]]
det(M) = 1
```

The equality `M Q_std M^T = Q_bfd` is exact over the integers. All five mapped
period balls overlap. Equivalent certificates were independently recovered at
128, 512, and 1024 bits.

Status: `PERIOD_J4_SLICE_PASS` for this pair.
