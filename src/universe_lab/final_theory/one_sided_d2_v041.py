"""Static v0.4.1 inventory for the two unresolved one-sided d=2 profiles.

This compiler records frozen finite inputs and conservative elimination cores.  It
does not prepare or execute a Sage/Singular request: an authorised v0.4.1 budget
is an external prerequisite, and even a supplied budget is not execution.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "final-theory-one-sided-d2-v0.4.1"
VERSION = "0.4.1"
VERDICT = "V041_INVENTORY_READY_ELIMINATION_NOT_RUN"
GLOBAL_VERDICT = "FINAL_THEORY_OPEN"
ON_QUOTIENT = "ON_QUOTIENT"
OFF_NATURALLY_LABELLED = "OFF_NATURALLY_LABELLED"
HUMAN_BUDGET_REQUIRED = "HUMAN_BUDGET_REQUIRED"
HUMAN_BUDGET_PRESENT = "HUMAN_BUDGET_PRESENT_ELIMINATION_NOT_RUN"
BUDGET_PATH = "config/v0.4.1_budget.json"
RESULT_PATH = "results/v0.4.1_one_sided_inventory.json"

ARTIFACT_PATHS = (
    "results/v0.4_weak_d2_classification.json",
    "results/v0.3.7_q5_free_partition.json",
    "certificates/d2_saturation/v0.3.5_direct_operator_system.json",
    "results/v0.3.3_local_operator_gc_n4.json",
    "results/v0.3.1_cpobc_relations_n4.json",
    "results/v0.3.2_cpobc_generator_reduction.json",
    "results/v0.3.2_cpobc_d2_classification.json",
    "results/v0.3.3_eq112_reduction_n4.json",
    "results/v0.3.3_atomisation_paths_n4.json",
)
# The identity justifying the ratio strata and the later exact chart result are
# pinned separately: neither may stand in for the other.
EXACT_F4_IDENTITY_PATH = "results/v0.3.2_cpobc_d2_classification.json"
EXACT_CHART_PATH = "results/v0.3.7_q5_free_elimination.json"
PINNED_ARTIFACT_HASHES = {
    "results/v0.4_weak_d2_classification.json": (
        "18e71f439913896fb370944c6479fc358d4d6d0d127162809ba46822ccd2fe65"
    ),
    "results/v0.3.7_q5_free_partition.json": (
        "7c4611e04f2c8d070b8652746a7830ea08e8e3257f22bde36ad03dc781d60f02"
    ),
    "certificates/d2_saturation/v0.3.5_direct_operator_system.json": (
        "5fa2cbd16503d8cd16bc09db07d3b82c1e25df17fcd133cb472875e0e5408e56"
    ),
    "results/v0.3.3_local_operator_gc_n4.json": (
        "7e884ad9bff83e9e1aba8048759802bcffddd4cffc4e59dbd6b799d4860f93ba"
    ),
    "results/v0.3.1_cpobc_relations_n4.json": (
        "8e9498fd6be13ff7553f1e3d2df6919b5a1595294a8feb2134467c63c5c1dda9"
    ),
    "results/v0.3.2_cpobc_generator_reduction.json": (
        "88363a527e7f015457f51ae94da5ac5e03c83fca588fe07a8bfd9e4fbb0ca52b"
    ),
    EXACT_F4_IDENTITY_PATH: ("c38b78ff66df02e1c628e165ea3c84a54779cc88adfa9f6cda88864f7dd2b719"),
    "results/v0.3.3_eq112_reduction_n4.json": (
        "e217862b767eb69c946a5b011d43957c608d1c4748192ce8a5562193ada61678"
    ),
    "results/v0.3.3_atomisation_paths_n4.json": (
        "b7c12b280ea80132c6d6ff967da7bd2ef64fa2b3ef6cf10ef0345c2162549980"
    ),
    EXACT_CHART_PATH: ("4c394fd5e4b864f3bb34debee51d536b1828c0f9a0d3a64b1d09142ef3b3ff14"),
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _stable_hash(value: Any) -> str:
    encoded = json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )
    return hashlib.sha256(encoded).hexdigest()


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def budget_gate_v041(root: Path) -> dict[str, Any]:
    """Fail closed when the distinct v0.4.1 human budget has not been supplied."""

    path = root.resolve() / BUDGET_PATH
    if not path.is_file():
        return {
            "expected_path": BUDGET_PATH,
            "status": HUMAN_BUDGET_REQUIRED,
            "elimination_executed": False,
            "fallback_budget_used": False,
            "reason": "No v0.4.1 budget is present; v0.3.7 is never a fallback.",
        }
    supplied = _load(path)
    required = {
        "timeout_seconds_per_chart",
        "total_wall_time_seconds",
        "memory_limit_gib",
    }
    missing = sorted(required - supplied.keys())
    unsupported = sorted(supplied.keys() - required)
    if missing:
        raise ValueError(f"v0.4.1 budget is missing required keys: {missing}")
    if unsupported:
        raise ValueError(f"v0.4.1 budget has unsupported keys: {unsupported}")
    values: dict[str, float] = {}
    for name in sorted(required):
        value = supplied[name]
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise TypeError(f"v0.4.1 budget {name} must be numeric")
        if not math.isfinite(float(value)) or float(value) <= 0:
            raise ValueError(f"v0.4.1 budget {name} must be positive and finite")
        values[name] = float(value)
    if values["timeout_seconds_per_chart"] > values["total_wall_time_seconds"]:
        raise ValueError("v0.4.1 per-chart timeout cannot exceed total wall time")
    return {
        "expected_path": BUDGET_PATH,
        "status": HUMAN_BUDGET_PRESENT,
        "sha256": _sha256(path),
        "authorised_limits": {
            "timeout_seconds_per_chart": int(values["timeout_seconds_per_chart"]),
            "total_wall_time_seconds": int(values["total_wall_time_seconds"]),
            "memory_limit_gib": values["memory_limit_gib"],
        },
        "elimination_executed": False,
        "fallback_budget_used": False,
        "reason": "A budget authorises a later human-directed run; this compiler is static.",
    }


def _bound_artifacts(root: Path) -> tuple[dict[str, dict[str, Any]], dict[str, str]]:
    loaded: dict[str, dict[str, Any]] = {}
    hashes: dict[str, str] = {}
    for relative in (*ARTIFACT_PATHS, EXACT_CHART_PATH):
        path = root / relative
        actual = _sha256(path)
        expected = PINNED_ARTIFACT_HASHES[relative]
        if actual != expected:
            raise AssertionError(f"pinned artifact changed: {relative}")
        loaded[relative] = _load(path)
        hashes[relative] = actual
    return loaded, hashes


def _relation_sets(partition: dict[str, Any], direct: dict[str, Any]) -> dict[str, dict[str, Any]]:
    shared_ids = sorted(partition["shared_core"]["matrix_relation_ids"])
    literal = direct["relations"]["LITERAL_PRINTED_QN_PLUS_1_BRANCH"]
    by_id = {record["relation_id"]: record for record in literal}
    if set(shared_ids) - set(by_id):
        raise AssertionError("Q5-free relation IDs are absent from the direct system")
    families = {relation_id: by_id[relation_id]["family"] for relation_id in shared_ids}
    counts = dict(sorted(Counter(families.values()).items()))
    expected = {"CPOBC": 700, "LOCAL_OPERATOR_GC": 255, "STRONG_OPERATOR_MSR": 21}
    if len(shared_ids) != 976 or counts != expected:
        raise AssertionError("the frozen Q5-free relation-family partition changed")
    if _stable_hash(shared_ids) != partition["shared_core"]["matrix_relation_ids_sha256"]:
        raise AssertionError("the Q5-free relation-ID digest changed")
    by_family = {
        family: sorted(identifier for identifier, found in families.items() if found == family)
        for family in expected
    }
    core_a = sorted(by_family["CPOBC"] + by_family["STRONG_OPERATOR_MSR"])
    core_b = sorted(by_family["CPOBC"] + by_family["LOCAL_OPERATOR_GC"])
    if len(core_a) != 721 or len(core_b) != 955:
        raise AssertionError("one-sided ablation core count changed")
    return {
        "q5_free_relation_ids": {
            "ids": shared_ids,
            "count": len(shared_ids),
            "sha256": _stable_hash(shared_ids),
        },
        "families": {
            family: {"ids": ids, "count": len(ids), "sha256": _stable_hash(ids)}
            for family, ids in sorted(by_family.items())
        },
        "fixed_vector_GC__strong_MSR": {
            "ids": core_a,
            "count": len(core_a),
            "sha256": _stable_hash(core_a),
        },
        "strong_GC__reachable_state_MSR": {
            "ids": core_b,
            "count": len(core_b),
            "sha256": _stable_hash(core_b),
        },
    }


def compile_one_sided_d2_v041(root: Path) -> dict[str, Any]:
    """Compile the finite static inventory, without elimination or solver calls."""

    root = root.resolve()
    artifacts, hashes = _bound_artifacts(root)
    weak = artifacts["results/v0.4_weak_d2_classification.json"]
    partition = artifacts["results/v0.3.7_q5_free_partition.json"]
    direct = artifacts["certificates/d2_saturation/v0.3.5_direct_operator_system.json"]
    gc = artifacts["results/v0.3.3_local_operator_gc_n4.json"]
    cpobc = artifacts["results/v0.3.1_cpobc_relations_n4.json"]
    reduction = artifacts["results/v0.3.2_cpobc_generator_reduction.json"]
    eq112 = artifacts["results/v0.3.3_eq112_reduction_n4.json"]
    f4_identity = artifacts[EXACT_F4_IDENTITY_PATH]["phase0"]["F4_R_commutation"]
    exact_charts = artifacts[EXACT_CHART_PATH]
    relation_sets = _relation_sets(partition, direct)

    on_counts = {
        "quotient_transition_variables": 131,
        "reduction_records_or_aliases": len(reduction["reduction_map"]),
        "CPOBC_records": len(cpobc["relations"]),
        "CPOBC_raw_word_equations": cpobc["counts"]["denominator_cleared_word_equations"],
        "CPOBC_inverse_rewrites": weak["direct_substitution"]["CPOBC_inverse_forms"][
            "checked_inverse_containing_equations"
        ],
        "MSR_source_constraints": len(cpobc["MSR_operator_constraints"]),
        "GC_spanning_tree_basis": gc["counts"]["spanning_tree_basis_relations"],
        "GC_all_same_endpoint_pairs": len(gc["all_pair_derivations"]),
    }
    if on_counts != {
        "quotient_transition_variables": 131,
        "reduction_records_or_aliases": 165,
        "CPOBC_records": 641,
        "CPOBC_raw_word_equations": 783,
        "CPOBC_inverse_rewrites": 712,
        "MSR_source_constraints": 24,
        "GC_spanning_tree_basis": 320,
        "GC_all_same_endpoint_pairs": 1529,
    }:
        raise AssertionError("ON quotient inventory count changed")
    labelled_paths = gc["counts"]["labelled_paths_by_endpoint_stage"]
    source_nodes_by_stage = {str(stage): labelled_paths[str(stage)] for stage in range(1, 5)}
    outgoing_by_stage = {str(stage): labelled_paths[str(stage + 1)] for stage in range(1, 5)}
    off_counts = {
        "labelled_transition_occurrences": gc["counts"]["labelled_transition_occurrences"],
        "source_nodes_by_stage": source_nodes_by_stage,
        "source_nodes_total": sum(source_nodes_by_stage.values()),
        "outgoing_transitions_by_source_stage": outgoing_by_stage,
    }
    if off_counts != {
        "labelled_transition_occurrences": 406,
        "source_nodes_by_stage": {"1": 1, "2": 2, "3": 7, "4": 40},
        "source_nodes_total": 50,
        "outgoing_transitions_by_source_stage": {"1": 2, "2": 7, "3": 40, "4": 357},
    }:
        raise AssertionError("OFF naturally labelled GC occurrence count changed")

    eq113 = eq112["path_consistency_branches"]
    eq139 = weak["direct_substitution"]["Eq139"]["branches"]
    chart_proof = {
        "Eq120_ratio_commutation_identity": {
            "source_path": EXACT_F4_IDENTITY_PATH,
            "source_sha256": hashes[EXACT_F4_IDENTITY_PATH],
            "identity": f4_identity["identity"],
            "assumption": f4_identity["assumption"],
            "certificate_residual": f4_identity["certificate_residual"],
            "verified": f4_identity["verified"],
        },
        "exact_chart_result_path": EXACT_CHART_PATH,
        "exact_chart_result_sha256": hashes[EXACT_CHART_PATH],
        "QQ_exact_resolved_chart_count": exact_charts["QQ_exact_resolved_chart_count"],
        "ratio_indices": exact_charts["chart_geometry"]["ratio_indices"],
        "all_R2_R3_R4_commuting_ratio_strata_covered": exact_charts["complete_chart_cover"][
            "all_R2_R3_R4_commuting_ratio_strata_covered"
        ],
        "shared_core_forces_Q1_Q4_commutativity": exact_charts["literal_forward_implication"][
            "Q5_free_shared_core_forces_Q1_Q4_commutativity"
        ],
    }
    if (
        chart_proof["Eq120_ratio_commutation_identity"]["verified"] is not True
        or chart_proof["Eq120_ratio_commutation_identity"]["certificate_residual"]
        != [["0", "0"], ["0", "0"]]
        or chart_proof["QQ_exact_resolved_chart_count"] != 21
        or chart_proof["ratio_indices"] != [2, 3, 4]
    ):
        raise AssertionError("the independently pinned R2--R4 exact chart result changed")

    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "version": VERSION,
        "finite_scope": "frozen source stages n<=4; static inventory only",
        "source_artifacts": hashes,
        "identification_modes": {
            ON_QUOTIENT: {"status": "COMPILED", "counts": on_counts},
            OFF_NATURALLY_LABELLED: {
                "status": "MECHANICALLY_AVAILABLE_FROM_GC_ARTIFACT_ONLY",
                "counts": off_counts,
                "not_compiled": {
                    "labelled_CPOBC_lift": "NOT_YET_COMPILED",
                    "labelled_MSR_lift": "NOT_YET_COMPILED",
                    "labelled_Eq113_lift": "NOT_YET_COMPILED",
                    "labelled_Eq139_lift": "NOT_YET_COMPILED",
                },
                "no_165_OFF_claim": True,
            },
        },
        "profiles": {
            "fixed_vector_GC__strong_MSR": {
                "identification_modes": {
                    ON_QUOTIENT: "STATIC_CORE_COMPILED_FULL_VECTOR_PROFILE_NOT_MATERIALISED",
                    OFF_NATURALLY_LABELLED: "OPEN_LABELLED_LIFTS_NOT_COMPILED",
                },
                "conservative_sufficient_no_go_core": "fixed_vector_GC__strong_MSR",
            },
            "strong_GC__reachable_state_MSR": {
                "identification_modes": {
                    ON_QUOTIENT: "STATIC_CORE_COMPILED_FULL_VECTOR_PROFILE_NOT_MATERIALISED",
                    OFF_NATURALLY_LABELLED: "OPEN_LABELLED_LIFTS_NOT_COMPILED",
                },
                "conservative_sufficient_no_go_core": "strong_GC__reachable_state_MSR",
            },
        },
        "full_ON_profile_inventory": {
            "fixed_vector_GC__strong_MSR": {
                "CPOBC": {
                    "source_relation_records": on_counts["CPOBC_records"],
                    "raw_word_equations": on_counts["CPOBC_raw_word_equations"],
                    "Q5_free_reduced_matrix_relations": 700,
                },
                "fixed_vector_GC": {
                    "source_basis_relations": on_counts["GC_spanning_tree_basis"],
                    "all_pair_equalities": on_counts["GC_all_same_endpoint_pairs"],
                    "components_per_relation": 2,
                    "strength": "VECTOR_EQUALITY_ON_FIXED_INITIAL_VECTOR",
                    "materialisation_status": "VECTOR_POLYNOMIALS_NOT_YET_COMPILED",
                },
                "strong_MSR": {
                    "source_constraints": on_counts["MSR_source_constraints"],
                    "Q5_free_nontrivial_reduced_matrix_relations": 21,
                    "components_per_relation": 4,
                    "strength": "OPERATOR_IDENTITY",
                },
            },
            "strong_GC__reachable_state_MSR": {
                "CPOBC": {
                    "source_relation_records": on_counts["CPOBC_records"],
                    "raw_word_equations": on_counts["CPOBC_raw_word_equations"],
                    "Q5_free_reduced_matrix_relations": 700,
                },
                "strong_GC": {
                    "source_basis_relations": on_counts["GC_spanning_tree_basis"],
                    "all_pair_equalities": on_counts["GC_all_same_endpoint_pairs"],
                    "Q5_free_nontrivial_reduced_matrix_relations": 255,
                    "components_per_relation": 4,
                    "strength": "OPERATOR_IDENTITY",
                },
                "reachable_state_MSR": {
                    "source_constraints": on_counts["MSR_source_constraints"],
                    "components_per_relation": 2,
                    "strength": "VECTOR_EQUALITY_ON_DECLARED_REACHABLE_STATE",
                    "materialisation_status": "VECTOR_POLYNOMIALS_NOT_YET_COMPILED",
                },
            },
        },
        "q5_free_relation_inventory": relation_sets,
        "ablation_core_interpretation": {
            "tag": "CONSERVATIVE_SUFFICIENT_NO_GO_CORE",
            "forward_rule": (
                "If a core forces Q1--Q4 commutativity, its corresponding one-sided "
                "full profile is proved commutative."
            ),
            "survival_rule": (
                "Survival of a core is not a counterexample to the corresponding full profile."
            ),
            "excluded_weak_constraints": {
                "fixed_vector_GC": "EXCLUDED_FROM_STRONG_MSR_CORE",
                "reachable_state_MSR": "EXCLUDED_FROM_STRONG_GC_CORE",
            },
            "excluded_Eq112_path_family": {
                "status": "EXCLUDED_FROM_ABLATION_CORES",
                "relation_count_per_branch": 25,
                "reason": "Q5-free shared core excludes EQ112_PATH_CONSISTENCY.",
            },
        },
        "supplemental_full_profile_gates": {
            "status": "NOT_SILENTLY_MERGED_INTO_ABLATION_CORE",
            "Eq113": {
                "derived_branch": {
                    "count": len(eq113["EQ113_QN_BRANCH"]),
                    "status": "SUPPLEMENTAL",
                },
                "literal_branch": {
                    "count": len(eq113["EQ113_QN_PLUS_1_BRANCH"]),
                    "status": "SUPPLEMENTAL",
                },
                "branches_kept_separate": True,
            },
            "Eq139": {
                "PRINTED_STRICT": {
                    "count": eq139["EQ139_PRINTED_STRICT_M_K_LT_N"]["instance_count"],
                    "status": "SUPPLEMENTAL",
                },
                "EQ145_COMPLETED": {
                    "count": eq139["EQ139_EQ145_COMPLETED_M_K_LE_N"]["instance_count"],
                    "status": "SUPPLEMENTAL",
                },
                "domains_kept_separate": True,
            },
        },
        "triangular_scout": {
            "status": "BOUNDED_EXACT_TRIANGULAR_SCOUT_NOT_GENERAL_D2_PROOF",
            "source_classification": weak["triangular_profile_scout"]["classification"],
            "profiles": {
                name: weak["triangular_profile_scout"]["profiles"][name]
                for name in (
                    "fixed_vector_GC__strong_MSR",
                    "strong_GC__reachable_state_MSR",
                )
            },
        },
        "chart_reuse_boundary": {
            "ON_QUOTIENT": {
                "reuse_status": "CONDITIONALLY_REUSABLE_AFTER_INDEPENDENT_F4_BINDING",
                "condition": "Retained CPOBC Eq120 implies pairwise commuting R_n=Q1^-1 Q_n.",
                "independent_exact_check": chart_proof,
                "chart_count": 21,
            },
            "OFF_NATURALLY_LABELLED": {
                "reuse_status": "NOT_AVAILABLE",
                "reason": (
                    "No Q-level reduction may be reused before the labelled lift is compiled."
                ),
            },
        },
        "budget_gate": budget_gate_v041(root),
        "elimination": {
            "elimination_executed": False,
            "solver_invoked": False,
            "elimination_result_claim": "NONE",
        },
        "verdict": VERDICT,
        "global_scientific_verdict": GLOBAL_VERDICT,
        "passed": True,
        "claim_boundary": (
            "This is an ON-quotient inventory of conservative sufficient cores, not an "
            "elimination result or an OFF-labelled lift."
        ),
    }
    payload["semantic_digest_sha256"] = semantic_digest(payload)
    return payload


def semantic_digest(payload: dict[str, Any]) -> str:
    """Return the stable digest excluding the self-referential digest field."""

    return _stable_hash(
        {key: value for key, value in payload.items() if key != "semantic_digest_sha256"}
    )


def write_one_sided_d2_v041_result(root: Path, payload: dict[str, Any]) -> Path:
    """Write the inventory in canonical repository location with LF line endings."""

    path = root.resolve() / RESULT_PATH
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return path
