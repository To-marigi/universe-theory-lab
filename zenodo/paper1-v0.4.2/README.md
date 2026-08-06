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

## Default: directly previewable PDF plus supplement

The default command writes exactly two files to the external output directory:

1. `paper1_statewise_operator_v0.4.2.pdf`, the final verified Preprint PDF;
2. `paper1_statewise_operator_v0.4.2_supplement.tar.gz`, the deterministic
   source/reproduction supplement.

This is the recommended Zenodo layout: the PDF is directly previewable from a
Publication/Preprint record, while the supplement remains a compact,
reproducible companion.  The supplement retains its own
`upload_checksums.json`, allowlist, metadata worksheet, witness table, source
bindings, and an external-PDF SHA-256 binding.  The PDF is not duplicated
inside the supplement.  A production build embeds a `source_commit_binding`
in `upload_checksums.json`: the full 40-hex commit, canonical repository URL,
the checked source hashes/sizes, and the automatic witness source.  The
builder does not assert that the commit is remotely visible, so
`tree_url = null` and `remote_visibility = NOT_VERIFIED_BY_BUILDER` until the
owner verifies the pushed commit.  The manifest is excluded from its own
source list, so this binding does not create a circular hash.

The machine-readable owner decision is
`zenodo/paper1-v0.4.2/owner_decision.json`, with the dated human record at
`reports/v0.4.2_paper1_owner_decision_amendment_2026-08-07.md`; that amendment
preserves and links the superseded 2026-08-06 record.  It binds acceptance of
the current 18-page PDF (SHA-256
`9f58867d91673c09229077cd651a35d16d10e90c618cc6ef6083fd4fb644fd43`), the
PDF-plus-supplement layout, CC BY 4.0, the actual-publication-date policy,
no-draft-reservation DOI policy, an initial empty relation list, and the
external-at-deposit commit policy.  Current publication date, DOI, and commit
values remain null in the metadata worksheet; the selected production commit
is nevertheless recorded inside the supplement manifest and external receipt.
Draft creation, freeze, submission, deposit, and
publication remain unperformed and unauthorized; no DOI reservation is
requested.

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
policies (actual Zenodo publication date, **no draft DOI reservation** with
Zenodo assigning/registering the DOI at publication, and external commit
binding at the deposit/build cycle).  The owner decision
artifact and dated report are checked into the supplement and fail closed if
their hashes, policies, or release gates drift.  Draft creation, manuscript
freeze, submission approval, deposit, and publication are still unperformed
and unauthorized; no DOI reservation is requested.

## Historical single-archive candidate

The older outer archive (`paper1_statewise_operator_v0.4.2_zenodo.tar.gz`) is
retained only as a historical candidate.  It is not the recommended Zenodo
outcome because it prevents direct PDF preview and predates the current DOI
policy.  New Paper I preparation must use the default PDF-plus-supplement
layout; the historical archive can be inspected offline with
`verify_paper1_bundle.py --archive <path>`.  That explicit command checks its
internal tar/member/PDF integrity only.  If an older inner supplement has no
`source_commit_binding`, the verifier labels the result
`historical_integrity_only`; it does not certify current metadata or source
provenance.  The historical outer wrapper's `commit_binding_embedded = false`
means the wrapper itself is unbound; a newly built wrapper records the actual
binding location as `inner_supplement.source_commit_binding`.  Strict directory
verification with `--root` rejects the historical layout even when the
archive itself is intact.

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
strict verifier requires exactly the PDF and supplement, checks their hashes,
the supplement tar/gzip metadata and semantic digest, final PDF/report paths,
metadata claim fragments, and forbidden or unexpected paths.  An inner
supplement can be checked directly with `--archive <path> --pdf <pdf-path>`.

For a local, non-production preview only, replace `--commit <REVISION>` with
`--unbound-preview`.  Its supplement manifest is explicitly marked
`status = UNBOUND_PREVIEW` with `commit = null`; the verifier rejects it and it
must never be uploaded or used as the release worksheet.  A production
manifest must show `source_commit_binding.status = PRODUCTION_COMMIT_BOUND`
and the full selected commit.

The focused regression test is:

```powershell
uv run pytest -q tests/test_paper1_zenodo_bundle_v042.py
```

Use `ZENODO_FORM_VALUES.md` for copy/paste-ready UI values, and
`UPLOAD_CHECKLIST.md` for the owner-facing Zenodo sequence, exact file names,
hashes, and publish/readback gates.
