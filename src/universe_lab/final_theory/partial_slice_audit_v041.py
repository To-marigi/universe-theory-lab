"""Fail-closed audit of the valid v0.4.1 strong-GC partial slice.

This module does not run Sage and does not import either v0.4.1 elimination
driver.  It independently rewrites the frozen source CPOBC and strong-GC
word relations through the frozen occurrence reconstruction, checks the
700+255 direct relation ledger, and binds the resulting locus to the exact
QQ chart certificates.

The proved inclusion has source-space direction

    P_sg+rMSR^ns intersection image(Phi_U)  subset  Phi(D_955),

where ``U`` is the domain of the frozen rational reconstruction and
``D_955`` is its 700-CPOBC plus 255-local-GC direct zero locus.  No claim is
made about source points outside ``image(Phi_U)``.
"""

from __future__ import annotations

import hashlib
import itertools
import json
from collections import Counter
from pathlib import Path
from typing import Any

SCHEMA = "final-theory-v041-strong-gc-partial-slice-audit-v0.4.1"
VERDICT_PROVED = "PROVED_PARTIAL_SLICE"
VERDICT_INVALID = "INVALID"
VERDICT_UNRESOLVED = "UNRESOLVED_MISSING_PROVENANCE"

SOURCE_CPOBC_PATH = "results/v0.3.1_cpobc_relations_n4.json"
REDUCTION_PATH = "results/v0.3.2_cpobc_generator_reduction.json"
LOCAL_GC_PATH = "results/v0.3.3_local_operator_gc_n4.json"
Q_PRESENTATION_PATH = "results/v0.3.3_q_only_presentation_n4.json"
CLASSIFICATION_PATH = "results/v0.3.2_cpobc_d2_classification.json"
DIRECT_PATH = "certificates/d2_saturation/v0.3.5_direct_operator_system.json"
INVENTORY_PATH = "results/v0.4.1_one_sided_inventory.json"
MANIFEST_PATH = "results/v0.4.1_one_sided_elimination_manifest.json"
CAMPAIGN_PATH = "results/v0.4.1_one_sided_elimination.json"
ORACLE_PATH = "results/v0.4.1_one_sided_elimination_oracle.json"
EQ120_PROVENANCE_PATH = "results/v0.4.2_eq120_source_provenance.json"
RESULT_PATH = "results/v0.4.1_partial_slice_audit.json"

EQ120_PROVENANCE_SCHEMA = "final-theory-v042-eq120-source-provenance-certificate-v0.4.2"

PROFILE = "strong_GC__reachable_state_MSR"
DIRECT_BRANCH = "LITERAL_PRINTED_QN_PLUS_1_BRANCH"
CHART_BRANCH = "DERIVED_APPENDIX_QN_BRANCH"

Word = tuple[str, ...]
Expression = dict[Word, int]


class MissingProvenance(RuntimeError):
    """A required map or certificate is absent."""


class InvalidEvidence(RuntimeError):
    """Present evidence contradicts its required binding."""


def _canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    )


def _stable_hash(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _load(root: Path, relative_path: str) -> dict[str, Any]:
    path = root / relative_path
    if not path.is_file():
        raise MissingProvenance(f"required artifact is absent: {relative_path}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise InvalidEvidence(f"cannot read JSON artifact: {relative_path}") from exc
    if not isinstance(payload, dict):
        raise InvalidEvidence(f"artifact is not a JSON object: {relative_path}")
    return payload


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise InvalidEvidence(message)


def _need(condition: bool, message: str) -> None:
    if not condition:
        raise MissingProvenance(message)


def _need_list(value: Any, message: str) -> list[Any]:
    if not isinstance(value, list):
        raise MissingProvenance(message)
    return value


def _need_dict(value: Any, message: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise MissingProvenance(message)
    return value


def _inverse_token(token: str) -> str:
    return token.removesuffix("^-1") if token.endswith("^-1") else f"{token}^-1"


def _free_reduce(word: Word) -> Word:
    reduced: list[str] = []
    for token in word:
        if reduced and reduced[-1] == _inverse_token(token):
            reduced.pop()
        else:
            reduced.append(token)
    return tuple(reduced)


def _normalise(expression: Expression) -> Expression:
    return {word: coefficient for word, coefficient in sorted(expression.items()) if coefficient}


def _add(left: Expression, right: Expression) -> Expression:
    result = dict(left)
    for word, coefficient in right.items():
        reduced = _free_reduce(word)
        result[reduced] = result.get(reduced, 0) + coefficient
    return _normalise(result)


def _scale(expression: Expression, coefficient: int) -> Expression:
    return _normalise({word: coefficient * value for word, value in expression.items()})


def _multiply(left: Expression, right: Expression) -> Expression:
    result: Expression = {}
    for left_word, left_coefficient in left.items():
        for right_word, right_coefficient in right.items():
            word = _free_reduce(left_word + right_word)
            result[word] = result.get(word, 0) + left_coefficient * right_coefficient
    return _normalise(result)


def _expression_from_record(terms: list[dict[str, Any]]) -> Expression:
    result: Expression = {}
    for term in terms:
        word = tuple(str(token) for token in term["word"])
        result[word] = result.get(word, 0) + int(term["coefficient"])
    return _normalise(result)


def _expression_record(expression: Expression) -> list[dict[str, Any]]:
    return [
        {"coefficient": coefficient, "word": list(word)}
        for word, coefficient in sorted(expression.items())
    ]


def _substitute_word(
    word: list[str],
    symbol_to_expression: dict[str, Expression],
) -> Expression:
    result: Expression = {(): 1}
    for symbol in word:
        expression = symbol_to_expression.get(symbol)
        if expression is None:
            raise MissingProvenance(f"no reconstruction for source symbol {symbol}")
        result = _multiply(result, expression)
    return result


def _node_token(token: str) -> str:
    inverse = token.endswith("^-1")
    base = token.removesuffix("^-1")
    if base.startswith("Q_"):
        return base + ("^-1" if inverse else "")
    if base.startswith("G_p"):
        return f"G:{base.removeprefix('G_')}" + (":INV" if inverse else "")
    raise MissingProvenance(f"unrecognised reduced generator token: {token}")


def _node_expression_record(expression: Expression) -> list[dict[str, Any]]:
    mapped: Expression = {}
    for word, coefficient in expression.items():
        node_word = tuple(_node_token(token) for token in word)
        mapped[node_word] = mapped.get(node_word, 0) + coefficient
    return _expression_record(_normalise(mapped))


def _artifact_integrity(
    root: Path,
    artifacts: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    direct = artifacts[DIRECT_PATH]
    manifest = artifacts[MANIFEST_PATH]
    campaign = artifacts[CAMPAIGN_PATH]
    oracle = artifacts[ORACLE_PATH]
    inventory = artifacts[INVENTORY_PATH]
    q_presentation = artifacts[Q_PRESENTATION_PATH]

    direct_digest = _stable_hash(
        {
            "dependency_nodes": direct.get("dependency_nodes"),
            "relations": direct.get("relations"),
            "transitions": direct.get("reconstructed_transition_predicates"),
        }
    )
    _require(
        direct.get("semantic_digest_sha256") == direct_digest,
        "direct-system semantic digest mismatch",
    )
    for path, payload in (
        (INVENTORY_PATH, inventory),
        (MANIFEST_PATH, manifest),
        (CAMPAIGN_PATH, campaign),
        (ORACLE_PATH, oracle),
    ):
        expected = payload.get("semantic_digest_sha256")
        _need(isinstance(expected, str), f"{path} lacks a semantic digest")
        actual = _stable_hash(
            {key: value for key, value in payload.items() if key != "semantic_digest_sha256"}
        )
        _require(expected == actual, f"{path} semantic digest mismatch")
    _require(
        direct.get("source_artifact") == Q_PRESENTATION_PATH,
        "direct system does not name the frozen Q presentation",
    )
    direct_source_byte_hash_matches = direct.get("source_artifact_sha256") == _sha256(
        root / Q_PRESENTATION_PATH
    )
    source_hashes = _need_list(
        q_presentation.get("source_hashes"),
        "Q presentation lacks source hashes",
    )
    source_hash_by_path = {
        str(record.get("path")): record.get("sha256")
        for record in source_hashes
        if isinstance(record, dict)
    }
    historical_source_byte_hash_matches = {
        source_path: source_hash_by_path.get(source_path) == _sha256(root / source_path)
        for source_path in (SOURCE_CPOBC_PATH, REDUCTION_PATH)
    }
    return {
        "passed": True,
        "direct_system_semantic_digest_sha256": direct_digest,
        "historical_byte_bridge": {
            "direct_to_current_Q_presentation_matches": direct_source_byte_hash_matches,
            "Q_presentation_to_current_sources_matches": historical_source_byte_hash_matches,
            "used_as_proof_gate": False,
            "reason": (
                "Release metadata hydration changed wrapper bytes.  The proof gate "
                "below independently re-substitutes every source relation and "
                "requires exact expression/digest equality with the direct system."
            ),
        },
        "source_artifact_sha256": {path: _sha256(root / path) for path in sorted(artifacts)},
    }


def _cpobc_pullback_audit(artifacts: dict[str, dict[str, Any]]) -> dict[str, Any]:
    source = artifacts[SOURCE_CPOBC_PATH]
    reduction = artifacts[REDUCTION_PATH]
    q_presentation = artifacts[Q_PRESENTATION_PATH]
    direct = artifacts[DIRECT_PATH]

    reduction_map = _need_list(
        reduction.get("reduction_map"),
        "occurrence reduction map is absent",
    )
    occurrence_expressions = {
        str(record["occurrence_id"]): _expression_from_record(record["reduced_expression"])
        for record in reduction_map
    }
    _require(len(occurrence_expressions) == 165, "expected 165 occurrence reconstructions")

    source_equations: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for relation in source.get("relations", []):
        equations = _need_list(
            relation.get("denominator_cleared_form", {}).get("noncommutative_polynomial_equations"),
            "source CPOBC equation list is absent",
        )
        source_equations.extend((relation, equation) for equation in equations)
    _require(len(source_equations) == 783, "expected 783 source CPOBC equations")
    source_keys = {
        (str(relation["relation_id"]), str(equation["equation_id"]))
        for relation, equation in source_equations
    }
    _require(len(source_keys) == 783, "source CPOBC equation IDs are not unique")

    reduced_records = _need_list(
        reduction.get("rewritten_relation_inventory"),
        "rewritten CPOBC inventory is absent",
    )
    reduced_by_key = {
        (str(record["relation_id"]), str(record["equation_id"])): record
        for record in reduced_records
    }
    _require(set(reduced_by_key) == source_keys, "source/reduction CPOBC IDs differ")

    inventory = _need_dict(
        q_presentation.get("relation_inventory"),
        "Q presentation relation inventory is absent",
    )
    identities = _need_list(
        inventory.get("CPOBC_identities"),
        "Q CPOBC identity inventory is absent",
    )
    residuals = _need_list(
        inventory.get("CPOBC_residuals"),
        "Q CPOBC residual inventory is absent",
    )
    q_by_key = {
        (str(record["relation_id"]), str(record["equation_id"])): record
        for record in identities + residuals
    }
    _require(set(q_by_key) == source_keys, "source/Q CPOBC IDs differ")

    identity_count = 0
    residual_count = 0
    for relation, equation in source_equations:
        key = (str(relation["relation_id"]), str(equation["equation_id"]))
        aliases = {
            str(alias): str(record["occurrence_id"])
            for alias, record in relation["transition_orbit"].items()
        }
        symbol_map = {
            alias: occurrence_expressions[occurrence_id] for alias, occurrence_id in aliases.items()
        }
        lhs = _substitute_word(list(equation["lhs_word"]), symbol_map)
        rhs = _substitute_word(list(equation["rhs_word"]), symbol_map)
        rewritten = _add(lhs, _scale(rhs, -1))
        record = _expression_record(rewritten)
        reduced_record = reduced_by_key[key]
        q_record = q_by_key[key]
        _require(
            reduced_record.get("reduced_residual_sha256") == _stable_hash(record),
            f"independent CPOBC rewrite digest mismatch at {key}",
        )
        if rewritten:
            residual_count += 1
            node_record = _node_expression_record(rewritten)
            _require(q_record.get("identity") is False, f"lost CPOBC residual at {key}")
            _require(
                q_record.get("residual_expression") == node_record,
                f"Q CPOBC expression mismatch at {key}",
            )
            _require(
                q_record.get("Q_dependency_residual_sha256") == _stable_hash(node_record),
                f"Q CPOBC digest mismatch at {key}",
            )
        else:
            identity_count += 1
            _require(q_record.get("identity") is True, f"lost CPOBC identity at {key}")
    _require((identity_count, residual_count) == (83, 700), "CPOBC 83/700 split changed")

    direct_by_branch = _need_dict(
        direct.get("relations"),
        "direct relation branches are absent",
    )
    branch_ledgers: dict[str, str] = {}
    expected_by_id = {
        f"{record['relation_id']}:{record['equation_id']}": record for record in residuals
    }
    for branch in sorted(direct_by_branch):
        records = [record for record in direct_by_branch[branch] if record.get("family") == "CPOBC"]
        by_id = {str(record["relation_id"]): record for record in records}
        _require(set(by_id) == set(expected_by_id), f"direct CPOBC IDs differ on {branch}")
        for identifier, expected in expected_by_id.items():
            observed = by_id[identifier]
            _require(
                observed.get("expression") == expected.get("residual_expression"),
                f"direct CPOBC expression mismatch at {identifier}",
            )
            _require(
                observed.get("provenance", {}).get("v033_digest")
                == expected.get("Q_dependency_residual_sha256"),
                f"direct CPOBC provenance mismatch at {identifier}",
            )
        branch_ledgers[branch] = _stable_hash(sorted(by_id))
    _require(
        len(set(branch_ledgers.values())) == 1,
        "CPOBC direct core is not shared across Eq.(113) branches",
    )
    return {
        "passed": True,
        "source_equation_count": 783,
        "identically_zero_pullback_count": identity_count,
        "nonzero_direct_pullback_count": residual_count,
        "direct_relation_id_sha256": next(iter(branch_ledgers.values())),
        "proof_rule": (
            "A source CPOBC point in image(Phi_U) evaluates each independently "
            "rewritten source word residual to zero; the 83 zero pullbacks need no "
            "relation and the other 700 are exactly the direct CPOBC records."
        ),
    }


def _signature_key(record: dict[str, Any]) -> tuple[int, int, int]:
    relation = tuple(int(value) for value in record["source_relation_rows"])
    precursor = int(record["precursor_code"])

    def relation_code(order: tuple[int, ...]) -> int:
        size = len(relation)
        code = 0
        for new_lower, old_lower in enumerate(order):
            for new_upper, old_upper in enumerate(order):
                if relation[old_lower] & (1 << old_upper):
                    code |= 1 << (new_lower * size + new_upper)
        return code

    def subset_code(order: tuple[int, ...]) -> int:
        return sum(
            1 << new_vertex
            for new_vertex, old_vertex in enumerate(order)
            if precursor & (1 << old_vertex)
        )

    canonical_relation, canonical_precursor = min(
        (relation_code(order), subset_code(order))
        for order in itertools.permutations(range(len(relation)))
    )
    return int(record["stage"]), canonical_relation, canonical_precursor


def _gc_pullback_audit(artifacts: dict[str, dict[str, Any]]) -> dict[str, Any]:
    reduction = artifacts[REDUCTION_PATH]
    local_gc = artifacts[LOCAL_GC_PATH]
    q_presentation = artifacts[Q_PRESENTATION_PATH]
    direct = artifacts[DIRECT_PATH]

    reduction_map = _need_list(
        reduction.get("reduction_map"),
        "occurrence reduction map is absent",
    )
    by_signature: dict[tuple[int, int, int], Expression] = {}
    for record in reduction_map:
        key = _signature_key(record)
        expression = _expression_from_record(record["reduced_expression"])
        previous = by_signature.get(key)
        if previous is not None:
            _require(previous == expression, f"conflicting reduction for signature {key}")
        by_signature[key] = expression
    _require(len(by_signature) == 131, "expected 131 quotient transition signatures")

    symbol_expressions: dict[str, Expression] = {}
    path_inventory = _need_dict(
        local_gc.get("path_inventory"),
        "strong-GC path inventory is absent",
    )
    labelled_transition_ids: set[str] = set()
    for stage_paths in path_inventory.values():
        for path in stage_paths:
            for transition in path.get("transitions", []):
                labelled_transition_ids.add(str(transition["labelled_occurrence_id"]))
                signature = transition.get("quotient_signature")
                _need(isinstance(signature, dict), "GC transition signature is absent")
                key = (
                    int(signature["stage"]),
                    int(signature["source_relation_code"]),
                    int(signature["precursor_code"]),
                )
                candidate_expression = by_signature.get(key)
                _need(
                    candidate_expression is not None,
                    f"no reduction for GC transition {key}",
                )
                assert candidate_expression is not None
                symbol = str(transition["quotient_operator_symbol"])
                previous = symbol_expressions.get(symbol)
                if previous is not None:
                    _require(
                        previous == candidate_expression,
                        f"conflicting GC symbol {symbol}",
                    )
                symbol_expressions[symbol] = candidate_expression
    _require(len(labelled_transition_ids) == 406, "expected 406 labelled GC transitions")
    _require(len(symbol_expressions) == 131, "expected 131 quotient GC symbols")

    basis = _need_list(
        local_gc.get("generating_relation_basis"),
        "strong-GC generating basis is absent",
    )
    _require(len(basis) == 320, "expected 320 strong-GC basis relations")
    _require(
        local_gc.get("proof_obligations", {}).get("basis_connectivity", {}).get("passed") is True,
        "strong-GC endpoint-wise basis connectivity is not certified",
    )

    inventory = _need_dict(
        q_presentation.get("relation_inventory"),
        "Q presentation relation inventory is absent",
    )
    identities = _need_list(
        inventory.get("local_operator_GC_identities"),
        "Q local-GC identity inventory is absent",
    )
    residuals = _need_list(
        inventory.get("local_operator_GC_residuals"),
        "Q local-GC residual inventory is absent",
    )
    q_by_id = {str(record["relation_id"]): record for record in identities + residuals}
    basis_by_id = {str(record["relation_id"]): record for record in basis}
    _require(set(q_by_id) == set(basis_by_id), "source/Q strong-GC IDs differ")

    identity_count = 0
    residual_count = 0
    for identifier, relation in basis_by_id.items():
        lhs = _substitute_word(list(relation["lhs_word"]), symbol_expressions)
        rhs = _substitute_word(list(relation["rhs_word"]), symbol_expressions)
        rewritten = _add(lhs, _scale(rhs, -1))
        q_record = q_by_id[identifier]
        _require(
            q_record.get("path_provenance")
            == {
                "lhs_path_id": relation["lhs_path_id"],
                "rhs_path_id": relation["rhs_path_id"],
            },
            f"strong-GC path provenance mismatch at {identifier}",
        )
        if rewritten:
            residual_count += 1
            node_record = _node_expression_record(rewritten)
            _require(q_record.get("identity") is False, f"lost GC residual at {identifier}")
            _require(
                q_record.get("residual_expression") == node_record,
                f"Q strong-GC expression mismatch at {identifier}",
            )
            _require(
                q_record.get("Q_dependency_residual_sha256") == _stable_hash(node_record),
                f"Q strong-GC digest mismatch at {identifier}",
            )
        else:
            identity_count += 1
            _require(q_record.get("identity") is True, f"lost GC identity at {identifier}")
    _require((identity_count, residual_count) == (65, 255), "GC 65/255 split changed")

    direct_by_branch = _need_dict(
        direct.get("relations"),
        "direct relation branches are absent",
    )
    expected_by_id = {str(record["relation_id"]): record for record in residuals}
    branch_ledgers: dict[str, str] = {}
    for branch in sorted(direct_by_branch):
        records = [
            record
            for record in direct_by_branch[branch]
            if record.get("family") == "LOCAL_OPERATOR_GC"
        ]
        by_id = {str(record["relation_id"]): record for record in records}
        _require(set(by_id) == set(expected_by_id), f"direct GC IDs differ on {branch}")
        for identifier, expected in expected_by_id.items():
            observed = by_id[identifier]
            _require(
                observed.get("expression") == expected.get("residual_expression"),
                f"direct GC expression mismatch at {identifier}",
            )
            _require(
                observed.get("provenance", {}).get("v033_digest")
                == expected.get("Q_dependency_residual_sha256"),
                f"direct GC provenance mismatch at {identifier}",
            )
        branch_ledgers[branch] = _stable_hash(sorted(by_id))
    _require(
        len(set(branch_ledgers.values())) == 1,
        "local-GC direct core is not shared across Eq.(113) branches",
    )
    return {
        "passed": True,
        "source_basis_relation_count": 320,
        "source_same_endpoint_pair_count": int(
            local_gc.get("counts", {}).get("same_endpoint_path_pairs", -1)
        ),
        "identically_zero_pullback_count": identity_count,
        "nonzero_direct_pullback_count": residual_count,
        "direct_relation_id_sha256": next(iter(branch_ledgers.values())),
        "proof_rule": (
            "Strong source GC kills the endpoint-wise 320-relation spanning-tree "
            "basis.  Independent substitution through Phi_U gives 65 identities "
            "and exactly the 255 local-operator-GC direct records."
        ),
    }


def _inverse_and_nonsingularity_audit(
    artifacts: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    reduction = artifacts[REDUCTION_PATH]
    direct = artifacts[DIRECT_PATH]
    nodes = _need_list(direct.get("dependency_nodes"), "dependency-node ledger is absent")
    predicates = _need_list(
        direct.get("reconstructed_transition_predicates"),
        "transition predicate ledger is absent",
    )
    inverse_predicates = _need_list(
        direct.get("explicit_two_sided_inverse_predicates"),
        "inverse predicate ledger is absent",
    )
    node_by_id = {str(record["node_id"]): record for record in nodes}
    predicate_by_occurrence = {str(record["occurrence_id"]): record for record in predicates}
    _require(len(predicate_by_occurrence) == 165, "expected 165 transition predicates")

    reduction_map = _need_list(
        reduction.get("reduction_map"),
        "occurrence reduction map is absent",
    )
    reduction_by_occurrence = {str(record["occurrence_id"]): record for record in reduction_map}
    _require(
        set(predicate_by_occurrence) == set(reduction_by_occurrence),
        "transition-predicate and occurrence-reduction domains differ",
    )
    for occurrence_id, record in reduction_by_occurrence.items():
        expected = _node_expression_record(_expression_from_record(record["reduced_expression"]))
        observed = predicate_by_occurrence[occurrence_id]
        _require(
            observed.get("reconstructed_expression") == expected,
            f"transition reconstruction mismatch at {occurrence_id}",
        )
        _require(
            observed.get("expression_sha256") == _stable_hash(expected),
            f"transition reconstruction digest mismatch at {occurrence_id}",
        )

    q_inverse_nodes = [record for record in nodes if record.get("kind") == "Q_GENERATOR_INVERSE"]
    b_inverse_nodes = [
        record for record in nodes if record.get("kind") == "FORMAL_TWO_SIDED_INVERSE_AUXILIARY"
    ]
    b_definition_nodes = {
        str(record["node_id"]): record
        for record in nodes
        if record.get("kind") == "EQ107_EQ108_LINEAR_EXPRESSION"
    }
    _require(len(q_inverse_nodes) == 4, "expected four Q inverse sites")
    _require(len(b_inverse_nodes) == 22, "expected 22 B inverse sites")
    _require(len(b_definition_nodes) == 22, "expected 22 B definitions")

    inverse_base_occurrences: dict[str, str] = {}
    for record in q_inverse_nodes:
        base = str(record["node_id"]).removesuffix("^-1")
        expected_expression = [{"coefficient": 1, "word": [base]}]
        hits = [
            occurrence_id
            for occurrence_id, predicate in predicate_by_occurrence.items()
            if predicate.get("reconstructed_expression") == expected_expression
        ]
        _require(len(hits) == 1, f"{base} does not identify one source occurrence")
        inverse_base_occurrences[str(record["node_id"])] = hits[0]
    for record in b_inverse_nodes:
        base = str(record["inverse_of_node"])
        definition = b_definition_nodes.get(base)
        _need(definition is not None, f"missing B definition for {base}")
        assert definition is not None
        occurrence_id = str(definition.get("v032_occurrence_id"))
        predicate = predicate_by_occurrence.get(occurrence_id)
        _need(predicate is not None, f"missing source occurrence for {base}")
        assert predicate is not None
        expected_expression = [
            {
                "coefficient": int(term["coefficient"]),
                "word": list(term["word_nodes"]),
            }
            for term in definition["terms"]
        ]
        _require(
            predicate.get("reconstructed_expression") == expected_expression,
            f"B definition/source occurrence mismatch at {base}",
        )
        inverse_base_occurrences[str(record["node_id"])] = occurrence_id
    _require(
        len(set(inverse_base_occurrences.values())) == 26,
        "the 26 inverse sites do not map to 26 distinct source occurrences",
    )

    expected_inverse_predicates: dict[tuple[str, str], tuple[str, str]] = {}
    for record in q_inverse_nodes:
        node_id = str(record["node_id"])
        base = node_id.removesuffix("^-1")
        expected_inverse_predicates[(node_id, base)] = (
            f"{node_id} * {base} = I",
            f"{base} * {node_id} = I",
        )
    for record in b_inverse_nodes:
        generator = str(record["auxiliary_generator"])
        base = str(record["inverse_of_node"])
        expected_inverse_predicates[(generator, base)] = tuple(
            str(value) for value in record["inverse_predicates"]
        )  # type: ignore[assignment]
    observed_inverse_predicates = {
        (str(record["generator"]), str(record["inverse_of_node"])): (
            str(record["left_predicate"]),
            str(record["right_predicate"]),
        )
        for record in inverse_predicates
    }
    _require(
        observed_inverse_predicates == expected_inverse_predicates,
        "explicit inverse predicate ledger does not equal the 4+22 inverse sites",
    )

    allowed_kinds = {
        "Q_GENERATOR",
        "Q_GENERATOR_INVERSE",
        "EQ107_EQ108_LINEAR_EXPRESSION",
        "FORMAL_TWO_SIDED_INVERSE_AUXILIARY",
        "EQ112_CONJUGATE",
        "EQ112_CONJUGATE_INVERSE",
    }
    _require(
        set(Counter(str(record.get("kind")) for record in nodes)) <= allowed_kinds,
        "dependency DAG contains an unclassified inverse mechanism",
    )
    for record in nodes:
        for dependency in record.get("dependencies", []):
            _require(
                dependency in node_by_id,
                f"dependency DAG refers to absent node {dependency}",
            )
    return {
        "passed": True,
        "reconstructed_transition_predicate_count": 165,
        "Q_inverse_site_count": len(q_inverse_nodes),
        "B_inverse_site_count": len(b_inverse_nodes),
        "inverse_site_source_occurrence_count": len(set(inverse_base_occurrences.values())),
        "inverse_site_to_source_occurrence_sha256": _stable_hash(
            dict(sorted(inverse_base_occurrences.items()))
        ),
        "proof_rule": (
            "At a source point in image(Phi_U), all 165 reconstructed matrices "
            "equal their source transition operators.  Source nonsingularity "
            "therefore supplies every transition determinant; in particular it "
            "supplies the four Q and 22 B determinants used by every rational inverse."
        ),
    }


def _eq120_ratio_identity() -> bool:
    import sympy as sp

    q11, q12, q21, q22 = sp.symbols("q11 q12 q21 q22")
    n11, n12, n21, n22 = sp.symbols("n11 n12 n21 n22")
    m11, m12, m21, m22 = sp.symbols("m11 m12 m21 m22")
    qn = sp.Matrix([[n11, n12], [n21, n22]])
    qm = sp.Matrix([[m11, m12], [m21, m22]])
    adj_q1 = sp.Matrix([[q22, -q12], [-q21, q11]])
    cleared_eq120 = qn * adj_q1 * qm - qm * adj_q1 * qn
    numerator = adj_q1 * qn * adj_q1 * qm - adj_q1 * qm * adj_q1 * qn
    residual = sp.expand(numerator - adj_q1 * cleared_eq120)
    return all(entry == 0 for entry in residual)


def _source_eq120_ledger(
    artifacts: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Independently identify the six antichain Eq.(105) source records."""

    source = artifacts[SOURCE_CPOBC_PATH]
    reduction = artifacts[REDUCTION_PATH]
    direct = artifacts[DIRECT_PATH]
    expected_pairs = {(2, 1), (3, 1), (3, 2), (4, 1), (4, 2), (4, 3)}
    expected_eq105_terms = [
        {"coefficient": 1, "word": ["A_n"]},
        {
            "coefficient": -1,
            "word": ["A_m", "A_prime_n", "A_prime_m^-1"],
        },
    ]
    by_pair: dict[tuple[int, int], dict[str, Any]] = {}
    for relation in _need_list(source.get("relations"), "source CPOBC relations are absent"):
        stage = _need_dict(relation.get("stage"), "source CPOBC stage is absent")
        pair = (int(stage["n"]), int(stage["m"]))
        source_causet = _need_dict(
            relation.get("source_causet"),
            "source CPOBC causet descriptor is absent",
        )
        rows_n = source_causet.get("stage_n", {}).get("canonical_relation_rows")
        rows_m = source_causet.get("stage_m", {}).get("canonical_relation_rows")
        reduced_precursor = relation.get("reduced_precursor", {})
        is_target = (
            pair in expected_pairs
            and isinstance(rows_n, list)
            and isinstance(rows_m, list)
            and all(int(value) == 0 for value in rows_n + rows_m)
            and reduced_precursor.get("A_precursor_code") == 1
            and reduced_precursor.get("A_prime_precursor_code") == 0
            and relation.get("branch") == "GREATER"
        )
        if not is_target:
            continue
        _require(pair not in by_pair, f"duplicate antichain Eq.(105) source pair {pair}")
        forms = _need_list(
            relation.get("inverse_containing_form", {}).get("forms"),
            f"Eq.(105) form absent at source pair {pair}",
        )
        _require(
            len(forms) == 1
            and forms[0].get("equation_id") == "eq105"
            and forms[0].get("residual_terms") == expected_eq105_terms,
            f"unexpected Eq.(105) free-word form at source pair {pair}",
        )
        denominator_cleared = _need_list(
            relation.get("denominator_cleared_form", {}).get("noncommutative_polynomial_equations"),
            f"Eq.(103) form absent at source pair {pair}",
        )
        _require(
            len(denominator_cleared) == 1
            and denominator_cleared[0].get("equation_id") == "eq103"
            and denominator_cleared[0].get("lhs_word") == ["A_n", "A_prime_m"]
            and denominator_cleared[0].get("rhs_word") == ["A_m", "A_prime_n"],
            f"unexpected Eq.(103) free-word form at source pair {pair}",
        )
        eq103_residual = _normalise(
            {
                tuple(denominator_cleared[0]["lhs_word"]): 1,
                tuple(denominator_cleared[0]["rhs_word"]): -1,
            }
        )
        derived_eq105 = _multiply(eq103_residual, {("A_prime_m^-1",): 1})
        _require(
            derived_eq105 == _expression_from_record(forms[0]["residual_terms"]),
            f"Eq.(103)-to-Eq.(105) right-inverse derivation failed at {pair}",
        )
        _require(
            relation.get("MSR_dependency", {}).get("used_to_generate_this_relation") is False,
            f"source Eq.(105) record unexpectedly depends on MSR at {pair}",
        )
        _require(
            relation.get("GC_dependency", {}).get("used_to_generate_this_relation") is False,
            f"source Eq.(105) record unexpectedly depends on GC at {pair}",
        )
        by_pair[pair] = relation
    _require(set(by_pair) == expected_pairs, "the unique six antichain Eq.(105) pairs changed")

    reduction_by_occurrence = {
        str(record["occurrence_id"]): record
        for record in _need_list(
            reduction.get("reduction_map"),
            "occurrence reduction map is absent",
        )
    }
    direct_occurrences = {
        str(record["occurrence_id"])
        for record in _need_list(
            direct.get("reconstructed_transition_predicates"),
            "direct transition predicates are absent",
        )
    }
    raw_inventory: list[dict[str, Any]] = []
    for pair in sorted(by_pair):
        relation = by_pair[pair]
        transitions = _need_dict(
            relation.get("transition_orbit"),
            f"transition orbit absent at source pair {pair}",
        )
        occurrence_ids = {
            alias: str(record["occurrence_id"]) for alias, record in sorted(transitions.items())
        }
        operator_variables = {
            alias: str(record["operator_variable"]) for alias, record in sorted(transitions.items())
        }
        _require(
            set(occurrence_ids.values()) <= direct_occurrences,
            f"Eq.(105) source occurrence lacks a direct predicate at {pair}",
        )
        raw_inventory.append(
            {
                "relation_id": str(relation["relation_id"]),
                "relation_hash": str(relation["relation_hash"]),
                "stages": {"n": pair[0], "m": pair[1]},
                "occurrence_ids": occurrence_ids,
                "operator_variables": operator_variables,
                "Eq105_form": relation["inverse_containing_form"]["forms"][0],
                "dependency_flags": {
                    "MSR_used_to_generate": False,
                    "GC_used_to_generate": False,
                    "Eq103_to_Eq105_right_inverse_verified": True,
                    "source_nonsingularity_required_for_cancellation": True,
                },
            }
        )

    pair_derivations: list[dict[str, Any]] = []
    for m, n in itertools.combinations((2, 3, 4), 2):
        relation_nm = by_pair[(n, m)]
        relation_m1 = by_pair[(m, 1)]
        relation_n1 = by_pair[(n, 1)]
        orbit_nm = relation_nm["transition_orbit"]
        orbit_m1 = relation_m1["transition_orbit"]
        orbit_n1 = relation_n1["transition_orbit"]

        occurrence_equalities = {
            "Tn": orbit_nm["A_n"]["occurrence_id"] == orbit_n1["A_n"]["occurrence_id"],
            "Tm": orbit_nm["A_m"]["occurrence_id"] == orbit_m1["A_n"]["occurrence_id"],
            "Gn": orbit_nm["A_prime_n"]["occurrence_id"] == orbit_n1["A_prime_n"]["occurrence_id"],
            "Gm": orbit_nm["A_prime_m"]["occurrence_id"] == orbit_m1["A_prime_n"]["occurrence_id"],
            "T1": orbit_m1["A_m"]["occurrence_id"] == orbit_n1["A_m"]["occurrence_id"],
            "G1": orbit_m1["A_prime_m"]["occurrence_id"] == orbit_n1["A_prime_m"]["occurrence_id"],
        }
        _require(
            all(occurrence_equalities.values()),
            f"source transition occurrences do not identify consistently at {(m, n)}",
        )

        g_occurrences = {
            1: str(orbit_m1["A_prime_m"]["occurrence_id"]),
            m: str(orbit_m1["A_prime_n"]["occurrence_id"]),
            n: str(orbit_n1["A_prime_n"]["occurrence_id"]),
        }
        for g_stage, occurrence_id in g_occurrences.items():
            reduced = reduction_by_occurrence.get(occurrence_id)
            _need(reduced is not None, f"no Q reduction for G{g_stage}")
            assert reduced is not None
            _require(
                reduced.get("reduced_expression") == [{"coefficient": 1, "word": [f"Q_{g_stage}"]}],
                f"G{g_stage} is not identified exactly with Q_{g_stage}",
            )

        substituted = _normalise(
            {
                ("T_1", f"G_{n}", "G_1^-1"): 1,
                ("T_1", f"G_{m}", "G_1^-1", f"G_{n}", f"G_{m}^-1"): -1,
            }
        )
        cancelled = _multiply(
            _multiply({("T_1^-1",): 1}, substituted),
            {(f"G_{m}",): 1},
        )
        expected_abstract = _normalise(
            {
                (f"G_{n}", "G_1^-1", f"G_{m}"): 1,
                (f"G_{m}", "G_1^-1", f"G_{n}"): -1,
            }
        )
        _require(
            cancelled == expected_abstract,
            f"free-word Eq.(120) derivation failed at {(m, n)}",
        )
        q_target = {
            tuple(token.replace("G_", "Q_") for token in word): coefficient
            for word, coefficient in expected_abstract.items()
        }
        cancellation_occurrences = {
            "left_T1": str(orbit_m1["A_m"]["occurrence_id"]),
            "right_Gm": str(orbit_m1["A_prime_n"]["occurrence_id"]),
        }
        _require(
            set(cancellation_occurrences.values()) <= direct_occurrences,
            f"Eq.(120) cancellation site lacks nonsingularity predicate at {(m, n)}",
        )
        source_ids = [
            str(relation_nm["relation_id"]),
            str(relation_m1["relation_id"]),
            str(relation_n1["relation_id"]),
        ]
        pair_derivations.append(
            {
                "indices": [m, n],
                "source_relation_ids": source_ids,
                "source_relation_content_sha256": _stable_hash(
                    [relation_nm, relation_m1, relation_n1]
                ),
                "occurrence_identifications": occurrence_equalities,
                "cancellation_occurrence_ids": cancellation_occurrences,
                "substituted_source_residual": _expression_record(substituted),
                "derived_abstract_residual": _expression_record(cancelled),
                "target_Q_residual": _expression_record(_normalise(q_target)),
                "verified": True,
            }
        )

    return {
        "raw_relation_count": len(raw_inventory),
        "raw_relation_inventory": raw_inventory,
        "raw_relation_ids_sha256": _stable_hash(
            [record["relation_id"] for record in raw_inventory]
        ),
        "pair_derivations": pair_derivations,
        "dependency_closure": {
            "CPOBC": True,
            "source_nonsingularity": True,
            "MSR": False,
            "GC": False,
            "occurrence_identification": True,
        },
        "passed": True,
    }


def _eq120_word_equality(
    label: str,
    lhs: tuple[str, ...],
    rhs: tuple[str, ...],
) -> dict[str, Any]:
    return {"label": label, "lhs_word": list(lhs), "rhs_word": list(rhs)}


def _validate_eq120_source_certificate(
    root: Path,
    artifacts: dict[str, dict[str, Any]],
    source_ledger: dict[str, Any],
    selected: list[dict[str, Any]],
) -> dict[str, Any]:
    """Bind the standalone certificate without importing its producer."""

    certificate_path = root / EQ120_PROVENANCE_PATH
    _need(certificate_path.is_file(), "source-native Eq.(120) certificate is absent")
    certificate = _load(root, EQ120_PROVENANCE_PATH)
    _require(
        certificate.get("schema_version") == EQ120_PROVENANCE_SCHEMA,
        "source-native Eq.(120) certificate schema changed",
    )
    semantic_digest = certificate.get("semantic_digest_sha256")
    _require(
        isinstance(semantic_digest, str)
        and semantic_digest
        == _stable_hash(
            {key: value for key, value in certificate.items() if key != "semantic_digest_sha256"}
        ),
        "source-native Eq.(120) certificate semantic digest mismatch",
    )

    source = artifacts[SOURCE_CPOBC_PATH]
    reduction = artifacts[REDUCTION_PATH]
    expected_input_hashes = {
        "source_cpobc_relations": {
            "path": SOURCE_CPOBC_PATH,
            "sha256": _sha256(root / SOURCE_CPOBC_PATH),
        },
        "generator_reduction": {
            "path": REDUCTION_PATH,
            "sha256": _sha256(root / REDUCTION_PATH),
        },
        "direct_system": {
            "path": DIRECT_PATH,
            "sha256": _sha256(root / DIRECT_PATH),
        },
    }
    _require(
        certificate.get("input_hashes") == expected_input_hashes,
        "source-native Eq.(120) input hashes changed",
    )

    primary = _need_dict(
        certificate.get("primary_source"),
        "Eq.(120) certificate primary source is absent",
    )
    primary_path = primary.get("path")
    _need(isinstance(primary_path, str), "Eq.(120) primary-source path is absent")
    assert isinstance(primary_path, str)
    local_primary = root / primary_path
    _need(local_primary.is_file(), "Eq.(120) primary-source PDF is absent")
    _require(
        primary.get("paper") == "arXiv:2603.25503v1"
        and primary.get("sha256") == _sha256(local_primary)
        and primary.get("equations_checked") == [103, 105, 115, 116, 117, 118, 119, 120],
        "Eq.(120) primary-source binding changed",
    )
    paper_versions = {
        str(record.get("id")): record
        for record in _need_list(
            source.get("paper_versions"),
            "source CPOBC paper-version ledger is absent",
        )
    }
    _require(
        paper_versions.get("arXiv:2603.25503v1", {}).get("sha256") == primary.get("sha256"),
        "source CPOBC artifact and Eq.(120) certificate cite different paper bytes",
    )

    selected_ids = sorted(str(record["relation_id"]) for record in selected)
    selected_digest = _stable_hash(selected_ids)
    _require(
        certificate.get("selected_700_relation_ids")
        == {
            "branch": DIRECT_BRANCH,
            "family": "CPOBC",
            "count": 700,
            "ordered_ids_sha256": selected_digest,
        },
        "Eq.(120) certificate is not bound to the canonical selected-700 ledger",
    )

    source_by_id = {
        str(record["relation_id"]): record
        for record in _need_list(source.get("relations"), "source CPOBC relations are absent")
    }
    expected_raw = _need_list(
        source_ledger.get("raw_relation_inventory"),
        "independent Eq.(120) raw ledger is absent",
    )
    certificate_raw = _need_list(
        certificate.get("raw_relation_inventory"),
        "certificate Eq.(120) raw ledger is absent",
    )
    _require(len(certificate_raw) == len(expected_raw) == 6, "Eq.(120) raw ledger is not six")
    expected_raw_ids = [str(record["relation_id"]) for record in expected_raw]
    _require(
        [str(record.get("relation_id")) for record in certificate_raw] == expected_raw_ids,
        "Eq.(120) certificate selected different source relations",
    )
    for expected, observed in zip(expected_raw, certificate_raw, strict=True):
        relation_id = str(expected["relation_id"])
        relation = source_by_id[relation_id]
        n = int(expected["stages"]["n"])
        m = int(expected["stages"]["m"])
        _require(
            relation_id == f"cpobc-relation-{relation['relation_hash'][:20]}",
            f"source relation ID/hash mismatch at {(n, m)}",
        )
        _require(
            observed.get("stage_pair") == [n, m]
            and observed.get("relation_id") == relation_id
            and observed.get("relation_hash") == relation.get("relation_hash")
            and observed.get("relation_content_sha256") == _stable_hash(relation)
            and observed.get("source_ids")
            == [
                relation["source_causet"]["stage_n"]["id"],
                relation["source_causet"]["stage_m"]["id"],
            ]
            and observed.get("bell_family_id") == relation["Bell_family"]["id"]
            and observed.get("precursor_codes") == {"B": 1, "Q": 0},
            f"source Eq.(120) raw descriptor mismatch at {(n, m)}",
        )
        transition_orbit = relation["transition_orbit"]
        expected_occurrences: dict[str, dict[str, str]] = {}
        for semantic_alias, source_alias, semantic_name in (
            ("B_n", "A_n", f"B_{n}"),
            ("Q_n", "A_prime_n", f"Q_{n}"),
            ("B_m", "A_m", f"B_{m}"),
            ("Q_m", "A_prime_m", f"Q_{m}"),
        ):
            occurrence = transition_orbit[source_alias]
            expected_occurrences[semantic_alias] = {
                "semantic_name": semantic_name,
                "occurrence_id": str(occurrence["occurrence_id"]),
                "orbit_id": str(occurrence["orbit_id"]),
                "operator_variable": str(occurrence["operator_variable"]),
            }
        _require(
            observed.get("occurrences") == expected_occurrences,
            f"source Eq.(120) occurrence descriptor mismatch at {(n, m)}",
        )
        raw_eq103 = relation["raw_noncommutative_relation"][0]
        _require(
            all(
                raw_eq103["operator_ids"][alias] == transition_orbit[alias]["occurrence_id"]
                for alias in ("A_n", "A_prime_n", "A_m", "A_prime_m")
            ),
            f"raw Eq.(103) occurrence provenance mismatch at {(n, m)}",
        )
        expected_eq103 = _eq120_word_equality(
            "Eq.(103)",
            (f"B_{n}", f"Q_{m}"),
            (f"B_{m}", f"Q_{n}"),
        )
        expected_eq105 = _eq120_word_equality(
            "Eq.(105)",
            (f"B_{n}",),
            (f"B_{m}", f"Q_{n}", f"Q_{m}^-1"),
        )
        _require(
            observed.get("eq103") == expected_eq103 and observed.get("eq105") == expected_eq105,
            f"source Eq.(103)/(105) semantic words changed at {(n, m)}",
        )
        _require(
            observed.get("dependency_flags")
            == {
                "CPOBC_axiom_instance": True,
                "MSR_used": False,
                "GC_used": False,
                "Eq108_used": False,
                "Eq112_used": False,
            },
            f"forbidden dependency entered source Eq.(120) record at {(n, m)}",
        )
        _require(
            relation.get("paper_equation_correspondence", {}).get("paper") == "arXiv:2603.25503v1"
            and relation.get("paper_equation_correspondence", {}).get("equations") == [103, 105],
            f"source relation lacks Eq.(103)/(105) paper binding at {(n, m)}",
        )

    reduction_by_occurrence = {
        str(record["occurrence_id"]): record
        for record in _need_list(
            reduction.get("reduction_map"),
            "occurrence reduction map is absent",
        )
    }
    q_occurrences = _need_list(
        certificate.get("q_occurrence_identification"),
        "Eq.(120) Q occurrence ledger is absent",
    )
    _require(len(q_occurrences) == 4, "Eq.(120) Q occurrence ledger is not four")
    q_ids_by_stage: dict[int, str] = {}
    for raw_record in certificate_raw:
        n, m = (int(value) for value in raw_record["stage_pair"])
        for stage_index, key in ((n, "Q_n"), (m, "Q_m")):
            occurrence_id = str(raw_record["occurrences"][key]["occurrence_id"])
            previous = q_ids_by_stage.get(stage_index)
            _require(
                previous is None or previous == occurrence_id,
                f"Q_{stage_index} source occurrence is inconsistent",
            )
            q_ids_by_stage[stage_index] = occurrence_id
    _require(set(q_ids_by_stage) == {1, 2, 3, 4}, "Q occurrence stage cover changed")
    for stage_index, observed in zip(range(1, 5), q_occurrences, strict=True):
        occurrence_id = q_ids_by_stage[stage_index]
        reduced = reduction_by_occurrence[occurrence_id]
        expected_expression = [{"coefficient": 1, "word": [f"Q_{stage_index}"]}]
        _require(
            observed
            == {
                "stage": stage_index,
                "semantic_name": f"Q_{stage_index}",
                "occurrence_id": occurrence_id,
                "transition_hash": reduced["transition_hash"],
                "orbit_id": reduced["orbit_id"],
                "source_id": reduced["source_id"],
                "operator_variable": reduced["operator_variable"],
                "identifier_rule": "definition of the source-causet gregarious transition",
                "reduced_expression": expected_expression,
                "used_as_identifier_only": True,
            }
            and reduced.get("stage") == stage_index
            and reduced.get("source_relation_rows") == [0] * stage_index
            and reduced.get("precursor") == []
            and reduced.get("transition_kind") == "GREGARIOUS"
            and reduced.get("reduced_expression") == expected_expression
            and reduced.get("exact") is True,
            f"independent Q_{stage_index} occurrence identification failed",
        )

    independent_pairs = {
        tuple(int(value) for value in record["indices"]): record
        for record in _need_list(
            source_ledger.get("pair_derivations"),
            "independent Eq.(120) pair ledger is absent",
        )
    }
    pair_certificates = _need_list(
        certificate.get("pair_certificates"),
        "Eq.(120) pair certificates are absent",
    )
    _require(
        [record.get("indices") for record in pair_certificates] == [[2, 3], [2, 4], [3, 4]],
        "Eq.(120) pair-certificate cover changed",
    )
    expected_pair_records: list[dict[str, Any]] = []
    for observed in pair_certificates:
        m, n = (int(value) for value in observed["indices"])
        independent = independent_pairs[(m, n)]
        source_ids = independent["source_relation_ids"]
        eq115 = _eq120_word_equality(
            "Eq.(115)",
            (f"B_{n}",),
            (f"B_{m}", f"Q_{n}", f"Q_{m}^-1"),
        )
        eq116 = _eq120_word_equality(
            "Eq.(116)",
            (f"B_{m}",),
            ("B_1", f"Q_{m}", "Q_1^-1"),
        )
        eq117 = _eq120_word_equality(
            "Eq.(117)",
            (f"B_{n}",),
            ("B_1", f"Q_{n}", "Q_1^-1"),
        )
        eq118 = _eq120_word_equality(
            "Eq.(118)",
            ("B_1", f"Q_{n}", "Q_1^-1"),
            ("B_1", f"Q_{m}", "Q_1^-1", f"Q_{n}", f"Q_{m}^-1"),
        )
        cancelled = _eq120_word_equality(
            "left-cancel B_1",
            (f"Q_{n}", "Q_1^-1"),
            (f"Q_{m}", "Q_1^-1", f"Q_{n}", f"Q_{m}^-1"),
        )
        target_equality = _eq120_word_equality(
            "Eq.(119)/(120)",
            (f"Q_{n}", "Q_1^-1", f"Q_{m}"),
            (f"Q_{m}", "Q_1^-1", f"Q_{n}"),
        )
        target_residual = [
            {"coefficient": 1, "word": target_equality["lhs_word"]},
            {"coefficient": -1, "word": target_equality["rhs_word"]},
        ]
        expected_pair = {
            "indices": [m, n],
            "orientation": {"k": 1, "m": m, "n": n},
            "source_relation_ids": source_ids,
            "source_relation_roles": {
                "paper_eq115_n_vs_m": source_ids[0],
                "paper_eq116_m_vs_k": source_ids[1],
                "paper_eq117_n_vs_k": source_ids[2],
            },
            "source_relation_content_sha256": independent["source_relation_content_sha256"],
            "paper_premises": [eq115, eq116, eq117],
            "free_word_derivation": [eq118, cancelled, target_equality],
            "target_residual": target_residual,
            "target_residual_display": (f"Q_{n}*Q_1^-1*Q_{m} - Q_{m}*Q_1^-1*Q_{n}"),
            "verified": True,
        }
        _require(
            observed == expected_pair
            and _expression_from_record(observed["target_residual"])
            == _expression_from_record(independent["target_Q_residual"]),
            f"Eq.(120) pair certificate failed independent recomputation at {(m, n)}",
        )
        expected_pair_records.append(expected_pair)

    direct_by_id = {str(record["relation_id"]): record for record in selected}
    expected_pair_bindings: list[dict[str, Any]] = []
    for pair in expected_pair_records:
        m, n = pair["indices"]
        source_relation_id = str(pair["source_relation_ids"][0])
        direct_relation_id = f"{source_relation_id}:eq103"
        direct_record = direct_by_id.get(direct_relation_id)
        _require(
            direct_record is not None,
            f"selected 700 lacks Eq.(120) pair record at {(m, n)}",
        )
        assert direct_record is not None
        expected_pair_bindings.append(
            {
                "indices": [m, n],
                "source_relation_id": source_relation_id,
                "selected_direct_relation_id": direct_relation_id,
                "selected_direct_relation_content_sha256": _stable_hash(direct_record),
                "direct_expression_used_as_source_proof": False,
            }
        )
    _require(
        certificate.get("selected_700_pair_bindings") == expected_pair_bindings,
        "Eq.(120) source proof is not exactly attached to its selected-700 records",
    )

    dependency = _need_dict(
        certificate.get("dependency_closure"),
        "Eq.(120) dependency closure is absent",
    )
    _require(
        dependency.get("B_reduced_expressions_used") is False
        and dependency.get("MSR_used") is False
        and dependency.get("GC_used") is False
        and dependency.get("Eq108_used") is False
        and dependency.get("Eq112_used") is False
        and dependency.get("dependency_closed") is True,
        "forbidden reduction entered the source-native Eq.(120) proof",
    )
    _require(
        certificate.get("counts")
        == {
            "unique_raw_relations": 6,
            "unique_Q_occurrences": 4,
            "unique_B_occurrences": 4,
            "k1_Eq120_instances": 3,
            "selected_direct_pair_bindings": 3,
        },
        "Eq.(120) certificate counts changed",
    )
    chart_gate = _need_dict(
        certificate.get("chart_cover_gate"),
        "Eq.(120) chart-cover gate is absent",
    )
    _require(
        chart_gate.get("partial_slice_955") == "CLOSED_SOURCE_NATIVE_EQ120_PREMISES"
        and chart_gate.get("abstract_R2_R4_partition") == "SOURCE_NATIVE_REUSABLE"
        and chart_gate.get("selected_700_direct_ideal_membership_claimed") is False,
        "Eq.(120) chart-cover scope boundary changed",
    )
    _require(
        certificate.get("verdict") == "V042_EQ120_SOURCE_NATIVE_PROVENANCE_PROVED"
        and certificate.get("passed") is True,
        "source-native Eq.(120) certificate does not emit its proved verdict",
    )
    return {
        "passed": True,
        "path": EQ120_PROVENANCE_PATH,
        "file_sha256": _sha256(certificate_path),
        "semantic_digest_sha256": semantic_digest,
        "schema_version": EQ120_PROVENANCE_SCHEMA,
        "raw_source_relation_count": 6,
        "Q_occurrence_identifier_count": 4,
        "k1_pair_certificate_count": 3,
        "selected_700_pair_binding_count": 3,
        "independent_free_word_recomputation_passed": True,
        "forbidden_semantic_dependencies_absent": True,
        "selected_700_direct_ideal_membership_claimed": False,
    }


def _eq120_premise_binding_audit(
    root: Path,
    artifacts: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Require the Eq.(120) premise, not merely its ratio consequence."""

    classification = artifacts[CLASSIFICATION_PATH]
    inventory = artifacts[INVENTORY_PATH]
    direct = artifacts[DIRECT_PATH]
    f4 = classification.get("phase0", {}).get("F4_R_commutation")
    _need(isinstance(f4, dict), "v0.3.2 classification lacks F4_R_commutation")
    _require(
        f4.get("verified") is True and f4.get("certificate_residual") == [["0", "0"], ["0", "0"]],
        "the exact Eq.(120)-to-ratio implication certificate failed",
    )
    chart_record = (
        inventory.get("chart_reuse_boundary", {})
        .get("ON_QUOTIENT", {})
        .get("independent_exact_check", {})
        .get("Eq120_ratio_commutation_identity")
    )
    _need(isinstance(chart_record, dict), "v0.4.1 inventory lacks the Eq.(120) record")
    _require(
        chart_record.get("source_path") == CLASSIFICATION_PATH
        and chart_record.get("source_sha256") == _sha256(root / CLASSIFICATION_PATH),
        "v0.4.1 Eq.(120) implication is not bound to the v0.3.2 classification",
    )

    source_ledger = _source_eq120_ledger(artifacts)
    selected = [
        record
        for record in direct.get("relations", {}).get(DIRECT_BRANCH, [])
        if record.get("family") == "CPOBC"
    ]
    _require(len(selected) == 700, "selected direct CPOBC count changed")
    exact_matches: dict[str, list[str]] = {}
    target_records: dict[str, list[dict[str, Any]]] = {}
    for left, right in itertools.combinations((2, 3, 4), 2):
        n, m = right, left
        target_expression = _normalise(
            {
                (f"Q_{n}", "Q_1^-1", f"Q_{m}"): 1,
                (f"Q_{m}", "Q_1^-1", f"Q_{n}"): -1,
            }
        )
        target_record = _expression_record(target_expression)
        negative_record = _expression_record(_scale(target_expression, -1))
        label = f"R{left}_R{right}"
        target_records[label] = target_record
        exact_matches[label] = sorted(
            str(record["relation_id"])
            for record in selected
            if record.get("expression") == target_record
            or record.get("expression") == negative_record
        )

    canonical_selected_ids = sorted(str(record["relation_id"]) for record in selected)
    selected_ids_digest = _stable_hash(canonical_selected_ids)
    certificate_path = root / EQ120_PROVENANCE_PATH
    derivation_present = certificate_path.is_file()
    certificate_validation = (
        _validate_eq120_source_certificate(root, artifacts, source_ledger, selected)
        if derivation_present
        else None
    )
    derivation_passed = bool(
        certificate_validation is not None and certificate_validation.get("passed") is True
    )
    literal_binding_passed = all(len(matches) >= 1 for matches in exact_matches.values())
    passed = literal_binding_passed or derivation_passed
    return {
        "passed": passed,
        "status": (
            "EQ120_PREMISES_PROVED_ON_SOURCE_SLICE"
            if passed
            else "MISSING_SOURCE_OR_IDEAL_PROVENANCE_FOR_EQ120_PREMISES"
        ),
        "classification_path": CLASSIFICATION_PATH,
        "classification_sha256": _sha256(root / CLASSIFICATION_PATH),
        "Eq120_to_ratio_commutation_identity_verified": True,
        "independent_source_ledger": source_ledger,
        "k1_target_pullbacks": target_records,
        "literal_selected_700_matches": exact_matches,
        "literal_binding_passed": literal_binding_passed,
        "source_native_certificate_hook": {
            "path": EQ120_PROVENANCE_PATH,
            "required_schema_version": EQ120_PROVENANCE_SCHEMA,
            "required_input_sha256": {
                "source_cpobc_relations": _sha256(root / SOURCE_CPOBC_PATH),
                "generator_reduction": _sha256(root / REDUCTION_PATH),
                "direct_system": _sha256(root / DIRECT_PATH),
            },
            "selected_700_relation_count": len(canonical_selected_ids),
            "selected_700_ordered_relation_ids_sha256": selected_ids_digest,
            "required_pair_indices": [[2, 3], [2, 4], [3, 4]],
            "required_raw_source_relation_count": 6,
            "semantic_digest_rule": (
                "SHA-256 of canonical JSON (sorted keys, compact separators, ASCII) "
                "after removing top-level semantic_digest_sha256"
            ),
        },
        "ideal_or_derivation_certificate_present": derivation_present,
        "ideal_or_derivation_certificate_passed": derivation_passed,
        "source_native_certificate_validation": certificate_validation,
        "missing_gate": (
            None
            if passed
            else (
                "A machine-checkable derivation that the three cleared k=1 "
                "Eq.(120) residuals hold on the nonsingular source reconstruction slice."
            )
        ),
        "claim_boundary": (
            (
                "The source-native proof establishes Eq.(120) on the nonsingular "
                "source locus and hence on its audited reconstruction slice; it "
                "does not claim direct-ideal membership away from that image."
            )
            if derivation_passed
            else (
                "The verified adjugate identity is only an implication with "
                "cleared Eq.(120) as premise; it does not supply that premise."
            )
        ),
    }


def _expected_chart_ids() -> set[str]:
    s1 = {
        f"{CHART_BRANCH}:S1_PIVOT_R{stage}:{coordinate}"
        for stage in (2, 3, 4)
        for coordinate in ("BOTH_NONZERO", "BOTH_ZERO", "LOWER_ONLY", "UPPER_ONLY")
    }
    s2 = {
        f"{CHART_BRANCH}:S2_PIVOT_M{stage}:{coordinate}"
        for stage in (2, 3, 4)
        for coordinate in ("BC_ZERO", "C_NONZERO", "C_ZERO_B_NONZERO")
    }
    return s1 | s2


def _independent_chart_components(request: dict[str, Any]) -> list[dict[str, Any]]:
    import sympy as sp

    symbols = {name: sp.Symbol(name) for name in request.get("variables", [])}
    substitutions = {
        name: sp.sympify(expression, locals=symbols)
        for name, expression in request.get("q_substitutions", {}).items()
    }
    q_matrices = {
        stage: sp.Matrix(
            [
                [substitutions[f"q{stage}_11"], substitutions[f"q{stage}_12"]],
                [substitutions[f"q{stage}_21"], substitutions[f"q{stage}_22"]],
            ]
        )
        for stage in range(1, 5)
    }
    result: list[dict[str, Any]] = []
    for left, right in itertools.combinations(range(1, 5), 2):
        commutator = (
            q_matrices[left] * q_matrices[right] - q_matrices[right] * q_matrices[left]
        ).applyfunc(sp.factor)
        _require(
            sp.expand(commutator[1, 1] + commutator[0, 0]) == 0,
            f"commutator trace identity failed for Q{left},Q{right}",
        )
        for row, column in ((0, 0), (0, 1), (1, 0)):
            expression = commutator[row, column]
            if expression != 0:
                result.append(
                    {
                        "pair": [left, right],
                        "entry": [row, column],
                        "expression": sp.sstr(expression),
                    }
                )
    return result


def _conditional_chart_exhaustiveness_lemma() -> dict[str, Any]:
    import sympy as sp

    alpha, beta, x, y, z, w = sp.symbols("alpha beta x y z w")
    diagonal_pivot = sp.diag(alpha, beta)
    candidate = sp.Matrix([[x, y], [z, w]])
    s1 = diagonal_pivot * candidate - candidate * diagonal_pivot
    nilpotent = sp.Matrix([[0, 1], [0, 0]])
    s2 = nilpotent * candidate - candidate * nilpotent
    s1_expected = sp.Matrix([[0, y * (alpha - beta)], [z * (beta - alpha), 0]])
    s2_expected = sp.Matrix([[z, w - x], [0, -z]])
    s1_centralizer_verified = all(sp.expand(entry) == 0 for entry in (s1 - s1_expected))
    s2_centralizer_verified = all(sp.expand(entry) == 0 for entry in (s2 - s2_expected))
    return {
        "passed": bool(s1_centralizer_verified and s2_centralizer_verified),
        "conditional_on": "pairwise commutation of invertible R2,R3,R4",
        "predicate_partition": (
            "some ratio has distinct eigenvalues (S1); otherwise some ratio is "
            "nonscalar (S2); otherwise all ratios are scalar (S3)"
        ),
        "first_pivot_partition": {
            "ordered_ratio_indices": [2, 3, 4],
            "S1_pivots": 3,
            "S2_pivots": 3,
        },
        "S1_exact_centralizer_verified": s1_centralizer_verified,
        "S1_Q1_coordinate_partition": [
            "b!=0,c!=0",
            "b!=0,c=0",
            "b=0,c!=0",
            "b=0,c=0",
        ],
        "S2_exact_centralizer_verified": s2_centralizer_verified,
        "S2_Q1_coordinate_partition": ["c!=0", "c=0,b!=0", "b=0,c=0"],
        "S3_rule": "R_n=lambda_n I, hence Q_n=lambda_n Q_1",
        "proof_boundary": (
            "This certifies 12+9+1 exhaustiveness only after pairwise ratio "
            "commutation has been established."
        ),
    }


def _chart_and_certificate_audit(
    root: Path,
    artifacts: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    manifest = artifacts[MANIFEST_PATH]
    campaign = artifacts[CAMPAIGN_PATH]
    oracle = artifacts[ORACLE_PATH]
    direct = artifacts[DIRECT_PATH]
    requests = _need_list(manifest.get("requests"), "QQ request list is absent")
    runs = _need_list(campaign.get("runs"), "QQ campaign run list is absent")
    profile_requests = [record for record in requests if record.get("profile") == PROFILE]
    profile_runs = [record for record in runs if record.get("profile") == PROFILE]
    _require(len(profile_requests) == 21, "expected 21 strong-GC QQ requests")
    _require(len(profile_runs) == 21, "expected 21 strong-GC QQ runs")
    _require(
        {str(record.get("chart_cover_id")) for record in profile_requests} == _expected_chart_ids(),
        "S1/S2 chart ID cover differs from the exact 12+9 partition",
    )
    expected_q_names = {
        f"q{stage}_{row}{column}" for stage in range(1, 5) for row in (1, 2) for column in (1, 2)
    }
    direct_records = direct.get("relations", {}).get(DIRECT_BRANCH)
    _need(isinstance(direct_records, list), "literal direct relation branch is absent")
    selected_ids = sorted(
        str(record["relation_id"])
        for record in direct_records
        if record.get("family") in {"CPOBC", "LOCAL_OPERATOR_GC"}
    )
    _require(len(selected_ids) == 955, "direct 955 relation selection changed")
    selected_digest = _stable_hash(selected_ids)
    cover_lemma = _conditional_chart_exhaustiveness_lemma()
    _require(cover_lemma["passed"] is True, "conditional chart-cover lemma failed")
    independently_recomputed_component_count = 0
    for request in profile_requests:
        _require(request.get("coefficient_modulus") == 0, "a profile request is not QQ")
        _require(request.get("saturation") is True, "a profile request omits saturation")
        _require(
            request.get("include_all_transition_predicates") is True,
            "a profile request omits transition nonsingularity",
        )
        _require(
            set(request.get("q_substitutions", {})) == expected_q_names,
            "a profile request does not parameterise exactly Q1--Q4",
        )
        _require(
            request.get("expected_selected_relation_count") == 955
            and request.get("expected_selected_relation_ids_sha256") == selected_digest
            and request.get("expected_relation_family_counts")
            == {"CPOBC": 700, "LOCAL_OPERATOR_GC": 255},
            "a profile request is not bound to the direct 955 core",
        )
        independent_components = _independent_chart_components(request)
        _require(
            request.get("commutator_components") == independent_components,
            f"independent commutator descriptor mismatch at {request.get('chart')}",
        )
        independently_recomputed_component_count += len(independent_components)
    _require(_eq120_ratio_identity(), "independent Eq.(120) ratio identity failed")

    run_by_chart = {str(record["chart"]): record for record in profile_runs}
    request_by_chart = {str(record["chart"]): record for record in profile_requests}
    _require(set(run_by_chart) == set(request_by_chart), "request/run chart sets differ")
    certificate_hashes: dict[str, str] = {}
    empty_count = 0
    no_noncomm_count = 0
    localised_nonempty_count = 0
    inverse_node_ids = {
        str(record["node_id"])
        for record in direct.get("dependency_nodes", [])
        if record.get("kind") in {"Q_GENERATOR_INVERSE", "FORMAL_TWO_SIDED_INVERSE_AUXILIARY"}
    }
    occurrence_ids = {
        str(record["occurrence_id"])
        for record in direct.get("reconstructed_transition_predicates", [])
    }
    _require(len(inverse_node_ids) == 26, "factor audit expected 26 inverse node IDs")
    _require(len(occurrence_ids) == 165, "factor audit expected 165 occurrence IDs")

    def delimited_identifier(origin: str, prefix: str, suffix: str) -> str | None:
        if origin.startswith(prefix) and origin.endswith(suffix):
            return origin[len(prefix) : len(origin) - len(suffix)]
        return None

    for chart in request_by_chart:
        run = run_by_chart[chart]
        certificate_path = run.get("certificate")
        _need(isinstance(certificate_path, str), f"certificate path absent for {chart}")
        path = root / certificate_path
        _need(path.is_file(), f"certificate absent for {chart}")
        certificate = json.loads(path.read_text(encoding="utf-8"))
        digest = _sha256(path)
        certificate_hashes[chart] = digest
        _require(run.get("certificate_sha256") == digest, f"certificate hash mismatch at {chart}")
        for key in (
            "chart",
            "chart_cover_id",
            "stratum",
            "request_semantic_digest_sha256",
            "selected_relation_ids_sha256",
            "selected_relation_family_counts",
            "chart_verdict",
        ):
            _require(run.get(key) == certificate.get(key), f"run/certificate {key} mismatch")
        _require(certificate.get("coefficient_field") == "QQ", f"non-QQ certificate at {chart}")
        _require(certificate.get("proof_eligible") is True, f"ineligible proof at {chart}")
        _require(
            certificate.get("selected_matrix_relation_count") == 955
            and certificate.get("selected_relation_ids_sha256") == selected_digest,
            f"certificate not bound to the 955 core at {chart}",
        )
        _require(
            certificate.get("relation_selection_checks_passed") is True,
            f"relation selection failed at {chart}",
        )
        _require(
            certificate.get("final_localisation_complete") is True,
            f"localisation incomplete at {chart}",
        )
        _require(
            certificate.get("commutator_coverage_complete") is True,
            f"commutator coverage incomplete at {chart}",
        )
        _require(certificate.get("zero_required_factor") is False, f"zero factor at {chart}")
        verdict = certificate.get("chart_verdict")
        _require(
            verdict in {"EXACT_EMPTY_CHART", "EXACT_NO_NONCOMMUTATIVE_SOLUTION_IN_CHART"},
            f"chart not exactly closed at {chart}",
        )
        for factor in certificate.get("inverse_factor_records", []):
            kind = factor.get("kind")
            origin = str(factor.get("origin"))
            if kind == "INVERSE_SITE":
                identifier = delimited_identifier(origin, "det(", ")")
                _require(
                    identifier in inverse_node_ids,
                    f"unknown inverse-site factor origin at {chart}: {origin}",
                )
            elif kind == "RECONSTRUCTED_TRANSITION":
                identifier = delimited_identifier(origin, "det(", ")")
                _require(
                    identifier in occurrence_ids,
                    f"unknown transition factor origin at {chart}: {origin}",
                )
            elif kind == "RATIONAL_DENOMINATOR":
                identifier = delimited_identifier(origin, "denominator(det(", "))")
                _require(
                    identifier in inverse_node_ids | occurrence_ids,
                    f"unknown rational-denominator origin at {chart}: {origin}",
                )
            else:
                raise InvalidEvidence(f"unclassified localisation factor at {chart}")
        if verdict == "EXACT_EMPTY_CHART":
            empty_count += 1
        else:
            no_noncomm_count += 1
            localised_nonempty_count += 1
            _require(
                certificate.get("reconstructed_transitions_checked") == 165,
                f"nonempty chart does not check all transitions at {chart}",
            )
    _require((empty_count, no_noncomm_count) == (12, 9), "expected 12 empty and 9 no-go charts")

    oracle_profile = _need_dict(
        oracle.get("profile_results", {}).get(PROFILE),
        "independent oracle lacks the strong-GC profile",
    )
    _require(
        oracle_profile.get("chart_count") == 21 and oracle_profile.get("exact_closed") == 21,
        "independent oracle does not close all 21 strong-GC charts",
    )
    oracle_core = _need_dict(
        oracle_profile.get("core"),
        "independent oracle lacks the 955 core ledger",
    )
    _require(
        oracle_core.get("sha256") == selected_digest
        and oracle_core.get("family_counts") == {"CPOBC": 700, "LOCAL_OPERATOR_GC": 255},
        "independent oracle core binding differs",
    )
    oracle_hashes = _need_dict(
        oracle.get("certificate_sha256_by_chart"),
        "independent oracle lacks certificate hashes",
    )
    _require(
        all(oracle_hashes.get(chart) == digest for chart, digest in certificate_hashes.items()),
        "independent oracle certificate hashes differ",
    )

    s3 = _need_dict(
        manifest.get("chart_cover", {}).get("S3_structural_certificate"),
        "S3 structural certificate is absent",
    )
    _require(
        s3.get("passed") is True
        and s3.get("Q_indices") == [1, 2, 3, 4]
        and s3.get("commutator_component_count") == 0,
        "S3 structural certificate changed",
    )
    return {
        "passed": True,
        "Eq120_ratio_identity_independently_verified": True,
        "S1_chart_count": 12,
        "S2_chart_count": 9,
        "S3_structurally_commuting": True,
        "conditional_exhaustiveness_lemma": cover_lemma,
        "independently_recomputed_nonzero_commutator_component_count": (
            independently_recomputed_component_count
        ),
        "all_omitted_commutator_components_independently_zero": True,
        "QQ_exact_empty_chart_count": empty_count,
        "QQ_exact_no_noncommutative_solution_chart_count": no_noncomm_count,
        "nonempty_charts_with_all_165_transition_predicates": localised_nonempty_count,
        "independent_oracle_bound": True,
        "certificate_set_sha256": _stable_hash(dict(sorted(certificate_hashes.items()))),
        "proof_rule": (
            "Conditional on Eq.(120), R2,R3,R4 commute on det(Q1)!=0.  The "
            "exact d=2 S1/S2/S3 simultaneous-form partition gives 12+9+1 charts.  The "
            "21 S1/S2 QQ certificates close every noncommutative Q1--Q4 branch; "
            "S3 commutes identically."
        ),
    }


def _proved_payload(root: Path) -> dict[str, Any]:
    required_paths = (
        SOURCE_CPOBC_PATH,
        REDUCTION_PATH,
        LOCAL_GC_PATH,
        Q_PRESENTATION_PATH,
        CLASSIFICATION_PATH,
        DIRECT_PATH,
        INVENTORY_PATH,
        MANIFEST_PATH,
        CAMPAIGN_PATH,
        ORACLE_PATH,
    )
    artifacts = {path: _load(root, path) for path in required_paths}
    checks: dict[str, dict[str, Any]] = {
        "artifact_integrity": _artifact_integrity(root, artifacts),
        "CPOBC_pullback": _cpobc_pullback_audit(artifacts),
        "strong_GC_pullback": _gc_pullback_audit(artifacts),
        "inverse_and_nonsingularity": _inverse_and_nonsingularity_audit(artifacts),
        "Eq120_premise_binding": _eq120_premise_binding_audit(root, artifacts),
        "chart_cover_and_QQ_certificates": _chart_and_certificate_audit(root, artifacts),
    }
    foundational_checks = (
        "artifact_integrity",
        "CPOBC_pullback",
        "strong_GC_pullback",
        "inverse_and_nonsingularity",
        "chart_cover_and_QQ_certificates",
    )
    _require(
        all(checks[name]["passed"] for name in foundational_checks),
        "a foundational partial-slice gate failed",
    )
    theorem_proved = checks["Eq120_premise_binding"]["passed"] is True
    verdict = VERDICT_PROVED if theorem_proved else VERDICT_UNRESOLVED
    payload: dict[str, Any] = {
        "schema_version": SCHEMA,
        "finite_scope": "ON quotient; n<=4; d=2; nonsingular; characteristic zero",
        "source_profile": {
            "name": PROFILE,
            "P": "source-native CPOBC + strong GC + reachable-state MSR + nonsingularity",
            "reachable_state_MSR_role": (
                "Retained in P but not used by the forward pullback into D_955; "
                "dropping an equation enlarges the direct target locus."
            ),
        },
        "maps_and_loci": {
            "Phi_U": (
                "the frozen 165-occurrence rational reconstruction on the open "
                "domain U where its 4 Q and 22 B inverse bases are nonsingular"
            ),
            "D_955": (
                "the U-locus satisfying exactly the 700 CPOBC and 255 "
                "local-operator-GC direct matrix relations, together with all "
                "165 reconstructed-transition nonsingularity predicates"
            ),
            "source_point": "x in P",
            "Q_preimage": "q in U with Phi_U(q)=x",
            "auxiliary_inverse_coordinates": (
                "not independent in d=2; they are adjugate/determinant values "
                "at the 4 Q and 22 B inverse bases"
            ),
            "chart_cover": (
                "the simultaneous-similarity S1/S2/S3 cover of commuting R_n=Q_1^-1 Q_n for n=2,3,4"
            ),
        },
        "inclusion": {
            "direction": "P intersection image(Phi_U) subset Phi_U(D_955)",
            "relation_locus_inclusion_proved": True,
            "quantified_relation_locus_form": (
                "For every x in P and every q in U with Phi_U(q)=x, q satisfies "
                "the 700+255 direct relations and all audited nonsingularity sites."
            ),
            "commutativity_consequence_proved": theorem_proved,
            "commutativity_gap": (
                None
                if theorem_proved
                else (
                    "The 21+S3 charts exhaust only the pairwise-commuting-ratio "
                    "locus; no artifact binds the three k=1 Eq.(120) premises "
                    "to the nonsingular source reconstruction slice."
                )
            ),
            "reverse_inclusion_claimed": False,
            "full_profile_coverage_claimed": False,
        },
        "checks": checks,
        "certificate_interpretation": {
            "certificates_total_in_historical_campaign": 42,
            "certificates_used_for_this_partial_theorem": 21,
            "used_profile": PROFILE,
            "established_here": (
                (
                    "The independently bound source-native Eq.(120) proof, the 21 "
                    "955-core certificates, and S3 prove Q1--Q4 commutativity on "
                    "P intersection image(Phi_U)."
                )
                if theorem_proved
                else (
                    "Conditionally on the missing Eq.(120)-premise binding, the 21 "
                    "955-core certificates plus S3 prove Q1--Q4 commutativity on "
                    "P intersection image(Phi_U).  Unconditionally they close only "
                    "the chart-covered commuting-ratio sublocus."
                )
            ),
            "other_21_certificates": (
                "They close the separate 721 reduced core arithmetically, but "
                "this audit does not assert its source-profile slice inclusion."
            ),
        },
        "claim_boundary": (
            (
                "The source-to-955 relation-locus inclusion, localisation, and "
                "source-native Eq.(120) proof establish the partial commutativity "
                "theorem on P intersection image(Phi_U).  No conclusion is obtained "
                "on P minus image(Phi_U), and no full-profile theorem is claimed."
            )
            if theorem_proved
            else (
                "The source-to-955 relation-locus inclusion and localisation are "
                "proved.  The partial commutativity theorem remains unresolved until "
                "Eq.(120) is attached to the source slice.  No conclusion is obtained "
                "on P minus image(Phi_U), and no full-profile theorem is claimed."
            )
        ),
        "passed": theorem_proved,
        "verdict": verdict,
    }
    payload["semantic_digest_sha256"] = _stable_hash(payload)
    return payload


def audit_partial_slice_v041(root: Path) -> dict[str, Any]:
    """Return one of the three required fail-closed audit verdicts."""

    root = root.resolve()
    try:
        return _proved_payload(root)
    except MissingProvenance as exc:
        payload: dict[str, Any] = {
            "schema_version": SCHEMA,
            "passed": False,
            "verdict": VERDICT_UNRESOLVED,
            "failure": str(exc),
            "claim_boundary": "No partial-slice theorem is emitted when a map is absent.",
        }
    except (InvalidEvidence, KeyError, TypeError, ValueError) as exc:
        payload = {
            "schema_version": SCHEMA,
            "passed": False,
            "verdict": VERDICT_INVALID,
            "failure": str(exc),
            "claim_boundary": "Contradictory or malformed evidence invalidates the audit.",
        }
    payload["semantic_digest_sha256"] = _stable_hash(payload)
    return payload


def write_partial_slice_audit_v041(root: Path, payload: dict[str, Any]) -> Path:
    """Write the deterministic audit artifact."""

    path = root.resolve() / RESULT_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return path
