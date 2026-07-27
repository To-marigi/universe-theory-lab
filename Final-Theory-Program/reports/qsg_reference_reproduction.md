# QSG reference reproduction

Source: arXiv:2603.25503v1.

The benchmark independently checks with exact matrices:

- the inverse-commutator implication used at the base of the TOBC induction;
- the `n=2` NTOBC relation that rejects a noncommuting probe and accepts a
  commuting probe;
- the CPOBC three-distinct-Pauli obstruction;
- one two-Pauli atomization-path probe, constructed from equations 140, 141,
  150, 151, 159, 162, and 163, including exact invertibility checks.

All executed residuals are symbolic/rational; no floating tolerance is used.

The continuous-parameter elimination for every two-Pauli pattern in the paper's
appendix has not been independently completed. The result is therefore
`PARTIAL_EXACT_REPRODUCTION`, not
`QSG_REFERENCE_RESULTS_REPRODUCED`.
