"""Independent red-team utilities for QG-Bench.

This package deliberately does not import :mod:`universe_lab.qgbench`.
"""

from universe_lab.qgaudit.oracle import (
    OracleSprinkling,
    continuum_kernel,
    discrete_kernel,
    sprinkle,
)

__all__ = ["OracleSprinkling", "continuum_kernel", "discrete_kernel", "sprinkle"]
