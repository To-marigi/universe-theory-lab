# Reproducing Paper I (v0.4.2 claim boundary)

This directory records the reproducibility contract for the scoped Paper I
working title, *Statewise versus operator Bell causality in finite quantum
sequential growth: exact separation and recovery at dimension two*.

As of 2026-08-06, the manuscript package is a
`PAPER_I_SCOPED_ARCHIVE_SUBMISSION_CANDIDATE_NOT_FROZEN`.  It is a
claim-locked archive/submission candidate for Paper I v0.4.2.  Its scientific
U2 layer remains `SEARCH_OPEN_NO_TERMINAL` with
`SOFT_RESOURCE_LIMIT_NONTERMINAL` and `u2_is_global_terminal=false`; its Paper
I editorial layer is
`PAPER_I_SCOPED_U2_RESOURCE_OPEN_LIMITATION_ACCEPTED`.  The current PDF/source
binding is complete, but owner review and approval still govern every external
action.  The source of truth
for what may be claimed is:

- `results/v0.4.2_paper1_claim_boundary.json` (machine-readable ledger), and
- `reports/v0.4.2_paper1_claim_boundary_2026-08-05.md` (human-readable
  evidence ledger), and
- `reports/v0.4.2_paper1_editorial_disposition_2026-08-06.md` (dated
  two-layer gate addendum).

The scope is characteristic-zero interpretation of QQ certificates, `d=2`,
finite source stages `n<=4`, declared nonsingular transitions, and occurrence
identification ON where the relevant artifact certifies it.  In particular,
the full 955 profile, the 721 profile, a complete finite ON lattice,
reachable-visible noncommutativity, and a full U2 auxiliary-ideal theorem are
not claims of this paper.

## Two version lanes

The two lanes below are deliberately separate.  A green historical release
test in a current v0.4 checkout is **not** evidence for a current Paper I
claim.

| lane | purpose | admissible evidence |
| --- | --- | --- |
| Current v0.4 | Paper I C1--C5 ledger, focused tests, current U2 limitation record | current artifacts and the focused commands in this document |
| Public frozen v0.3.9 | historical strong/strong baseline release | the frozen commit `cba86eae795e1e985c4ba1bcd3dabe4eb2773fab`, its release manifest, and `REPRODUCING_v0.3.9.md`, executed in a checkout of that commit |

Do not run `test_reproduce_v037.py`, `test_reproduce_v039.py`, or
`scripts/reproduce_v039.py` in the current tree and report their result as a
v0.4/Paper I green check.  They are historical-release checks only.

## 1. Current v0.4 lane

Work from the repository root.  Use a clean checkout for a reproducibility
run; the ledger validator is read-only, but some unrelated experimental
commands in this repository may write artifacts.

```powershell
git status --short
uv sync --frozen --group dev
```

An empty `git status --short` is the expected starting condition.  The
repository includes its Python dependencies in the lockfile; this step does
not require the historical v0.3.9 checkout.

### 1.1 Validate the claim ledger

```powershell
uv run python scripts/validate_v042_paper1_claim_boundary.py
```

Expected output:

```text
paper1_claim_boundary=OK
```

The validator checks the five active claims (C1--C5), their pinned evidence,
the mandatory nonclaims, the fail-closed U2 boundary, and the owner-only
publication gate.  It does not establish any theorem beyond the ledger's
stated scope.

### 1.2 Validate the manuscript package

```powershell
uv run python scripts/validate_v042_paper1_manuscript.py
```

Expected output:

```text
paper1_manuscript=OK
```

This validator authenticates the manuscript files, bibliography closure,
claim-ledger binding, bounded-scout M -> E -> manuscript-manifest binding,
nonclaims, and owner-only publication gates.  It does not build a PDF or
widen the scientific claim boundary.

### 1.3 Check the compact electronic supplement

```powershell
uv run python scripts/extract_v042_paper1_witness_tables.py --check
```

Expected output:

```text
paper1_witness_tables=OK
```

The tracked result `results/v0.4.2_paper1_witness_tables.json` is a compact,
proof-facing electronic supplement.  The check authenticates the complete
weak ledger, the independent observability artifact, and the independent
exact-arithmetic oracle before regenerating the supplement in memory.  It
then requires both the self-excluding semantic digest and the exact canonical
bytes to match.  The compact result retains 3,283 sorted natural IDs and their
family digests, plus the 165 occurrence to 131 orbit map; it does not copy the
complete residual payload into the manuscript.

The 1.6 MiB `results/v0.4_weak_d2_classification.json` remains the complete
electronic-ledger authority.  The compact supplement is an authenticated
index and selected exact witness table, not a replacement authority and not a
new theorem.  Do not paste all 3,283 records into the PDF.  Any future
supplement refresh must use the explicit `--write` maintenance mode, review
the resulting raw and semantic hashes, and update the manuscript manifest in
the same change.  Ordinary reproduction uses `--check` only.

### 1.4 Check the archived literature-delta snapshot offline

```powershell
uv run python scripts/normalize_v042_paper1_arxiv_delta_response.py --check
uv run pytest -q -p no:cacheprovider `
  tests/final_theory/test_normalize_v042_paper1_arxiv_delta_response.py
```

These commands use no network.  They regenerate the normalized screening
ledger from the archived 1,091,434-byte Atom response and require exact
agreement with the tracked 497,237-byte JSON ledger.  The authoritative query
semantics come only from the archived Atom feed title and self-link.  Both
encode `submittedDate`, the compact window `202607311500` through
`202608052359`, the eight declared categories, `start=0`,
`max_results=2000`, and an empty `id_list`.  The snapshot contains 556
entries: all 556 have `published` timestamps inside that submitted-date
window and at or before the feed timestamp, none is outside either boundary,
533 match no report-defined target rule, 23 were inspected at title/abstract
level and found nonmaterial, and zero are material to C1--C5.  The raw
response and normalized ledger SHA-256 values are
`8f1b253e2eebaa4788f19616c15ef4cc250da80bfc0d640eea4bd01b7eee08a3`
and
`39e12901c8db41a63070cb4ea1794a1da415aeea8c8df0160df79d7224a42c29`.

This submitted-date snapshot does not generally cover later versions whose
original submission predates the window.  The separately tracked exact-ID
version checks cover only Xu `arXiv:2607.26672` and Srivastava--Surya
`arXiv:2603.25503`.  The earlier unarchived 524-count observation has unknown
query provenance and unknown ID membership; comparison with the archived 556
set is unauthorized.  It remains non-authoritative provenance, and no
524-member set or count difference is inferred.  In the reference archive,
the query has `LOCAL_ARTIFACTS` status because its raw and normalized datasets
are retained.  The two separately excluded hits remain `METADATA_ONLY`.

Immediately before submission, the minimum deterministic contract is a
full-overlap `submittedDate` snapshot beginning at
`2026-07-31T15:00:00Z`, plus repeat exact-ID version checks for Xu and
Srivastava--Surya.  Whether to add general pre-window version-update coverage
remains an explicit editorial decision.  Archive the new response,
regenerate the ledger, and reread every triggered candidate.

### 1.4a Check the dated Zenodo-preparation literature gate offline

```powershell
uv run python scripts/normalize_v042_paper1_zenodo_gate_20260806.py --check
uv run pytest -q -p no:cacheprovider `
  tests/final_theory/test_normalize_v042_paper1_zenodo_gate_20260806.py
```

The 2026-08-06 gate is the current dated implementation of that minimum
contract.  It archives a 1,091,452-byte full-overlap Atom response, a
5,201-byte exact-ID response, a 1,957-byte retrieval receipt, and a
504,422-byte normalized ledger.  The full-overlap, exact-ID, receipt, and
normalized-ledger SHA-256 values are respectively
`c2b42041557a012f2847b069c3f217863a0b435249422cc8c2f35a4cd7fdf9e4`,
`d95502ec8339d3f378080a60adfdde70b59f5942519e2aad6ce0d69d4b97166d`,
`434da49c430eed3790e389fd513575b6c57ef7d04b787d29dd3a568805bdf41d`,
and
`3b8f474592ec6c5ed31a2463e2a1fd924afee7bcea90da44c8b3e22052b9642a`.

Its feed cutoff is `2026-08-06T00:47:37Z`.  Comparison to the immediately
preceding gate is by versioned arXiv ID: all 556 IDs, normalized metadata, and
screening decisions agree; 401 response-order moves are explicitly
nonmaterial; and the same 23 inspected candidates yield zero material C1--C5
deltas.  The separate exact-ID response keeps Xu and Srivastava--Surya at
version 1.  The gate remains a bounded title/abstract and exact-ID check, not
an exhaustive novelty, priority, absence, or general pre-window update claim.
It is artifact-specific: a later submission or deposit requires a new dated
archive and normalizer rather than reuse of this 2026-08-06 observation.

### 1.4b Check the Zenodo predraft literature gate offline

```powershell
uv run python scripts/normalize_v042_paper1_zenodo_predraft_gate_20260806T1123Z.py --check
uv run pytest -q -p no:cacheprovider `
  tests/final_theory/test_normalize_v042_paper1_zenodo_predraft_gate_20260806T1123Z.py
```

This fresh predraft gate replays no network request.  It verifies the archived
full-overlap Atom response (1,422,899 bytes), exact-ID response (5,201 bytes),
retrieval receipt (2,004 bytes), and normalized ledger (700,160 bytes), with
SHA-256 values
`a7e0bef901b70998fa64d3f4f6f7e8882ee8b7508ea935f9cafc664ce1218cf4`,
`fbe8a6498392001e23a85ca9cd6765fc404de1f915acc0a4d4fd4761b8bdba43`,
`0b56aa1a0cc49f023110d8f19e3ef7772f22eda92848403f1f624daaa8784428`, and
`4066604659f286dcdb134e295bd2c31c1736c7583a4ac2c8d51d65eeb9a84f6b`.
The full-overlap feed cutoff is `2026-08-06T11:28:07Z`; all 722 returned
records are in-window and at or before that cutoff.  The screen has 694
no-target records, 28 title/abstract-inspected nonmaterial records, and zero
material C1--C5 deltas.  The tracked exact IDs `arXiv:2607.26672` and
`arXiv:2603.25503` remain `v1`.
The normalized reconciliation deliberately records
`metadata_equal_by_id=false` because the two shared IDs gained category-only
metadata; `metadata_changes_reviewed=true` binds the Sol review of
`2608.02182v1` and `2608.02458v1`.

The versioned-ID delta contract is exact and ID-keyed: 178 added IDs, 12
missing v1 IDs replaced by v2, 166 new bases, two category-only shared-ID
changes, and no shared screening-decision change.  Its five fixed digests are
`13812bafc110aa41761be9733585fcc4dcdb6dfb3ae83e42cf24de867df89dc6`,
`e6ab3dd1239a3304cc10db37d989f4a5b95569b451c786cdd5d7e767c5bb3daa`,
`3c2dc8184c8d1a2b28ae739e85020bc5e423383f3f0e14ae7a3e6bc70e09b23b`,
`4d8ae8e5a42b5ce970c6297ba85372f26c5e325b7af8d9f494f92c0807209087`, and
`ec8a00b5ff3693ce402ec32906fa1adcbd6d59f872e2cc95fe490593f91d3425`.
The gate is a bounded technical title/abstract and exact-ID check.  It does
not establish exhaustive coverage, novelty, priority, absence, or general
pre-window version-update coverage, and it does not authorize manuscript
freeze, submission, deposit, or publication.  Only the dated human report and
research note are supplement members; raw Atom, receipt, normalized-ledger,
and third-party artifacts remain excluded.

### 1.5 Run the focused Paper I tests

```powershell
uv run pytest -q -p no:cacheprovider `
  tests/final_theory/test_paper1_claim_boundary_v042.py `
  tests/final_theory/test_paper1_manuscript_v042.py `
  tests/final_theory/test_extract_v042_paper1_witness_tables.py `
  tests/final_theory/test_normalize_v042_paper1_arxiv_delta_response.py `
  tests/final_theory/test_normalize_v042_paper1_submission_gate_response.py `
  tests/final_theory/test_normalize_v042_paper1_zenodo_gate_20260806.py `
  tests/final_theory/test_normalize_v042_paper1_zenodo_predraft_gate_20260806T1123Z.py `
  tests/final_theory/test_weak_d2_v04.py `
  tests/final_theory/test_weak_d2_v04_oracle.py `
  tests/final_theory/test_weak_d2_observability_v042.py `
  tests/final_theory/test_q5_free_elimination_v037.py `
  tests/final_theory/test_eq120_source_provenance_v042.py `
  tests/final_theory/test_v041_partial_slice_audit.py `
  tests/final_theory/test_semantic_recovery_v042.py `
  tests/final_theory/test_v042_stage7_fixture_portability.py `
  tests/final_theory/test_build_v042_paper1_pdf.py `
  tests/test_paper1_zenodo_bundle_v042.py
```

This is the focused Paper I regression set: manuscript and claim-boundary
validation, compact-supplement extraction, archived literature-ledger
normalization, weak/weak separation, its weak oracle and observability
boundary, the q5-free elimination and its oracle checks, the source-native
Eq. (120) lemma, the SR3b-A proper slice, and the SR3b-M conditional recovery
lemmas.  It is intentionally not a
repository-wide unbounded test run.  The pass count is a dated observation
rather than a fixed contract: retain the actual count and tool versions from
each reproduction run in its manuscript record.  The focused command above
observed 202 passing tests in the current tree on 2026-08-06.

## 2. Public frozen v0.3.9 lane

The public baseline is the immutable commit
`cba86eae795e1e985c4ba1bcd3dabe4eb2773fab`.  Check it out in a separate
worktree, rather than changing the current v0.4 worktree in place:

```powershell
git cat-file -e cba86eae795e1e985c4ba1bcd3dabe4eb2773fab^{commit}
git worktree add --detach ..\universe-theory-lab-v039 cba86eae795e1e985c4ba1bcd3dabe4eb2773fab
Set-Location ..\universe-theory-lab-v039
uv sync --frozen --group dev
uv run python scripts/reproduce_v039.py
```

If the commit object is not locally available, obtain the released repository
using the procedure in `REPRODUCING_v0.3.9.md`; do not replace it with a test
against the current v0.4 tree.  The expected historical scientific boundary is
still `FINAL_THEORY_OPEN`.  Its role in Paper I is limited to the C1
strong/strong comparison baseline.

## 3. U2 determinantal subroute: reproduce the limitation, not a theorem

The U2 auxiliary-ideal work remains a reproducibility and limitation record only.
Its status is SOFT_RESOURCE_LIMIT_NONTERMINAL, while the global SR2-V status
remains SEARCH_OPEN_NO_TERMINAL. Neither a bounded GF(32003) result nor a
non-unit minor basis proves a QQ theorem or a non-unit theorem for all 543 rows.

This is a two-layer gate.  Scientifically, `u2_is_global_terminal=false` and
the global search remains open.  Editorially, Paper I accepts the scoped
limitation under
`PAPER_I_SCOPED_U2_RESOURCE_OPEN_LIMITATION_ACCEPTED`; a later manuscript
freeze requires this explicit scoped limitation or a terminal SR2-V outcome,
not a U2 terminal verdict.  The dated authority is
`reports/v0.4.2_paper1_editorial_disposition_2026-08-06.md`.

The formal historical authority is reports/v0.4.2_sr2v_auxiliary_ideal_determinantal_pilot_2026-08-05.md,
including stage-8 attempt 20260804T234311036034Z-ee5eba925784438285676c05f2f6a716,
fingerprint 635005783896e88186615cad2bc3d29b650c554f92ab95003280a9c396863d78,
and its SOFT_RESOURCE_LIMIT / clean-postflight record.

### 3.1 Bounded-scout inputs and portable clone boundary

Three tracked input fixtures are authoritative:

- results/v0.4.2_sr2v_q5_free_auxiliary_ideal_stage7_request.json
  (raw SHA-256 456330c1fdb2abacea6b8a98d03dc9a78dbdbb72dcae7adff8f56740ae23098f);
- results/v0.4.2_sr2v_q5_free_auxiliary_ideal_stage7_result.json
  (raw SHA-256 f6f4d0c04cef65dcd454e61a23fcbcd7f932a500b3e2177fa69bf45447e04c14);
- results/v0.4.2_sr2v_q5_free_auxiliary_ideal_bounded_scout_polynomial_subset.json
  (raw SHA-256 718d484df2e3bb111383b49e90aba4cd3244ce6a3b907da016fc888635307c94).

The subset contains exactly 20 sorted records / 2,508 terms. It binds root
semantic digest 09b8ab346af957016be9a11f0f38b6fa94a1bee7310b2fe046633baef2f15688,
the full-arena ID-to-SHA ledger digest
da1f36484ea8b03a16bfd84f05104f27e66c61c8fbb144d2ea36d3d26acc1402, and
canonical records digest 02fa681dd799fe42c4a5b9f8a6d636ccc4ba098b4f41bbd9967f636a3d77c2a6.
The row-185 scout selects 18 records / 2,307 terms; fixed candidate-row-10
selects all 20 / 2,508. The subset is the authority even if a local full arena
is present.

Thus a fresh clone can run these two bounded derived scouts without restoring
or regenerating the 3,161-record, 134,213,882-byte gzip-compressed polynomial
arena. This does not reproduce the full 3,161-record arena, the full bundle,
the historical stage-8 raw event, or its postflight payload. It is not a
reexecution of the old stage-7 worker: it is a separately pinned derived
calculation using the stage-7 request/result as provenance inputs. The
mathematical verdict and resource-open boundary are unchanged.

With no local arena chunks, only the subset is read. If any full-arena chunk
is present, all chunks must be present; the legacy authenticated scanner checks
them as an unused mirror and requires canonical record and term-count equality
with the subset. A partial or disagreeing mirror fails closed.

The input contract M is results/v0.4.2_sr2v_q5_free_auxiliary_ideal_bounded_scout_reproduction_manifest.json
(semantic 61dcc8686d8ed886b299156ff366d07e50035ed322f506ff2ccae71016e7b385).
Its input mode is BOUNDED_SCOUT_SUBSET_ONLY and its derivation status is
DERIVED_CALCULATION_NOT_STAGE7_WORKER_REEXECUTION. It pins both scout sources,
the extraction/helper/worker sources, uv.lock, compose.yaml, all raw fixture
hashes, the root/subset digests, and sagemath/sagemath:10.9 at RepoDigest
sha256:e068670ae5863b54b2550e72437ec637b0283acb0dc712c8584c124dbf44e667.
Both Sage services in compose.yaml use the corresponding digest-qualified
image reference, rather than relying on the mutable tag alone.
The pure-Python loader verifies these bindings before Sage import and never
contacts Docker.

The separate self-bound expectation artifact E is results/v0.4.2_sr2v_q5_free_auxiliary_ideal_bounded_scout_expectations.json
(semantic fd4a7fb3c9734abb324bf7d2e4bcb6c4296c3bb7e15f0c218b408a46f7f745da).
It binds M without a digest cycle. Its current status is PINNED, with
row185_normal_form core digest
bd2d390ea996ea5149578bb569d6bba98fecbcb96b1b00d0fe8ff7b365f00deb and
candidate_minor_only core digest
cb9252dbc9d1610d3d0410f0d8f111a862b341cee59a4ced20bb8527c66a1c87.
The row-185 recomputation has three nonzero new minors and a 4-polynomial /
1,215-term non-unit minor-only basis. The candidate recomputation has five
generators and the same 4-polynomial / 1,215-term non-unit basis. The scouts
fail closed on a core-digest mismatch.

The older full-result digests
dc89668ac743214b4c84ee732672f7542e1517c2c200409cff2db54cc1d5d177 and
02f2ab4fbb53e8c91b5e67eb686a35543e61a51db2f912191f7621a002e4f947 are
retained only as NONDETERMINISTIC_LEGACY_OBSERVATION_NOT_A_REPRODUCTION_EXPECTATION:
they included timing values and are not expected output digests. The v2 scouts
emit a deterministic certificate_core / certificate_core_digest_sha256; timing
and mirror observations are only in runtime_observation. The top-level
reproduction_contract records M/E semantic digests without source-version data
in the mathematical core.

The tracked authority includes the root, the three fixtures, M, E, the
extraction script, and both scout scripts. Check a complete local full-arena
mirror without mutation:

~~~powershell
uv run python scripts/extract_v042_bounded_scout_polynomial_subset.py --check
~~~

--write is an explicit fixture-maintenance action; if it changes the subset,
rebuild and review M and the E binding.

First validate the resolved Compose model, then explicitly re-check local image
provenance as defense in depth:

~~~powershell
docker compose config --quiet
$expected = 'sha256:e068670ae5863b54b2550e72437ec637b0283acb0dc712c8584c124dbf44e667'
$actual = docker image inspect --format '{{json .RepoDigests}}' sagemath/sagemath:10.9
if ($LASTEXITCODE -ne 0 -or $actual -notmatch [regex]::Escape($expected)) {
  throw "unexpected Sage image RepoDigest: $actual"
}
~~~

The following are read-only bounded derived computations; they create no
campaign attempt and no longer need arena restoration in a fresh clone:

~~~powershell
docker compose run --rm --no-deps --entrypoint sage sage-solver -python scripts/reproduce_v042_row185_normal_form_scout.py .
docker compose run --rm --no-deps --entrypoint sage sage-solver -python scripts/reproduce_v042_candidate_minor_only_scout.py . 10
~~~

The Sage-free focused check covers clone fallback, raw/record bindings, local
mismatch/ambiguity, source drift, both needed sets, mirror behavior, expectation
states, and exclusion of timing keys from certificate-core digests:

~~~powershell
uv run pytest -q -p no:cacheprovider tests/final_theory/test_v042_stage7_fixture_portability.py
~~~

Raw supervised attempts remain untracked, including stage-8 raw events/postflight.
Their absence prevents raw historical replay. No fixture or expectation widens
the theorem boundary. Do not rerun the recorded stage-8 fingerprint: a new U2
run needs a separately fixed mathematical candidate and resource contract.
### 3.2 Postflight process audit

After any new Sage/container computation, verify the same zero-survivor policy
used by the supervised campaign.  This command is read-only and fails if a
stale `sr2v-aux-` container or a legacy `sage`, `sage-eval`, or `Singular`
worker remains in the long-lived Sage service.  It verifies the current
postflight state; it cannot replay the untracked historical raw attempt:

```powershell
uv run python -c "from pathlib import Path; from universe_lab.final_theory.sr2v_q5_free_auxiliary_ideal_campaign_v042 import preflight_process_audit; preflight_process_audit(Path('.')); print('process_audit=OK')"
```

Expected output is `process_audit=OK`.  A failure is an operational failure,
not an inconclusive mathematical result; retain the process evidence and do
not report the attempted computation as cleanly reproduced.

## 4. TeX build status

The host workstation still has neither `latexmk` nor `pdflatex`.  The
canonical candidate was built and checked on 2026-08-06 with the pinned
container entry point below, run from the repository root:

```powershell
uv run python scripts/build_v042_paper1_pdf.py --dry-run
uv run python scripts/build_v042_paper1_pdf.py
```

The helper fixes the image to
`texlive/texlive:latest-medium@sha256:d79913b74afcf48a53ec2ad0d54b70ad3e36d65b4f1de13d811435883c2f1fd9`.
There is no mutable-tag or host-TeX fallback.  The source command
`\bibliography{../v0.3.9_d2_commutativity_short_report/references,references}`
requires repository-relative context: mounting only this manuscript directory
breaks the shared bibliography path.  The helper therefore copies the paper
directory and the shared `references.bib` into a repository-shaped temporary
mirror below `tmp/pdfs/`, runs `latexmk` inside that mirror, and removes the
mirror on success or failure.

The final `main.log` is authoritative for build diagnostics.  An overfull
horizontal box, an undefined reference or citation, a LaTeX/Package error, a
nonzero Docker exit, a missing log/PDF, or an output-integrity mismatch makes
the helper fail.  On success it atomically replaces
`output/pdf/paper1_statewise_operator_v0.4.2.pdf` and prints a JSON record
containing the image reference, toolchain, page-count availability, byte count,
SHA-256, diagnostics, and output path.  The generated PDF is intentionally
untracked and is not required by the read-only manuscript validator in a fresh
clone.

The current dated build and all-page visual inspection are recorded in
`reports/v0.4.2_paper1_pdf_build_2026-08-06.md`.  The source-bound observation
is an 18-page, 427745-byte PDF with SHA-256
`9f58867d91673c09229077cd651a35d16d10e90c618cc6ef6083fd4fb644fd43`.
All 18 pages were rendered at 144 dpi and inspected; every blocking and box
diagnostic is zero, no clipping or overlap was found, and no intentional
draft-proof box remains.  The manifest records
`CURRENT_SOURCE_FINAL_BUILD_AND_ALL_PAGE_VISUAL_QA_VERIFIED` and a completed
PDF/source rebind, while submission and deposit remain owner-only and
unauthorized.  Any later source or PDF change reopens that fail-closed gate.
This is layout/build verification only and does not widen C1--C5 or any
nonclaim.

## 5. Reporting a reproduction

Record the current commit, `uv --version`, Python version, command output,
and any Docker/Sage image digest.  State the lane explicitly.  A valid current
Paper I report says that the current v0.4 ledger and focused tests passed, and
that U2 remains resource-open.  A valid v0.3.9 report says that the frozen
historical release reproduced in its own checkout.  Do not merge those two
sentences into one green verdict.
