"""The sequential-growth family lies in the 955 core identically in its couplings.

The commutator span gate sampled four exact coupling choices and found each of
them to be an exact core solution.  This module removes the sampling.  Working
over the rational function field ``QQ(t_0,...,t_4)`` it certifies that the
classical sequential-growth assignment satisfies every CPOBC and strong-GC
matrix entry **identically in the couplings**, so the whole growth family -- not
four of its points -- lies in the core scheme.

Two identities are certified, both symbolically:

* the timid first-column identity ``p[timid] = 1 - sum(non-timid p)`` holds at
  every one of the 24 sources, which is what lets the growth characters be
  extended to a point of the chart at all;
* all 4,152 nonzero streamed core entries vanish as rational functions of ``t``.

Specialising ``t_k = 1`` must reproduce the 131 frozen growth characters, and the
run aborts if it does not.

Scope this does not extend: the growth assignment still fixes every ``A:*:11`` to
one, so the family sweeps the first diagonal entry and never the second.  The
limitation that gate 13 recorded is untouched, and a witness outcome off the
growth family remains possible.

The construction is undefined where a denominator ``lambda(n,0)`` vanishes or a
reachable-state product vanishes; those loci are emitted explicitly rather than
being silently avoided.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import sympy

from universe_lab.final_theory import source_native_955_commutator_span_v042 as span
from universe_lab.final_theory import source_native_955_slack_term_preflight_v042 as terms
from universe_lab.final_theory.causal_sets import maximal_elements_in_subset

SLACK_INVENTORY_PATH = span.SLACK_INVENTORY_PATH
MIXED_MANIFEST_PATH = span.MIXED_MANIFEST_PATH
REDUCTION_PATH = span.REDUCTION_PATH
COMMUTATOR_SPAN_PATH = span.RESULT_PATH
RESULT_PATH = "results/v0.4.2_955_growth_family_identity.json"

SCHEMA = "final-theory-v042-955-growth-family-identity-v1"
VERDICT = "V042_955_GROWTH_FAMILY_SOLVES_THE_CORE_IDENTICALLY_IN_THE_COUPLINGS_CERTIFIED"

COUPLING_COUNT = 5


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def _semantic_digest(payload: dict[str, Any]) -> str:
    semantic = {key: value for key, value in payload.items() if key != "semantic_digest_sha256"}
    return hashlib.sha256(_canonical_json(semantic).encode("utf-8")).hexdigest()


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _couplings() -> tuple[sympy.Symbol, ...]:
    return sympy.symbols(f"t0:{COUPLING_COUNT}")


def _lambda(upper: int, lower: int, couplings: tuple[sympy.Symbol, ...]) -> sympy.Expr:
    if not 0 <= lower <= upper:
        raise ValueError("lambda indices must satisfy 0 <= b <= a")
    return sympy.expand(
        sympy.Add(
            *(
                sympy.binomial(upper - lower, index - lower) * couplings[index]
                for index in range(lower, upper + 1)
            )
        )
    )


def _symbolic_characters(
    reduction: dict[str, Any], couplings: tuple[sympy.Symbol, ...]
) -> tuple[dict[str, sympy.Expr], set[sympy.Expr]]:
    characters: dict[str, sympy.Expr] = {}
    denominators: set[sympy.Expr] = set()
    for record in reduction["reduction_map"]:
        orbit = str(record["orbit_id"])
        relation = tuple(int(row) for row in record["source_relation_rows"])
        precursor = int(record["precursor_code"])
        denominator = _lambda(len(relation), 0, couplings)
        denominators.add(denominator)
        maximal_count = len(maximal_elements_in_subset(relation, precursor))
        value = sympy.cancel(
            _lambda(precursor.bit_count(), maximal_count, couplings) / denominator
        )
        previous = characters.setdefault(orbit, value)
        if sympy.cancel(previous - value) != 0:
            raise AssertionError(f"orbit {orbit} has two distinct symbolic characters")
    if len(characters) != 131:
        raise AssertionError("expected 131 ON orbit characters")
    return characters, denominators


def compile_growth_family_identity_v042(root: Path) -> dict[str, Any]:
    """Certify that the growth family solves the core identically in the couplings."""

    root = root.resolve()
    paths = {
        SLACK_INVENTORY_PATH: root / SLACK_INVENTORY_PATH,
        MIXED_MANIFEST_PATH: root / MIXED_MANIFEST_PATH,
        REDUCTION_PATH: root / REDUCTION_PATH,
        COMMUTATOR_SPAN_PATH: root / COMMUTATOR_SPAN_PATH,
    }
    slack = span._load(paths[SLACK_INVENTORY_PATH])
    mixed = span._load(paths[MIXED_MANIFEST_PATH])
    reduction = span._load(paths[REDUCTION_PATH])
    predecessor = span._load(paths[COMMUTATOR_SPAN_PATH])
    for name, artifact in (
        (SLACK_INVENTORY_PATH, slack),
        (MIXED_MANIFEST_PATH, mixed),
        (COMMUTATOR_SPAN_PATH, predecessor),
    ):
        if artifact.get("semantic_digest_sha256") != terms._semantic_digest(artifact):
            raise AssertionError(f"{name} is not at its frozen semantic digest")
    if predecessor.get("verdict") != span.GLOBAL_VERDICT:
        raise AssertionError("the commutator span predecessor is not at its certified verdict")

    couplings = _couplings()
    characters, denominators = _symbolic_characters(reduction, couplings)

    specialised = {
        orbit: sympy.nsimplify(value.subs(dict.fromkeys(couplings, 1)))
        for orbit, value in characters.items()
    }
    frozen = {
        orbit: sympy.Rational(str(value))
        for orbit, value in mixed["variables"]["CSG_diagonal_character"].items()
    }
    if specialised != frozen:
        raise AssertionError("setting every coupling to one does not reproduce the frozen values")

    names: list[str] = []
    matrices, _states, _expansion = terms._compile_matrices(slack, names)
    index_of = {name: index for index, name in enumerate(names)}
    representative_to_orbit = {
        str(record["representative_occurrence_id"]): str(record["orbit_id"])
        for record in slack["operator_namespace"]["orbit_inventory"]
    }
    character_of = {
        representative: characters[orbit]
        for representative, orbit in representative_to_orbit.items()
    }

    assignment: list[sympy.Expr] = [sympy.Integer(0)] * len(names)
    timid = {
        str(record["timid_orbit_representative"]) for record in slack["timid_slack_recurrences"]
    }
    for representative in sorted(set(matrices) - timid):
        assignment[index_of[f"A:{representative}:00"]] = character_of[representative]
        assignment[index_of[f"A:{representative}:11"]] = sympy.Integer(1)

    canonical_paths = {
        str(record["source_id"]): list(record["operator_word_later_on_left"])
        for record in slack["source_state_recurrence"]["canonical_paths"]
    }
    first_column_failures: list[str] = []
    reachable_products: set[sympy.Expr] = set()
    for record in slack["timid_slack_recurrences"]:
        source_id = str(record["source_id"])
        representative = str(record["timid_orbit_representative"])
        product = sympy.Integer(1)
        for symbol in canonical_paths[source_id]:
            product *= character_of[terms._operator(symbol)]
        product = sympy.cancel(product)
        reachable_products.add(product)
        base_first = sympy.Integer(1)
        base_second = sympy.Integer(1)
        for operator, coefficient in zip(
            record["non_timid_orbit_representatives"],
            record["non_timid_coefficients"],
            strict=True,
        ):
            base_first -= int(coefficient) * character_of[str(operator)]
            base_second -= int(coefficient)
        if sympy.cancel(character_of[representative] - base_first) != 0:
            first_column_failures.append(source_id)
        assignment[index_of[f"u:{source_id}:0"]] = sympy.Integer(0)
        assignment[index_of[f"u:{source_id}:1"]] = sympy.cancel((1 - base_second) / product)
    if first_column_failures:
        raise AssertionError(
            f"the timid first-column identity fails symbolically at {first_column_failures}"
        )

    ledger = terms.OperationLedger()
    block_counts: dict[str, int] = {}
    nonvanishing = 0
    streamed = 0
    for block, records in (
        ("CPOBC", slack["raw_source_system"]["CPOBC_equations"]),
        ("strong_GC", slack["raw_source_system"]["strong_GC_basis"]),
    ):
        count = 0
        for record in records:
            left = terms._word_matrix(record["lhs_source_word"], matrices, ledger)
            right = terms._word_matrix(record["rhs_source_word"], matrices, ledger)
            for row in range(2):
                for column in range(2):
                    residual = terms._add(
                        left[row][column], terms._scale(-1, right[row][column], ledger), ledger
                    )
                    if not residual:
                        continue
                    count += 1
                    streamed += 1
                    total = sympy.Integer(0)
                    for monomial, coefficient in residual.items():
                        value = sympy.Integer(coefficient)
                        for index in monomial:
                            value *= assignment[index]
                        total += value
                    if sympy.cancel(total) != 0:
                        nonvanishing += 1
        block_counts[block] = count
    if nonvanishing:
        raise AssertionError(
            f"{nonvanishing} core entries do not vanish identically in the couplings"
        )

    coupling_denominators = sorted(str(sympy.factor(value)) for value in denominators)
    product_numerators = sorted(
        {
            str(sympy.factor(sympy.numer(sympy.cancel(value))))
            for value in reachable_products
            if sympy.cancel(value) != 1
        }
    )

    payload: dict[str, Any] = {
        "schema_version": SCHEMA,
        "profile": "strong_GC__reachable_state_MSR",
        "scope": {
            "finite_source_stages": "n<=4",
            "dimension": 2,
            "field": "QQ(t_0,...,t_4)",
            "identification_mode": "ON_QUOTIENT",
            "chart": "unrestricted 476-coordinate source-native slack chart",
        },
        "source_artifact_sha256": {path: _sha256(value) for path, value in paths.items()},
        "predecessor_binding": {
            "kind": "CANONICAL_JSON_SEMANTIC_DIGEST",
            COMMUTATOR_SPAN_PATH: predecessor["semantic_digest_sha256"],
            SLACK_INVENTORY_PATH: slack["semantic_digest_sha256"],
            MIXED_MANIFEST_PATH: mixed["semantic_digest_sha256"],
        },
        "upgrade_over_the_predecessor": (
            "The span gate verified four sampled couplings.  This removes the sampling: the "
            "growth family satisfies the core identically in t, so every non-degenerate "
            "coupling gives a point of the scalar variety."
        ),
        "symbolic_characters": {
            "orbits": len(characters),
            "distinct_values": len({sympy.srepr(value) for value in characters.values()}),
            "specialisation_at_all_ones_reproduces_frozen_values": True,
            "values_sha256": _digest(
                {orbit: str(value) for orbit, value in sorted(characters.items())}
            ),
        },
        "timid_first_column_identity": {
            "statement": "p[timid] = 1 - sum(non-timid p) at every source",
            "sources_checked": len(slack["timid_slack_recurrences"]),
            "symbolic_failures": 0,
            "role": (
                "This identity is what allows the growth characters to extend to a point of "
                "the chart at all; it is verified in t, not at a sampled coupling."
            ),
        },
        "core_identity": {
            "field": "QQ(t_0,...,t_4)",
            "streamed_nonzero_entries": streamed,
            "per_block": block_counts,
            "entries_not_vanishing_identically": nonvanishing,
            "second_diagonal_value": "every A:*:11 is fixed to 1 by the growth assignment",
        },
        "excluded_locus": {
            "reason": (
                "The construction is undefined where a coupling denominator or a "
                "reachable-state product vanishes."
            ),
            "coupling_denominators_required_nonzero": coupling_denominators,
            "reachable_product_numerators_required_nonzero": product_numerators,
            "count": len(coupling_denominators) + len(product_numerators),
        },
        "claim_boundary": [
            "This places the growth family inside the core; it decides no commutator question.",
            "Every A:*:11 stays one, so the second diagonal is still never varied and the gate "
            "13 limitation is untouched.",
            "A witness outcome off the growth family remains possible.",
            "The growth family is a small part of the scalar variety S, not all of it.",
            "No statement about the mixed locus or the unrestricted profile follows.",
        ],
        "solver_status": {
            "symbolic_rational_function_runs": 1,
            "Groebner_or_saturation_runs": 0,
            "finite_field_runs": 0,
            "numerical_runs": 0,
            "Sage_runs": 0,
            "solver_run": False,
        },
        "unrestricted_source_native_955_status": "OPEN",
        "commutativity_proved_for_full_profile": False,
        "witness_certified": False,
        "search_terminal": False,
        "passed": True,
        "verdict": VERDICT,
    }
    payload["semantic_digest_sha256"] = _semantic_digest(payload)
    return payload


def write_growth_family_identity_v042(root: Path) -> Path:
    payload = compile_growth_family_identity_v042(root)
    destination = root / RESULT_PATH
    destination.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return destination


if __name__ == "__main__":
    repository_root = Path(__file__).resolve().parents[3]
    print(write_growth_family_identity_v042(repository_root))
