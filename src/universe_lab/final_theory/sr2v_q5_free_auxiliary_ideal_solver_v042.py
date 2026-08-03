"""Thin Sage/Singular worker for the SR2-V Q5-free auxiliary-ideal solver stage.

This module is the first solver invocation of the whole SR2-V campaign.  It
does not reinterpret or import ``d2_sage_backend_v035.py``'s v0.3.5
direct-operator proof schema; it only reuses the same general shape of
host-side subprocess/timeout driver against the same ``sage`` Docker Compose
service.

Per ``reports/v0.4.2_sr2v_q5_free_auxiliary_ideal_execution_plan.md``, six
ideals are tested for the whole ring:

* non-aligned ``J_k = <A_i*h+B_i : all 1,127 full-M0 Schur rows>`` in
  ``U_k[h]`` for ``k`` in ``{2,3,4}``;
* aligned ``<A_i*h+B_i2*w2+B_i3*w3+B_i4*w4>`` on each ``w_j=1`` normalisation,
  together with the equal-ratio relations ``d2,d3,d4``.

Each ideal is tested via one Rabinowitsch equation ``1-z*s_k`` rather than by
literal localisation, where ``s_k`` is the certified denominator-clearing
product already frozen in the bundle. Every generator is read back from the
verified two-tier Phase-A bundle (``sr2v_q5_free_auxiliary_ideal_bundle_v042``)
by content, not recomputed from source, so this module binds to the frozen
``polynomial_arena`` by SHA-256, not by trusting arena-relative integers.

Nothing here claims a unit-ideal theorem. A Groebner basis reaching ``[1]``
without an independently re-evaluated Nullstellensatz lift is recorded as
``UNIT_IDEAL_FOUND_CERTIFICATE_PENDING``, per the execution plan's section 6.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import time
from collections.abc import Iterable, Iterator, Mapping, Sequence
from fractions import Fraction
from pathlib import Path
from typing import Any

import sympy as sp

from universe_lab.final_theory import sr2v_bottom_msr_global_csg_v042 as bottom_global
from universe_lab.final_theory import sr2v_q5_free_auxiliary_ideal_bundle_v042 as bundle
from universe_lab.final_theory import sr2v_q5_free_auxiliary_ideal_manifest_v042 as manifest
from universe_lab.final_theory import sr2v_scalar_lattice_v042 as lattice
from universe_lab.final_theory import weak_d2_visible_torus_scout_v042 as torus

BUDGET_PATH = "config/v0.4.2_sr2v_q5_free_auxiliary_ideal_budget.json"
SOLVER_DIRECTORY = "results/v0.4.2_sr2v_q5_free_auxiliary_ideal_solver"
WORKER_MODULE_PATH = "src/universe_lab/final_theory/sr2v_q5_free_auxiliary_ideal_solver_v042.py"

NON_ALIGNED_CHARTS = ("U2", "U3", "U4")
ALIGNED_CHARTS = ("aligned_w2_equals_1", "aligned_w3_equals_1", "aligned_w4_equals_1")
ALL_CHARTS = (*NON_ALIGNED_CHARTS, *ALIGNED_CHARTS)

#: The chart-quotient polynomial ids (d2/d3/d4 cleared, and each chart's
#: Rabinowitsch localiser) are not carried in the small Git-tracked root --
#: only the generator ids are. They are recovered once, cheaply, by
#: recomputing the chart polynomials in isolation (a few seconds; no full
#: 1,127-row rebuild) and locating their content by SHA-256 inside the
#: committed ``polynomial_arena`` chunks. See ``resolve_chart_quotient_ids``.
_CLEARED_QUOTIENT_NAMES = ("d2", "d3", "d4")
_RABINOWITSCH_NAMES = ("d2", "d3", "d4", "f_tilde")


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def load_human_budget(root: Path) -> dict[str, Any]:
    """Read the campaign-specific external budget file without inventing defaults."""

    path = root / BUDGET_PATH
    if not path.is_file():
        raise FileNotFoundError(f"external budget file is required: {BUDGET_PATH}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    required = {"timeout_seconds_per_chart", "total_wall_time_seconds", "memory_limit_gib"}
    missing = required - set(payload)
    if missing:
        raise ValueError(f"budget is missing required keys: {missing}")
    unsupported = set(payload) - required
    if unsupported:
        raise ValueError(f"budget has unsupported, unauthorised keys: {unsupported}")
    for name in required:
        value = payload[name]
        if not isinstance(value, int | float):
            raise TypeError(f"budget {name} must be numeric")
        if not (value > 0):
            raise ValueError(f"budget {name} must be positive and finite")
    timeout = payload["timeout_seconds_per_chart"]
    total = payload["total_wall_time_seconds"]
    if timeout > total:
        raise ValueError("timeout_seconds_per_chart cannot exceed total_wall_time_seconds")
    return {
        "path": BUDGET_PATH,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "timeout_seconds_per_chart": int(timeout),
        "total_wall_time_seconds": int(total),
        "memory_limit_gib": payload["memory_limit_gib"],
        "memory_limit_bytes": int(payload["memory_limit_gib"] * 1024 * 1024 * 1024),
    }


def _committed_root(root: Path) -> dict[str, Any]:
    return bundle._load(root / bundle.ROOT_RESULT_PATH)  # noqa: SLF001


def resolve_chart_quotient_ids(root: Path) -> dict[str, Any]:
    """Recover d2/d3/d4 (cleared) and every chart's Rabinowitsch localiser id.

    These live in the full logical payload, which the two-tier bundle does not
    retain, but the *content* is already present in the committed
    ``polynomial_arena``: the bundle module already interned it while framing
    the frozen generator tables. Recomputing the closed-form chart polynomials
    in an empty arena is cheap (a few seconds; it does not touch the 1,127
    Schur rows), and content-addressed lookup against the committed chunks
    proves the recomputation reproduces exactly what was frozen -- this
    function fails closed if any of the seven targets is missing.
    """

    committed = _committed_root(root)
    context = torus._build_context(root)  # noqa: SLF001
    operator_context = lattice._build_context(root)  # noqa: SLF001
    upper_symbols = {
        variable: sp.Symbol(f"a{index}") for index, variable in enumerate(context.variables)
    }
    lower_symbols = {
        variable: sp.Symbol(f"b{index}") for index, variable in enumerate(context.variables)
    }
    coordinates = manifest._base_coordinates(  # noqa: SLF001
        context, operator_context, upper_symbols, lower_symbols
    )
    factor_basis = manifest._lambda_factor_basis()  # noqa: SLF001
    bottom_payload = manifest._load(root / bottom_global.RESULT_PATH)  # noqa: SLF001
    _bottom_localization, active_bottom_localising_product = manifest._bottom_localization_ledger(  # noqa: SLF001
        bottom_payload, factor_basis
    )
    chart_polynomials = manifest._chart_polynomials(context, coordinates)  # noqa: SLF001
    width = len(coordinates.active_names)

    arena = manifest.PolynomialArena()
    localized_arena = manifest.LocalizedArena()
    chart_records = {
        name: manifest._clearing_certificate(  # noqa: SLF001
            {name: polynomial}, localized_arena, arena, factor_basis
        )
        for name, polynomial in chart_polynomials.items()
    }
    targets: dict[str, str] = {}
    for name in _CLEARED_QUOTIENT_NAMES:
        cleared_id = chart_records[name]["cleared_coefficient_polynomial_ids"][name]
        targets[f"cleared_{name}"] = arena.records[cleared_id]["sha256"]
    for name in _RABINOWITSCH_NAMES:
        cleared_id = chart_records[name]["cleared_coefficient_polynomial_ids"][name]
        cleared = arena.polynomial(cleared_id)
        localization_id = arena.intern(
            manifest._localization_polynomial(  # noqa: SLF001
                cleared, width, active_bottom_localising_product
            )
        )
        targets[f"rabinowitsch_{name}"] = arena.records[localization_id]["sha256"]

    directory = root / bundle.BUNDLE_DIRECTORY
    chunks = [
        record
        for record in committed["chunk_ledger"]["chunks"]
        if record["arena"] == "polynomial_arena"
    ]
    wanted = set(targets.values())
    found: dict[str, dict[str, Any]] = {}
    for record in bundle.read_arena_chunks(directory, chunks):
        if record["sha256"] in wanted and record["sha256"] not in found:
            found[record["sha256"]] = record
            if len(found) == len(wanted):
                break
    missing = [label for label, digest in targets.items() if digest not in found]
    if missing:
        raise AssertionError(f"chart quotient targets absent from the committed arena: {missing}")

    resolved = {
        "cleared": {
            name: found[targets[f"cleared_{name}"]]["polynomial_id"]
            for name in _CLEARED_QUOTIENT_NAMES
        },
        "rabinowitsch": {
            name: found[targets[f"rabinowitsch_{name}"]]["polynomial_id"]
            for name in _RABINOWITSCH_NAMES
        },
    }
    for stage, name in ((2, "d2"), (3, "d3"), (4, "d4")):
        expected = committed["chart_generator_ids"]["charts"][f"U{stage}"][
            "planned_Rabinowitsch_localization_polynomial_id"
        ]
        if resolved["rabinowitsch"][name] != expected:
            raise AssertionError(f"U{stage} Rabinowitsch id disagrees with the committed root")
    for fixed in (2, 3, 4):
        expected = committed["chart_generator_ids"]["charts"][f"aligned_w{fixed}_equals_1"][
            "planned_Rabinowitsch_localization_polynomial_id"
        ]
        if resolved["rabinowitsch"]["f_tilde"] != expected:
            raise AssertionError(
                f"aligned_w{fixed} Rabinowitsch id disagrees with the committed root"
            )
    return {
        "resolved": resolved,
        "terms": {
            name: found[digest]["terms"]
            for name, digest in {
                **{f"cleared_{n}": targets[f"cleared_{n}"] for n in _CLEARED_QUOTIENT_NAMES},
                **{f"rabinowitsch_{n}": targets[f"rabinowitsch_{n}"] for n in _RABINOWITSCH_NAMES},
            }.items()
        },
    }


#: A generator is stored as ``[[exponent_list, numerator, denominator], ...]``
#: over the *full* ring (base 52 variables plus whichever auxiliary variables
#: the chart uses), sorted by exponent tuple with no duplicate exponents --
#: the same shape ``PolynomialArena`` already uses, just extended in width.
GeneratorTerms = list[list[Any]]


def _extend_terms(
    serial_terms: Sequence[Sequence[Any]],
    width: int,
    bump_index: int | None,
) -> dict[tuple[int, ...], Fraction]:
    """Embed a base-52-variable term list into the full ring.

    ``bump_index`` sets that one ring coordinate's exponent to 1 on every term
    -- used to represent multiplication by an auxiliary variable such as
    ``h``. Pass ``None`` for a coefficient with no auxiliary factor.
    """

    result: dict[tuple[int, ...], Fraction] = {}
    for exponent_pairs, numerator, denominator in serial_terms:
        full = [0] * width
        for index, power in exponent_pairs:
            full[index] = power
        if bump_index is not None:
            full[bump_index] = 1
        key = tuple(full)
        result[key] = result.get(key, Fraction(0)) + Fraction(int(numerator), int(denominator))
    return result


def _merge_terms(
    parts: Iterable[Mapping[tuple[int, ...], Fraction]],
) -> dict[tuple[int, ...], Fraction]:
    merged: dict[tuple[int, ...], Fraction] = {}
    for part in parts:
        for key, value in part.items():
            total = merged.get(key, Fraction(0)) + value
            if total:
                merged[key] = total
            elif key in merged:
                del merged[key]
    return merged


def _serialise_terms(terms: Mapping[tuple[int, ...], Fraction]) -> GeneratorTerms:
    return [
        [
            [[index, power] for index, power in enumerate(exponent) if power],
            value.numerator,
            value.denominator,
        ]
        for exponent, value in sorted(terms.items())
        if value
    ]


def stream_polynomial_arena(root: Path) -> Iterator[dict[str, Any]]:
    """Stream every committed ``polynomial_arena`` record, checked chunk by chunk."""

    committed = _committed_root(root)
    directory = root / bundle.BUNDLE_DIRECTORY
    chunks = [
        record
        for record in committed["chunk_ledger"]["chunks"]
        if record["arena"] == "polynomial_arena"
    ]
    yield from bundle.read_arena_chunks(directory, chunks)


def _non_aligned_generator_terms(
    width: int,
    h_index: int,
    a_terms: Sequence[Sequence[Any]],
    b_terms: Sequence[Sequence[Any]],
) -> GeneratorTerms:
    """Build ``h*A+B`` directly as full-width terms; no Sage parsing involved."""

    merged = _merge_terms(
        [_extend_terms(a_terms, width, h_index), _extend_terms(b_terms, width, None)]
    )
    return _serialise_terms(merged)


def _aligned_generator_terms(
    width: int,
    index_by_auxiliary: Mapping[str, int],
    coefficients: Mapping[str, Sequence[Sequence[Any]]],
) -> GeneratorTerms:
    """Build ``h*A+constant+sum(w_j*B_j)`` directly as full-width terms."""

    merged = _merge_terms(
        _extend_terms(terms, width, index_by_auxiliary.get(key))
        for key, terms in coefficients.items()
    )
    return _serialise_terms(merged)


def _plain_generator_terms(width: int, terms: Sequence[Sequence[Any]]) -> GeneratorTerms:
    return _serialise_terms(_extend_terms(terms, width, None))


def _rabinowitsch_generator_terms(
    width: int, z_index: int, localiser_terms: Sequence[Sequence[Any]]
) -> GeneratorTerms:
    """Build ``1-z*localiser`` directly as full-width terms."""

    one = {(0,) * width: Fraction(1)}
    z_times_localiser = {
        key: -value for key, value in _extend_terms(localiser_terms, width, z_index).items()
    }
    return _serialise_terms(_merge_terms([one, z_times_localiser]))


def build_chart_ideal(root: Path, chart_name: str) -> dict[str, Any]:
    """Materialise one chart's full ideal from the verified bundle as term lists.

    This does not run Sage. It only reads back frozen, already-verified
    content; the polynomial ring variables and the Rabinowitsch equation match
    ``reports/v0.4.2_sr2v_q5_free_auxiliary_ideal_execution_plan.md`` sections
    3 and 4 exactly. Generators are structured ``[exponent, numerator,
    denominator]`` term lists rather than Sage source text: some coefficients
    in this campaign run to hundreds of thousands of terms, and building a
    single chained-``+`` expression string that large blows CPython's
    recursion limit during ``compile()``/``sage_eval`` well before Sage ever
    sees it. A term list is read on the Sage side with an O(term-count) dict
    construction instead.
    """

    if chart_name not in ALL_CHARTS:
        raise AssertionError(f"unknown chart: {chart_name}")
    committed = _committed_root(root)
    chart = committed["chart_generator_ids"]["charts"][chart_name]
    base_variables = list(committed["ring_binding"]["polynomial_arena_variable_order"])
    if base_variables != [*(f"t{i}" for i in (1, 2, 3, 4)), *(f"s{i}" for i in range(48))]:
        raise AssertionError("the frozen active-variable order changed")
    auxiliary_variables = (
        ["h"] if chart_name in NON_ALIGNED_CHARTS else list(chart["auxiliary_variables"])
    )
    ring_variables = [*base_variables, *auxiliary_variables, "z"]
    if len(set(ring_variables)) != len(ring_variables):
        raise AssertionError("ring variable name collision")
    width = len(ring_variables)
    index_by_auxiliary = {name: ring_variables.index(name) for name in auxiliary_variables}
    z_index = ring_variables.index("z")

    quotient = resolve_chart_quotient_ids(root)
    needed_ids: set[int] = set()
    for generator in chart["generator_polynomial_ids"]:
        needed_ids.update(int(value) for value in generator[1:])
    needed_ids.add(quotient["resolved"]["rabinowitsch"][_rabinowitsch_key(chart_name)])
    if chart_name in ALIGNED_CHARTS:
        needed_ids.update(quotient["resolved"]["cleared"].values())

    by_id: dict[int, list[Any]] = {}
    for record in stream_polynomial_arena(root):
        identifier = int(record["polynomial_id"])
        if identifier in needed_ids:
            by_id[identifier] = record["terms"]
            if len(by_id) == len(needed_ids):
                break
    missing = needed_ids - set(by_id)
    if missing:
        raise AssertionError(
            f"{chart_name}: polynomial ids absent from the committed arena: {missing}"
        )

    dropped_zero_generators = 0
    generators: list[GeneratorTerms] = []
    if chart_name in NON_ALIGNED_CHARTS:
        h_index = index_by_auxiliary["h"]
        for entry in chart["generator_polynomial_ids"]:
            a_terms, b_terms = by_id[int(entry[1])], by_id[int(entry[2])]
            if not a_terms and not b_terms:
                # 0*h+0 contributes nothing to the ideal; dropping a zero
                # generator never changes what it generates.
                dropped_zero_generators += 1
                continue
            generators.append(_non_aligned_generator_terms(width, h_index, a_terms, b_terms))
    else:
        key_order = list(chart["generator_auxiliary_key_order"])
        for entry in chart["generator_polynomial_ids"]:
            coefficients = {
                key: by_id[int(entry[1 + index])] for index, key in enumerate(key_order)
            }
            if not any(coefficients.values()):
                dropped_zero_generators += 1
                continue
            generators.append(_aligned_generator_terms(width, index_by_auxiliary, coefficients))
        for name in _CLEARED_QUOTIENT_NAMES:
            generators.append(
                _plain_generator_terms(width, by_id[quotient["resolved"]["cleared"][name]])
            )

    rabinowitsch_id = quotient["resolved"]["rabinowitsch"][_rabinowitsch_key(chart_name)]
    generators.append(_rabinowitsch_generator_terms(width, z_index, by_id[rabinowitsch_id]))

    return {
        "chart": chart_name,
        "ring_variables": ring_variables,
        "generator_count": len(generators),
        "dropped_zero_generator_count": dropped_zero_generators,
        "generators": generators,
        "generators_digest_sha256": _digest(generators),
        "committed_root_semantic_digest_sha256": committed["semantic_digest_sha256"],
        "committed_full_logical_payload_digest_sha256": committed["full_logical_payload"][
            "semantic_digest_sha256"
        ],
        "committed_chart_manifest_sha256": chart["chart_manifest_sha256"],
        "committed_generator_manifest_sha256": chart["generator_manifest_sha256"],
    }


def _rabinowitsch_key(chart_name: str) -> str:
    return "f_tilde" if chart_name in ALIGNED_CHARTS else chart_name.lower().replace("u", "d")


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, ensure_ascii=True, sort_keys=True)


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_chart_ideal_file(root: Path, chart_name: str) -> Path:
    directory = root / SOLVER_DIRECTORY / "ideals"
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{chart_name}.json"
    if path.is_file():
        existing = _load_json(path)
        if (
            existing.get("committed_root_semantic_digest_sha256")
            == _committed_root(root)["semantic_digest_sha256"]
        ):
            return path
    ideal = build_chart_ideal(root, chart_name)
    _write_json(path, ideal)
    return path


#: Reads the ideal from a file inside the container rather than through the
#: host-container pipe: a chart's generator text can run to hundreds of MiB to
#: low GiB, and ``subprocess.communicate`` would otherwise have to buffer all
#: of it on both ends. Only this small driver script and a tiny
#: ``{ideal_file, memory_limit_bytes}`` payload cross the pipe; the file itself
#: is read directly off the bind-mounted repository.
_WORKER_SCRIPT = r"""
import json
import resource
import sys
import time

request = json.loads(sys.stdin.read())
memory_limit_bytes = int(request["memory_limit_bytes"])
resource.setrlimit(resource.RLIMIT_AS, (memory_limit_bytes, memory_limit_bytes))

with open(request["ideal_file"], encoding="utf-8") as handle:
    payload = json.load(handle)
ring_variables = payload["ring_variables"]
generators_terms = payload["generators"]
width = len(ring_variables)


def to_polynomial(ring, serial_terms):
    # Built as a single dict->polynomial construction, not a chained Sage
    # expression: some generators carry hundreds of thousands of terms, and
    # sage_eval on that large a source string exceeds CPython's recursion
    # limit during compile() before Sage ever sees it.
    data = {}
    for exponent_pairs, numerator, denominator in serial_terms:
        exponent = [0] * width
        for index, power in exponent_pairs:
            exponent[index] = power
        data[tuple(exponent)] = QQ(numerator) / QQ(denominator)
    return ring(data)


started = time.perf_counter()
ring = PolynomialRing(QQ, ring_variables, order="degrevlex")
gens = [to_polynomial(ring, terms) for terms in generators_terms]
parse_seconds = time.perf_counter() - started

ideal = ring.ideal(gens)
gb_started = time.perf_counter()
basis = ideal.groebner_basis()
gb_seconds = time.perf_counter() - gb_started

is_unit_ideal = len(basis) == 1 and basis[0].is_unit()
result = {
    "chart": payload["chart"],
    "ring_variable_count": len(ring_variables),
    "generator_count": len(gens),
    "parse_seconds": parse_seconds,
    "groebner_seconds": gb_seconds,
    "basis_size": len(basis),
    "is_unit_ideal": bool(is_unit_ideal),
    "max_ru_maxrss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    "sage_version": str(sage.version.version),
    "singular_version": singular.version().splitlines()[0],
}
print(json.dumps(result))
"""


def _decode(value: bytes | str | None) -> str:
    if value is None:
        return ""
    return value.decode("utf-8", errors="replace") if isinstance(value, bytes) else value


def run_sage_groebner_request(
    root: Path,
    chart_name: str,
    ideal_file: Path,
    *,
    memory_limit_bytes: int,
    timeout_seconds: int,
) -> dict[str, Any]:
    """Send one chart's ideal to the ``sage`` Compose service and compute its basis.

    ``ideal_file`` must already sit under ``root`` (the repository is bind-
    mounted into the container at ``/home/sage/work``), and is read directly by
    the worker rather than piped in, since it can run to hundreds of MiB.

    Fail-closed on timeout: the process and its container-side child are both
    killed, and the result records ``TIMEOUT`` rather than a fabricated basis.
    This mirrors ``d2_sage_backend_v035.run_sage_request``'s host-side shape
    without importing or reusing any of its v0.3.5 ideal-construction code.
    """

    container_path = "/home/sage/work/" + ideal_file.resolve().relative_to(root).as_posix()
    payload = {
        "chart": chart_name,
        "ideal_file": container_path,
        "memory_limit_bytes": memory_limit_bytes,
    }
    command = [
        "docker",
        "compose",
        "exec",
        "-T",
        "sage",
        "sage",
        "-c",
        _WORKER_SCRIPT,
    ]
    started = time.perf_counter()
    process = subprocess.Popen(
        command,
        cwd=root,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        stdout, stderr = process.communicate(_canonical_json(payload), timeout=timeout_seconds)
    except subprocess.TimeoutExpired as exc:
        subprocess.run(
            ["docker", "compose", "exec", "-T", "sage", "pkill", "-f", "sage -c"],
            cwd=root,
            check=False,
            capture_output=True,
            text=True,
            timeout=20,
        )
        process.kill()
        try:
            stdout, stderr = process.communicate(timeout=20)
        except subprocess.TimeoutExpired:
            stdout = _decode(exc.stdout)
            stderr = _decode(exc.stderr)
        return {
            "chart": chart_name,
            "exit_status": "TIMEOUT",
            "wall_time_seconds": time.perf_counter() - started,
            "time_limit_seconds": timeout_seconds,
            "stdout_tail": (stdout or "")[-4000:],
            "stderr_tail": (stderr or "")[-4000:],
        }
    wall_time = time.perf_counter() - started
    if process.returncode != 0:
        return {
            "chart": chart_name,
            "exit_status": f"ERROR_{process.returncode}",
            "wall_time_seconds": wall_time,
            "time_limit_seconds": timeout_seconds,
            "stdout_tail": stdout[-4000:],
            "stderr_tail": stderr[-8000:],
        }
    lines = [line for line in stdout.splitlines() if line.strip()]
    if not lines:
        return {
            "chart": chart_name,
            "exit_status": "EMPTY_BACKEND_RESPONSE",
            "wall_time_seconds": wall_time,
            "time_limit_seconds": timeout_seconds,
            "stdout_tail": stdout[-8000:],
            "stderr_tail": stderr[-8000:],
        }
    try:
        result = json.loads(lines[-1])
    except json.JSONDecodeError:
        return {
            "chart": chart_name,
            "exit_status": "NON_JSON_BACKEND_RESPONSE",
            "wall_time_seconds": wall_time,
            "time_limit_seconds": timeout_seconds,
            "stdout_tail": stdout[-8000:],
            "stderr_tail": stderr[-8000:],
        }
    result["exit_status"] = "COMPLETED"
    result["host_observed_wall_time_seconds"] = wall_time
    result["time_limit_seconds"] = timeout_seconds
    return result


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--chart", choices=ALL_CHARTS, help="run only this chart")
    parser.add_argument(
        "--materialize-only",
        action="store_true",
        help="write the ideal file(s) without invoking Sage",
    )
    arguments = parser.parse_args(argv)
    root = Path(__file__).resolve().parents[3]
    charts = [arguments.chart] if arguments.chart else list(ALL_CHARTS)
    budget = load_human_budget(root)

    for chart_name in charts:
        path = write_chart_ideal_file(root, chart_name)
        print(_canonical_json({"chart": chart_name, "ideal_file": str(path)}))
        if arguments.materialize_only:
            continue
        result = run_sage_groebner_request(
            root,
            chart_name,
            path,
            memory_limit_bytes=budget["memory_limit_bytes"],
            timeout_seconds=budget["timeout_seconds_per_chart"],
        )
        result_path = root / SOLVER_DIRECTORY / "results" / f"{chart_name}.json"
        _write_json(result_path, result)
        print(_canonical_json({"chart": chart_name, "result": result}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
