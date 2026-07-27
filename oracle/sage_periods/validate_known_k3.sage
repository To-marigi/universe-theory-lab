from sage.all import *

import json
import time

from lefschetz_family import EllipticSurface

R = PolynomialRing(QQ, names=("X", "Y", "Z"))
X, Y, Z = R.gens()
S = PolynomialRing(R, "t")
t = S.gen()

alpha = QQ(3)
beta = QQ(5)
n = 3
P = (
    -Z * Y**2 * t**n
    + X**3 * t**n
    - 3 * alpha * X * Z**2 * t**n
    + (t ** (2 * n) + 1 - 2 * beta * t**n) * Z**3
)

started = time.time()
surface = EllipticSurface(P, nbits=128)
periods = surface.period_matrix
intersection = surface.intersection_product

payload = {
    "case": "shioda_k3_sphere_packing_example",
    "alpha": str(alpha),
    "beta": str(beta),
    "n": int(n),
    "nbits": int(128),
    "runtime_seconds": time.time() - started,
    "period_shape": [int(value) for value in periods.dimensions()],
    "period_matrix": [[str(value) for value in row] for row in periods.rows()],
    "intersection_shape": [int(value) for value in intersection.dimensions()],
    "intersection_matrix": [
        [int(value) for value in row] for row in intersection.rows()
    ],
    "fibre_types": [str(value) for value in surface.types],
}
print(json.dumps(payload, sort_keys=True))
