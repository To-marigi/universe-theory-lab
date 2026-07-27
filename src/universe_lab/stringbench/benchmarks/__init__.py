"""Executable String-Compiler benchmark suites."""

from universe_lab.stringbench.benchmarks.f_heterotic_8d import run_f_heterotic_8d
from universe_lab.stringbench.benchmarks.narain_period_v0_2 import (
    run_narain_period_v0_2,
)
from universe_lab.stringbench.benchmarks.stringbench_v0_3 import (
    run_j30_v0_3,
    run_stringbench_v0_3,
)

__all__ = [
    "run_f_heterotic_8d",
    "run_j30_v0_3",
    "run_narain_period_v0_2",
    "run_stringbench_v0_3",
]
