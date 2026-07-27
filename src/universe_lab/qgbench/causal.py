"""有限因果集合の構成と、ラベルに依存しない不変量。"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray


def validate_causal_matrix(matrix: NDArray[np.bool_]) -> None:
    """有限半順序の厳密順序行列であることを検査する。

    行列は自然ラベルである必要はない。非反射性、非対称性、推移性を検査する。
    """

    relation = np.asarray(matrix, dtype=bool)
    if relation.ndim != 2 or relation.shape[0] != relation.shape[1]:
        raise ValueError("causal matrix must be square")
    if np.any(np.diag(relation)):
        raise ValueError("strict causal order must be irreflexive")
    if np.any(relation & relation.T):
        raise ValueError("strict causal order must be asymmetric")
    # Boolean matrix product is the relational composition R∘R.
    # uint8 は中間点数が 256 の倍数で桁あふれし得るため使わない。
    integer_relation = relation.astype(np.int32)
    composed = (integer_relation @ integer_relation) > 0
    if np.any(composed & ~relation):
        raise ValueError("causal order must be transitive")


def link_matrix(causal: NDArray[np.bool_]) -> NDArray[np.bool_]:
    """推移簡約（被覆関係）を返す。"""

    relation = np.asarray(causal, dtype=bool)
    validate_causal_matrix(relation)
    integer_relation = relation.astype(np.int32)
    through_intermediate = (integer_relation @ integer_relation) > 0
    return relation & ~through_intermediate


def interval_cardinalities(causal: NDArray[np.bool_]) -> NDArray[np.int64]:
    """各順序対 (i,j) の開区間 |I(i,j)| を返す。"""

    relation = np.asarray(causal, dtype=bool)
    return relation.astype(np.int64) @ relation.astype(np.int64)


def permute_relation(
    matrix: NDArray[np.bool_], permutation: NDArray[np.integer]
) -> NDArray[np.bool_]:
    """同じ抽象因果集合を別ラベルで表す。"""

    order = np.asarray(permutation)
    return np.asarray(matrix)[np.ix_(order, order)]


def unpermute_matrix(
    matrix: NDArray[np.floating], permutation: NDArray[np.integer]
) -> NDArray[np.float64]:
    """`permute_relation` のラベル変更を元へ戻す。"""

    order = np.asarray(permutation)
    inverse = np.argsort(order)
    return np.asarray(matrix, dtype=float)[np.ix_(inverse, inverse)]
