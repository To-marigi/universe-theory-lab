# Period precision report

| case | bits | runtime seconds | max component radius |
| --- | --- | --- | --- |
| j4-standard | 128 | 5.751 | 1.550e-16 |
| j4-standard | 256 | 5.968 | 5.538e-55 |
| j4-standard | 512 | 6.908 | 4.007e-132 |
| j4-standard | 1024 | 7.296 | 3.663e-286 |
| j4-bfd | 128 | 5.919 | 2.038e-05 |
| j4-bfd | 256 | 5.947 | 4.746e-48 |
| j4-bfd | 512 | 6.518 | 7.326e-129 |
| j4-bfd | 1024 | 7.301 | 4.833e-283 |
| j4-alternate | 128 | 5.252 | 2.943e-10 |
| j4-alternate | 256 | 6.456 | 1.845e-44 |
| j4-alternate | 512 | 6.698 | 3.971e-127 |
| j4-alternate | 1024 | 8.228 | 1.916e-266 |
| j4-maximal | 128 | 5.177 | 2.185e-07 |
| j4-maximal | 256 | 5.469 | 7.315e-44 |
| j4-maximal | 512 | 6.198 | 6.006e-118 |
| j4-maximal | 1024 | 7.879 | 7.526e-281 |

The basis-invariant positive Hodge pairing has overlapping certified balls at
every adjacent precision. Integer marking certificates pass from 256 through
1024 bits for both pairs. The recorded 128-bit maximal failure demonstrates
that insufficient precision is rejected rather than silently rounded.
