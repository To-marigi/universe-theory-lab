from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

from universe_lab.final_theory.cpobc_d2_v032 import generator_reduction_v032

ROOT = Path(__file__).resolve().parents[2]
TARGET_IDS = {"msr:p1-0", "msr:p2-0", "msr:p2-2"}
ZERO_DIGEST = "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945"


def _residual_from_source_constraint(
    constraint: dict[str, object],
    reduction_map: dict[str, dict[str, object]],
) -> dict[tuple[str, ...], int]:
    """Independently add the source MSR terms after their stored Q lift."""

    residual: defaultdict[tuple[str, ...], int] = defaultdict(int)
    residual[()] = -1
    terms = constraint["terms"]
    assert isinstance(terms, list)
    for term in terms:
        assert isinstance(term, dict)
        lifted = reduction_map[term["transition_id"]]
        summands = lifted["reduced_expression"]
        assert isinstance(summands, list)
        for summand in summands:
            assert isinstance(summand, dict)
            residual[tuple(summand["word"])] += (
                int(term["coefficient"]) * int(summand["coefficient"])
            )
    return {word: coefficient for word, coefficient in residual.items() if coefficient}


def test_v042_scout_msr_candidates_have_unique_zero_q_lifts() -> None:
    """The three scout labels are source constraints, not omitted Q equations."""

    source = json.loads(
        (ROOT / "results/v0.3.1_cpobc_relations_n4.json").read_text(
            encoding="utf-8"
        )
    )
    reduction = generator_reduction_v032()
    reduction_map = {
        record["occurrence_id"]: record for record in reduction["reduction_map"]
    }
    source_constraints = {
        record["constraint_id"]: record
        for record in source["MSR_operator_constraints"]
        if record["constraint_id"] in TARGET_IDS
    }
    assert set(source_constraints) == TARGET_IDS
    assert all(
        _residual_from_source_constraint(constraint, reduction_map) == {}
        for constraint in source_constraints.values()
    )

    rewritten = {
        record["constraint_id"]: record
        for record in reduction["rewritten_MSR_inventory"]
        if record["constraint_id"] in TARGET_IDS
    }
    assert set(rewritten) == TARGET_IDS
    assert all(
        record["missing_occurrences"] == []
        and record["reduced_residual"] == []
        and record["reduced_residual_sha256"] == ZERO_DIGEST
        and record["identity_after_reduction"]
        for record in rewritten.values()
    )

    presentation = json.loads(
        (ROOT / "results/v0.3.3_q_only_presentation_n4.json").read_text(
            encoding="utf-8"
        )
    )
    assert {
        record["constraint_id"]
        for record in presentation["relation_inventory"]["strong_MSR_identities"]
    } == TARGET_IDS

    direct = json.loads(
        (ROOT / "certificates/d2_saturation/v0.3.5_direct_operator_system.json").read_text(
            encoding="utf-8"
        )
    )
    for branch, records in direct["relations"].items():
        assert len(records) == 1001, branch
        assert not {
            record["relation_id"] for record in records
        }.intersection(TARGET_IDS)
