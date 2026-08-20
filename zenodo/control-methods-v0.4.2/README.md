# Control/methods preprint v0.4.2: Zenodo upload package

This directory defines the deterministic upload package for:

*Fail-closed reproducibility for finite quantum sequential growth: exact
controls, independent replay, and resource boundaries*.

The package preparation is authorized, but Zenodo access, draft creation, DOI
reservation, upload, and publication remain human actions. The builder and
verifier do not call Zenodo.

## Upload layout

The production build writes exactly two upload files:

1. `finite_qsg_fail_closed_methods_v0.4.2.pdf`
2. `finite_qsg_fail_closed_methods_v0.4.2_supplement.tar.gz`

The PDF is directly previewable. The deterministic supplement contains the
TeX source, bibliography, reproduction instructions, selected evidence and
tests, licensing information, and `upload_checksums.json`. The PDF is not
duplicated inside the supplement; the manifest binds it by SHA-256.

## Build, commit, then package

From the repository root:

```powershell
.\.venv\Scripts\python.exe scripts/build_v042_control_methods_pdf.py
# Commit the final PDF, its result/report, and every source before continuing.
.\.venv\Scripts\python.exe zenodo/control-methods-v0.4.2/build_bundle.py `
  --output-dir <new-empty-output-directory> `
  --commit <full-final-source-commit>
.\.venv\Scripts\python.exe zenodo/control-methods-v0.4.2/verify_bundle.py `
  --root <output-directory>
```

The standalone PDF and every supplement source must be byte-identical to the
selected commit. An untracked or stale PDF is rejected even when its local
result JSON is internally consistent.

The output directory must be new or empty. A successful production build also
writes `ZENODO_UPLOAD_RECEIPT.md` beside, not inside, the upload directory.
The receipt records both file hashes, sizes, PDF page count, supplement
semantic digest, and the exact source commit without creating a circular
archive hash.

Use `ZENODO_FORM_VALUES.md` for copy/paste-ready metadata and
`UPLOAD_CHECKLIST.md` for the human deposit sequence. The actual publication
date and Zenodo-assigned DOI are intentionally absent until the human
depositor publishes the record.

## Scientific boundary

This package reports bounded controls and methodology. It does not assert
candidate-model validity, a continuum limit, production observables, full
955/721 resolution, solver impossibility, or a final theory. Paper I at
`10.5281/zenodo.21861533` is a separate published record and is not modified.
