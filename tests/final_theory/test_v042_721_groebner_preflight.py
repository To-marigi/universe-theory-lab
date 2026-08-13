from __future__ import annotations

import sys
from pathlib import Path

import sympy

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from probe_v042_721_groebner_preflight_worker import (  # noqa: E402
    _relation_polys,
    _scalars_to_sympy,
)


def test_cache_monomial_keys_are_decoded_as_tokens_not_characters() -> None:
    units = [
        {
            "entries": [
                {
                    "row": 0,
                    "column": 0,
                    "scalar": {"M_A_00|M_B_11": 1, "M_C_01": -1},
                }
            ]
        }
    ]

    polynomials, variables = _scalars_to_sympy(units)

    assert variables == {"M_A_00", "M_B_11", "M_C_01"}
    assert polynomials == [
        sympy.Symbol("M_A_00") * sympy.Symbol("M_B_11")
        - sympy.Symbol("M_C_01")
    ]


def test_any_inverse_relation_variable_activates_the_full_relation() -> None:
    relations = _relation_polys({"M_Q_2_01"})

    assert len(relations) == 1
    assert str(relations[0]) == (
        "D_Q_2*(M_Q_2_00*M_Q_2_11 - M_Q_2_01*M_Q_2_10) - 1"
    )
