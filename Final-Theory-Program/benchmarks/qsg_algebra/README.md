# QSG algebra benchmark

The benchmark separates:

- exact checks of necessary identities and Pauli obstructions from the cited
  QSG paper;
- a new bounded rational-matrix ansatz search in dimensions three and four;
- full representation certification, which is not yet achieved.

No small numerical residual is accepted; all executed relation checks use
SymPy exact arithmetic.
