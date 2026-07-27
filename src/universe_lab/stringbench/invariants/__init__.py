"""Independent invariant calculations used by both duality frontends."""

from universe_lab.stringbench.invariants.kodaira import (
    fiber_configuration_euler_sum,
    infer_kodaira_fiber,
    kodaira_euler_number,
)
from universe_lab.stringbench.invariants.lattices import (
    LatticeInvariants,
    analyze_gram_matrix,
)
from universe_lab.stringbench.invariants.modular import (
    K3ModularInvariants,
    modular_invariants_from_quartic,
)
from universe_lab.stringbench.invariants.weierstrass import (
    cubic_discriminant,
    short_j_invariant,
    short_weierstrass_discriminant,
)

__all__ = [
    "K3ModularInvariants",
    "LatticeInvariants",
    "analyze_gram_matrix",
    "cubic_discriminant",
    "fiber_configuration_euler_sum",
    "infer_kodaira_fiber",
    "kodaira_euler_number",
    "modular_invariants_from_quartic",
    "short_j_invariant",
    "short_weierstrass_discriminant",
]
