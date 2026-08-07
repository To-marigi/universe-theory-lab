# Paper I v0.4.2: Zenodo manual-upload checklist

This is an owner gate for a new Paper I preprint record.  It is not an
automatic publish script.  Do not edit the frozen v0.3.9 software record or
copy the root `.zenodo.json` / `CITATION.cff` into this package.

The approved owner policies are recorded in
`owner_decision.json` and
`reports/v0.4.2_paper1_owner_decision_amendment_2026-08-07.md`, which preserves
and links the superseded 2026-08-06 record: the accepted final PDF
is 18 pages, 428286 bytes, with SHA-256
`c112b987b4efb76312892481dd033598b939a0a8becfc4ac0e0eca4070dbfa2e`, the
directly previewable PDF-plus-supplement layout is accepted, the Paper I license is CC BY 4.0 (the
repository software remains MIT), and initial related identifiers are `[]`.
Publication date, DOI, and final commit values remain null under their stated
policies.  Draft creation, freeze, submission, deposit, and publication remain
unperformed and unauthorized.  No DOI reservation is requested.

**The literature gate is current.**  The `2026-08-07T1600Z` predraft gate was
cut against the current candidate
`c112b987b4efb76312892481dd033598b939a0a8becfc4ac0e0eca4070dbfa2e` and is the
active authority: `verify_paper1_bundle.py`'s `ZENODO_PREDRAFT_*` bindings
point to it.  Its fixed submittedDate window had accumulated real arXiv
index catch-up since the `2026-08-06T2315Z` gate (722 -> 908 records); every
added, missing, version-replaced, or newly rule-triggered ID within that
still-closed window was individually reviewed by title/abstract and found
nonmaterial to C1--C5.  See
`reports/v0.4.2_paper1_zenodo_predraft_literature_gate_2026-08-07_20260807T1600Z.md`
for the full result.  The superseded `2026-08-06T2315Z` gate (cut against the
withdrawn `9f58867d…fd43` candidate) remains bound only as the historical
predecessor document inside the supplement.

**Owner acceptance of the current PDF bytes is now recorded.**  The all-page
visual QA of the current bytes was performed by the assistant session that made
the last addition, not by the owner directly; the owner separately accepted
these exact bytes (SHA-256
`c112b987b4efb76312892481dd033598b939a0a8becfc4ac0e0eca4070dbfa2e`), per
`reports/v0.4.2_paper1_owner_decision_amendment_2026-08-07.md`, and
`build_paper1_bundle.py`/`verify_paper1_bundle.py` bind that acceptance
sentence as a required fragment.  This still does not by itself authorize
**Save draft** — see the release gate below.  A later deposit attempt still
requires a freshly timestamped literature gate cut immediately beforehand,
per the same reasoning that withdrew the `2026-08-06` candidate: a dated gate
becomes stale while time passes.  Publication, push, DOI, and other owner
release gates remain false; remote visibility is still pending owner
verification.

## 0. Owner decisions before packaging

- [ ] The owner has selected the final source commit and final verified PDF.
- [ ] The owner accepts the **PDF-plus-supplement layout** below (the default).
- [ ] The former single outer archive is retained only as a historical
      candidate and is not the new Zenodo upload layout.
- [ ] Publication date, license, relations, DOI handling, and the final
      publish action have an owner decision.
- [ ] The production worksheet retains `license = CC BY 4.0`; do not replace
      the repository's MIT software license decision.

The metadata worksheet is a UI worksheet, not a Zenodo API payload.  Null
owner fields are intentionally not silently filled by these tools.

## 1. Build and verify the default PDF-plus-supplement set

From the repository root, with the final generated PDF present:

```powershell
uv run python scripts/normalize_v042_paper1_zenodo_predraft_gate_20260807T1600Z.py --check
uv run python zenodo/paper1-v0.4.2/build_paper1_bundle.py `
  --output-dir ..\paper1-v0.4.2-upload `
  --commit <owner-approved-final-commit>
uv run python zenodo/paper1-v0.4.2/verify_paper1_bundle.py `
  --root ..\paper1-v0.4.2-upload
```

- [ ] The builder and verifier both exit successfully.
- [ ] The output directory is outside the repository and was new or empty.
- [ ] The builder summary and supplement `upload_checksums.json` show
      `source_commit_binding.status = PRODUCTION_COMMIT_BOUND`, the full
      40-hex selected commit, the canonical repository URL, and
      `tree_url = null` / `remote_visibility = NOT_VERIFIED_BY_BUILDER` until
      the owner verifies remote visibility.  The binding's checked source
      hashes/sizes exactly cover `manifest.files`, including the automatic
      `results/v0.4.2_paper1_witness_tables.json` witness.
- [ ] The output directory contains **exactly two files**:

      `paper1_statewise_operator_v0.4.2.pdf`
      `paper1_statewise_operator_v0.4.2_supplement.tar.gz`

- [ ] The builder summary and verifier worksheet both state
      `layout = pdf_and_supplement` and list exactly those two Zenodo files.
- [ ] Record the standalone PDF SHA-256/byte count, supplement SHA-256/byte
      count and manifest semantic digest, PDF page count, and selected commit
      in the release notes.
- [ ] Confirm the owner decision artifact/report hashes in the builder summary
      and that all release gates remain false.

The strict verifier checks deterministic gzip/tar metadata, outer and inner
manifest digests, member hashes/sizes, the final PDF source/report binding,
metadata claim fragments, and the absence of forbidden or unexpected paths.

For a local non-production preview only, `--unbound-preview` may replace
`--commit <owner-approved-final-commit>`.  The supplement manifest is then
explicitly marked `status = UNBOUND_PREVIEW` with `commit = null`; strict
verification rejects it.  It has no Git blob binding and must never be
uploaded or used as the release worksheet.

## 2. Exact Zenodo file list (default)

Upload **two** files, exactly as named:

```text
paper1_statewise_operator_v0.4.2.pdf
paper1_statewise_operator_v0.4.2_supplement.tar.gz
```

The supplement's `upload_checksums.json` records the source members, embeds
the selected source commit binding, and binds the standalone PDF by SHA-256.
Do not add a second PDF, a raw reference
PDF/text, a retrieval receipt, a raw Atom response, or a repository snapshot.

## 3. Historical single-archive boundary

`paper1_statewise_operator_v0.4.2_zenodo.tar.gz` is a historical local
candidate only.  Do not select it for the current Zenodo preprint record; its
single-file form prevents direct PDF preview and it predates the current DOI
policy.  It may be inspected offline with `verify_paper1_bundle.py --archive`
for integrity/provenance comparison only.  Strict `--root` verification must
reject it as an ineligible current upload layout even if its integrity passes.
The legacy outer wrapper may report `commit_binding_embedded = false`; this
refers only to the wrapper.  New historical wrappers place the production or
explicit `UNBOUND_PREVIEW` binding in the inner supplement at
`inner_supplement.source_commit_binding`.  An older inner supplement without
that field is accepted only by explicit `--archive` integrity mode, never as
current provenance or a current upload candidate.

## 4. Zenodo draft metadata

- [ ] Create a **new upload** (not “new version” of the v0.3.9 software
      record).
- [ ] Resource type: `Publication / Preprint`.
- [ ] Title: `Statewise versus operator Bell causality in finite quantum
      sequential growth: exact separation and recovery at dimension two`.
- [ ] Creator: `Osaki, Kenichi`; ORCID `0009-0003-9256-7089`; affiliation
      `Independent researcher`.
- [ ] Language: `English`; version: `0.4.2`; access: `Open`.
- [ ] Copy the public abstract and keywords from `ZENODO_FORM_VALUES.md`.
      Add the detailed scope text under **Additional descriptions → Technical
      info** and the AI disclosure under **Additional descriptions →
      Other**; do not put those internal claim-boundary details in the
      main public description.
- [ ] Keep communities, funding, and related identifiers empty unless the
      owner explicitly decides otherwise.
- [ ] Keep the local worksheet publication date null.  Zenodo may prefill a
      required draft-date field; do not treat that saved-draft date as the
      publication date.  Before publication, the owner must confirm and record
      the actual first-public Zenodo date.
- [ ] Use CC BY 4.0 for Paper I.  The repository software license remains MIT.
- [ ] DOI policy is **no draft reservation**: leave DOI blank and do **not**
      click “Get a DOI now!”.  Zenodo assigns/registers the DOI at publication.

## 5. Save draft, preview, and publish gate

- [x] A literature gate for the current candidate has been cut, checked, and
      recorded (`2026-08-07T1600Z`, `verify_paper1_bundle.py`'s
      `ZENODO_PREDRAFT_*` bindings point to it). This step alone does not
      authorize **Save draft**; do not publish yet.
- [x] Owner acceptance of the current PDF bytes
      (`c112b987b4efb76312892481dd033598b939a0a8becfc4ac0e0eca4070dbfa2e`) is
      recorded in
      `reports/v0.4.2_paper1_owner_decision_amendment_2026-08-07.md`. Both
      the builder and verifier fail closed on this fragment.
- [ ] If meaningful time has passed since the `2026-08-07T1600Z` gate was cut,
      a fresh gate is cut immediately beforehand rather than reusing this one;
      a dated gate is evidence for its own moment, not a standing guarantee.
- [ ] Check title, creator, ORCID, affiliation, resource type, version,
      description, keywords, license/date/relations in the preview.
- [ ] Confirm the displayed upload file list is exactly the selected layout
      above and record Zenodo's displayed bytes/checksums.
- [ ] Compare the final PDF preview page count/content with the locally bound
      final PDF.  Stop if Zenodo or local values differ.
- [ ] Give the owner the draft URL, the exact commit recorded in both
      `source_commit_binding` and the external receipt, all recorded SHA-256
      values, layout, and owner-only metadata choices.
- [ ] Before any later draft-save action, manuscript freeze, deposit, or
      publication, run and record a newly timestamped literature gate.  If it
      finds material change, stop and resolve it before any approval.
- [ ] Obtain explicit owner approval to publish this draft.
- [ ] Publish once; do not overwrite the v0.3.9 software record.

## 6. Post-publication readback

- [ ] Record public record URL, version DOI, concept DOI, publication date,
      and publication timestamp.
- [ ] Read back metadata and the exact file name/byte/checksum list from the
      public page or API and compare with the local worksheet.
- [ ] Download the published file(s) and compare local SHA-256 values.  For
      the default layout, place both downloaded files in a clean directory and
      re-run `verify_paper1_bundle.py --root <directory>`.
- [ ] Preserve the DOI and the supplement's source-commit binding plus final
      external receipt in the release notes.  Any later scientific or file change receives a new version;
      never mutate this record in place.
