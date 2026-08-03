# CPOBC non-Git artifact snapshot 2026-08-03

Successor snapshot record under the backup policy established on 2026-08-01.
The policy itself is unchanged; this report only adds the census, digests, and
transfer verification for a new immutable NAS object.

## 1. Trigger

Policy condition 4.1: an expensive campaign produced important Git-ignored
outputs. The SR2-V Q5-free auxiliary-ideal Phase-A compile finished for the
first time and its two coefficient arenas are deliberately stored outside Git.

## 2. Source state

- Source commit at archive time: `24c4170`
- Root manifest (tracked in Git):
  `results/v0.4.2_sr2v_q5_free_auxiliary_ideal_bundle_root.json`
- Root semantic digest at archive time:
  `4c137b6c302066df91813e0333e84684df538a40fbdc6843f1d92eee10b25845`
- Full logical payload digest:
  `2a79c1d0b9fd464ba9c80e970cad948b21920f8d25e7403256ccbc27017a5a8a`

### 2.1 Root superseded, archive unchanged

The verifier contract was tightened after this archive was made: an absent
recompilation check no longer counts as a pass, the recompiled compiler,
bundle and `uv.lock` digests are now compared against the committed code
binding, and the frozen verdict was renamed to state that digests and solver
inputs are frozen rather than every byte of the manifest. The root was
therefore regenerated and re-verified.

The archived chunks are unaffected. Regeneration produced all nine chunks
**bit-identically** -- every uncompressed SHA-256, gzip SHA-256 and byte count
matched, as did the row index, chart generator tables and arena
correspondence digests -- so this NAS object remains the authoritative cold
backup and was deliberately not duplicated under a second name.

Current root, verified by an independent recompilation on 2026-08-03:

- Root semantic digest:
  `aa246d3856a5f12e67a326222d906ce5b7239d83053fd5b902d2e5e5b6d54e7c`
- Root verdict:
  `SR2V_Q5_FREE_AUXILIARY_IDEAL_FULL_MANIFEST_DIGEST_AND_SOLVER_INPUTS_FROZEN_NO_SOLVER_RUN`
- Full logical payload digest: unchanged, and now reproduced across six
  independent compiles.

## 3. File census

Nine Git-ignored chunk files under
`results/v0.4.2_sr2v_q5_free_auxiliary_ideal_bundle/`, totalling 134,213,882
bytes:

| bytes | file |
|---:|---|
| 16,743,680 | `localized_coefficient_arena.0000.jsonl.gz` |
| 16,317,260 | `polynomial_arena.0000.jsonl.gz` |
| 16,218,640 | `polynomial_arena.0001.jsonl.gz` |
| 16,327,642 | `polynomial_arena.0002.jsonl.gz` |
| 16,774,533 | `polynomial_arena.0003.jsonl.gz` |
| 16,411,524 | `polynomial_arena.0004.jsonl.gz` |
| 16,623,138 | `polynomial_arena.0005.jsonl.gz` |
| 16,482,185 | `polynomial_arena.0006.jsonl.gz` |
| 2,315,280 | `polynomial_arena.0007.jsonl.gz` |

Each chunk is compact canonical JSONL compressed with deterministic gzip
(level 6, `mtime=0`, no embedded filename). Their uncompressed content totals
2,124,026,895 bytes, and the per-chunk uncompressed SHA-256 values -- the
mathematical authority -- are recorded in the tracked root manifest, not here.

## 4. NAS object

`Y:\universe-theory-lab-backup\artifacts\non_git_snapshots\cpobc-phase-a-bundle-24c4170-20260803.tar.gz`

Archive properties:

- entries: 10 (nine chunk files plus their directory entry);
- source bytes: 134,213,882;
- archive bytes: 134,195,946;
- SHA-256:
  `c21b8f8b7839866b068c9973b356d442ba61a6c9ed70c40116893a60730b41fa`;
- post-move NAS hash: exact match.

The archive was created and content-listed on the local workspace, then moved
to the NAS. It was not expanded, executed, or read by any solver there. The
2026-08-01 snapshot was not overwritten or removed.

## 5. Restore procedure

Copy the archive to a local disk, verify its SHA-256 against the value above,
extract it locally into `results/`, then run

```bash
uv run python -m universe_lab.final_theory.sr2v_q5_free_auxiliary_ideal_bundle_v042 --verify
```

which streams every chunk against the tracked ledger and independently
recompiles Phase A. A missing chunk or any digest mismatch yields
`OPEN_ARTIFACT_INCOMPLETE` rather than a partial pass.

## 6. Publication route

The same compressed bundle is the intended Zenodo supplemental dataset at
publication time. Zenodo's ordinary limit is well above its 128 MiB size, so no
Git LFS and no custom binary container are required.
