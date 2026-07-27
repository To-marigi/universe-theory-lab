# QSG representation search

Dimensions three and four were searched over ordered four-tuples drawn from a
six-matrix rational library: two diagonal matrices, upper and lower Jordan
matrices, a shifted cycle, and a shifted reversal.

Every test is exact. Commuting tuples are removed. Survivors of the implemented
CPOBC core relations are retained as search leads, but none has a full
transition-algebra, Markov-sum, covariance, Bell-family, irreducibility, and
extension certificate.

This search is finite and deliberately incomplete. Its only valid scientific
status is:

```text
QSG_SEARCH_INCONCLUSIVE
```

It does not justify `QSG_NO_REPRESENTATION_UP_TO_D`, and no survivor is labeled
`QSG_NONCOMMUTATIVE_REPRESENTATION_FOUND`.
