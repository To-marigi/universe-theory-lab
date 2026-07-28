# Final-Theory v0.3.2 d=2 frontier note - 2026-07-28

## Primary-literature facts

The local PDF for Srivastava and Surya, arXiv:2603.25503v1, was checked
visually rather than relying on extracted text.  Equations (107), (108),
(112), and (114) occur on PDF page 27; Eq. (120) on page 28; Eqs. (129) and
(130) on page 29; and the Pauli-proportional choice Eq. (165) on page 35.
Equation (165) fixes each Q_n to one of two individual Pauli directions.  It
does not classify a general invertible 2x2 representation.

The paper assumes nonsingular transition operators in the algebraic
development used here.  All project statements and the finite-restriction
lemma retain that assumption.

## Independent project derivations

With R_n=Q_1^-1 Q_n, the k=1 instance of Eq. (120) gives pairwise commuting
R_2, R_3, R_4.  A symbolic adjugate identity certifies this without floating
point arithmetic.  The monomial family

`Q_1=q_1 sigma_x`, `Q_n=sigma_x diag(a_n,b_n)`

passes every admissible n<=4 instance of Eqs. (120), (129), and (130) and has
exact nonzero commutator branches.  This is evidence that the general d=2
frontier is not closed by the paper's Pauli-proportional ansatz.  It is only a
necessary-relation witness.

Paper Eqs. (107) and (108) reduce every one of the 165 finite transition
occurrences to 24 causet-indexed gregarious matrices.  All MSR constraints are
rewritten; three become free-word identities and twenty-one remain exact
constraints among the reduced generators.  This is a project derivation, not
a statement quoted from the paper.

## Unresolved boundary

Twenty of the 24 gregarious matrices are attached to non-antichain causets.
Reducing them further by Eq. (112) requires explicit atomisation paths and
operator-level GC identities.  The frozen v0.3.1 compiler records only
combinatorial GC endpoint provenance, not those operator equations.
Consequently the current reduced d=2 presentation has 96 scalar matrix-entry
variables before determinant saturation and gauge.  No S1, S2, or S3
elimination was executed, no representation or no-go was certified, and no
vector measure was constructed.

The defensible release token is `CPOBC_D2_PARTIAL`.
