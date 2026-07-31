# Reproducing v0.3.9

v0.3.9 makes the v0.3 baseline audit resolve the frozen branch through the
remote-tracking ref that a clone already has.  It reruns no solver, alters no
certificate, and moves no verdict: `scientific_change` is `NONE`.

## Environment

```console
git clone --branch codex/final-theory-v0.3.9-audit-ref-portability-20260730 https://github.com/To-marigi/universe-theory-lab.git
cd universe-theory-lab
uv sync --frozen
```

The repository's default branch is
`codex/final-theory-v0.3.5-d2-saturated-elimination-20260729`, so a plain
`git clone` checks out v0.3.5 and does not provide the v0.3.9 entry point.  The
explicit `--branch` above checks out this release branch.  Do not add
`--single-branch`: the baseline audit also needs the remote-tracking ref for
the frozen v0.3 branch.

A full clone is required.  The baseline audits resolve the v0.2 and v0.3
production and freeze commits, their ancestry, and both annotated freeze tags,
none of which a shallow clone contains.  If you fetched with `--depth`, run
`git fetch --unshallow --tags` before verifying.

Unlike v0.3.8, **no manual step is needed**.  v0.3.8 required creating a local
head for `codex/final-theory-v0.3-novelty-first-20260728` before the v0.3
baseline audit would pass; `audit_v031.resolve_frozen_branch` now accepts
`refs/remotes/origin/<branch>` directly, and the matching workaround has been
removed from CI.

### Resolver boundary

The fallback resolves `refs/remotes/origin/<branch>`.  A full clone using the
conventional remote name `origin` is in scope.  Arbitrary remote names are
deliberately **not** generalised over: a checkout whose remote is named
something else must either add an `origin` remote or create the local head
itself.  A local head, if present, still takes precedence, so an ordinary
working copy is unaffected.

## Verify

```console
uv run python scripts/reproduce_v039.py
```

The command succeeds only if all of the following hold:

1. everything v0.3.8 verified still holds — the line-ending bridge regenerates
   exactly, every JSON Pointer binding resolves, bridge targets use
   virtual-CRLF raw digests, and the frozen Phase 1, Phase 2 and scope-addendum
   gates pass.  These are checked by `reproduce_v038.verify_v038` with
   `check_release_manifest=False`, so v0.3.9 does not reimplement them;
2. the v0.3.8 release manifest still pins as the declared baseline: schema
   `final-theory-release-manifest-v0.3.8`, 193 files, semantic digest
   `e4b50d41263e296860fd8a0e39aa3490510b40b48e99c8848fa035b8da7eed01`;
3. every one of those 193 entries is byte-identical or a member of a declared
   change set — `V039_INTENTIONAL_AUDIT_PORTABILITY_CHANGE`,
   `V039_INTENTIONAL_RELEASE_METADATA_UPDATE`,
   `V039_INTENTIONAL_HISTORICAL_TEST_REBASE`,
   `V039_INTENTIONAL_AUTHOR_IDENTITY`, or `V039_NEW_RELEASE_SUPPORT`.
   Any undeclared difference fails immediately;
4. the v0.3.9 release manifest regenerates byte-for-byte and excludes itself.

The individual checks are:

```console
uv run python scripts/build_v039_release_manifest.py --check
uv run pytest -q tests/final_theory/test_audit_ref_portability_v039.py
uv run pytest -q tests/final_theory/test_reproduce_v039.py
uv run ruff check scripts/build_v039_release_manifest.py scripts/build_v039_deposit_archive.py scripts/reproduce_v039.py scripts/verify_bundle_v039.py
```

## If you have the Zenodo bundle rather than the repository

The deposited bundle is a curated archive of the files named by
`results/v0.3.9_release_manifest.json`, plus that manifest — 206 files, 48.0
MiB. It is **not** a repository snapshot, and it deliberately excludes
third-party material: the 52 PDFs under `references/papers/`, the 52 texts
extracted from them under `references/text/`, and the 3 vendored archives under
`oracle/sage_periods/vendor/`. None of it is covered by this repository's MIT
licence — no reference record carries a licence field for any entry.

The provenance records travel with the bundle, so the exclusion can be worked
around rather than merely explained:

| record | what it gives |
| --- | --- |
| `references/manifest.json` | for each of the 52 archived papers: arXiv identifier, URL, byte size, page count, SHA-256, and the name of the text extracted from it. 19 records also carry a DOI; 7 of the 59 are `METADATA_ONLY`, with no PDF archived |
| `references/sources.json` | the 59-entry catalogue those records index — title, authors, version-pinned URL, what each source was used for, and its claim boundary |
| `oracle/sage_periods/source_manifest.json` | for each of the 3 vendored archives: upstream repository, commit, SHA-256, plus the `sagemath/sagemath:10.8` container digest |

So the papers and the vendored archives can be fetched from their sources and
checked against the recorded digests. The extracted texts carry **no digest of
their own** — only a filename — and are reproduced by re-extracting from the
corresponding PDF rather than verified directly.

From the bundle alone you can verify byte integrity:

```console
uv run python scripts/verify_bundle_v039.py --root <extracted bundle>
```

That checks every recorded SHA-256, the manifest's own semantic digest, and the
absence of extra files.

**You cannot run `scripts/reproduce_v039.py` from the bundle.** This is a
measured limit, not a caution. The line-ending bridge is regenerated from
`git ls-files`, and the frozen baseline audits resolve commits, annotated tags
and a branch. Staging the manifest plus every bridge target and every bridge
consumer — 335 files, 121.5 MiB — still fails, because the tracked-file set
itself comes from git. Adding files cannot close this gap.

Full reproduction therefore requires the repository at the released commit:

```console
git clone --branch codex/final-theory-v0.3.9-audit-ref-portability-20260730 https://github.com/To-marigi/universe-theory-lab.git
```

### Rebuilding the bundle

The archive is reproducible from the repository, not only verifiable.
`scripts/build_v039_deposit_archive.py` packs the manifest's files plus the
manifest in sorted order, with every member fixed to mode 0644, uid/gid 0,
empty owner names, and an `mtime` taken from the packaged commit's author date.
The gzip wrapper stores neither a filename nor a timestamp, so the output
depends on the packaged commit and on nothing else about the machine.

```console
uv run python scripts/build_v039_deposit_archive.py --output <path>/final-theory-bench-v0.3.9.tar.gz --commit <released commit> --expect-sha256 <recorded digest>
```

The builder refuses to run if any packed file differs from its recorded
SHA-256, so a stale or dirty checkout cannot be archived under the release's
name. Because `mtime` comes from the commit, the archive digest is bound to
that commit: a recorded digest is only checkable when it is quoted together
with the commit it was built from.

## The v0.3.8 release is unchanged

No v0.3.8 document or artifact is edited by v0.3.9.
`results/v0.3.8_release_manifest.json` is carried into the v0.3.9 manifest as
the historical baseline, and `REPRODUCING_v0.3.8.md` remains correct for
reproducing v0.3.8 itself — including its manual prerequisite, which applied to
that release and still does.

## Expected verdicts

```text
Phase 1  LITERAL_Q1_Q4_COMMUTATIVITY_PROVED
Phase 2  LEMMA_GENERAL_SCALAR_CHAIN_FIBER_EXACT
Global   FINAL_THEORY_OPEN
scientific_change  NONE
```

`FINAL_THEORY_OPEN` is unchanged and is not affected by this release.
