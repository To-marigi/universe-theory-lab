# Control/methods v0.4.2: Zenodo manual-upload checklist

The local package is designed to leave only account-bound Zenodo actions to the
human depositor. Do not modify the already-published Paper I record.

## 1. Local release candidate

- [ ] The production builder and strict verifier both pass.
- [ ] The output directory contains exactly the PDF and supplement named in
      `ZENODO_FORM_VALUES.md`.
- [ ] `ZENODO_UPLOAD_RECEIPT.md` records the same two hashes and sizes as the
      files selected for upload.
- [ ] The receipt shows the intended full source commit and
      `PRODUCTION_COMMIT_BOUND`.
- [ ] The standalone PDF is tracked and byte-identical to that source commit.
- [ ] The PDF page count and SHA-256 match the final PDF-build report.
- [ ] The all-page visual-QA record is `PASS`.
- [ ] The selected source commit is available wherever the depositor intends
      readers to obtain repository history. If remote visibility is not
      verified, do not invent a Git tree URL in Zenodo metadata.

## 2. Create a new record

- [ ] In Zenodo, choose **New upload**.
- [ ] Do not choose **New version** on Paper I DOI
      `10.5281/zenodo.21861533`.
- [ ] Upload exactly the two files from the verified output directory.

      ```text
      finite_qsg_fail_closed_methods_v0.4.2.pdf
      finite_qsg_fail_closed_methods_v0.4.2_supplement.tar.gz
      ```

- [ ] Wait until neither file is in a pending state.
- [ ] Select `finite_qsg_fail_closed_methods_v0.4.2.pdf` as the default
      preview.
- [ ] Compare the UI file sizes/checksums with the external receipt.

## 3. Enter metadata

- [ ] Copy the fields from `ZENODO_FORM_VALUES.md` without paraphrasing the
      scope boundary.
- [ ] Choose `Publication` -> `Preprint`.
- [ ] Answer that the upload has no existing DOI.
- [ ] Do not click **Get a DOI now!**; this package contains no reserved DOI.
- [ ] Set the publication date to the actual date this preprint will first be
      public. Do not trust the draft-creation default without checking it.
- [ ] Select `Open` / `Public`, `CC BY 4.0`, and `English`.
- [ ] Select the author's matching ORCID record.
- [ ] Add Paper I DOI `10.5281/zenodo.21861533` with relation `References`.
- [ ] Leave AI systems out of creator and contributor fields.

## 4. Preview and publish

- [ ] Save the draft and resolve every validation message.
- [ ] Preview the landing page and open the PDF preview.
- [ ] Confirm title, creator order, ORCID, abstract, technical scope, license,
      publication date, related identifier, filenames, and default preview.
- [ ] Confirm the PDF contains no reserved DOI placeholder.
- [ ] The human depositor performs the final **Publish** action.

## 5. Immediate readback

- [ ] Record the Zenodo record URL, version DOI, concept DOI, publication
      timestamp, and displayed citation.
- [ ] Download both published files and compare SHA-256 and byte counts with
      `ZENODO_UPLOAD_RECEIPT.md`.
- [ ] Confirm the landing-page metadata matches the worksheet.
- [ ] Preserve the readback as a new dated report; do not rewrite the local
      pre-publication receipt.

For significant later file changes, create a new record version. Zenodo's
2026-08-20 documentation describes minor file corrections within 30 days and
requires the resulting edit draft to be published within 45 days of the
original publication; treat those windows as recovery mechanisms, not as a
substitute for this pre-publication verification.
