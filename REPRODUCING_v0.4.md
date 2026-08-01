# Reproducing the v0.4 weak-semantics result

The frozen artifact is
`results/v0.4_weak_d2_classification.json`. It contains every direct
residual record, all 165 reduction/alias-catalog assignments and determinants, the
Eq. (113)/(139) branch audits, and the exact triangular rank scouts.

Those 165 records are not 165 independent naturally labelled transition
variables.  They lie over the 131 occurrence-identified quotient orbits.  The
certified witness is therefore an `ON_QUOTIENT` result.  Its extension to the
natural 406-occurrence `OFF_NATURALLY_LABELLED` system remains conditional
until the labelled relation compiler and direct verification exist; see
`reports/v0.4_scope_addendum_v0.4.1.md`.

From the repository root with the Python 3.12 environment installed:

```powershell
uv sync --frozen
uv run python scripts/reproduce_v04.py
uv run pytest tests/final_theory/test_weak_d2_v04.py tests/final_theory/test_weak_d2_v04_oracle.py -q
```

The reproducer must print:

```text
"regenerated_exactly": true
"verdict": "WEAK_D2_NONCOMMUTATIVE_WITNESS_CERTIFIED"
"passed": true
```

To intentionally rebuild the frozen JSON after changing the compiler:

```powershell
uv run python scripts/reproduce_v04.py --write
```

All certificate arithmetic uses `fractions.Fraction`. The one-sided profile
scouts use the module's sparse Gaussian elimination over exact rational
numbers. No numerical solver, finite field, Gröbner basis, or saturation is
part of the witness certificate. The second test module independently
reconstructs the witness with SymPy `Rational`/`Matrix` arithmetic and does
not import the v0.4 compiler.

The v0.3.8/v0.3.9 release-manifest and line-ending-bridge tests are
historical raw-byte checks. They are expected to reject this later v0.4
worktree because its reference catalog and result allowlist intentionally
differ. Reproduce that public release from its pinned v0.3.9 commit; use the
commands above for the v0.4 scientific result.
