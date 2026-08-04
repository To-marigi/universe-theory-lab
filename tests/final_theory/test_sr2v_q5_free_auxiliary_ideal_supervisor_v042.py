"""Fast behavioural tests for the SR2-V auxiliary-ideal supervisor primitives."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import pytest

from universe_lab.final_theory import sr2v_q5_free_auxiliary_ideal_supervisor_v042 as sup


def _budget_payload(**updates: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "timeout_seconds_per_chart": 10,
        "total_wall_time_seconds": 100,
        "memory_limit_gib": 8,
    }
    payload.update(updates)
    return payload


def _fingerprint(
    *, chart: str = "U2", policy: dict[str, object] | None = None
) -> sup.AttemptFingerprint:
    budget = sup.validate_budget(_budget_payload())
    return sup.create_attempt_fingerprint(
        chart=chart,
        coefficient_modulus=32003,
        recipe_payload_digest_sha256="1" * 64,
        budget_payload_digest_sha256=budget.payload_sha256,
        worker_source_sha256="2" * 64,
        container_image_digest="sagemath/sagemath@sha256:" + "3" * 64,
        monomial_order="degrevlex",
        execution_policy=policy or {"escalation_sizes": [16, 32, None]},
    )


def _request_verified_message(request_digest: str) -> dict[str, object]:
    return {
        "event": "REQUEST_VERIFIED",
        "message_type": "progress",
        "request_payload_sha256": request_digest,
        "schema_version": "sr2v-q5-free-worker-message-v1",
    }


def _write_production_event_log(
    attempt: sup.AttemptDirectory,
    *,
    worker_messages: Sequence[Mapping[str, object]],
    status: str = "BUILD_COMPLETED",
    process_returncode: int = 0,
) -> sup.HashChainSummary:
    if attempt.events_path.exists():
        attempt.events_path.unlink()
    with sup.HashChainJsonlWriter(attempt.events_path) as events:
        events.append({"event": "CONTAINER_LAUNCH_REQUESTED"})
        for message in worker_messages:
            events.append({"event": "WORKER_MESSAGE", "message": message})
        events.append(
            {
                "cleanup_verified": True,
                "container_contract_verified": True,
                "event": "CONTAINER_ATTEMPT_FINISHED",
                "host_process_termination_verified": True,
                "postflight_audit_verified": True,
                "process_returncode": process_returncode,
                "status": status,
            }
        )
        return events.summary


def _production_attempt(
    tmp_path: Path,
    *,
    method: str = "build_only",
    modulus: int = 32003,
    recipe_updates: Mapping[str, object] | None = None,
    status: str = "BUILD_COMPLETED",
    strict_protocol_replay: bool = True,
    worker_result_updates: Mapping[str, object] | None = None,
) -> sup.AttemptDirectory:
    recipe: dict[str, object] = {"chart": "U2", "method": method, "modulus": modulus}
    if recipe_updates is not None:
        recipe.update(recipe_updates)
    envelope = sup.create_recipe_envelope(recipe)
    recipe_digest = str(envelope["payload_digest_sha256"])
    worker_text = "# frozen worker\n"
    worker_digest = hashlib.sha256(worker_text.encode("utf-8")).hexdigest()
    worker_path = "src/universe_lab/final_theory/sr2v_q5_free_auxiliary_ideal_worker_v042.py"
    execution_policy: dict[str, object] = {
        "single_worker": True,
        "source_bindings": {worker_path: worker_digest},
    }
    if strict_protocol_replay:
        execution_policy["runtime_binding_schema"] = "sr2v-runtime-binding-v1"
    fingerprint = sup.create_attempt_fingerprint(
        chart="U2",
        coefficient_modulus=modulus,
        recipe_payload_digest_sha256=recipe_digest,
        budget_payload_digest_sha256=sup.validate_budget(_budget_payload()).payload_sha256,
        worker_source_sha256=worker_digest,
        container_image_digest="sha256:" + "3" * 64,
        monomial_order="degrevlex",
        execution_policy=execution_policy,
    )
    attempt = sup.create_attempt_directory(tmp_path, fingerprint, attempt_id="production")
    sup.atomic_write_json(attempt.path / "request.json", envelope)
    sup.atomic_write_json(
        attempt.path / "source_snapshot.json",
        {
            "records": {
                worker_path: {"sha256": worker_digest, "text": worker_text},
            },
            "schema_version": "sr2v-solver-source-snapshot-v1",
        },
    )
    worker_result: dict[str, object] = {
        "coefficient_field": "QQ" if modulus == 0 else f"GF({modulus})",
        "event": "WORKER_FINISHED",
        "message_type": "result",
        "method": method,
        "schema_version": "sr2v-q5-free-worker-message-v1",
        "status": status,
    }
    if worker_result_updates is not None:
        worker_result.update(worker_result_updates)
    worker_messages: list[Mapping[str, object]] = []
    if strict_protocol_replay:
        worker_messages = [_request_verified_message(recipe_digest), worker_result]
    event_summary = _write_production_event_log(
        attempt,
        worker_messages=worker_messages,
        process_returncode=sup.exit_code_for_status(status),
        status=status,
    )
    sup.record_attempt_result(
        attempt,
        status=status,
        wall_time_seconds=1,
        details={
            "cleanup_verified": True,
            "container_contract_verified": True,
            "container_image_digest": "sha256:" + "3" * 64,
            "event_log_head_sha256": event_summary.head_sha256,
            "event_log_record_count": event_summary.record_count,
            "event_log_valid": True,
            "host_process_termination_verified": True,
            "postflight_audit_verified": True,
            "postflight_legacy_processes": [],
            "postflight_stale_containers": [],
            "process_returncode": sup.exit_code_for_status(status),
            "request_payload_sha256": recipe_digest,
            "terminal_attempt_status": status,
            "terminal_cleanup_verified": True,
            "terminal_process_returncode": sup.exit_code_for_status(status),
            "worker_result": worker_result,
            "worker_source_sha256": worker_digest,
        },
    )
    return attempt


def _determinantal_policy(*, task_kind: str, modulus: int = 32003) -> dict[str, object]:
    policy: dict[str, object] = {
        "certificate_requirement": "EXACT_EXPONENT_MEMBERSHIP_DIRECT_LIFT_PENDING",
        "coefficient_scope": ("QQ_EXACT_CANDIDATE" if modulus == 0 else "FINITE_FIELD_SCOUT_ONLY"),
        "schema_version": "sr2v-determinantal-cegar-policy-v1",
        "task_kind": task_kind,
    }
    policy["semantic_digest_sha256"] = sup.canonical_payload_sha256(policy)
    return policy


def _determinantal_certificate_result_fields(
    policy: Mapping[str, object], *, direct_lift: bool = False
) -> dict[str, Any]:
    effective_rows = [{"A_term_count": 1, "B_term_count": 1}]
    certificate_core: dict[str, object] = {
        "certificate_requirement": policy["certificate_requirement"],
        "coefficient_scope": policy["coefficient_scope"],
        "conditions_certified_over_selected_field": False,
        "direct_J_lift_verified": direct_lift,
        "effective_rows": effective_rows,
        "entry_condition": {},
        "minor_candidates": [],
        "minor_prefix_trace": [],
        "policy_semantic_digest_sha256": policy["semantic_digest_sha256"],
        "row_unit_associate_relations": [],
        "subset_implication_rule": (
            "SELECTED_ENTRY_UNIT_AND_ALL_EFFECTIVE_SELECTED_A_IN_RADICAL_OF_"
            "SELECTED_MINOR_SUBIDEAL_IMPLIES_FULL_I1_AND_FULL_A_RADICAL_I2"
        ),
    }
    return {
        "certificate_bytes": len(sup.canonical_json_bytes(certificate_core)),
        "certificate_scope": "SCOUT_ONLY",
        "certificate_sha256": sup.canonical_payload_sha256(certificate_core),
        "certificate_term_accounting": 2,
        "determinantal_certificate_schema": "sr2v-determinantal-certificate-v1",
        "determinantal_conditions_certified": False,
        "direct_J_lift_verified": direct_lift,
        "effective_rows": effective_rows,
        "entry_condition": {},
        "generated_minor_terms": 0,
        "minor_candidates": [],
        "minor_prefix_trace": [],
        "policy_semantic_digest_sha256": policy["semantic_digest_sha256"],
        "row_unit_associate_relations": [],
        "subset_implication_verified": False,
    }


def _rewrite_authenticated_worker_result(
    attempt: sup.AttemptDirectory, result: sup.JsonObject
) -> None:
    details = result["details"]
    assert isinstance(details, dict)
    worker_result = details["worker_result"]
    request_digest = details["request_payload_sha256"]
    status = result["status"]
    process_returncode = details["process_returncode"]
    assert isinstance(worker_result, Mapping)
    assert isinstance(request_digest, str)
    assert isinstance(status, str)
    assert isinstance(process_returncode, int)
    event_summary = _write_production_event_log(
        attempt,
        worker_messages=[_request_verified_message(request_digest), worker_result],
        process_returncode=process_returncode,
        status=status,
    )
    details["event_log_head_sha256"] = event_summary.head_sha256
    details["event_log_record_count"] = event_summary.record_count
    sup.atomic_write_json(attempt.result_path, result, overwrite=True)


def test_strict_budget_accepts_the_exact_integer_contract() -> None:
    budget = sup.validate_budget(_budget_payload())

    assert budget.timeout_seconds_per_chart == 10
    assert budget.total_wall_time_seconds == 100
    assert budget.memory_limit_gib == 8
    assert budget.memory_limit_bytes == 8 * 1024**3
    assert budget.payload_sha256 == sup.canonical_payload_sha256(budget.to_payload())


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("timeout_seconds_per_chart", True),
        ("timeout_seconds_per_chart", 1.5),
        ("timeout_seconds_per_chart", "10"),
        ("timeout_seconds_per_chart", 0),
        ("timeout_seconds_per_chart", -1),
        ("total_wall_time_seconds", False),
        ("total_wall_time_seconds", 2.5),
        ("total_wall_time_seconds", 0),
        ("total_wall_time_seconds", -1),
        ("memory_limit_gib", True),
        ("memory_limit_gib", 8.0),
        ("memory_limit_gib", 0),
        ("memory_limit_gib", -8),
    ],
)
def test_strict_budget_rejects_bool_noninteger_zero_and_negative(
    field: str, bad_value: object
) -> None:
    with pytest.raises((TypeError, ValueError)):
        sup.validate_budget(_budget_payload(**{field: bad_value}))


def test_strict_budget_rejects_missing_extra_and_per_chart_over_total() -> None:
    missing = _budget_payload()
    del missing["memory_limit_gib"]
    with pytest.raises(ValueError, match="keys do not match"):
        sup.validate_budget(missing)

    with pytest.raises(ValueError, match="unsupported"):
        sup.validate_budget({**_budget_payload(), "workers": 1})

    with pytest.raises(ValueError, match="cannot exceed"):
        sup.validate_budget(
            _budget_payload(timeout_seconds_per_chart=101, total_wall_time_seconds=100)
        )


def test_canonical_json_is_order_independent_and_rejects_nonfinite_values() -> None:
    left = {"z": 1, "a": ["日本語", {"b": 2, "a": 1}]}
    right = {"a": ["日本語", {"a": 1, "b": 2}], "z": 1}

    assert sup.canonical_json_bytes(left) == sup.canonical_json_bytes(right)
    assert sup.canonical_payload_sha256(left) == sup.canonical_payload_sha256(right)
    with pytest.raises(ValueError, match="non-finite"):
        sup.canonical_json_bytes({"bad": float("nan")})
    with pytest.raises(ValueError, match="non-finite"):
        sup.canonical_json_bytes({"bad": float("inf")})


def test_recipe_envelope_copies_and_verifies_the_canonical_payload() -> None:
    recipe: dict[str, Any] = {"chart": "U2", "generators": [[1, 2]], "modulus": 32003}
    envelope = sup.create_recipe_envelope(recipe)
    recipe["generators"].append([3, 4])

    verified = sup.verify_recipe_envelope(envelope)

    assert verified.payload == {"chart": "U2", "generators": [[1, 2]], "modulus": 32003}
    assert verified.payload_digest_sha256 == sup.canonical_payload_sha256(verified.payload)
    assert verified.envelope_digest_sha256 == sup.canonical_payload_sha256(envelope)


@pytest.mark.parametrize("mutation", ["payload", "digest", "schema", "extra"])
def test_recipe_envelope_rejects_every_binding_mutation(mutation: str) -> None:
    envelope = sup.create_recipe_envelope({"chart": "U2", "generators": [1, 2]})
    changed = json.loads(json.dumps(envelope))
    if mutation == "payload":
        changed["payload"]["generators"].append(3)
    elif mutation == "digest":
        changed["payload_digest_sha256"] = "f" * 64
    elif mutation == "schema":
        changed["schema_version"] = "old"
    else:
        changed["unexpected"] = True

    with pytest.raises(sup.EnvelopeValidationError):
        sup.verify_recipe_envelope(changed)


def test_attempt_fingerprint_is_content_addressed_and_policy_order_independent() -> None:
    first = _fingerprint(policy={"sizes": [16, None], "stage": "groebner"})
    second = _fingerprint(policy={"stage": "groebner", "sizes": [16, None]})
    different = _fingerprint(chart="U3", policy={"stage": "groebner", "sizes": [16, None]})

    assert first.sha256 == second.sha256
    assert first.identity == second.identity
    assert different.sha256 != first.sha256
    assert sup.canonical_payload_sha256(first.identity) == first.sha256


@pytest.mark.parametrize("modulus", [True, -1, 1.5])
def test_attempt_fingerprint_rejects_noncanonical_modulus(modulus: object) -> None:
    budget = sup.validate_budget(_budget_payload())
    with pytest.raises((TypeError, ValueError)):
        sup.create_attempt_fingerprint(
            chart="U2",
            coefficient_modulus=modulus,  # type: ignore[arg-type]
            recipe_payload_digest_sha256="1" * 64,
            budget_payload_digest_sha256=budget.payload_sha256,
            worker_source_sha256="2" * 64,
            container_image_digest="image@sha256:" + "3" * 64,
            monomial_order="degrevlex",
            execution_policy={},
        )


def test_attempt_directory_is_bound_and_never_overwritten(tmp_path: Path) -> None:
    fingerprint = _fingerprint()
    attempt = sup.create_attempt_directory(
        tmp_path,
        fingerprint,
        attempt_id="attempt_001",
        created_at_utc="2026-08-04T00:00:00Z",
    )

    assert attempt.path == tmp_path / fingerprint.sha256 / "attempt_001"
    manifest = sup.read_json_object(attempt.manifest_path)
    state = sup.read_json_object(attempt.state_path)
    assert manifest["identity"] == fingerprint.identity
    assert manifest["fingerprint_sha256"] == fingerprint.sha256
    assert state["lifecycle_status"] == "PREPARED"
    assert b"\r\n" not in attempt.manifest_path.read_bytes()

    with pytest.raises(FileExistsError):
        sup.create_attempt_directory(tmp_path, fingerprint, attempt_id="attempt_001")
    with pytest.raises(ValueError, match="unsafe"):
        sup.create_attempt_directory(tmp_path, fingerprint, attempt_id="../escape")


def test_attempt_directory_rejects_an_identity_digest_mismatch(tmp_path: Path) -> None:
    valid = _fingerprint()
    invalid = sup.AttemptFingerprint(valid.identity, "f" * 64)

    with pytest.raises(ValueError, match="does not reproduce"):
        sup.create_attempt_directory(tmp_path, invalid, attempt_id="attempt_001")


def test_atomic_json_is_non_overwriting_by_default_and_replaceable_explicitly(
    tmp_path: Path,
) -> None:
    path = tmp_path / "record.json"
    sup.atomic_write_json(path, {"version": 1})

    with pytest.raises(FileExistsError):
        sup.atomic_write_json(path, {"version": 2})
    assert sup.read_json_object(path) == {"version": 1}

    sup.atomic_write_json(path, {"version": 3}, overwrite=True)
    assert sup.read_json_object(path) == {"version": 3}
    assert path.read_bytes().endswith(b"\n")
    assert b"\r\n" not in path.read_bytes()
    assert not list(tmp_path.glob("*.tmp"))


def test_attempt_state_replacement_is_atomic(tmp_path: Path) -> None:
    attempt = sup.create_attempt_directory(tmp_path, _fingerprint(), attempt_id="state_test")

    sup.write_attempt_state(attempt, "RUNNING", {"stage": "load"})

    state = sup.read_json_object(attempt.state_path)
    assert state["lifecycle_status"] == "RUNNING"
    assert state["details"] == {"stage": "load"}


def test_hash_chain_jsonl_flushes_each_append_and_verifies(tmp_path: Path) -> None:
    path = tmp_path / "events.jsonl"
    with sup.HashChainJsonlWriter(path) as writer:
        first = writer.append({"event": "started", "sequence_from_worker": 7})
        assert path.read_text(encoding="utf-8").count("\n") == 1
        second = writer.append({"event": "heartbeat", "rss_bytes": 123})
        assert writer.summary == sup.HashChainSummary(2, second)

    summary = sup.verify_hash_chain_jsonl(path)
    records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    assert summary == sup.HashChainSummary(2, second)
    assert records[0]["previous_sha256"] == sup.ZERO_SHA256
    assert records[0]["record_sha256"] == first
    assert records[1]["previous_sha256"] == first
    assert b"\r\n" not in path.read_bytes()
    with pytest.raises(FileExistsError):
        sup.HashChainJsonlWriter(path)


def test_hash_chain_rejects_tampering_truncation_and_crlf(tmp_path: Path) -> None:
    original = tmp_path / "original.jsonl"
    with sup.HashChainJsonlWriter(original) as writer:
        writer.append({"event": "one"})
        writer.append({"event": "two"})

    tampered = tmp_path / "tampered.jsonl"
    records = [json.loads(line) for line in original.read_text(encoding="utf-8").splitlines()]
    records[0]["payload"]["event"] = "changed"
    tampered.write_bytes(b"\n".join(sup.canonical_json_bytes(record) for record in records) + b"\n")
    with pytest.raises(sup.HashChainValidationError):
        sup.verify_hash_chain_jsonl(tampered)

    truncated = tmp_path / "truncated.jsonl"
    truncated.write_bytes(original.read_bytes()[:-1])
    with pytest.raises(sup.HashChainValidationError, match="LF-terminated"):
        sup.verify_hash_chain_jsonl(truncated)

    crlf = tmp_path / "crlf.jsonl"
    crlf.write_bytes(original.read_bytes().replace(b"\n", b"\r\n"))
    with pytest.raises(sup.HashChainValidationError, match="LF-terminated"):
        sup.verify_hash_chain_jsonl(crlf)

    boolean_sequence = tmp_path / "boolean_sequence.jsonl"
    record = json.loads(original.read_text(encoding="utf-8").splitlines()[0])
    record["sequence"] = False
    core = {key: value for key, value in record.items() if key != "record_sha256"}
    record["record_sha256"] = sup.canonical_payload_sha256(core)
    boolean_sequence.write_bytes(sup.canonical_json_bytes(record) + b"\n")
    with pytest.raises(sup.HashChainValidationError, match="sequence"):
        sup.verify_hash_chain_jsonl(boolean_sequence)


@pytest.mark.parametrize(
    ("status", "classification", "exit_code"),
    [
        ("COMPLETED", sup.StatusClassification.SUCCESS, 0),
        ("BUILD_COMPLETED", sup.StatusClassification.SUCCESS, 0),
        ("DETERMINANTAL_INVENTORY_COMPLETED", sup.StatusClassification.SUCCESS, 0),
        ("REDUNDANCY_AUDIT_COMPLETED", sup.StatusClassification.SUCCESS, 0),
        ("DETERMINANTAL_GF_SCOUT_PASSED", sup.StatusClassification.NONTERMINAL, 2),
        (
            "DETERMINANTAL_CONDITIONS_CERTIFIED_DIRECT_LIFT_PENDING",
            sup.StatusClassification.NONTERMINAL,
            2,
        ),
        ("DETERMINANTAL_SUBSET_INCONCLUSIVE", sup.StatusClassification.NONTERMINAL, 2),
        ("TIMEOUT", sup.StatusClassification.NONTERMINAL, 2),
        ("UNIT_IDEAL_FOUND_CERTIFICATE_PENDING", sup.StatusClassification.NONTERMINAL, 2),
        ("WEAK_D2_OPEN_RESOURCE_LIMIT", sup.StatusClassification.NONTERMINAL, 2),
        ("KILL_UNVERIFIED", sup.StatusClassification.OPERATIONAL_ERROR, 3),
        ("ERROR_137", sup.StatusClassification.OPERATIONAL_ERROR, 3),
        ("SOMETHING_NEW", sup.StatusClassification.INVALID, 4),
    ],
)
def test_every_nonterminal_or_unknown_status_recommends_nonzero(
    status: str, classification: sup.StatusClassification, exit_code: int
) -> None:
    assert sup.classify_status(status) is classification
    assert sup.exit_code_for_status(status) == exit_code
    assert (exit_code == 0) is (classification is sup.StatusClassification.SUCCESS)


def test_attempt_result_is_bound_written_once_and_self_classifying(tmp_path: Path) -> None:
    attempt = sup.create_attempt_directory(tmp_path, _fingerprint(), attempt_id="result_test")
    result = sup.record_attempt_result(
        attempt,
        status="TIMEOUT",
        wall_time_seconds=9.25,
        details={"last_stage": "groebner"},
    )

    assert result["fingerprint_sha256"] == attempt.fingerprint_sha256
    assert result["status_classification"] == "NONTERMINAL"
    assert result["recommended_exit_code"] == 2
    with pytest.raises(FileExistsError):
        sup.record_attempt_result(
            attempt,
            status="COMPLETED",
            wall_time_seconds=1,
            details={},
        )


@pytest.mark.parametrize("bad_wall", [True, -1, float("nan"), float("inf"), "1"])
def test_attempt_result_rejects_invalid_wall_times(tmp_path: Path, bad_wall: object) -> None:
    attempt = sup.create_attempt_directory(
        tmp_path, _fingerprint(), attempt_id=f"bad_wall_{str(bad_wall).replace('-', 'n')}"
    )
    with pytest.raises((TypeError, ValueError)):
        sup.record_attempt_result(
            attempt,
            status="TIMEOUT",
            wall_time_seconds=bad_wall,  # type: ignore[arg-type]
            details={},
        )


def test_history_aggregates_wall_time_and_blocks_same_fingerprint_timeout(
    tmp_path: Path,
) -> None:
    completed_fingerprint = _fingerprint(chart="U2")
    timed_out_fingerprint = _fingerprint(chart="U3")
    future_fingerprint = _fingerprint(chart="U4")
    completed = sup.create_attempt_directory(
        tmp_path, completed_fingerprint, attempt_id="completed"
    )
    timed_out = sup.create_attempt_directory(
        tmp_path, timed_out_fingerprint, attempt_id="timed_out"
    )
    sup.record_attempt_result(completed, status="COMPLETED", wall_time_seconds=30.25, details={})
    sup.record_attempt_result(timed_out, status="TIMEOUT", wall_time_seconds=40.5, details={})

    history = sup.load_attempt_history(tmp_path)
    retry = sup.evaluate_attempt_permission(
        tmp_path,
        budget=sup.validate_budget(_budget_payload()),
        fingerprint_sha256=timed_out_fingerprint.sha256,
    )
    future = sup.evaluate_attempt_permission(
        tmp_path,
        budget=sup.validate_budget(_budget_payload()),
        fingerprint_sha256=future_fingerprint.sha256,
    )

    assert history.aggregate_wall_time_seconds == pytest.approx(70.75)
    assert history.completed_attempt_count == 2
    assert history.status_counts == (("COMPLETED", 1), ("TIMEOUT", 1))
    assert retry.allowed is False
    assert retry.reason == "SAME_FINGERPRINT_TIMEOUT_RETRY_FORBIDDEN"
    assert future.allowed is True
    assert future.effective_timeout_seconds == 10


def test_permission_caps_timeout_to_floor_of_remaining_aggregate_budget(
    tmp_path: Path,
) -> None:
    past_fingerprint = _fingerprint(chart="U2")
    future_fingerprint = _fingerprint(chart="U4")
    past = sup.create_attempt_directory(tmp_path, past_fingerprint, attempt_id="past")
    sup.record_attempt_result(past, status="COMPLETED", wall_time_seconds=95.5, details={})

    permission = sup.evaluate_attempt_permission(
        tmp_path,
        budget=sup.validate_budget(_budget_payload()),
        fingerprint_sha256=future_fingerprint.sha256,
    )

    assert permission.allowed is True
    assert permission.remaining_wall_time_seconds == pytest.approx(4.5)
    assert permission.effective_timeout_seconds == 4


def test_permission_accounts_for_current_planning_and_finalization_reserve(
    tmp_path: Path,
) -> None:
    permission = sup.evaluate_attempt_permission(
        tmp_path,
        budget=sup.validate_budget(_budget_payload()),
        fingerprint_sha256=_fingerprint(chart="U4").sha256,
        current_campaign_elapsed_seconds=5.25,
        finalization_reserve_seconds=2,
    )

    assert permission.allowed is True
    assert permission.remaining_wall_time_seconds == pytest.approx(94.75)
    assert permission.effective_timeout_seconds == 10

    exhausted_by_reserve = sup.evaluate_attempt_permission(
        tmp_path,
        budget=sup.validate_budget(_budget_payload()),
        fingerprint_sha256=_fingerprint(chart="U4").sha256,
        current_campaign_elapsed_seconds=98.5,
        finalization_reserve_seconds=2,
    )
    assert exhausted_by_reserve.allowed is False
    assert exhausted_by_reserve.reason == "TOTAL_WALL_TIME_BUDGET_EXHAUSTED"


def test_permission_blocks_exhausted_budget_and_any_incomplete_attempt(tmp_path: Path) -> None:
    past_fingerprint = _fingerprint(chart="U2")
    future_fingerprint = _fingerprint(chart="U4")
    past = sup.create_attempt_directory(tmp_path, past_fingerprint, attempt_id="past")
    sup.record_attempt_result(past, status="ERROR_1", wall_time_seconds=100, details={})

    exhausted = sup.evaluate_attempt_permission(
        tmp_path,
        budget=sup.validate_budget(_budget_payload()),
        fingerprint_sha256=future_fingerprint.sha256,
    )
    assert exhausted.allowed is False
    assert exhausted.reason == "TOTAL_WALL_TIME_BUDGET_EXHAUSTED"

    other_root = tmp_path / "incomplete"
    sup.create_attempt_directory(other_root, past_fingerprint, attempt_id="still_running")
    incomplete = sup.evaluate_attempt_permission(
        other_root,
        budget=sup.validate_budget(_budget_payload()),
        fingerprint_sha256=future_fingerprint.sha256,
    )
    assert incomplete.allowed is False
    assert incomplete.reason == "INCOMPLETE_ATTEMPT_REQUIRES_RECOVERY"


def test_permission_blocks_campaign_after_unverified_cleanup(tmp_path: Path) -> None:
    unsafe_fingerprint = _fingerprint(chart="U2")
    future_fingerprint = _fingerprint(chart="U4")
    unsafe = sup.create_attempt_directory(tmp_path, unsafe_fingerprint, attempt_id="unsafe")
    sup.record_attempt_result(
        unsafe,
        status="KILL_UNVERIFIED",
        wall_time_seconds=1,
        details={},
    )

    permission = sup.evaluate_attempt_permission(
        tmp_path,
        budget=sup.validate_budget(_budget_payload()),
        fingerprint_sha256=future_fingerprint.sha256,
    )

    assert permission.allowed is False
    assert permission.reason == "UNSAFE_TERMINATION_REQUIRES_RECOVERY"


def test_history_fails_closed_when_a_result_binding_is_tampered(tmp_path: Path) -> None:
    fingerprint = _fingerprint()
    attempt = sup.create_attempt_directory(tmp_path, fingerprint, attempt_id="tampered")
    sup.record_attempt_result(attempt, status="COMPLETED", wall_time_seconds=1, details={})
    result = sup.read_json_object(attempt.result_path)
    result["recommended_exit_code"] = 9
    sup.atomic_write_json(attempt.result_path, result, overwrite=True)

    with pytest.raises(sup.AttemptHistoryError, match="exit code"):
        sup.load_attempt_history(tmp_path)


def test_production_history_revalidates_all_bound_artifacts(tmp_path: Path) -> None:
    _production_attempt(tmp_path)

    history = sup.load_attempt_history(tmp_path)

    assert history.completed_attempt_count == 1
    assert history.status_counts == (("BUILD_COMPLETED", 1),)


def test_legacy_production_history_keeps_the_pre_replay_generation_boundary(
    tmp_path: Path,
) -> None:
    _production_attempt(tmp_path, strict_protocol_replay=False)

    history = sup.load_attempt_history(tmp_path)

    assert history.completed_attempt_count == 1
    assert history.status_counts == (("BUILD_COMPLETED", 1),)


@pytest.mark.parametrize(
    ("field", "forged_value"),
    [
        ("method", "determinantal_cegar_v1"),
        (
            "certificate",
            {
                "certificate_schema": "sr2v-determinantal-certificate-v1",
                "verified": True,
            },
        ),
    ],
)
def test_strict_history_rejects_worker_result_fields_absent_from_authenticated_event(
    tmp_path: Path, field: str, forged_value: sup.JsonValue
) -> None:
    attempt = _production_attempt(tmp_path)
    result = sup.read_json_object(attempt.result_path)
    details = result["details"]
    assert isinstance(details, dict)
    worker_result = details["worker_result"]
    assert isinstance(worker_result, dict)
    worker_result[field] = forged_value
    sup.atomic_write_json(attempt.result_path, result, overwrite=True)

    with pytest.raises(sup.AttemptHistoryError, match="authenticated worker result"):
        sup.load_attempt_history(tmp_path)


def test_strict_history_binds_authenticated_worker_method_to_request(tmp_path: Path) -> None:
    attempt = _production_attempt(tmp_path)
    result = sup.read_json_object(attempt.result_path)
    details = result["details"]
    assert isinstance(details, dict)
    worker_result = details["worker_result"]
    request_digest = details["request_payload_sha256"]
    assert isinstance(worker_result, dict)
    assert isinstance(request_digest, str)
    worker_result["method"] = "determinantal_cegar_v1"
    event_summary = _write_production_event_log(
        attempt,
        worker_messages=[_request_verified_message(request_digest), worker_result],
    )
    details["event_log_head_sha256"] = event_summary.head_sha256
    details["event_log_record_count"] = event_summary.record_count
    sup.atomic_write_json(attempt.result_path, result, overwrite=True)

    with pytest.raises(sup.AttemptHistoryError, match="method disagrees"):
        sup.load_attempt_history(tmp_path)


@pytest.mark.parametrize(
    ("method", "status"),
    [
        ("determinantal_cegar_v1", "COMPLETED"),
        ("determinantal_inventory_v1", "COMPLETED"),
        ("build_only", "DETERMINANTAL_INVENTORY_COMPLETED"),
    ],
)
def test_strict_history_rejects_rehashed_status_from_another_method_contract(
    tmp_path: Path, method: str, status: str
) -> None:
    _production_attempt(tmp_path, method=method, status=status)

    with pytest.raises(sup.AttemptHistoryError, match="status is not allowed"):
        sup.load_attempt_history(tmp_path)


@pytest.mark.parametrize(
    ("modulus", "status"),
    [
        (32003, "DETERMINANTAL_CONDITIONS_CERTIFIED_DIRECT_LIFT_PENDING"),
        (0, "DETERMINANTAL_GF_SCOUT_PASSED"),
    ],
)
def test_strict_history_rejects_rehashed_determinantal_coefficient_scope(
    tmp_path: Path, modulus: int, status: str
) -> None:
    _production_attempt(
        tmp_path,
        method="determinantal_cegar_v1",
        modulus=modulus,
        status=status,
    )

    with pytest.raises(sup.AttemptHistoryError, match="coefficient scope"):
        sup.load_attempt_history(tmp_path)


def test_strict_history_rejects_rehashed_direct_lift_claim_from_scout_generation(
    tmp_path: Path,
) -> None:
    policy = _determinantal_policy(task_kind="COMBINED_SUBSET_CERTIFICATE")
    attempt = _production_attempt(
        tmp_path,
        method="determinantal_cegar_v1",
        recipe_updates={"determinantal_policy": policy},
        status="DETERMINANTAL_SUBSET_INCONCLUSIVE",
        worker_result_updates=_determinantal_certificate_result_fields(policy),
    )
    assert sup.load_attempt_history(tmp_path).completed_attempt_count == 1
    result = sup.read_json_object(attempt.result_path)
    details = result["details"]
    assert isinstance(details, dict)
    worker_result = details["worker_result"]
    assert isinstance(worker_result, dict)
    worker_result.update(_determinantal_certificate_result_fields(policy, direct_lift=True))
    _rewrite_authenticated_worker_result(attempt, result)

    with pytest.raises(sup.AttemptHistoryError, match="cannot claim a direct J lift"):
        sup.load_attempt_history(tmp_path)


def test_strict_history_rejects_rehashed_inventory_payload_without_matching_digest(
    tmp_path: Path,
) -> None:
    policy = _determinantal_policy(task_kind="INVENTORY_ONLY")
    inventory_core: dict[str, object] = {
        "discarded_minors": [],
        "effective_rows": [],
        "generated_minor_terms": 0,
        "minor_candidates": [],
        "policy_semantic_digest_sha256": policy["semantic_digest_sha256"],
        "raw_selected_row_count": 0,
        "row_unit_associate_relations": [],
    }
    inventory_fields: dict[str, Any] = {
        **inventory_core,
        "determinantal_inventory_schema": "sr2v-determinantal-inventory-v1",
        "inventory_sha256": sup.canonical_payload_sha256(inventory_core),
    }
    attempt = _production_attempt(
        tmp_path,
        method="determinantal_inventory_v1",
        recipe_updates={"determinantal_policy": policy},
        status="DETERMINANTAL_INVENTORY_COMPLETED",
        worker_result_updates=inventory_fields,
    )
    assert sup.load_attempt_history(tmp_path).completed_attempt_count == 1
    result = sup.read_json_object(attempt.result_path)
    details = result["details"]
    assert isinstance(details, dict)
    worker_result = details["worker_result"]
    assert isinstance(worker_result, dict)
    worker_result["generated_minor_terms"] = 1
    _rewrite_authenticated_worker_result(attempt, result)

    with pytest.raises(sup.AttemptHistoryError, match="inventory digest"):
        sup.load_attempt_history(tmp_path)


@pytest.mark.parametrize(
    ("mutation", "expected_error"),
    [
        ("duplicate_result", "exactly one"),
        ("result_not_last", "last worker protocol message"),
        ("wrong_request_digest", "request digest disagrees"),
        ("request_not_first", "REQUEST_VERIFIED"),
        ("duplicate_request_verified", "REQUEST_VERIFIED"),
    ],
)
def test_strict_history_replays_authenticated_worker_protocol_fail_closed(
    tmp_path: Path, mutation: str, expected_error: str
) -> None:
    attempt = _production_attempt(tmp_path)
    result = sup.read_json_object(attempt.result_path)
    details = result["details"]
    assert isinstance(details, dict)
    worker_result = details["worker_result"]
    request_digest = details["request_payload_sha256"]
    assert isinstance(worker_result, Mapping)
    assert isinstance(request_digest, str)
    request_verified = _request_verified_message(request_digest)
    late_progress: dict[str, object] = {
        "event": "LATE_PROGRESS",
        "message_type": "progress",
        "schema_version": "sr2v-q5-free-worker-message-v1",
    }
    worker_messages: list[Mapping[str, object]]
    if mutation == "duplicate_result":
        worker_messages = [request_verified, worker_result, worker_result]
    elif mutation == "result_not_last":
        worker_messages = [request_verified, worker_result, late_progress]
    elif mutation == "wrong_request_digest":
        worker_messages = [_request_verified_message("f" * 64), worker_result]
    elif mutation == "request_not_first":
        worker_messages = [late_progress, request_verified, worker_result]
    else:
        worker_messages = [request_verified, request_verified, worker_result]
    event_summary = _write_production_event_log(
        attempt,
        worker_messages=worker_messages,
    )
    details["event_log_head_sha256"] = event_summary.head_sha256
    details["event_log_record_count"] = event_summary.record_count
    sup.atomic_write_json(attempt.result_path, result, overwrite=True)

    with pytest.raises(sup.AttemptHistoryError, match=expected_error):
        sup.load_attempt_history(tmp_path)


@pytest.mark.parametrize(
    "mutation",
    [
        "details",
        "worker_result",
        "request",
        "events",
        "runtime",
        "runtime_downgrade",
        "source",
    ],
)
def test_production_history_cannot_be_downgraded_or_tampered(tmp_path: Path, mutation: str) -> None:
    attempt = _production_attempt(tmp_path)
    if mutation in {"details", "runtime", "runtime_downgrade", "worker_result"}:
        result = sup.read_json_object(attempt.result_path)
        details = result["details"]
        assert isinstance(details, dict)
        if mutation == "details":
            result["details"] = {}
        elif mutation == "worker_result":
            details["worker_result"] = None
            details["process_returncode"] = None
        elif mutation == "runtime":
            details["postflight_stale_containers"] = ["ghost-worker"]
        else:
            for key in (
                "container_contract_verified",
                "event_log_valid",
                "host_process_termination_verified",
                "postflight_audit_verified",
                "postflight_legacy_processes",
                "postflight_stale_containers",
            ):
                details.pop(key)
        sup.atomic_write_json(attempt.result_path, result, overwrite=True)
    elif mutation == "request":
        request = sup.read_json_object(attempt.path / "request.json")
        payload = request["payload"]
        assert isinstance(payload, dict)
        payload["chart"] = "U3"
        sup.atomic_write_json(attempt.path / "request.json", request, overwrite=True)
    elif mutation == "events":
        attempt.events_path.write_bytes(
            attempt.events_path.read_bytes().replace(b"FINISHED", b"CHANGED!")
        )
    else:
        snapshot = sup.read_json_object(attempt.path / "source_snapshot.json")
        records = snapshot["records"]
        assert isinstance(records, dict)
        record = next(iter(records.values()))
        assert isinstance(record, dict)
        record["text"] = "# changed worker\n"
        sup.atomic_write_json(attempt.path / "source_snapshot.json", snapshot, overwrite=True)

    with pytest.raises(sup.AttemptHistoryError):
        sup.load_attempt_history(tmp_path)


def test_success_cannot_impersonate_a_prelaunch_artifact_failure(tmp_path: Path) -> None:
    attempt = _production_attempt(tmp_path)
    result = sup.read_json_object(attempt.result_path)
    details = result["details"]
    assert isinstance(details, dict)
    details["failure_phase"] = "ARTIFACT_WRITE"
    details["launch_may_have_occurred"] = False
    sup.atomic_write_json(attempt.result_path, result, overwrite=True)
    (attempt.path / "request.json").unlink()
    (attempt.path / "source_snapshot.json").unlink()

    with pytest.raises(sup.AttemptHistoryError):
        sup.load_attempt_history(tmp_path)


@pytest.mark.parametrize(
    ("status", "cleanup_verified"),
    [
        ("ERROR_CAMPAIGN_ARTIFACT_WRITE", True),
        ("HOST_INTERRUPTED", True),
        ("KILL_UNVERIFIED", False),
    ],
)
def test_prelaunch_artifact_failure_is_a_complete_auditable_attempt(
    tmp_path: Path, status: str, cleanup_verified: bool
) -> None:
    worker_digest = "2" * 64
    fingerprint = sup.create_attempt_fingerprint(
        chart="U2",
        coefficient_modulus=32003,
        recipe_payload_digest_sha256="1" * 64,
        budget_payload_digest_sha256=sup.validate_budget(_budget_payload()).payload_sha256,
        worker_source_sha256=worker_digest,
        container_image_digest="sha256:" + "3" * 64,
        monomial_order="degrevlex",
        execution_policy={
            "single_worker": True,
            "source_bindings": {
                "src/universe_lab/final_theory/"
                "sr2v_q5_free_auxiliary_ideal_worker_v042.py": worker_digest
            },
        },
    )
    attempt = sup.create_attempt_directory(tmp_path, fingerprint, attempt_id="artifact_failure")
    sup.record_attempt_result(
        attempt,
        status=status,
        wall_time_seconds=1,
        details={
            "cleanup_verified": cleanup_verified,
            "container_image_digest": "sha256:" + "3" * 64,
            "event_log_head_sha256": None,
            "event_log_record_count": None,
            "event_log_valid": False,
            "failure_phase": "ARTIFACT_WRITE",
            "launch_may_have_occurred": False,
            "process_returncode": None,
            "request_payload_sha256": "1" * 64,
            "worker_result": None,
            "worker_source_sha256": worker_digest,
        },
    )

    history = sup.load_attempt_history(tmp_path)

    assert history.completed_attempt_count == 1
    assert history.status_counts == ((status, 1),)


@pytest.mark.parametrize(
    ("status", "process_returncode"),
    [
        ("TIMEOUT", 143),
        ("ERROR_WORKER_PROTOCOL", 0),
        ("ERROR_WORKER_EXIT_STATUS_MISMATCH", 0),
    ],
)
def test_supervisor_status_override_preserves_authenticated_worker_payload(
    tmp_path: Path, status: str, process_returncode: int
) -> None:
    attempt = _production_attempt(tmp_path)
    result = sup.read_json_object(attempt.result_path)
    result["status"] = status
    classification = sup.classify_status(status)
    result["status_classification"] = classification.value
    result["recommended_exit_code"] = sup.exit_code_for_status(status)
    details = result["details"]
    assert isinstance(details, dict)
    details["process_returncode"] = process_returncode
    details["terminal_attempt_status"] = status
    details["terminal_process_returncode"] = process_returncode
    worker_result = details["worker_result"]
    request_digest = details["request_payload_sha256"]
    assert isinstance(worker_result, Mapping)
    assert isinstance(request_digest, str)
    event_summary = _write_production_event_log(
        attempt,
        worker_messages=[_request_verified_message(request_digest), worker_result],
        status=status,
        process_returncode=process_returncode,
    )
    details["event_log_head_sha256"] = event_summary.head_sha256
    details["event_log_record_count"] = event_summary.record_count
    sup.atomic_write_json(attempt.result_path, result, overwrite=True)

    history = sup.load_attempt_history(tmp_path)

    assert history.status_counts == ((status, 1),)


def test_outer_finalizer_failure_preserves_authenticated_timeout_gate(tmp_path: Path) -> None:
    attempt = _production_attempt(tmp_path)
    result = sup.read_json_object(attempt.result_path)
    result["status"] = "ERROR_CAMPAIGN_FINALIZE"
    result["status_classification"] = sup.StatusClassification.OPERATIONAL_ERROR.value
    result["recommended_exit_code"] = 3
    details = result["details"]
    assert isinstance(details, dict)
    details.update(
        {
            "failure_phase": "FINALIZE",
            "launch_may_have_occurred": True,
            "process_returncode": 143,
            "terminal_attempt_status": "TIMEOUT",
            "terminal_cleanup_verified": True,
            "terminal_process_returncode": 143,
        }
    )
    worker_result = details["worker_result"]
    request_digest = details["request_payload_sha256"]
    assert isinstance(worker_result, Mapping)
    assert isinstance(request_digest, str)
    event_summary = _write_production_event_log(
        attempt,
        worker_messages=[_request_verified_message(request_digest), worker_result],
        status="TIMEOUT",
        process_returncode=143,
    )
    details["event_log_head_sha256"] = event_summary.head_sha256
    details["event_log_record_count"] = event_summary.record_count
    sup.atomic_write_json(attempt.result_path, result, overwrite=True)

    history = sup.load_attempt_history(tmp_path)

    assert attempt.fingerprint_sha256 in history.timed_out_fingerprints
