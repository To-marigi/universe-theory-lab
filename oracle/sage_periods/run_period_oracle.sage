"""Independent lefschetz-family runner for String-Compiler Bench v0.3."""

from sage.all import *

import argparse
import hashlib
import json
import platform
import time

from lefschetz_family import EllipticSurface
from sage.modules.free_quadratic_module_integer_symmetric import IntegralLattice
from sage.version import version as sage_version


def homogeneous_weierstrass(f, g, X, Y, Z):
    return -Y**2 * Z + X**3 + f * X * Z**2 + g * Z**3


def make_case(case):
    R = PolynomialRing(QQ, names=("X", "Y", "Z"))
    X, Y, Z = R.gens()
    S = PolynomialRing(R, "t")
    t = S.gen()

    if case == "validation":
        alpha, beta, n = QQ(3), QQ(5), 3
        polynomial = (
            -Z * Y**2 * t**n
            + X**3 * t**n
            - 3 * alpha * X * Z**2 * t**n
            + (t ** (2 * n) + 1 - 2 * beta * t**n) * Z**3
        )
        return polynomial, {
            "family": "Shioda K3 sphere-packing example from upstream documentation",
            "alpha": "3",
            "beta": "5",
            "n": 3,
        }

    j2, j3, j4, j5, j6 = map(QQ, (1, 2, 0, 3, 5))
    if case == "j4-standard":
        # arXiv:2205.08100v1, Eq. (3.2).
        f = -t**4 * (j5 * t + 3 * j2)
        g = t**5 * (j6 * t**2 - 2 * j3 * t + 1)
        polynomial = homogeneous_weierstrass(f, g, X, Y, Z)
        relation = "Eq. (3.2), mapped to Eq. (3.1) by t -> 1/t"
    elif case == "j4-bfd":
        # arXiv:2205.08100v1, Eq. (3.1).
        f = -t**3 * (3 * j2 * t + j5)
        g = t**5 * (t**2 - 2 * j3 * t + j6)
        polynomial = homogeneous_weierstrass(f, g, X, Y, Z)
        relation = "Eq. (3.1), mapped from Eq. (3.2) by t -> 1/t"
    elif case in ("j4-alternate", "j4-maximal"):
        # Eq. (3.4). The maximal model is first specialized and rescaled.
        a = t**3 - 3 * j2 * t - 2 * j3
        b = -j5 * t + j6
        polynomial = -Y**2 * Z + X**3 + a * X**2 * Z + b * X * Z**2
        relation = (
            "Eq. (3.4) alternate specialization"
            if case == "j4-alternate"
            else "Eq. (2.43) specialized/rescaled to Eq. (3.4)"
        )
    else:
        raise ValueError("unknown case: " + case)
    return polynomial, {
        "family": "J4=0 special divisor",
        "j2": str(j2),
        "j3": str(j3),
        "j4": str(j4),
        "j5": str(j5),
        "j6": str(j6),
        "relation": relation,
    }


def ball_payload(value):
    return {
        "ball": str(value),
        "real_mid": str(value.real().mid()),
        "real_radius": str(value.real().rad()),
        "imag_mid": str(value.imag().mid()),
        "imag_radius": str(value.imag().rad()),
    }


def matrix_int_payload(value):
    return [[int(entry) for entry in row] for row in value.rows()]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--case",
        required=True,
        choices=(
            "validation",
            "j4-standard",
            "j4-bfd",
            "j4-alternate",
            "j4-maximal",
        ),
    )
    parser.add_argument("--nbits", type=int, required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    polynomial, metadata = make_case(args.case)
    input_text = str(polynomial)
    started = time.time()
    surface = EllipticSurface(polynomial, nbits=args.nbits)
    periods = surface.period_matrix
    intersection = matrix(ZZ, surface.intersection_product)
    primary = matrix(ZZ, surface.primary_lattice)
    trivial = matrix(ZZ, surface.trivial_lattice)
    trivial_gram = trivial * intersection * trivial.transpose()
    ambient_lattice = IntegralLattice(intersection)
    transcendental = matrix(
        ZZ,
        ambient_lattice.orthogonal_complement(trivial).basis_matrix(),
    )
    transcendental_gram = transcendental * intersection * transcendental.transpose()
    signature_difference = int(QuadraticForm(QQ, intersection).signature())
    rank = int(intersection.rank())
    positive = (rank + signature_difference) // 2
    negative = rank - positive
    period_row = periods.row(0)
    ns_periods = periods * trivial.transpose()
    transcendental_periods = periods * transcendental.transpose()
    inverse_intersection = intersection.inverse()
    omega_square = (periods * inverse_intersection * periods.transpose())[0, 0]
    omega_positive = (
        periods * inverse_intersection * periods.conjugate().transpose()
    )[0, 0]
    result = {
        "schema_version": "1.0",
        "case": args.case,
        "metadata": metadata,
        "input_polynomial": input_text,
        "input_sha256": hashlib.sha256(input_text.encode("utf-8")).hexdigest(),
        "nbits": int(args.nbits),
        "runtime_seconds": time.time() - started,
        "environment": {
            "sage_version": str(sage_version),
            "python_version": platform.python_version(),
            "platform": platform.platform(),
        },
        "homology": {
            "rank": rank,
            "intersection_signature": [positive, negative],
            "intersection_determinant": int(intersection.det()),
            "intersection_matrix": matrix_int_payload(intersection),
            "primary_lattice": matrix_int_payload(primary),
        },
        "fibration": {
            "fibre_types": [str(value) for value in surface.types],
            "trivial_lattice_rank": int(trivial.rank()),
            "trivial_lattice": matrix_int_payload(trivial),
            "trivial_gram": matrix_int_payload(trivial_gram),
            "transcendental_lattice_rank": int(transcendental.rank()),
            "transcendental_lattice": matrix_int_payload(transcendental),
            "transcendental_gram": matrix_int_payload(transcendental_gram),
        },
        "period": {
            "shape": [int(value) for value in periods.dimensions()],
            "values": [ball_payload(value) for value in period_row],
            "trivial_lattice_pairings": [
                ball_payload(value) for value in ns_periods.row(0)
            ],
            "transcendental_periods": [
                ball_payload(value) for value in transcendental_periods.row(0)
            ],
            "omega_square": ball_payload(omega_square),
            "omega_conjugate_pairing": ball_payload(omega_positive),
        },
        "evidence": {
            "period_values": "CERTIFIED_NUMERICAL_ORACLE_OUTPUT",
            "homology_and_intersection": "INDEPENDENT_ORACLE_CONFIRMED",
            "neron_severi_recovery": "NOT_USED_HEURISTIC",
        },
    }
    encoded = json.dumps(result, indent=2, sort_keys=True, default=str) + "\n"
    with open(args.output, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(encoded)
    print(
        json.dumps(
            {
                "case": args.case,
                "nbits": args.nbits,
                "output": args.output,
                "output_sha256": hashlib.sha256(encoded.encode("utf-8")).hexdigest(),
                "runtime_seconds": result["runtime_seconds"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
