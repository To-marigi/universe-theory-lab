# Reproducing the scoped control/methods preprint

This protocol reproduces the methods record. It does not authorize candidate
sampling, production trajectories, approximate fallback, or solver execution.

From the repository root, use the pinned project environment:

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests/final_theory/test_v042_phase_b_control_methods_scope_closure.py tests/final_theory/test_v042_phase_b_control_exact_scaling_design.py tests/final_theory/test_v042_phase_b_control_implementation_preflight.py tests/final_theory/test_v042_phase_b_control_scaling_review.py tests/final_theory/test_v042_phase_b_hard_supervisor.py tests/final_theory/test_v042_phase_c_method_completion.py tests/test_control_methods_zenodo_bundle_v042.py
.\.venv\Scripts\ruff.exe check scripts/build_v042_control_methods_pdf.py zenodo/control-methods-v0.4.2/build_bundle.py zenodo/control-methods-v0.4.2/verify_bundle.py src/universe_lab/final_theory/phase_b_control_methods_scope_closure_v042.py tests/test_control_methods_zenodo_bundle_v042.py
.\.venv\Scripts\mypy.exe scripts/build_v042_control_methods_pdf.py zenodo/control-methods-v0.4.2/build_bundle.py zenodo/control-methods-v0.4.2/verify_bundle.py src/universe_lab/final_theory/phase_b_control_methods_scope_closure_v042.py
```

Build the PDF only in the digest-pinned, network-disabled container:

```powershell
.\.venv\Scripts\python.exe scripts/build_v042_control_methods_pdf.py
```

After committing the final source and PDF-build record, build and verify the
two-file Zenodo upload set:

```powershell
.\.venv\Scripts\python.exe zenodo/control-methods-v0.4.2/build_bundle.py --output-dir <new-empty-directory-outside-repository> --commit <full-final-commit>
.\.venv\Scripts\python.exe zenodo/control-methods-v0.4.2/verify_bundle.py --root <output-directory>
```

The manuscript is bound to the JSON artifacts listed in the supplement
manifest. The published Paper I Zenodo record is immutable. Zenodo upload and
publication are human actions and are not performed by these commands.
