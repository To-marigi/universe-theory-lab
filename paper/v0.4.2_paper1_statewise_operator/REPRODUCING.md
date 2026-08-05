# Reproducing Paper I (v0.4.2 claim boundary)

This directory records the reproducibility contract for the scoped Paper I
working title, *Statewise versus operator Bell causality in finite quantum
sequential growth: exact separation and recovery at dimension two*.

As of 2026-08-05, the manuscript package is
`SCOPED_MANUSCRIPT_ASSEMBLY_READY`; submission remains
`OWNER_AND_MANUSCRIPT_REVIEW_PENDING`.  The source of truth for what may be
claimed is:

- `results/v0.4.2_paper1_claim_boundary.json` (machine-readable ledger), and
- `reports/v0.4.2_paper1_claim_boundary_2026-08-05.md` (human-readable
  evidence ledger).

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

### 1.3 Run the focused Paper I tests

```powershell
uv run pytest -q -p no:cacheprovider `
  tests/final_theory/test_paper1_claim_boundary_v042.py `
  tests/final_theory/test_weak_d2_v04.py `
  tests/final_theory/test_weak_d2_observability_v042.py `
  tests/final_theory/test_eq120_source_provenance_v042.py `
  tests/final_theory/test_v041_partial_slice_audit.py `
  tests/final_theory/test_semantic_recovery_v042.py
```

This is the focused Paper I regression set: weak/weak separation and its
observability boundary, the source-native Eq. (120) lemma, the SR3b-A proper
slice, the SR3b-M conditional recovery lemmas, and the claim-boundary
validator.  It is intentionally not a repository-wide unbounded test run.
A current-tree run on 2026-08-05 observed 45 passing tests.  That is a dated
observation rather than a required fixed count: retain the actual count and
tool versions from each reproduction run in its manuscript record.

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

The v0.4.2 Paper I `main.tex` scaffold is present.  On this workstation neither
`latexmk` nor `pdflatex` is installed, so its PDF build is unverified.  This is
a documented toolchain absence, not a passing TeX check.

After installing a TeX toolchain, run one of the following from this directory:

```powershell
if (Get-Command latexmk -ErrorAction SilentlyContinue) {
  latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
} elseif (Get-Command pdflatex -ErrorAction SilentlyContinue) {
  pdflatex -interaction=nonstopmode -halt-on-error main.tex
  bibtex main
  if ($LASTEXITCODE -ne 0) { throw 'BibTeX failed' }
  pdflatex -interaction=nonstopmode -halt-on-error main.tex
  pdflatex -interaction=nonstopmode -halt-on-error main.tex
} else {
  throw 'TeX build unavailable: install latexmk or pdflatex before claiming PDF reproduction'
}
```

When LaTeX is introduced, a successful build only verifies manuscript
compilation.  It must be reported alongside the current claim validator and
focused Paper I tests; it does not widen C1--C5 or remove any nonclaim.

## 5. Reporting a reproduction

Record the current commit, `uv --version`, Python version, command output,
and any Docker/Sage image digest.  State the lane explicitly.  A valid current
Paper I report says that the current v0.4 ledger and focused tests passed, and
that U2 remains resource-open.  A valid v0.3.9 report says that the frozen
historical release reproduced in its own checkout.  Do not merge those two
sentences into one green verdict.
