# Handoff — Final-Theory Bench, publication track

Written 2026-07-31. Read this before touching the release machinery.

---

## 1. Where things stand

```
branch      codex/final-theory-v0.3.9-audit-ref-portability-20260730
last green  run 30624874873 on 4f54ee2 — success, 359 tests
HEAD        a later commit; its own CI run is a separate observation
verdict     FINAL_THEORY_OPEN   (unchanged, and not up for revision)
deposit     approved; target 4f54ee2 — see §4 and §5
```

A commit cannot record its own hash or its own CI run, so §1 always names the
last commit that was actually observed green. Check `git log` for HEAD.

Mechanical blockers to a Zenodo deposit: **none**. What remains is the owner's
decision, listed in §5.

---

## 2. The scientific result

One theorem, and it is narrower than its title suggests.

> Let `K` be algebraically closed of characteristic zero and let
> `(Q_1,…,Q_5) ∈ GL_2(K)^5` satisfy the literal (printed `Q_{n+1}`) branch of
> the frozen, nonsingular, source-stage `n ≤ 4` compilation of the CPOBC,
> general-covariance and Markov-sum relations, materialised as strong operator
> identities. Then `[Q_i, Q_j] = 0` for `1 ≤ i < j ≤ 4`.

Paper source: `paper/v0.3.7_d2_commutativity/main.tex`, PDF at
`output/pdf/v0.3.7_d2_commutativity_short_report.pdf`.

### What this is, relative to the literature

Srivastava & Surya, *Implementing Bell causality in Quantum Sequential Growth*
(arXiv:2603.25503v1) rules out the ansatz `Q̂_n ∝ σ_i` in its Appendix, then
states in the Abstract that a non-trivial representation "must be higher
dimensional". That inference was never proved. This work proves it, under the
stated restrictions. It **extends** the paper; it does not overturn it.

As of 2026-07-31 the paper is still v1, has no journal reference, no erratum,
and **zero citations on INSPIRE** (verify via
`https://inspirehep.net/api/literature?q=refersto%20recid%203136377` — the web
UI needs JavaScript, the JSON API does not).

### Three things a reviewer will ask, already answered in the paper

1. **Is it a restatement of Theorem 3.7?** No. The family
   `Q_n = σ_1 diag(a_n, b_n)` with `a_n b_n ≠ 0`, `a_n ≠ ±b_n` satisfies
   Eqs. (120), (129) and (130), is noncommutative, and lies outside Eq. (165)
   for *every* generator. The full CPOBC/GC/MSR inventory is essential.
2. **Is it a corollary of Lemma 3.10?** No. That lemma needs some fixed `Q_k`
   central in the whole infinite subalgebra; this conclusion is confined to
   indices ≤ 4 and neither follows from it nor triggers it.
3. **Does a `d = 2` representation exist at all?** Yes — commutative ones
   (e.g. `Q_n = λ_n Q_1`). Never write "no `d = 2` representation exists".
   Write "every `d = 2` representation is commutative".

### Not claimed

`d ≥ 3`; singular transitions; stages `n ≥ 5`; weak or occurrence-dependent
operator semantics; any restriction/lifting theorem to the infinite CPOBC
algebra; anything about continuum limits, Lorentz symmetry, or Einstein's
equations. The strong operator profile is **our formalisation and a
strengthening**, not a hypothesis attributed to the source paper.

### The Eq. (113) ambiguity — still open

Eq. (112) gives `Ĝ⁰_n = Ŝ_α Q̂_n Ŝ_α⁻¹`; path-independence yields
`[Ŝ_α⁻¹Ŝ_β, Q̂_n] = 0`, index `n`. Printed Eq. (113) shows `Q̂_{n+1}`. No
derivational route to `n+1` was found. Separately, Eq. (139) genuinely carries
`Q̂_{n+1}`, and the paper's own `n = 2` substitution there produces `Q̂_3`.

Both readings are kept as frozen branches. **Do not assert a typo.** The main
theorem is deliberately independent of the answer: it is proved from a
`Q_5`-free subsystem of 2,552 of the 2,564 canonical numerators.

Under the literal reading, `Q_5` is *entirely unconstrained* by the `n ≤ 4`
system — all 12 `Q_5`-dependent numerators vanish identically in its four
coordinates. An earlier "noncommutative representation found" verdict was
withdrawn for exactly this reason: the noncommutativity was generic motion in a
free fibre, not a constrained solution.

---

## 3. Release architecture

Three releases, each a strict discipline over the previous.

| Version | Content | Guard |
| --- | --- | --- |
| v0.3.7 | the theorem, first release metadata | manifest vs curated path list |
| v0.3.8 | CRLF → LF canonicalisation + legacy hash bridge | vs v0.3.7 manifest, 3 classes |
| v0.3.9 | audit ref-resolution portability | vs v0.3.8 manifest, 4 classes |

**The rule that matters:** each builder loads the previous manifest and requires
every entry to be byte-identical or a member of an explicitly declared change
set. Anything else raises. This is why several release-preparation steps in this
project were caught rather than shipped.

v0.3.9 classification, pinned by tests:

```
UNCHANGED_RAW_BYTES                          188
V039_INTENTIONAL_AUDIT_PORTABILITY_CHANGE      2   ci.yml, audit_v031.py
V039_INTENTIONAL_RELEASE_METADATA_UPDATE       2   .zenodo.json, CITATION.cff
V039_INTENTIONAL_HISTORICAL_TEST_REBASE        1   test_reproduce_v038.py
                                             ───
                                             193
manifest file_count 205  (193 baseline + 12 new support)
```

`scripts/reproduce_v039.py` reuses
`reproduce_v038.verify_v038(root, check_release_manifest=False)` rather than
reimplementing the bridge and the frozen Phase 1/2/scope gates. That seam
already existed; use it.

### v0.3.8's bridge, in one paragraph

Artifacts written by Python on Windows carried CRLF, and every recorded
`certificate_sha256` was computed over those CRLF bytes, while git's index
stores LF. Any clone therefore failed every recorded raw-byte hash. v0.3.8
canonicalised tracked text to LF, fixed the writers with `newline="\n"`, and —
crucially — did **not** rewrite the digests inside frozen artifacts. Instead
`results/v0.3.8_line_ending_bridge.json` records 1,007 historical bindings
across 84 consumers and 207 targets by JSON Pointer, so each legacy CRLF-era
hash stays verifiable against the canonical LF file. Rewriting in place was
rejected because it would propagate into request digests and digest-derived
filenames.

---

## 4. The deposit bundle

```
archive   final-theory-bench-v0.3.9.tar.gz
builder   scripts/build_v039_deposit_archive.py   (--output is required)
files     206  (205 manifest entries + the self-excluded manifest)
size      48.0 MiB extracted
```

Deterministic: entries sorted by path, `mtime` fixed to the commit's author
date, uid/gid 0, empty uname/gname, mode 0644, gzip `mtime=0`. Built twice,
byte-identical. Round-tripped: extracted and verified with
`scripts/verify_bundle_v039.py`, `missing 0 / mismatch 0 / extra 0`.

**The archive digest is bound to the packaged commit**, because `mtime` is that
commit's author date. Never quote one without the other. Rebuild with:

```console
uv run python scripts/build_v039_deposit_archive.py --output <path>/final-theory-bench-v0.3.9.tar.gz --commit <commit>
```

The builder was validated against the archive that predates it: at `313e915`,
with the then-current 203-entry manifest, it reproduces
`97a220b4180f4de58735dcc795b3d59377cd9b8300de4c0ecc50ce87d3e78860`,
7,202,298 bytes, byte for byte. That archive is superseded — the current
manifest has 204 entries — but the reproduction is what establishes that the
builder is the same procedure that produced the original.

### The approved deposit

```
commit    4f54ee27ebbaf0747b7ed8e53df98ac5a458e649   (CI 30624874873, green)
sha256    7719dfd01954f21e7bbc72473138bc88ab04d4d7ae840edcea5a7128a8eec537
size      7,209,209 bytes / 206 members / 48.0 MiB extracted
manifest  205 entries, 2e3229c2b274e8c206a8c2ae531c0aad6a665b1b727f5c37187f0235c7b6ed7d
```

Two earlier candidates are superseded and must not be deposited: `a190306c…`
at `1f93809`, which predates the prose corrections, and `550b129e…` at
`8cc5a64`, which predates them and the metadata refresh.

Built twice byte-identical; extracted and checked with
`scripts/verify_bundle_v039.py` — `missing 0 / mismatch 0 / extra 0`, manifest
digest intact. **The archive is not committed.** Rebuild it from the commit
above; do not go looking for a copy.

The commit and the digest are absent from `.zenodo.json` deliberately. Both are
functions of the tree, so a file inside the archive cannot state either without
invalidating itself — the same circularity as embedding a reserved DOI. They go
into the Zenodo form, whose metadata sits outside the archive and stays editable
after publication.

### The title, deliberately

The deposit title leads with the result and carries `Final-Theory Bench` as a
parenthetical identifier, not as the opening words. Inside the repository
`Final-Theory` names the *target under test* — the verdict is
`FINAL_THEORY_OPEN` — but a Zenodo search result shows the title alone, where
that reading is unavailable and the name looks like a claim. `CITATION.cff`
follows the same shape. **Do not move the project name back to the front.**

The archive filename, the module paths under `src/universe_lab/final_theory/`
and the verdict tokens keep the name, which is what preserves the correspondence
between the record and the code.

### Excluded, deliberately

`references/papers/` (52 PDFs), `references/text/` (52 extracted texts),
`oracle/sage_periods/vendor/` (3 archives), the 7 ignored files under
`results/`, and anything else outside the manifest.

Reason: third-party copyright. **No reference record carries a licence field for
any entry.** The default arXiv licence grants arXiv a distribution right, not
third parties. Depositing those files under this repository's MIT `LICENSE`
would misrepresent their terms in a record that cannot be withdrawn.

Where the provenance actually lives — measured 2026-07-31, because the earlier
description of this was wrong in two ways at once:

| record | contents |
| --- | --- |
| `references/manifest.json` | 59 records. The 52 `PDF_AND_TEXT` ones carry `sha256`, `bytes`, `pages`, `local_file`, `text_file`; 19 carry a `doi`; 7 are `METADATA_ONLY`. **This is the file with the digests.** |
| `references/sources.json` | the 59-entry catalogue `manifest.json` indexes. Human-readable: id, title, authors, url, used_for, claim_boundary. **No `sha256`, no `doi`.** |
| `oracle/sage_periods/source_manifest.json` | the 3 vendored archives — upstream repository, commit, `sha256` — plus the `sagemath/sagemath:10.8` container digest. Added to the manifest in this release so the bundle can honour its own instruction. |

The earlier text said `references/sources.json` recorded "DOI, URL, retrieval
date and SHA-256". It records none of the digests, and the vendor record was not
in the bundle at all, so the deposit told readers to check digests it did not
ship. Both are fixed. **The extracted texts have no digest of their own** — only
a `text_file` name — so they are reproduced by re-extracting from the PDF, not
verified directly.

### The bundle cannot verify itself — measured, not assumed

```
203 files (manifest only)                → fails immediately
329 files (+ all 126 bridge targets)     → fails
335 files (+ all bridge consumers)       → fails, 121.5 MiB
```

Those three counts are the sets as they were measured, against the 203-entry
manifest; the builder added since does not move the boundary.

The bridge is regenerated from `git ls-files`, and the baseline audits resolve
commits, annotated tags and a branch. **No file set closes this gap.** Do not
try again by adding files.

`scripts/verify_bundle_v039.py` provides what a deposit honestly can: every
recorded SHA-256, the manifest's own semantic digest, and the absence of extra
files. Full reproduction needs the repository. `REPRODUCING_v0.3.9.md` states
this with the measurements above.

---

## 5. Owner decisions — settled 2026-07-31

Both are decided. Recorded so a new session does not reopen them.

1. **Deposit target: `4f54ee27ebbaf0747b7ed8e53df98ac5a458e649`**, with the
   archive `7719dfd0…`. Commit and digest were approved together, because the
   digest is a function of the commit and approving one without the other
   approves nothing. See §4.
2. **Permanent publication: approved.** The owner accepted the actual terms: a
   version DOI cannot be withdrawn, withdrawal leaves a tombstone that keeps the
   DOI and URL, and what is frozen is *that version's files* — metadata stays
   editable after publication and later versions attach to the same concept DOI.

A third item from the earlier list, committing the deposit-archive builder, is
done — see §4 and §8.

### Still not done, and not the agent's to do

The deposit itself. It needs the owner's Zenodo account, and no agent performs
it. Invariant §7-6 continues to apply to everything else: tags, mail, and any
further publication each need their own approval in chat.

**DOI: not yet recorded.** When the deposit is executed, capture three things —
the version DOI, the concept DOI, and the record URL — and write them here.
Then add the DOI to `CITATION.cff` and the README **in a later version**: writing
it into the current tree changes the archive digest and breaks the binding the
deposit itself records.

`sandbox.zenodo.org` is a separate instance with its own accounts, and DOIs
there are throwaway. Rehearsing the whole deposit on it costs one signup and
removes the only real unknown: what publication actually does.

**The deposit itself is the owner's action.** It requires their Zenodo account,
and no agent performs it.

---

## 6. Open — work items, none blocking

| Item | Note |
| --- | --- |
| Public-repo rights audit | The excluded third-party material is still reachable from the public GitHub branch. Separate from the Zenodo question, but real. |
| `.gitignore` allowlist | Add `!results/v0.3.9_*.json`. Those files were force-added, so nothing is broken; it is a consistency gap. Do it in a later version, where its classification cost is not a surprise. |
| mypy | 11 errors on Windows, all in `d2_sage_backend_v035.py`: 2 bytes/str assignments, 1 shadowed name, 3 unused ignores, 1 missing annotation, 4 platform-conditional `resource.getrusage`. **The Linux CI runner reports 7** — the four `resource` errors do not arise there. Same debt, two platforms; the comment in `ci.yml` quotes 11 without saying which. The CI job is advisory by design. That file is proof-bearing solver code bound to frozen digests — clear it in its own change, with a full test rerun. |
| `paper/paper.md` AI disclosure | Same tool/part split as the corrected `.zenodo.json`, and now imprecise for the same reason — see §10. In the v0.3.8 baseline and undeclared, so a fix needs a new change class. Do it in a version that is already touching the paper. |
| `v031.py:370` wording | `"completeness_scope": "physical certification precondition only; no representation exists"`. In context it means the artifact constructs no representation — `dimension` is 3, `field` is `NOT_CONSTRUCTED` — and it is not a d=2 claim. Quoted alone it reads as a nonexistence theorem. In the v0.3.8 baseline and undeclared; rephrase in a later version. |
| `actions/checkout@v4` | Node 20 deprecation warning. Works. Bump when convenient. |
| 7 unpushed tags | Only the two freeze tags the audits need were published. The rest are provenance, not requirements. |
| JOSS | Everything mechanical is in place: OSI licence, public repo, issue tracker, green CI, `CONTRIBUTING.md`, `paper/paper.md`. Only the owner's scope/maturity judgement remains — **and it does not gate Zenodo**, which applies no editorial review. The v0.3.8 readiness artifact conflated the two; v0.3.9 separates them. |
| Author enquiry | Bundle ready at `outreach/2026-07-30_rri_enquiry/` (gitignored on purpose: unsent mail, third-party details). **No email address is published** for either author — RRI lists only a phone and office. Waiting for a journal version, which will carry a corresponding-author address, is the reliable route. Update the manifest digest quoted inside the bundle, or drop it, before sending. |
| arXiv | Needs endorsement: since January 2026, an institutional address alone is insufficient. Personal endorsement from an established gr-qc author is the realistic path, and the Eq. (113) enquiry is a natural opening. Not urgent. |

---

## 7. Invariants — do not violate

1. **Frozen artifacts are immutable.** Corrections go in a new version plus an
   addendum naming what it supersedes. Earlier digests must stay valid.
2. **Exact over numeric.** No float is a certificate. Finite-field runs are
   scouts; only characteristic-zero results are proof-bearing.
3. **No silent capability downgrade.** If a backend is missing, fail loudly.
   Never fall back to a weaker solver and report success.
4. **Resource budgets are human-owned**, read from `config/*_budget.json`. Never
   invent a default; stop and ask.
5. **Claims stay in three buckets** — known literature, independent derivation,
   unresolved. Never empty `unresolved_components` for tidiness.
6. **Never publish, deposit, push a tag, or send mail without explicit approval
   in chat.** Approval is per-action.
7. Do not update `FINAL_THEORY_OPEN`.
8. **Never enable the Zenodo GitHub integration for this repository.** Its own
   page states what it does: it downloads "a .zip-ball of each new release" —
   the whole tree — and mints a DOI for it. That would publish the third-party
   material §4 excludes, permanently, under this repository's MIT framing.
   Deposits here are manual and consist of exactly one file, the archive in §4.
   As of 2026-07-31 the per-repository toggle is off and no GitHub release
   exists, so nothing has been taken. Flipping the toggle alone is harmless;
   creating a release with it on is not.

---

## 8. Traps already paid for

Every one of these was a real failure in this project. They share one shape:
**something that verified only on the authoring machine.**

- **CRLF raw-byte hashes.** 83 of 159 manifest files. Fixed in v0.3.8.
- **Unpublished refs.** Two annotated freeze tags and a frozen branch existed
  only locally; the audits require them. Published.
- **Shallow checkout.** `actions/checkout` defaults to depth 1; the baseline
  audits need full history. `fetch-depth: 0`.
- **Bare branch resolution.** `git rev-parse <branch>` never falls back to
  `refs/remotes/origin/<branch>`, and a clone has no local head for a branch it
  did not check out. Fixed in v0.3.9.
- **Packaging.** Closed. `scripts/build_v039_deposit_archive.py` is committed,
  and it reproduces the hand-built archive byte for byte. This was the last
  instance of the family; no step of the release is machine-bound now.

A second family, found 2026-07-31 while preparing the deposit: **prose nobody
measured.** Each instance read as correct and was internally consistent. Each
broke the moment the artifact it described was opened and counted.

- **`203 files`** in `.zenodo.json`, after the manifest had reached 204.
- **The AI disclosure** credited Codex with implementation and test scaffolding
  in the same release where Claude wrote the deposit-archive builder and its
  tests.
- **"`references/sources.json` records DOI, URL, retrieval date and SHA-256"** —
  it records none of the digests; `references/manifest.json` does. The repo's own
  `references/README.md` had the split right the whole time. Only the
  deposit-facing prose was wrong, and the vendor record was not in the bundle at
  all, so the deposit instructed readers to check digests it did not ship.
- **"v0.3.9 contains this change and nothing else"** in the audit report, after
  v0.3.9 had gained the deposit-archive builder.

The rule that follows: **a sentence entering a permanent record is measured
against the artifact it describes, not reviewed for plausibility.** Three of
those four survived an independent audit and a green CI.

Operational traps:

- **`gh run watch --exit-status` returned 0 for a failed run.** Always re-read
  the conclusion with `gh run view --json status,conclusion`.
- **Editing a manifest-tracked file without rebuilding the manifest** broke CI
  twice. After touching anything in the manifest, rerun the builder.
- **A CI job once hung 23 minutes and was cancelled at the 30-minute cap.** The
  same commit passed on re-run in 7m30s, and the same tests take 74 s locally.
  Judged a one-off runner event; the timeout was deliberately *not* raised.
  If it recurs at the same point, it is real — investigate rather than extend.
- **Do not "fix" a hang or a red gate by loosening a limit** before establishing
  that the limit is the cause.

---

## 9. Orientation

```
paper/v0.3.7_d2_commutativity/main.tex   the short report
paper/paper.md                           JOSS draft
REPRODUCING_v0.3.9.md                    verification, incl. bundle boundary
reports/v0.3.9_audit_ref_portability.md  what v0.3.9 changed and why
reports/v0.3.9_publication_readiness.md  blockers, Zenodo vs JOSS separated
results/v0.3.9_release_manifest.json     204 entries, self-excluded
results/v0.3.8_line_ending_bridge.json   1,007 bindings / 84 consumers / 207 targets
scripts/build_v039_release_manifest.py   declared-change guard
scripts/build_v039_deposit_archive.py    deterministic deposit packaging
scripts/reproduce_v039.py                full verification
scripts/verify_bundle_v039.py            offline bundle integrity
src/universe_lab/final_theory/audit_v031.py   resolve_frozen_branch
AGENTS.md                                research-source preservation rules
CONTRIBUTING.md                          invariants, AI-disclosure requirement
```

Verification, in order of cost:

```console
uv run python scripts/reproduce_v039.py     # full, needs the git repository
uv run pytest -q                            # 359 tests, ~6 min
uv run ruff check .
uv run python scripts/verify_bundle_v039.py --root <extracted bundle>
```

---

## 10. AI disclosure

**Re-check this whenever an AI writes code into a release.** In v0.3.9 the
disclosure went stale within one session: it attributed implementation and test
scaffolding to Codex, while the deposit-archive builder and its tests were
written by Claude. `.zenodo.json` was corrected. Two things make this worth a
standing check rather than a one-off fix:

- **`.zenodo.json` ships inside the archive**, so its disclosure is frozen at
  deposit. The Zenodo form's metadata stays editable after publication; the file
  does not.
- `CONTRIBUTING.md` requires disclosure of **which tool, for which part**. A
  disclosure that is true in substance can still fail that test.

`paper/paper.md` carries the same split and is also now imprecise, but it sits
in the v0.3.8 baseline undeclared, so correcting it costs a new declared change
class. Deferred — see §6.

Both `.zenodo.json` and the paper record that OpenAI Codex assisted with
implementation, test scaffolding, artifact checks and prose, and that Anthropic
Claude assisted with research design, the `Q_5`-free proof strategy, symbolic
cross-checks and prior-art review. The human author selected scope and budgets,
reviewed the work, and is responsible for every claim. AI systems are not
listed as authors. Keep this accurate — arXiv's policy places full
responsibility on the author regardless of how content was produced, and the
one-year ban it introduced in May 2026 targets unverified AI output such as
hallucinated references.
