# Reproducing the scoped control/methods draft

This is a draft only. It does not authorize candidate sampling, production
trajectories, or solver execution.

From the repository root, use the pinned project environment:

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests/final_theory/test_v042_phase_b_control_methods_scope_closure.py tests/final_theory/test_v042_phase_b_control_exact_scaling_design.py tests/final_theory/test_v042_phase_b_control_implementation_preflight.py tests/final_theory/test_v042_phase_b_control_scaling_review.py tests/final_theory/test_v042_phase_c_method_completion.py
.\.venv\Scripts\ruff.exe check src/universe_lab/final_theory/phase_b_control_methods_scope_closure_v042.py
.\.venv\Scripts\mypy.exe src/universe_lab/final_theory/phase_b_control_methods_scope_closure_v042.py
```

The manuscript is bound to the JSON artifacts listed in
`results/v0.4.2_phase_b_control_methods_scope_closure_20260817.json`.  A PDF
build must be performed in a pinned TeX environment before any owner-approved
release.  The published Paper I Zenodo record is immutable.
