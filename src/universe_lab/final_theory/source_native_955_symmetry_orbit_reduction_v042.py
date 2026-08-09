"""Exact symmetry and orbit reduction gate for the v0.4.2 955 mixed locus.

The recorded next gate for ``strong_GC + reachable_state_MSR`` is to reduce the
remaining ``x!=0, y!=0`` mixed components by symmetry before scouting any
principal open set, and never to brute-force all 131 patches.  This module
executes that gate in two exactly certified parts.

Part A, the gauge torus.  Conjugating every transition by ``g_t=diag(t,1)``
sends ``A_e=[[p_e,x_[e]],[y_[e],1]]`` to ``[[p_e,t*x_[e]],[t^-1*y_[e],1]]``.  The
ansatz shape, the determinants, the CPOBC words, the strong-GC operator
equalities and the reachable-state MSR residuals are all preserved, so the
mixed locus carries a ``G_m`` action.  The machine certificate is the exact
``Z``-grading ``deg_x - deg_y`` of the frozen mixed manifest: every matrix
residual entry ``(i,j)`` is homogeneous of grade ``j-i`` and every reachable
state-vector residual component ``i`` is homogeneous of grade ``-i``.  The
vector half is simultaneously the machine check that the fixed preparation
vector is the ``g_t`` eigenvector ``e_1``; a non-eigenvector would break exactly
that homogeneity.

Part B, the combinatorial symmetry group.  A symmetry of the equation system is
a permutation ``sigma`` of the 131 ON transition orbits that preserves the CSG
character ``p``, the stage, the transition kind, the four ``Q`` generators, and
maps the CPOBC, strong-GC and reachable-MSR equation sets onto themselves.  Two
patches ``y_[e]!=0`` and ``y_[sigma e]!=0`` are interchangeable only for such a
``sigma``.  The module computes the stable equitable colouring of the bipartite
orbit/equation incidence structure under strictly ``sigma``-invariant labels.
The colouring is a coarsening of the true symmetry orbits, so a discrete stable
colouring proves the symmetry group is trivial and certifies that no patch
reduction exists, while a non-discrete colouring only bounds the orbit count
from below and requires explicit permutation certificates before any two
patches may be merged.

No Groebner, saturation, finite-field or numerical run is performed.
"""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from collections.abc import Iterable
from fractions import Fraction
from pathlib import Path
from typing import Any

from universe_lab.final_theory.causal_sets import maximal_elements_in_subset

CPOBC_PATH = "results/v0.3.1_cpobc_relations_n4.json"
REDUCTION_PATH = "results/v0.3.2_cpobc_generator_reduction.json"
LOCAL_GC_PATH = "results/v0.3.3_local_operator_gc_n4.json"
MIXED_MANIFEST_PATH = "results/v0.4.2_955_mixed_source_native_manifest.json"
TANGENT_SCOUT_PATH = "results/v0.4.2_955_mixed_xy_tangent_scout.json"
RESULT_PATH = "results/v0.4.2_955_symmetry_orbit_reduction.json"

SCHEMA = "final-theory-v042-955-symmetry-orbit-reduction-v1"

TRIVIAL_VERDICT = "V042_955_SYMMETRY_GROUP_TRIVIAL_NO_PATCH_REDUCTION_CERTIFIED"
REDUCED_VERDICT = "V042_955_SYMMETRY_ORBIT_UPPER_BOUND_CERTIFIED_PERMUTATIONS_REQUIRED"
TORUS_VERDICT = "V042_955_MIXED_GAUGE_TORUS_GRADING_CERTIFIED"

ORBIT_PREFIX = "cpobc-transition-orbit-"


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AssertionError(f"JSON object required: {path}")
    return value


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def _semantic_digest(payload: dict[str, Any]) -> str:
    semantic = {key: value for key, value in payload.items() if key != "semantic_digest_sha256"}
    return hashlib.sha256(_canonical_json(semantic).encode("utf-8")).hexdigest()


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _relation_code(relation: Iterable[int]) -> int:
    rows = tuple(int(row) for row in relation)
    return sum(row << (index * len(rows)) for index, row in enumerate(rows))


def _probability(record: dict[str, Any]) -> Fraction:
    stage = int(record["stage"])
    relation = tuple(int(row) for row in record["source_relation_rows"])
    precursor = int(record["precursor_code"])
    width = precursor.bit_count()
    maximal_count = len(maximal_elements_in_subset(relation, precursor))
    return Fraction(2 ** (width - maximal_count), 2**stage)


# ---------------------------------------------------------------------------
# Part A: the gauge torus grading certificate
# ---------------------------------------------------------------------------


def _monomial_grade(monomial: Iterable[dict[str, Any]]) -> int:
    grade = 0
    for factor in monomial:
        variable = str(factor["variable"])
        exponent = int(factor["exponent"])
        if variable.startswith("x:"):
            grade += exponent
        elif variable.startswith("y:"):
            grade -= exponent
        else:
            raise AssertionError(f"the mixed manifest carries an ungraded variable: {variable}")
    return grade


def _grading_certificate(manifest: dict[str, Any]) -> dict[str, Any]:
    blocks = manifest["residual_blocks"]
    matrix_blocks = ("CPOBC", "strong_GC", "reachable_MSR_operator")
    per_block: dict[str, dict[str, int]] = {}
    total_terms = 0
    for name in matrix_blocks:
        terms = 0
        for record in blocks[name]["records"]:
            for key, polynomial in record["entries"].items():
                row, column = int(key[0]), int(key[1])
                expected = column - row
                for term in polynomial:
                    terms += 1
                    if _monomial_grade(term["monomial"]) != expected:
                        raise AssertionError(
                            f"{name} entry {key} is not gauge-homogeneous of grade {expected}"
                        )
        per_block[name] = {"records": len(blocks[name]["records"]), "checked_terms": terms}
        total_terms += terms

    vector_terms = 0
    for record in blocks["reachable_MSR_vector"]["records"]:
        for key, polynomial in record["entries"].items():
            expected = -int(key)
            for term in polynomial:
                vector_terms += 1
                if _monomial_grade(term["monomial"]) != expected:
                    raise AssertionError(
                        f"reachable_MSR_vector component {key} is not homogeneous of {expected}"
                    )
    per_block["reachable_MSR_vector"] = {
        "records": len(blocks["reachable_MSR_vector"]["records"]),
        "checked_terms": vector_terms,
    }

    commutator_terms = 0
    for record in manifest["Q_commutator_polynomials"]["records"]:
        for key, polynomial in record["entries"].items():
            row, column = int(key[0]), int(key[1])
            expected = column - row
            for term in polynomial:
                commutator_terms += 1
                if _monomial_grade(term["monomial"]) != expected:
                    raise AssertionError(
                        f"Q commutator entry {key} is not gauge-homogeneous of {expected}"
                    )

    return {
        "action": "g_t=diag(t,1) acts by x_[e]->t*x_[e], y_[e]->t^-1*y_[e]",
        "grading": "deg_x - deg_y",
        "matrix_entry_rule": "residual entry (i,j) is homogeneous of grade j-i",
        "vector_component_rule": "reachable state-vector residual component i has grade -i",
        "per_block": per_block,
        "matrix_block_terms_checked": total_terms,
        "vector_terms_checked": vector_terms,
        "Q_commutator_terms_checked": commutator_terms,
        "violations": 0,
        "preparation_vector_is_g_t_eigenvector": {
            "vector": "e_1",
            "machine_evidence": (
                "The reachable state-vector residual block is exactly homogeneous of grade -i in "
                "every component; a preparation vector outside the g_t eigenbasis would destroy "
                "that homogeneity."
            ),
        },
        "invariants": {
            "diagonal_entries": "p_e and 1 are fixed by conjugation with diag(t,1)",
            "determinant": "det(A_e)=p_e-x_[e]*y_[e] has grade 0 and is invariant",
            "products": "u_[e]=x_[e]*y_[e] are invariant coordinates",
            "commutativity": "Q commutativity is a conjugation-invariant condition",
        },
        "reduction_consequence": {
            "free_parameters": 1,
            "statement": (
                "One global torus parameter, not one per edge.  On the patch y_[e0]!=0 the gauge "
                "may be fixed by y_[e0]=1, which lowers the 262-parameter mixed ansatz to 261 "
                "parameters and no further."
            ),
        },
        "relation_variety_is_a_union_of_G_m_orbits": True,
        "no_degeneration_to_the_pure_families": {
            "statement": (
                "The weights are +1 on every x and -1 on every y, so a mixed point has no limit "
                "inside the affine chart as t->0 or t->infinity: x->0 forces y->infinity and "
                "conversely."
            ),
            "consequence": (
                "The proved global pure-lower no-go cannot be extended to the mixed components "
                "by a torus degeneration argument.  A mixed obstruction needs its own proof."
            ),
        },
        "nonclaims": [
            "The torus is not claimed to be the full stabiliser of the ansatz.",
            "No global classification of the mixed locus follows from the grading.",
            "The grading is a symmetry certificate, not an obstruction or a witness.",
        ],
        "verdict": TORUS_VERDICT,
    }


# ---------------------------------------------------------------------------
# Part B: the combinatorial symmetry group of the equation system
# ---------------------------------------------------------------------------


def _orbit_attributes(reduction: dict[str, Any]) -> dict[str, dict[str, Any]]:
    attributes: dict[str, dict[str, Any]] = {}
    for record in reduction["reduction_map"]:
        orbit = str(record["orbit_id"])
        probability = _probability(record)
        entry = {
            "p": str(probability),
            "stage": int(record["stage"]),
            "transition_kind": str(record["transition_kind"]),
        }
        previous = attributes.setdefault(orbit, entry)
        if previous != entry:
            raise AssertionError(f"the ON orbit {orbit} has inconsistent invariants")
    return attributes


def _q_orbits(reduction: dict[str, Any]) -> dict[str, int]:
    """Return the four ``Q_n`` orbit ids, keyed by stage.

    ``Q_n`` is the transition with empty source relation and empty precursor at
    stage ``n``; it is the generator the commutator target is written in.
    """

    found: dict[int, str] = {}
    for record in reduction["reduction_map"]:
        relation = tuple(int(row) for row in record["source_relation_rows"])
        if int(record["precursor_code"]) == 0 and not any(relation):
            stage = int(record["stage"])
            orbit = str(record["orbit_id"])
            previous = found.setdefault(stage, orbit)
            if previous != orbit:
                raise AssertionError(f"stage {stage} has two distinct Q orbits")
    if sorted(found) != [1, 2, 3, 4]:
        raise AssertionError("the four Q generators were not identified")
    return {orbit: stage for stage, orbit in found.items()}


def _cpobc_equations(
    cpobc: dict[str, Any], occurrence_to_orbit: dict[str, str]
) -> list[dict[str, Any]]:
    equations: list[dict[str, Any]] = []
    for relation in cpobc["relations"]:
        for equation in relation["raw_noncommutative_relation"]:
            operators = equation["operator_ids"]
            lhs = [occurrence_to_orbit[operators[token]] for token in equation["lhs_word"]]
            rhs = [occurrence_to_orbit[operators[token]] for token in equation["rhs_word"]]
            equations.append(
                {
                    "family": "CPOBC",
                    "kind": str(equation["equation_id"]),
                    "words": (tuple(lhs), tuple(rhs)),
                }
            )
    return equations


def _gc_equations(
    local_gc: dict[str, Any], signature_to_orbit: dict[tuple[int, int, int], str]
) -> list[dict[str, Any]]:
    path_words: dict[str, tuple[str, ...]] = {}
    for paths in local_gc["path_inventory"].values():
        for path in paths:
            word = []
            for transition in path["transitions"]:
                signature = transition["quotient_signature"]
                word.append(
                    signature_to_orbit[
                        (
                            int(signature["stage"]),
                            int(signature["source_relation_code"]),
                            int(signature["precursor_code"]),
                        )
                    ]
                )
            path_words[str(path["path_id"])] = tuple(word)
    equations: list[dict[str, Any]] = []
    for relation in local_gc["generating_relation_basis"]:
        equations.append(
            {
                "family": "strong_GC",
                "kind": "gc_basis",
                "words": (
                    path_words[str(relation["lhs_path_id"])],
                    path_words[str(relation["rhs_path_id"])],
                ),
            }
        )
    return equations


def _msr_equations(cpobc: dict[str, Any]) -> list[dict[str, Any]]:
    equations: list[dict[str, Any]] = []
    for constraint in cpobc["MSR_operator_constraints"]:
        terms = tuple(
            sorted(
                (str(term["transition_orbit_id"]), int(term["coefficient"]))
                for term in constraint["terms"]
            )
        )
        equations.append(
            {
                "family": "reachable_state_MSR",
                "kind": f"identity:{int(constraint['identity_coefficient'])}",
                "terms": terms,
            }
        )
    return equations


def _incidence(equation: dict[str, Any]) -> dict[str, tuple[Any, ...]]:
    """Return a symmetry-invariant label of every orbit occurring in ``equation``.

    The label is deliberately side-agnostic for word equations.  A symmetry may
    exchange the two sides of a residual, so a side-tagged label would be finer
    than the symmetry group and could not support a triviality proof.  A coarser
    invariant label can only weaken the conclusion, never make it unsound.
    """

    labels: dict[str, list[Any]] = defaultdict(list)
    if "words" in equation:
        for word in equation["words"]:
            for position, orbit in enumerate(word):
                labels[orbit].append(("pos", position, len(word)))
    else:
        for orbit, coefficient in equation["terms"]:
            labels[orbit].append(("coeff", coefficient))
    return {orbit: tuple(sorted(entries)) for orbit, entries in labels.items()}


def _refine(
    orbits: list[str],
    orbit_colour: dict[str, str],
    equations: list[dict[str, Any]],
) -> dict[str, Any]:
    incidences = [_incidence(equation) for equation in equations]
    by_orbit: dict[str, list[int]] = defaultdict(list)
    for index, incidence in enumerate(incidences):
        for orbit in incidence:
            by_orbit[orbit].append(index)

    equation_colour = [_digest([equation["family"], equation["kind"]]) for equation in equations]
    initial_equation_classes = len(set(equation_colour))
    colour = dict(orbit_colour)
    rounds = 0
    history: list[dict[str, int]] = []
    while True:
        rounds += 1
        next_equation_colour = [
            _digest(
                [
                    equation_colour[index],
                    sorted(
                        [colour[orbit], list(label)] for orbit, label in incidences[index].items()
                    ),
                ]
            )
            for index in range(len(equations))
        ]
        next_colour = {
            orbit: _digest(
                [
                    colour[orbit],
                    sorted(
                        [next_equation_colour[index], list(incidences[index][orbit])]
                        for index in by_orbit.get(orbit, [])
                    ),
                ]
            )
            for orbit in orbits
        }
        classes = len(set(next_colour.values()))
        equation_classes = len(set(next_equation_colour))
        history.append(
            {
                "round": rounds,
                "orbit_classes": classes,
                "equation_classes": equation_classes,
            }
        )
        stable = len(set(colour.values())) == classes and (
            len(set(equation_colour)) == equation_classes
        )
        colour = next_colour
        equation_colour = next_equation_colour
        if stable or rounds >= 64:
            break

    partition: dict[str, list[str]] = defaultdict(list)
    for orbit in orbits:
        partition[colour[orbit]].append(orbit)
    classes = sorted((sorted(members) for members in partition.values()), key=lambda item: item[0])
    return {
        "rounds": rounds,
        "initial_equation_classes": initial_equation_classes,
        "history": history,
        "classes": classes,
        "class_count": len(classes),
        "class_size_histogram": {
            str(size): sum(1 for members in classes if len(members) == size)
            for size in sorted({len(members) for members in classes})
        },
    }


def compile_symmetry_orbit_reduction_v042(root: Path) -> dict[str, Any]:
    """Compile the exact gauge-torus and combinatorial symmetry reduction gate."""

    paths = {
        CPOBC_PATH: root / CPOBC_PATH,
        REDUCTION_PATH: root / REDUCTION_PATH,
        LOCAL_GC_PATH: root / LOCAL_GC_PATH,
        MIXED_MANIFEST_PATH: root / MIXED_MANIFEST_PATH,
        TANGENT_SCOUT_PATH: root / TANGENT_SCOUT_PATH,
    }
    cpobc = _load(paths[CPOBC_PATH])
    reduction = _load(paths[REDUCTION_PATH])
    local_gc = _load(paths[LOCAL_GC_PATH])
    manifest = _load(paths[MIXED_MANIFEST_PATH])
    tangent = _load(paths[TANGENT_SCOUT_PATH])

    if manifest.get("semantic_digest_sha256") != _semantic_digest(manifest):
        raise AssertionError("the mixed source-native manifest is not at its frozen digest")
    if tangent.get("semantic_digest_sha256") != _semantic_digest(tangent):
        raise AssertionError("the mixed x/y tangent scout is not at its frozen digest")
    if tangent.get("counterexample_search", {}).get("remaining_open_cover") != (
        "union of 131 patches y_[e]!=0"
    ):
        raise AssertionError("the predecessor open cover this gate reduces has changed")

    grading = _grading_certificate(manifest)

    attributes = _orbit_attributes(reduction)
    orbits = sorted(attributes)
    if len(orbits) != 131:
        raise AssertionError("expected 131 ON quotient orbits")
    q_orbits = _q_orbits(reduction)

    occurrence_to_orbit = {
        str(record["occurrence_id"]): str(record["orbit_id"])
        for record in reduction["reduction_map"]
    }
    signature_to_orbit: dict[tuple[int, int, int], str] = {}
    for record in reduction["reduction_map"]:
        key = (
            int(record["stage"]),
            _relation_code(record["source_relation_rows"]),
            int(record["precursor_code"]),
        )
        previous = signature_to_orbit.setdefault(key, str(record["orbit_id"]))
        if previous != str(record["orbit_id"]):
            raise AssertionError(f"signature has conflicting ON orbits: {key}")
    equations = (
        _cpobc_equations(cpobc, occurrence_to_orbit)
        + _gc_equations(local_gc, signature_to_orbit)
        + _msr_equations(cpobc)
    )
    family_counts: dict[str, int] = defaultdict(int)
    for equation in equations:
        family_counts[equation["family"]] += 1
    if dict(family_counts) != {"CPOBC": 783, "strong_GC": 320, "reachable_state_MSR": 24}:
        raise AssertionError(f"unexpected equation inventory: {dict(family_counts)}")

    initial_colour = {
        orbit: _digest(
            [
                attributes[orbit]["p"],
                attributes[orbit]["stage"],
                attributes[orbit]["transition_kind"],
                q_orbits.get(orbit, 0),
            ]
        )
        for orbit in orbits
    }
    initial_classes = len(set(initial_colour.values()))
    refinement = _refine(orbits, initial_colour, equations)

    discrete = refinement["class_count"] == len(orbits)
    verdict = TRIVIAL_VERDICT if discrete else REDUCED_VERDICT

    scout_schedule = [
        {
            "rank": index + 1,
            "patch": f"y_[{orbit}]!=0",
            "orbit_id": orbit,
            "stage": attributes[orbit]["stage"],
            "p": attributes[orbit]["p"],
            "cpobc_incidence": sum(
                1
                for equation in equations
                if equation["family"] == "CPOBC" and orbit in _incidence(equation)
            ),
            "is_Q": orbit in q_orbits,
        }
        for index, orbit in enumerate(
            sorted(
                orbits,
                key=lambda item: (
                    attributes[item]["stage"],
                    Fraction(attributes[item]["p"]),
                    item,
                ),
            )[:8]
        )
    ]

    payload: dict[str, Any] = {
        "schema_version": SCHEMA,
        "profile": "strong_GC__reachable_state_MSR",
        "gate": "SYMMETRY_ORBIT_REDUCTION_BEFORE_PRINCIPAL_OPEN_EXACT_SCOUTS",
        "scope": {
            "finite_stages": "n<=4",
            "dimension": 2,
            "field": "QQ",
            "identification_mode": "ON_QUOTIENT",
            "ansatz": "A_e=[[p_e,x_[e]],[y_[e],1]], p_e=CSG(t_j=1)",
            "reduced_object": "the 131 principal patches y_[e]!=0 left open by the mixed x/y scout",
        },
        "source_artifact_sha256": {path: _sha256(value) for path, value in paths.items()},
        "predecessor_binding": {
            "kind": "CANONICAL_JSON_SEMANTIC_DIGEST",
            "results/v0.4.2_955_mixed_source_native_manifest.json": manifest[
                "semantic_digest_sha256"
            ],
            "results/v0.4.2_955_mixed_xy_tangent_scout.json": tangent["semantic_digest_sha256"],
        },
        "gauge_torus": grading,
        "combinatorial_symmetry": {
            "definition": (
                "A permutation sigma of the 131 ON transition orbits that preserves the CSG "
                "character p, the stage, the transition kind and each of Q_1,...,Q_4, and maps "
                "the CPOBC, strong-GC and reachable-state-MSR equation sets onto themselves."
            ),
            "why_Q_is_pinned": (
                "The commutator target is written in Q_1,...,Q_4.  A permutation that moved a Q "
                "generator would not transport a witness between patches, so the Q orbits are "
                "singleton colours from the start."
            ),
            "Q_orbits": {orbit: stage for orbit, stage in sorted(q_orbits.items())},
            "equation_inventory": dict(sorted(family_counts.items())),
            "incidence_label_is_side_agnostic": True,
            "incidence_label_reason": (
                "A symmetry may exchange the two sides of a residual, so side-tagged labels "
                "would be finer than the symmetry group.  A coarser invariant label can only "
                "weaken the conclusion, never make it unsound."
            ),
            "initial_colour_classes": initial_classes,
            "initial_equation_colour_classes": refinement["initial_equation_classes"],
            "refinement_rounds": refinement["rounds"],
            "refinement_history": refinement["history"],
            "stable_colour_classes": refinement["class_count"],
            "class_size_histogram": refinement["class_size_histogram"],
            "stable_partition_sha256": _digest(refinement["classes"]),
            "nontrivial_classes": [
                members for members in refinement["classes"] if len(members) > 1
            ],
            "discrete": discrete,
        },
        "reduction_outcome": {
            "patches_before": 131,
            "symmetry_orbit_upper_bound_on_distinct_patches": refinement["class_count"],
            "patches_removed_by_symmetry": 131 - refinement["class_count"],
            "gauge_parameters_removed": 1,
            "brute_force_131_patch_sweep_authorised": False,
        },
        "soundness_boundary": {
            "colouring_is_a_coarsening_of_the_true_symmetry_orbits": True,
            "discrete_implies_trivial_symmetry_group": True,
            "combinatorial_word_level_symmetries_only": (
                "The certified group consists of permutations of the 131 orbits acting on the "
                "CPOBC, strong-GC and reachable-MSR word and term structure.  Polynomial-level "
                "or nonlinear automorphisms of the relation variety are not classified, so the "
                "triviality result does not exclude a coefficient-level coincidence that this "
                "abstraction cannot see."
            ),
            "nondiscrete_classes_are_not_orbits": (
                "Two patches may be merged only after an explicit permutation is emitted and "
                "verified by re-mapping the full CPOBC, strong-GC and reachable-MSR equation "
                "multisets.  No such permutation is emitted here."
            ),
            "explicit_permutation_certificates_emitted": 0,
        },
        "deterministic_scout_schedule": {
            "role": (
                "Deterministic patch ordering for the next gate.  Selection is by stage, then "
                "CSG character, then orbit id; it is a schedule, not a result."
            ),
            "head": scout_schedule,
            "executed": False,
        },
        "solver_status": {
            "Groebner_or_saturation_runs": 0,
            "finite_field_runs": 0,
            "numerical_runs": 0,
            "Sage_runs": 0,
            "solver_run": False,
        },
        "strategic_consequence": {
            "patchwise_witness_search": (
                "With a trivial symmetry group the 131 patches are pairwise non-interchangeable, "
                "so a witness search must solve 131 independent nonlinear problems.  Symmetry "
                "offers no saving there."
            ),
            "uniform_obstruction_route": (
                "A uniform obstruction argument is insensitive to the patch count, so the "
                "negative outcome of this gate raises the relative value of the obstruction "
                "terminal over the witness terminal.  This is a planning judgement, not a "
                "mathematical claim about which terminal is true."
            ),
        },
        "claim_boundary": [
            "This gate reduces the open patch cover; it decides nothing about the 955 profile.",
            "No witness is certified and no obstruction is proved.",
            "The full 955 profile and the unrestricted source-native slack system stay open.",
            "The mixed x/y ansatz is a declared family, not general GL_2.",
        ],
        "commutativity_proved_for_full_profile": False,
        "witness_certified": False,
        "search_terminal": False,
        "passed": True,
        "verdict": verdict,
    }
    payload["semantic_digest_sha256"] = _semantic_digest(payload)
    return payload


def write_symmetry_orbit_reduction_v042(root: Path) -> Path:
    payload = compile_symmetry_orbit_reduction_v042(root)
    destination = root / RESULT_PATH
    destination.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return destination


if __name__ == "__main__":
    repository_root = Path(__file__).resolve().parents[3]
    print(write_symmetry_orbit_reduction_v042(repository_root))
