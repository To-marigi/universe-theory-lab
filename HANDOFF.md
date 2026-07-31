# Handoff — Final-Theory Bench, publication track

Written 2026-07-31. Read this before touching the release machinery.

---

## 1. Where things stand

```
branch      codex/final-theory-v0.3.9-audit-ref-portability-20260730
last green  run 30619471105 on 8cc5a64 — success, 359 tests
HEAD        a later commit; its own CI run is a separate observation
verdict     FINAL_THEORY_OPEN   (unchanged, and not up for revision)
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
manifest file_count 204  (193 baseline + 11 new support)
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
files     205  (204 manifest entries + the self-excluded manifest)
size      47.9 MiB extracted
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

### Excluded, deliberately

`references/papers/` (52 PDFs), `references/text/` (52 extracted texts),
`oracle/sage_periods/vendor/` (3 archives), the 7 ignored files under
`results/`, and anything else outside the manifest.

Reason: third-party copyright. `references/sources.json` records DOI, URL,
retrieval date and SHA-256 for 59 entries but **no licence field for any of
them**. The default arXiv licence grants arXiv a distribution right, not third
parties. Depositing those files under this repository's MIT `LICENSE` would
misrepresent their terms in a record that cannot be withdrawn. Readers can fetch
the originals and check them against the recorded digests.

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

## 5. Open — owner decisions

Nothing below should be actioned without the owner saying so in chat.

1. **Fix the v1 commit**, then rebuild the archive at it and **approve that
   archive** for deposit. The two are one decision now: the digest is a function
   of the commit, so approving a digest without naming its commit approves
   nothing.
2. **Approve permanent publication.** A Zenodo DOI cannot be withdrawn. This is
   the only genuine blocker.

Item 4 of the previous list — commit the deposit-archive builder — is done. See
§4 and §8.

**The deposit itself is the owner's action.** It requires their Zenodo account,
and no agent performs it.

---

## 6. Open — work items, none blocking

| Item | Note |
| --- | --- |
| Public-repo rights audit | The excluded third-party material is still reachable from the public GitHub branch. Separate from the Zenodo question, but real. |
| `.gitignore` allowlist | Add `!results/v0.3.9_*.json`. Those files were force-added, so nothing is broken; it is a consistency gap. Do it in a later version, where its classification cost is not a surprise. |
| mypy | 11 errors on Windows, all in `d2_sage_backend_v035.py`: 2 bytes/str assignments, 1 shadowed name, 3 unused ignores, 1 missing annotation, 4 platform-conditional `resource.getrusage`. **The Linux CI runner reports 7** — the four `resource` errors do not arise there. Same debt, two platforms; the comment in `ci.yml` quotes 11 without saying which. The CI job is advisory by design. That file is proof-bearing solver code bound to frozen digests — clear it in its own change, with a full test rerun. |
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

Both `.zenodo.json` and the paper record that OpenAI Codex assisted with
implementation, test scaffolding, artifact checks and prose, and that Anthropic
Claude assisted with research design, the `Q_5`-free proof strategy, symbolic
cross-checks and prior-art review. The human author selected scope and budgets,
reviewed the work, and is responsible for every claim. AI systems are not
listed as authors. Keep this accurate — arXiv's policy places full
responsibility on the author regardless of how content was produced, and the
one-year ban it introduced in May 2026 targets unverified AI output such as
hallucinated references.
