# Reproducing v0.3.8

v0.3.8 is a canonical-LF serialization migration over the frozen v0.3.7
scientific artifacts.  Verification does not require Sage and does not rerun
Phase 1 or Phase 2 elimination.

## Environment

From a clean repository checkout:

```console
uv sync --frozen
```

Git attributes require LF for tracked text and mark known binary formats as
binary.  The regression test rejects CRLF and lone carriage returns in tracked
text independently of `core.autocrlf`.

## Verify

Run the complete compatibility and scientific regression:

```console
uv run python scripts/reproduce_v038.py
```

The command succeeds only if all of the following hold:

1. the line-ending bridge regenerates exactly and every JSON Pointer binding
   resolves;
2. bridge targets use virtual-CRLF raw digests and non-targets use current raw
   digests;
3. the frozen Phase 1, Phase 2, and scope-addendum semantic/gate checks pass;
4. the v0.3.8 release manifest regenerates byte-for-byte.

The individual release checks are:

```console
uv run python scripts/build_v038_line_ending_bridge.py --check
uv run python scripts/build_v038_release_manifest.py --check
uv run pytest -q tests/final_theory/test_line_ending_bridge_v038.py
uv run pytest -q tests/final_theory/test_reproduce_v038.py
uv run pytest -q tests/test_line_endings.py
uv run ruff check scripts/build_v038_release_manifest.py scripts/reproduce_v038.py src/universe_lab/artifact_migration_v038.py tests/final_theory/test_reproduce_v038.py
```

## Historical v0.3.7 manifest

Do not use an exact rebuild of `results/v0.3.7_release_manifest.json` as the
v0.3.8 migration check.  That file intentionally preserves raw CRLF-era
digests.  The v0.3.8 builder instead audits every historical entry as one of:
unchanged raw bytes, a declared line-ending bridge target, or an explicit
v0.3.8 writer/support update.  Any fourth category fails the build.

## Expected verdicts

The reproduction summary must report:

```text
Phase 1  LITERAL_Q1_Q4_COMMUTATIVITY_PROVED
Phase 2  LEMMA_GENERAL_SCALAR_CHAIN_FIBER_EXACT
Scope    V037_SCOPE_ADDENDUM_CERTIFIED
Global   FINAL_THEORY_OPEN
Change   NONE
```

These are the v0.3.7 scientific verdicts.  v0.3.8 changes byte serialization
and compatibility verification only.
