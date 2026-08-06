# Paper I v0.4.2 Zenodo bundle (owner-gated template)

This directory defines the deterministic, owner-gated upload candidate for
Paper I:

*Statewise versus operator Bell causality in finite quantum sequential growth:
exact separation and recovery at dimension two*.

The tools package and verify bytes locally.  They do not authorize a
publication, call Zenodo, or change the repository's scientific files.  The
metadata worksheet still requires owner confirmation of publication date,
final Git commit, relations, and DOI.  The Paper I license decision is already
recorded as CC BY 4.0; the repository software license remains MIT.

The command-line builder requires an explicit source binding choice:
`--commit <REVISION>` is mandatory for a production/archive build; the only
exception is the visibly labelled `--unbound-preview` mode for local
experimentation.  `--commit` and `--unbound-preview` cannot be combined.

## Default: one Zenodo upload file

The default command writes exactly one file to the external output directory:

`paper1_statewise_operator_v0.4.2_zenodo.tar.gz`

This outer archive contains exactly three deterministic members under its
fixed package prefix:

1. `paper1_statewise_operator_v0.4.2.pdf`, the final verified PDF;
2. `paper1_statewise_operator_v0.4.2_supplement.tar.gz`, the existing source /
   reproduction supplement archive;
3. `upload_checksums.json`, the outer self-excluding manifest.

The inner supplement retains its own `upload_checksums.json`, allowlist,
metadata worksheet, witness table, source bindings, and external-PDF binding.
The outer manifest binds the actual PDF and inner archive bytes, checks the
inner semantic digest, and records the exact Zenodo upload list.  The commit
binding is summary-only and is never embedded in either archive, avoiding a
circular hash.

The machine-readable owner decision is
`zenodo/paper1-v0.4.2/owner_decision.json`, with the dated human record at
`reports/v0.4.2_paper1_owner_decision_2026-08-06.md`.  It binds acceptance of
the current 18-page PDF (SHA-256
`9f58867d91673c09229077cd651a35d16d10e90c618cc6ef6083fd4fb644fd43`), the
strict single-archive layout, CC BY 4.0, the actual-publication-date policy,
draft DOI-reservation policy, an initial empty relation list, and the
external-at-deposit commit policy.  Current publication date, DOI, and commit
values remain null.  Draft creation, DOI reservation, freeze, submission,
deposit, and publication remain unperformed and unauthorized.

The final PDF is read-only input.  The builder copies only
`output/pdf/paper1_statewise_operator_v0.4.2.pdf`, whose source/report binding
is `reports/v0.4.2_paper1_pdf_build_2026-08-06.md`; a pending source/PDF
rebind fails closed.  A fresh clone without that generated PDF therefore
fails closed until the owner provides the exact final verified input.

The supplement carries the Paper I TeX source, both bibliography files, the
reproduction protocol, pinned PDF-build helper, claim/evidence ledgers,
compact witness table, and the dated build/literature/U2 reports, including
the 2026-08-06 Zenodo literature report and note.  Raw Atom responses,
normalized ledgers, retrieval receipts, third-party reference PDFs/texts,
vendored archives, and the repository root README remain excluded.  Full
reproduction still requires the repository and pinned toolchains.

## Recorded owner policies and pending release actions

`metadata.template.json` remains a UI worksheet, not a Zenodo API payload.  It
records the approved CC BY 4.0 Paper I license and initial empty relations.
`publication_date`, `doi`, and `final_commit` remain null under their approved
policies (actual Zenodo publication date, DOI reservation in the Zenodo draft,
and external commit binding at the deposit/build cycle).  The owner decision
artifact and dated report are checked into the supplement and fail closed if
their hashes, policies, or release gates drift.  Draft creation, DOI
reservation, manuscript freeze, submission approval, deposit, and publication
are still unperformed and unauthorized.

## Historical two-file layout (owner waiver only)

The old PDF + supplement directory remains available for an owner who has a
specific Zenodo workflow that requires two uploads.  It is never selected by
default and the builder refuses it unless both options are explicit:

```powershell
uv run python zenodo/paper1-v0.4.2/build_paper1_bundle.py `
  --output-dir ..\paper1-v0.4.2-upload `
  --layout two-file `
  --owner-waiver `
  --commit <owner-approved-final-commit>
```

The resulting exact upload list is:

1. `paper1_statewise_operator_v0.4.2.pdf`
2. `paper1_statewise_operator_v0.4.2_supplement.tar.gz`

Verification of this layout also requires an explicit waiver flag.  Without
it, a two-file directory is reported as a policy failure rather than silently
accepted.

## Local commands

From the repository root, with the generated final PDF present:

```powershell
uv run python zenodo/paper1-v0.4.2/build_paper1_bundle.py `
  --output-dir ..\paper1-v0.4.2-upload `
  --commit <owner-approved-final-commit>
uv run python zenodo/paper1-v0.4.2/verify_paper1_bundle.py `
  --root ..\paper1-v0.4.2-upload
```

`--output-dir` must point outside the repository and be new or empty.  The
strict verifier requires exactly one outer archive and checks canonical
tar/gzip metadata, outer/inner manifest semantic digests, member SHA-256 and
sizes, final PDF/report paths, metadata claim fragments, and forbidden or
unexpected paths.  To verify the explicit waiver layout, add
`--allow-two-file-owner-waiver` to the verifier's `--root` command.  An inner
supplement can be checked directly with `--archive <path> --pdf <pdf-path>`.

For a local, non-production preview only, replace `--commit <REVISION>` with
`--unbound-preview`; record that the resulting summary has no commit binding
and never upload that preview.

The focused regression test is:

```powershell
uv run pytest -q tests/test_paper1_zenodo_bundle_v042.py
```

Use `UPLOAD_CHECKLIST.md` for the owner-facing Zenodo UI sequence and the
final worksheet of exact file names, hashes, and publish/readback gates.
