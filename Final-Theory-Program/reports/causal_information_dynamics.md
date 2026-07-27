# Causal-information dynamics v2

The candidate uses the sparse order-theoretic action

```text
S_theta =
  theta_link      * Delta(link_count)
+ theta_diamond   * Delta(diamond_count)
+ theta_precursor * |precursor|
```

implemented through exact rational fugacities `2/3`, `3/2`, and `4/5`.
The values are simple pre-registered rationals and are not fitted to held-out
observables.

For each unlabeled source, precursor down-sets are grouped into automorphism
orbits. Aggregate branch weight equals orbit multiplicity times local weight.
Dividing by the exact source sum produces a rational probability. The Kraus
coefficient is stored as the square root of that exact rational and multiplies
the matrix unit from the source history ray to the target history ray.

No Einstein–Hilbert, Fierz–Pauli, target dimension, Spin-2 pole, neural
black-box action, or held-out objective is present.

The candidate is explicit but branch-diagonal. It is not a newly discovered
noncommutative QSG representation.
