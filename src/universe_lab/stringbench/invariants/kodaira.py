"""A cautious subset of the Kodaira/Tate vanishing-order classifier."""

from __future__ import annotations

from dataclasses import dataclass

from universe_lab.stringbench.evidence import EvidenceState


@dataclass(frozen=True, slots=True)
class KodairaInference:
    fiber_type: str | None
    ade_type: str | None
    evidence_state: EvidenceState
    reason: str


def kodaira_euler_number(fiber_type: str) -> int:
    """Return the topological Euler number of a Kodaira fiber."""

    fixed = {
        "I0": 0,
        "II": 2,
        "III": 3,
        "IV": 4,
        "IV*": 8,
        "III*": 9,
        "II*": 10,
    }
    if fiber_type in fixed:
        return fixed[fiber_type]
    if fiber_type.startswith("I") and fiber_type.endswith("*"):
        index = fiber_type[1:-1]
        if index.isdigit():
            return int(index) + 6
    if fiber_type.startswith("I") and fiber_type[1:].isdigit():
        return int(fiber_type[1:])
    raise ValueError(f"unsupported Kodaira fiber: {fiber_type}")


def fiber_configuration_euler_sum(fibers: tuple[str, ...]) -> int:
    """Sum fiber Euler numbers; an elliptic K3 configuration must total 24."""

    return sum(kodaira_euler_number(fiber) for fiber in fibers)


def infer_kodaira_fiber(
    ord_f: int,
    ord_g: int,
    ord_delta: int,
    *,
    split: bool | None = None,
) -> KodairaInference:
    """Infer only cases fixed by the supplied orders.

    Split/non-split monodromy changes gauge algebras for several fiber types.
    The routine therefore refuses to invent an ADE algebra when ``split`` data
    are required but absent.
    """

    if min(ord_f, ord_g, ord_delta) < 0:
        raise ValueError("vanishing orders must be non-negative")
    if ord_f >= 4 and ord_g >= 6 and ord_delta >= 12:
        return KodairaInference(
            None,
            None,
            EvidenceState.BLOCKED,
            "non-minimal (4,6,12) locus requires resolution data",
        )
    exact = {
        (0, 0, 0): ("I0", None),
        (1, 1, 2): ("II", None),
        (1, 2, 3): ("III", "A1"),
        (2, 2, 4): ("IV", "A2" if split else None),
        (3, 4, 8): ("IV*", "E6" if split else None),
        (3, 5, 9): ("III*", "E7"),
        (4, 5, 10): ("II*", "E8"),
    }
    if (ord_f, ord_g, ord_delta) in exact:
        fiber, ade = exact[(ord_f, ord_g, ord_delta)]
        if fiber in {"IV", "IV*"} and split is None:
            return KodairaInference(
                fiber,
                None,
                EvidenceState.PARTIAL,
                "fiber type fixed, gauge algebra requires monodromy/splitting data",
            )
        return KodairaInference(fiber, ade, EvidenceState.EXACT_SYMBOLIC, "Kodaira table")
    if ord_f == 0 and ord_g == 0 and ord_delta >= 1:
        return KodairaInference(
            f"I{ord_delta}",
            f"A{ord_delta - 1}" if split else None,
            EvidenceState.EXACT_SYMBOLIC if split is not None else EvidenceState.PARTIAL,
            "multiplicative fiber; algebra depends on split/non-split data",
        )
    if ord_f >= 2 and ord_g >= 3 and ord_delta >= 6:
        n = ord_delta - 6
        return KodairaInference(
            f"I{n}*",
            f"D{n + 4}" if split else None,
            EvidenceState.EXACT_SYMBOLIC if split is not None else EvidenceState.PARTIAL,
            "star fiber; algebra depends on monodromy/splitting data",
        )
    return KodairaInference(
        None,
        None,
        EvidenceState.BLOCKED,
        "orders do not determine a supported minimal Kodaira case",
    )
