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
        "target_sha256": targets,
        "committed_root_semantic_digest_sha256": committed["semantic_digest_sha256"],
    }


def resolve_chart_quotient_ids_cached(root: Path) -> dict[str, Any]:
    """``resolve_chart_quotient_ids`` memoised against the committed root digest.

    The resolution streams every arena chunk and costs about fifty seconds, but
    its answer is a function of the frozen root alone. The cache is keyed on
    that root's semantic digest, so a re-frozen bundle invalidates it rather
    than silently reusing identifiers from a different freeze.
    """

    path = root / SOLVER_DIRECTORY / "chart_quotient_ids.json"
    expected = _committed_root(root)["semantic_digest_sha256"]
    if path.is_file():
        cached = _load_json(path)
        if cached.get("committed_root_semantic_digest_sha256") == expected:
            return cached
    resolved = resolve_chart_quotient_ids(root)
    _write_json(path, resolved)
    return resolved


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


def _unique_preserving_order(rows: Iterable[tuple[int, ...]]) -> list[tuple[int, ...]]:
    """Drop repeated generator coefficient tuples, keeping first appearance.

    Two M0 rows that reduce to the same coefficient tuple give the *same*
    polynomial, and repeating a generator never changes the ideal it
    generates. In this campaign that removes about a third of the non-zero
    rows, so it is both safe and worth doing before any Groebner call.
    """

    seen: set[tuple[int, ...]] = set()
    unique: list[tuple[int, ...]] = []
    for row in rows:
        if row in seen:
            continue
        seen.add(row)
        unique.append(row)
    return unique


def build_chart_recipe(root: Path, chart_name: str, *, modulus: int = 0) -> dict[str, Any]:
    """Describe one chart's ideal by arena identifier, without materialising it.

    The polynomial data itself is never loaded here. Reading the ~19.1 million
    arena terms into Python lists costs tens of GiB, so the host only decides
    *which* frozen arena records combine into which generator and hands that
    recipe to the Sage worker, which streams the same committed chunks and
    converts each record straight into a Singular polynomial.

    Two reductions are applied, both of which leave the generated ideal
    unchanged: a row whose coefficients are all zero is dropped, and a
    coefficient tuple that repeats an earlier row is dropped. In this campaign
    that takes the non-aligned charts from 1,127 rows to 543.

    ``modulus`` of ``0`` means the exact field ``QQ``; a prime selects
    ``GF(p)`` for a screening run, which is not a proof over ``QQ``.
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
    index_by_auxiliary = {name: ring_variables.index(name) for name in auxiliary_variables}

    quotient = resolve_chart_quotient_ids_cached(root)
    rabinowitsch_id = quotient["resolved"]["rabinowitsch"][_rabinowitsch_key(chart_name)]

    entries = chart["generator_polynomial_ids"]
    if chart_name in NON_ALIGNED_CHARTS:
        key_order = ["h", "constant"]
    else:
        key_order = list(chart["generator_auxiliary_key_order"])
    rows: list[tuple[int, ...]] = [
        tuple(int(value) for value in entry[1 : 1 + len(key_order)]) for entry in entries
    ]
    nonzero_rows = [row for row in rows if any(row)]
    unique_rows = _unique_preserving_order(nonzero_rows)

    #: Each generator is ``sum(auxiliary_variable * arena_polynomial)``. The
    #: ``constant`` slot has no auxiliary factor, so its multiplier index is
    #: ``None``; every other slot multiplies by exactly one ring variable.
    generators: list[list[list[int | None]]] = [
        [
            [index_by_auxiliary.get(key), identifier]
            for key, identifier in zip(key_order, row, strict=True)
            if identifier or key == "constant"
        ]
        for row in unique_rows
    ]
    if chart_name in ALIGNED_CHARTS:
        generators.extend(
            [[None, int(quotient["resolved"]["cleared"][name])]] for name in _CLEARED_QUOTIENT_NAMES
        )

    needed_ids = sorted(
        {int(pair[1]) for generator in generators for pair in generator if pair[1] is not None}
    )
    chunks = [
        {
            "path": "/home/sage/work/"
            + (Path(bundle.BUNDLE_DIRECTORY) / str(record["path"])).as_posix(),
            "gzip_bytes": record["gzip_bytes"],
            "gzip_sha256": record["gzip_sha256"],
            "uncompressed_bytes": record["uncompressed_bytes"],
            "uncompressed_sha256": record["uncompressed_sha256"],
            "record_count": record["record_count"],
        }
        for record in committed["chunk_ledger"]["chunks"]
        if record["arena"] == "polynomial_arena"
    ]
    recipe = {
        "chart": chart_name,
        "modulus": int(modulus),
        "ring_variables": ring_variables,
        "z_index": ring_variables.index("z"),
        "rabinowitsch_polynomial_id": rabinowitsch_id,
        "generator_count": len(generators) + 1,
        "source_row_count": len(entries),
        "dropped_zero_row_count": len(rows) - len(nonzero_rows),
        "dropped_duplicate_row_count": len(nonzero_rows) - len(unique_rows),
        "generators": generators,
        "needed_polynomial_ids": needed_ids,
        "chunks": chunks,
        "generators_digest_sha256": _digest(generators),
        "committed_root_semantic_digest_sha256": committed["semantic_digest_sha256"],
        "committed_full_logical_payload_digest_sha256": committed["full_logical_payload"][
            "semantic_digest_sha256"
        ],
        "committed_chart_manifest_sha256": chart["chart_manifest_sha256"],
        "committed_generator_manifest_sha256": chart["generator_manifest_sha256"],
    }
    return recipe


def _rabinowitsch_key(chart_name: str) -> str:
    return "f_tilde" if chart_name in ALIGNED_CHARTS else chart_name.lower().replace("u", "d")


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, ensure_ascii=True, sort_keys=True)


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_chart_recipe_file(root: Path, chart_name: str, *, modulus: int = 0) -> Path:
    directory = root / SOLVER_DIRECTORY / "recipes"
    directory.mkdir(parents=True, exist_ok=True)
    suffix = "QQ" if not modulus else f"GF{modulus}"
    path = directory / f"{chart_name}.{suffix}.json"
    if path.is_file():
        existing = _load_json(path)
        if (
            existing.get("committed_root_semantic_digest_sha256")
            == _committed_root(root)["semantic_digest_sha256"]
            and existing.get("modulus") == modulus
        ):
            return path
    _write_json(path, build_chart_recipe(root, chart_name, modulus=modulus))
    return path


#: The worker streams the committed arena chunks itself and turns each needed
#: record straight into a Singular polynomial. Nothing materialises the whole
#: coefficient set in Python: the 19.1 million arena terms cost tens of GiB as
#: nested Python lists but only a few hundred MiB as Singular's packed sparse
#: representation. Chunk digests are verified incrementally while streaming, so
#: this stays as fail-closed as ``bundle.read_arena_chunks``.
_WORKER_SCRIPT = r"""
import gzip
import hashlib
import json
import resource
import sys
import time

request = json.loads(sys.stdin.read())
memory_limit_bytes = int(request["memory_limit_bytes"])
resource.setrlimit(resource.RLIMIT_AS, (memory_limit_bytes, memory_limit_bytes))
stage_only = request.get("stage_only")


def plain(value):
    # sage -c runs the Sage preparser, so numeric literals and anything derived
    # from them become Sage types (Integer, RealDoubleElement, ...) that the
    # json module refuses to encode. Everything crossing the JSON boundary is
    # coerced back to a plain Python number here.
    if isinstance(value, bool) or value is None:
        return value
    try:
        if value == int(value):
            return int(value)
    except (TypeError, ValueError, OverflowError):
        pass
    try:
        return float(value)
    except (TypeError, ValueError):
        return str(value)


def progress(stage, **fields):
    # Written to stderr so a killed request still leaves evidence of how far it
    # got; stdout carries only the final JSON result.
    fields["stage"] = stage
    fields["elapsed"] = float(time.perf_counter() - script_started)
    fields["rss_kib"] = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    sys.stderr.write(json.dumps(fields, default=plain) + "\n")
    sys.stderr.flush()


script_started = time.perf_counter()
with open(request["recipe_file"], encoding="utf-8") as handle:
    recipe = json.load(handle)
progress("recipe_loaded", chart=recipe["chart"])

ring_variables = recipe["ring_variables"]
width = len(ring_variables)
modulus = int(recipe["modulus"])
field = QQ if modulus == 0 else GF(modulus)
ring = PolynomialRing(field, ring_variables, order="degrevlex")
gens_by_index = list(ring.gens())
needed = set(int(value) for value in recipe["needed_polynomial_ids"])
needed.add(int(recipe["rabinowitsch_polynomial_id"]))

started = time.perf_counter()
by_id = {}
scanned_records = 0
loaded_terms = 0
for chunk_index, chunk in enumerate(recipe["chunks"]):
    digest = hashlib.sha256()
    seen_in_chunk = 0
    with gzip.open(chunk["path"], "rb") as handle:
        for line in handle:
            digest.update(line)
            seen_in_chunk += 1
            record = json.loads(line)
            identifier = int(record["polynomial_id"])
            if identifier in needed and identifier not in by_id:
                data = {}
                for exponent_pairs, numerator, denominator in record["terms"]:
                    exponent = [0] * width
                    for index, power in exponent_pairs:
                        exponent[index] = power
                    data[tuple(exponent)] = field(numerator) / field(denominator)
                by_id[identifier] = ring(data)
                loaded_terms += len(data)
            scanned_records += 1
    if seen_in_chunk != int(chunk["record_count"]):
        raise AssertionError(chunk["path"] + ": record count does not match the ledger")
    if digest.hexdigest() != chunk["uncompressed_sha256"]:
        raise AssertionError(chunk["path"] + ": uncompressed digest does not match the ledger")
    progress(
        "chunk_verified",
        chunk_index=chunk_index,
        chunks=len(recipe["chunks"]),
        loaded=len(by_id),
        needed=len(needed),
        loaded_terms=loaded_terms,
    )
missing = sorted(needed - set(by_id))
if missing:
    raise AssertionError("arena is missing polynomial ids: " + repr(missing[:8]))
load_seconds = time.perf_counter() - started
progress("load_complete", load_seconds=float(load_seconds), loaded_terms=loaded_terms)

build_started = time.perf_counter()
gens = []
for generator in recipe["generators"]:
    total = ring.zero()
    for multiplier_index, identifier in generator:
        piece = by_id[int(identifier)]
        if multiplier_index is not None:
            piece = gens_by_index[int(multiplier_index)] * piece
        total += piece
    if total:
        gens.append(total)
localiser = by_id[int(recipe["rabinowitsch_polynomial_id"])]
gens.append(ring.one() - gens_by_index[int(recipe["z_index"])] * localiser)
build_seconds = time.perf_counter() - build_started

del by_id
generator_terms = sum(int(polynomial.number_of_terms()) for polynomial in gens)
progress(
    "build_complete",
    build_seconds=float(build_seconds),
    generators=len(gens),
    generator_terms=generator_terms,
)

generator_term_counts = sorted(
    (int(polynomial.number_of_terms()) for polynomial in gens), reverse=True
)

gb_seconds = None
basis_size = None
is_unit_ideal = None
if stage_only != "build":
    ideal = ring.ideal(gens)
    gb_started = time.perf_counter()
    progress("groebner_started", generators=len(gens), generator_terms=generator_terms)
    basis = ideal.groebner_basis()
    gb_seconds = float(time.perf_counter() - gb_started)
    basis_size = len(basis)
    is_unit_ideal = bool(basis_size == 1 and basis[0].is_unit())
    progress("groebner_complete", groebner_seconds=gb_seconds, basis_size=basis_size)

result = {
    "chart": recipe["chart"],
    "modulus": modulus,
    "coefficient_field": "QQ" if modulus == 0 else ("GF(%d)" % modulus),
    "ring_variable_count": width,
    "arena_records_scanned": scanned_records,
    "arena_polynomials_loaded": len(needed),
    "generator_count": len(gens),
    "generator_terms": generator_terms,
    "largest_generator_term_counts": generator_term_counts[:10],
    "median_generator_term_count": generator_term_counts[len(generator_term_counts) // 2],
    "load_seconds": load_seconds,
    "build_seconds": build_seconds,
    "groebner_seconds": gb_seconds,
    "basis_size": basis_size,
    "is_unit_ideal": is_unit_ideal,
    "stage_only": stage_only,
    "max_ru_maxrss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    "sage_version": str(sage.version.version),
    "singular_version": singular.version().splitlines()[0],
}
print(json.dumps(result, default=plain))
"""


def _decode(value: bytes | str | None) -> str:
    if value is None:
        return ""
    return value.decode("utf-8", errors="replace") if isinstance(value, bytes) else value


def _progress_records(stderr_text: str) -> list[dict[str, Any]]:
    """Recover the worker's stage markers from stderr.

    A killed request still leaves these, so a timeout reports how far it got --
    which chunk it was verifying, or whether it had reached Groebner at all --
    instead of only that it ran out of time.
    """

    records: list[dict[str, Any]] = []
    for line in stderr_text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("{"):
            continue
        try:
            value = json.loads(stripped)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict) and "stage" in value:
            records.append(value)
    return records


#: The container-side worker is launched by ``sage -c``, but the process that
#: actually appears in the container's process table is ``sage-eval``, so a
#: ``pkill -f "sage -c"`` matches nothing. A real run was observed surviving its
#: own timeout that way, holding 6.6 GiB and a full core for eleven minutes past
#: the approved limit.
#:
#: ``sage -c`` concatenates any trailing arguments onto the script itself, so
#: the request id cannot be passed as a separate argv entry. It is instead
#: embedded as a comment on the script's first line: the whole script text is
#: part of the command line, so ``pgrep -f`` matches it there.
_WORKER_TAG = "sr2v_auxiliary_ideal_worker"


def _tagged_worker_script(request_id: str) -> str:
    return f"# {_WORKER_TAG}={request_id}\n{_WORKER_SCRIPT}"


def _kill_container_worker(root: Path, request_id: str) -> dict[str, Any]:
    """Kill this request's container-side worker, and report what happened.

    Fail-closed in the reporting sense: the caller records the outcome instead
    of assuming the kill worked, because a surviving worker silently violates
    the sequential single-worker resource contract.
    """

    pattern = f"{_WORKER_TAG}={request_id}"
    outcome: dict[str, Any] = {"pattern": pattern}
    try:
        killed = subprocess.run(
            ["docker", "compose", "exec", "-T", "sage", "pkill", "-9", "-f", pattern],
            cwd=root,
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
        outcome["pkill_returncode"] = killed.returncode
        survivors = subprocess.run(
            ["docker", "compose", "exec", "-T", "sage", "pgrep", "-c", "-f", pattern],
            cwd=root,
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
        remaining = (survivors.stdout or "0").strip() or "0"
        outcome["surviving_worker_count"] = int(remaining)
        outcome["worker_terminated"] = outcome["surviving_worker_count"] == 0
    except (OSError, subprocess.SubprocessError, ValueError) as error:
        outcome["worker_terminated"] = False
        outcome["error"] = f"{type(error).__name__}: {error}"
    return outcome


def run_sage_groebner_request(
    root: Path,
    chart_name: str,
    recipe_file: Path,
    *,
    memory_limit_bytes: int,
    timeout_seconds: int,
    stage_only: str | None = None,
) -> dict[str, Any]:
    """Send one chart's recipe to the ``sage`` Compose service and compute its basis.

    ``recipe_file`` must already sit under ``root`` (the repository is bind-
    mounted into the container at ``/home/sage/work``). Only the recipe and
    this driver script cross the pipe; the worker streams the arena chunks
    itself.

    Fail-closed on timeout: the host process and the container-side worker are
    both killed, the kill is verified, and the result records ``TIMEOUT``
    rather than a fabricated basis. This mirrors
    ``d2_sage_backend_v035.run_sage_request``'s host-side shape without
    importing or reusing any of its v0.3.5 ideal-construction code.
    """

    container_path = "/home/sage/work/" + recipe_file.resolve().relative_to(root).as_posix()
    request_id = _digest([chart_name, container_path, time.time_ns()])[:20]
    payload = {
        "chart": chart_name,
        "recipe_file": container_path,
        "memory_limit_bytes": memory_limit_bytes,
        "stage_only": stage_only,
    }
    command = [
        "docker",
        "compose",
        "exec",
        "-T",
        "sage",
        "sage",
        "-c",
        _tagged_worker_script(request_id),
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
        kill_outcome = _kill_container_worker(root, request_id)
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
            "request_id": request_id,
            "container_worker_kill": kill_outcome,
            "progress_tail": _progress_records(stderr or ""),
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
    result["request_id"] = request_id
    result["progress_tail"] = _progress_records(stderr)
    return result


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--chart", choices=ALL_CHARTS, help="run only this chart")
    parser.add_argument(
        "--recipe-only",
        action="store_true",
        help="write the recipe file(s) without invoking Sage",
    )
    parser.add_argument(
        "--modulus",
        type=int,
        default=0,
        help=(
            "0 (default) computes over QQ; a prime screens over GF(p), "
            "which is a scout result and never a proof over QQ"
        ),
    )
    parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=None,
        help="override the per-chart timeout downwards for a screening run",
    )
    parser.add_argument(
        "--stage-only",
        choices=("build",),
        default=None,
        help="stop after building the generators, before any Groebner call",
    )
    arguments = parser.parse_args(argv)
    root = Path(__file__).resolve().parents[3]
    charts = [arguments.chart] if arguments.chart else list(ALL_CHARTS)
    budget = load_human_budget(root)
    timeout_seconds = budget["timeout_seconds_per_chart"]
    if arguments.timeout_seconds is not None:
        if arguments.timeout_seconds > timeout_seconds:
            raise ValueError("the approved per-chart timeout may only be lowered, never raised")
        timeout_seconds = arguments.timeout_seconds

    suffix = "QQ" if not arguments.modulus else f"GF{arguments.modulus}"
    for chart_name in charts:
        path = write_chart_recipe_file(root, chart_name, modulus=arguments.modulus)
        print(_canonical_json({"chart": chart_name, "recipe_file": str(path)}))
        if arguments.recipe_only:
            continue
        result = run_sage_groebner_request(
            root,
            chart_name,
            path,
            memory_limit_bytes=budget["memory_limit_bytes"],
            timeout_seconds=timeout_seconds,
            stage_only=arguments.stage_only,
        )
        stage_suffix = f".{arguments.stage_only}" if arguments.stage_only else ""
        result_path = (
            root / SOLVER_DIRECTORY / "results" / f"{chart_name}.{suffix}{stage_suffix}.json"
        )
        _write_json(result_path, result)
        print(_canonical_json({"chart": chart_name, "result": result}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
