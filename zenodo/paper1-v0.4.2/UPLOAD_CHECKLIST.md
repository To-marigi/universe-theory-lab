# Paper I v0.4.2: Zenodo manual-upload checklist

This is an owner gate for a new Paper I preprint record.  It is not an
automatic publish script.  Do not edit the frozen v0.3.9 software record or
copy the root `.zenodo.json` / `CITATION.cff` into this package.

## 0. Owner decisions before packaging

- [ ] The owner has selected the final source commit and final verified PDF.
- [ ] The owner accepts the **single-archive layout** below (the default).
- [ ] If two uploads are genuinely required, the owner has recorded a
      **two-file owner waiver** and will use both explicit waiver flags.
- [ ] Publication date, license, relations, DOI handling, and the final
      publish action have an owner decision.

The metadata worksheet is a UI worksheet, not a Zenodo API payload.  Null
owner fields are intentionally not silently filled by these tools.

## 1. Build and verify the default single archive

From the repository root, with the final generated PDF present:

```powershell
uv run python scripts/normalize_v042_paper1_zenodo_gate_20260806.py --check
uv run python zenodo/paper1-v0.4.2/build_paper1_bundle.py `
  --output-dir ..\paper1-v0.4.2-upload `
  --commit <owner-approved-final-commit>
uv run python zenodo/paper1-v0.4.2/verify_paper1_bundle.py `
  --root ..\paper1-v0.4.2-upload
```

- [ ] The builder and verifier both exit successfully.
- [ ] The output directory is outside the repository and was new or empty.
- [ ] The builder summary shows `commit_binding` for the selected revision and
      includes `results/v0.4.2_paper1_witness_tables.json` in
      `checked_sources` / `automatic_sources`.
- [ ] The output directory contains **exactly one file**:

      `paper1_statewise_operator_v0.4.2_zenodo.tar.gz`

- [ ] The builder summary and verifier worksheet both state
      `layout = single_archive` and
      `zenodo_upload_files = [paper1_statewise_operator_v0.4.2_zenodo.tar.gz]`.
- [ ] Record the outer archive SHA-256 and byte count, outer manifest semantic
      digest, inner supplement SHA-256 and semantic digest, final PDF SHA-256,
      PDF byte count, page count, and selected commit in the release notes.

The strict verifier checks deterministic gzip/tar metadata, outer and inner
manifest digests, member hashes/sizes, the final PDF source/report binding,
metadata claim fragments, and the absence of forbidden or unexpected paths.

For a local non-production preview only, `--unbound-preview` may replace
`--commit <owner-approved-final-commit>`.  This mode is explicit, has no Git
blob binding, and must never be uploaded or used as the release worksheet.

## 2. Exact Zenodo file list (default)

Upload **one** file, exactly as named:

```text
paper1_statewise_operator_v0.4.2_zenodo.tar.gz
```

The outer archive's `upload_checksums.json` records the two payload members
and the exact one-file Zenodo list.  Do not add a second PDF, a raw reference
PDF/text, a retrieval receipt, a raw Atom response, or a repository snapshot.

## 3. Explicit two-file owner-waiver path

Use this only when the owner has documented why Zenodo must receive two
separate files.  The builder must be invoked with both options:

```powershell
uv run python zenodo/paper1-v0.4.2/build_paper1_bundle.py `
  --output-dir ..\paper1-v0.4.2-upload-two-file `
  --layout two-file `
  --owner-waiver `
  --commit <owner-approved-final-commit>
uv run python zenodo/paper1-v0.4.2/verify_paper1_bundle.py `
  --root ..\paper1-v0.4.2-upload-two-file `
  --allow-two-file-owner-waiver
```

The exact two-file upload list in this waiver mode is:

```text
paper1_statewise_operator_v0.4.2.pdf
paper1_statewise_operator_v0.4.2_supplement.tar.gz
```

- [ ] The summary says `layout = two_file_owner_waiver` and
      `owner_waiver = true`.
- [ ] The verifier command includes
      `--allow-two-file-owner-waiver`.
- [ ] No additional files are present.

Without the waiver, two-file output is a policy failure even if its hashes are
valid.

## 4. Zenodo draft metadata

- [ ] Create a **new upload** (not “new version” of the v0.3.9 software
      record).
- [ ] Resource type: `Publication / Preprint`.
- [ ] Title: `Statewise versus operator Bell causality in finite quantum
      sequential growth: exact separation and recovery at dimension two`.
- [ ] Creator: `Osaki, Kenichi`; ORCID `0009-0003-9256-7089`; affiliation
      `Independent researcher`.
- [ ] Language: `English`; version: `0.4.2`; access: `Open`.
- [ ] Copy the description and keywords from `metadata.template.json` after
      owner review.  Preserve the finite/nonsingular, occurrence-ON, d=2,
      n<=4, QQ, C1--C5, N1--N6, U2 boundary, and AI non-author wording.
- [ ] Keep communities, funding, and related identifiers empty unless the
      owner explicitly decides otherwise.
- [ ] Select publication date and license deliberately; these are not inferred
      by the builder.

## 5. Save draft, preview, and publish gate

- [ ] Save the Zenodo draft; do not publish yet.
- [ ] Check title, creator, ORCID, affiliation, resource type, version,
      description, keywords, license/date/relations in the preview.
- [ ] Confirm the displayed upload file list is exactly the selected layout
      above and record Zenodo's displayed bytes/checksums.
- [ ] Compare the final PDF preview page count/content with the locally bound
      final PDF.  Stop if Zenodo or local values differ.
- [ ] Give the owner the draft URL, exact commit, all recorded SHA-256 values,
      layout, and owner-only metadata choices.
- [ ] Obtain explicit owner approval to publish this draft.
- [ ] Publish once; do not overwrite the v0.3.9 software record.

## 6. Post-publication readback

- [ ] Record public record URL, version DOI, concept DOI, publication date,
      and publication timestamp.
- [ ] Read back metadata and the exact file name/byte/checksum list from the
      public page or API and compare with the local worksheet.
- [ ] Download the published file(s) and compare local SHA-256 values.  For
      the default layout, re-run `verify_paper1_bundle.py --archive` on the
      downloaded outer archive.
- [ ] Preserve the DOI and final external commit association in the release
      notes.  Any later scientific or file change receives a new version;
      never mutate this record in place.
