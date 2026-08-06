# Paper I v0.4.2 — Zenodo form values

This worksheet is complete for creating a **draft only**.  It does not
authorize publication, DOI reservation, manuscript freeze, or a Git push.
All release gates in `owner_decision.json` remain `false` until a saved
external draft is recorded locally and later owner-only approvals are given.

Create a **new upload**, not a new version of Zenodo record `21720863` (the
separate v0.3.9 software record).

The fresh `2026-08-06T2315Z` predraft literature gate is complete: its
722-record comparison against the 1123Z predecessor has zero added/missing,
metadata, screening, version, and candidate deltas, and the two tracked
records remain at `v1`.  This exact handoff may be used to **Save draft**;
it does not authorize publication, DOI reservation, a Git push, manuscript
freeze, or deposit.  Those release gates remain `false`, and
`remote_visibility = NOT_VERIFIED_BY_BUILDER` is pending owner verification.
Any later draft-save attempt, freeze, or deposit requires a newly timestamped
literature gate.

## Core fields

| Zenodo field | Final input |
| --- | --- |
| Resource type | `Publication` → `Preprint` |
| Title | Copy the title below exactly. |
| Do you already have a DOI? | `No, I need one` |
| Version | `0.4.2` |
| Access right | `Open` |
| License | `CC BY 4.0` |
| Language | `English` |

### Title

```text
Statewise versus operator Bell causality in finite quantum sequential growth: exact separation and recovery at dimension two
```

### Creator

| Creator field | Final input |
| --- | --- |
| Person type | `Person` |
| Given name | `Kenichi` |
| Family name | `Osaki` |
| Citation display | `Osaki, Kenichi` |
| ORCID | `0009-0003-9256-7089` |
| Affiliation | `Independent researcher` |

Search by the ORCID first and select the matching `Kenichi Osaki` profile.  If
manual entry is required, use the split given/family names above.
`Independent researcher` is the approved non-institutional wording; do not
invent an institutional affiliation.

### Main public description

Paste this in the main **Description** field.  It is the public-facing English
abstract, not the full internal claim ledger.

```text
We present a bounded analysis of the finite, nonsingular, occurrence-ON quantum sequential-growth presentation at dimension d=2 and source stages n<=4. The preprint records five ledger-bound results: a frozen strong/strong commutativity baseline; an exact rational fixed-vector/general-covariance and reachable-state/martingale witness of noncommutativity; a source-native Eq. (120) lemma; commutativity on a proper reconstruction slice; and conditional statewise-to-operator recovery lemmas. Its purpose is to make the distinction between statewise and operator semantics auditable, rather than to classify all finite semantics. In particular, it does not claim the full 955 or 721 profiles, a complete finite occurrence-ON classification, or a reachable-visible witness. The bounded U2 auxiliary-ideal investigation is retained as a reproducibility and resource-boundary record, not as a unit-ideal theorem.
```

### Additional descriptions

In Zenodo's **Additional descriptions** UI, add these two separate entries.
Choose the listed selectable type for each entry; do not merge them into the
main Description field.

#### Additional description 1

| Field | Value |
| --- | --- |
| Type | `Technical info` |

Zenodo has no separate title box for an additional description.  Paste the
heading as the first sentence of the description itself:

```text
Scope and claim boundary. Paper I is a claim-locked archive/submission candidate giving a scoped characteristic-zero interpretation of exact QQ certificates for finite quantum sequential growth at dimension d=2, source stages n<=4, declared nonsingular transitions, and certified occurrence-ON artifacts. C1 is the frozen v0.3.7/v0.3.9 literal strong-GC/strong-MSR comparison baseline, which forces Q1 through Q4 commutativity on its recorded denominator-open 21-chart/S3 certificate and does not use Q5. C2 is an exact rational weak/weak separation: fixed-vector GC plus reachable-state MSR admits a noncommutative witness, but its reachable span has rank one, so the witness is not claimed to be reachable-visible. C3 proves the six raw antichain CPOBC source identities behind Eq. (120) from source nonsingularity alone. C4 proves commutativity only on the proper reconstruction slice P_sGC+rMSR intersect image(Phi_U), not on the full 955 profile or its image complement. C5 gives conditional statewise-to-operator recovery: evaluation injectivity on the declared residual family is necessary and sufficient, with exact same-residual two-probe and non-scalar 2x2 centralizer endpoints; the ordinary single-Omega profile is not claimed to supply those probes. The explicit nonclaims N1--N6 cover the full 955 and 721 profiles, a complete finite ON lattice, reachable-visible weak noncommutativity, a full U2 ideal theorem, occurrence-OFF classification, relation minimality, n>=5, d>=3, singular transitions, and infinite-system conclusions. Scientifically, the global SR2-V status remains SEARCH_OPEN_NO_TERMINAL, U2 remains SOFT_RESOURCE_LIMIT_NONTERMINAL, and u2_is_global_terminal=false. The Paper I editorial disposition is PAPER_I_SCOPED_U2_RESOURCE_OPEN_LIMITATION_ACCEPTED; this is a scoped resource-open limitation, not a QQ theorem or a terminal verdict. The upload excludes third-party reference PDFs/texts and vendored archives; the complete weak electronic ledger remains authoritative, while the compact supplement is an authenticated navigation and selected-witness layer. Full reproduction requires the repository, pinned toolchains, and its exact claim-bound evidence.
```

#### Additional description 2

| Field | Value |
| --- | --- |
| Type | `Other` |

Again, paste the heading inside the description because there is no separate
title field:

```text
Authorship and AI assistance. The human author is responsible for all claims. OpenAI Codex (Luna/Sol) and Anthropic Claude assisted bounded implementation, audit, and drafting; AI systems are not authors and are not proof authorities.
```

### Keywords

Enter these as separate keywords:

```text
causal sets
quantum sequential growth
finite quantum sequential growth
Bell causality
CPOBC
statewise observability
statewise-to-operator recovery
exact rational certificates
noncommutative matrices
operator semantics
exact symbolic computation
computer-assisted proof
reproducibility
```

## Leave these empty

| Zenodo field | Final value |
| --- | --- |
| Communities | Empty (`[]`) |
| Funding | Empty (`[]`) |
| Related/alternate identifiers | Empty (`[]`) |
| Existing DOI | Empty (`null`) |
| Additional titles | Empty |
| Contributors | Empty; AI systems are not contributors/authors |
| Additional dates | Empty |
| References | Empty; the bibliography is in the PDF |
| Repository URL / Software fields | Empty; this record is a Preprint |
| Journal / imprint / thesis / conference | Empty |
| Domain-specific fields | Empty |

Do not add the v0.3.9 concept DOI or a commit URL as a relation unless the
owner records a later, explicit decision.

## Publication date and DOI policy

The local worksheet values remain `null`:

```text
publication_date = null
doi = null
```

For a saved draft, Zenodo may require or prefill a date.  That UI value is not
an approval to publish and is not a locally recorded publication date.  Before
publication, the owner must confirm the actual first-public Zenodo date and
record it in the release record.

**DOI instruction:** Select `No, I need one`, but do not click “Get a DOI
now!”.  No draft reservation; Zenodo assigns/registers DOI at publication.
There is no DOI to paste into the draft form.

Keep `Publisher = Zenodo`, `Visibility = Public`, and embargo disabled.  The
optional copyright box may be left empty; CC BY 4.0 remains the controlling
reuse statement.

## Exact commit value

This repository-tracked worksheet intentionally does not hard-code its own
commit, which would create a circular self-reference.  The production
supplement's `upload_checksums.json` embeds `source_commit_binding` with the
exact full 40-hex SHA, canonical repository URL, checked source hashes/sizes,
and automatic witness.  The builder does not verify that the selected commit
is pushed, so its `tree_url` is explicitly `null` and
`remote_visibility = NOT_VERIFIED_BY_BUILDER` until the owner verifies the
remote state.  Copy the same exact SHA from the generated
`ZENODO_UPLOAD_RECEIPT.md` delivered next to (not inside) the upload
directory and compare the two values.  Under the current empty-related-
identifier policy, the SHA is provenance for local verification and is not
pasted into a Zenodo field.  Do not invent a `/tree/<SHA>` link, use an older
candidate SHA, or put a placeholder into Zenodo.

Immediately before publication, run a fresh date-stamped literature gate.  If
that changes any release file, commit the approved changes, rebuild with the
new full SHA using `--commit`, and replace the upload set and receipt together.

## File selection

The default upload layout is exactly these two files:

```text
paper1_statewise_operator_v0.4.2.pdf
paper1_statewise_operator_v0.4.2_supplement.tar.gz
```

The supplement binds the external PDF by SHA-256 and embeds the selected
source-commit binding; do not upload a second PDF
or the historical `paper1_statewise_operator_v0.4.2_zenodo.tar.gz` archive.
The historical archive predates the current DOI policy and does not provide
direct PDF preview.  Use the two-file set only when its external receipt shows
the same production commit as the embedded `source_commit_binding` and strict
verification passes.  The tracked worksheet's `archive_sha256` remains
`null`; the external receipt carries the generated supplement hash without a
self-reference.  A `--unbound-preview` supplement has
`status = UNBOUND_PREVIEW` and `commit = null`; the verifier rejects it and it
is never an upload candidate.

After uploading both files, explicitly select the standalone PDF as Zenodo's
default preview and compare its displayed size/checksum with the external
receipt before saving the draft.  Confirm that the uploaded supplement's
`source_commit_binding.commit` exactly matches the external receipt SHA.

## Draft-only handoff receipt

If the owner later creates and saves the Zenodo draft, record locally (without
publishing): the draft URL/record identifier, creation timestamp, displayed
file names and SHA-256 values, the UI publication-date value, and confirmation
that “Get a DOI now!” was not used.  Only after that receipt may
`draft_created` be considered for a separate owner-approved update; it is
`false` now.
