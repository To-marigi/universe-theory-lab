# Reproducing v0.3.9

v0.3.9 makes the v0.3 baseline audit resolve the frozen branch through the
remote-tracking ref that a clone already has.  It reruns no solver, alters no
certificate, and moves no verdict: `scientific_change` is `NONE`.

## Environment

```console
git clone https://github.com/To-marigi/universe-theory-lab.git
cd universe-theory-lab
uv sync --frozen
```

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
   `V039_INTENTIONAL_RELEASE_METADATA_UPDATE`, or `V039_NEW_RELEASE_SUPPORT`.
   Any undeclared difference fails immediately;
4. the v0.3.9 release manifest regenerates byte-for-byte and excludes itself.

The individual checks are:

```console
uv run python scripts/build_v039_release_manifest.py --check
uv run pytest -q tests/final_theory/test_audit_ref_portability_v039.py
uv run pytest -q tests/final_theory/test_reproduce_v039.py
uv run ruff check scripts/build_v039_release_manifest.py scripts/reproduce_v039.py
```

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
