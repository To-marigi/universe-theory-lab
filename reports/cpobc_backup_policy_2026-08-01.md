# CPOBC backup policy and non-Git artifact snapshot

Established: 2026-08-01

## 1. Backup decision

The Git repository and its pushed GitHub branch are the authoritative backup
for source code, scripts, tests, configuration, tracked result JSON, reports,
and manuscript source. Do not maintain a second unpacked repository tree on
the NAS. A NAS worktree would duplicate Git, drift silently, and invite slow
execution against network storage.

The NAS is used only for material that is not adequately protected by Git:

| material | backup route |
|---|---|
| tracked code/config/tests/reports/result JSON | Git commit plus push; no NAS copy |
| versioned research PDFs | local `references/papers/` plus filename-preserving NAS mirror |
| expensive Git-ignored certificates and generated research outputs | one immutable compressed snapshot on NAS |
| virtual environments, caches, `tmp/`, generated Python bytecode | no backup |
| `.env`, unsent correspondence, third-party/private details | excluded from NAS snapshot |

## 2. NAS operating rule

NAS paths are cold backup storage only.

- Do not run Python, Sage, Singular, tests, notebooks, binaries, or manuscript
  builds from the NAS.
- Do not extract archives on the NAS.
- Do not point solvers, package managers, caches, temporary directories, or
  reference-text extraction at the NAS.
- To restore, copy an archive to a local disk, verify its SHA-256, and extract
  it locally.
- Hash verification may read the stored archive, but no contained file is
  executed or expanded there.

## 3. Snapshot created on 2026-08-01

The clean pushed Git state was commit
`c3f60ba1c42c794b549996ee0bc9a55ea0a5da3f`. A read-only audit found 512
research-shaped files excluded by `.gitignore` under `certificates/`,
`results/`, and the generated paper PDF:

- 504 certificate/progress/benchmark files, 67,833,659 bytes;
- 7 legacy generated result/notebook files, 52,752 bytes;
- 1 generated manuscript PDF, 322,360 bytes.

The archive was created and content-listed on the local workspace, then moved
to the NAS without being expanded there.

NAS object:

`Y:\universe-theory-lab-backup\artifacts\non_git_snapshots\cpobc-nongit-research-artifacts-c3f60ba-20260801.tar.gz`

Archive properties:

- entries: 512;
- source bytes: 68,208,771;
- compressed bytes: 4,590,362;
- SHA-256:
  `69500bbe912de40234b213c3ca157ad0ef91be7f0dea156f1b7b956b7ce96be0`;
- post-move NAS hash: exact match.

This snapshot intentionally excludes the Git worktree, `references/papers/`
(backed up separately), `tmp/`, caches, environments, `.env`, and `outreach/`.

## 4. Future snapshot cadence

Do not create a NAS artifact archive on every commit. Create a new immutable
snapshot only after one of the following:

1. a successful expensive solver/certificate campaign produces important
   Git-ignored outputs;
2. a result needed for publication or independent verification remains
   intentionally outside Git;
3. the local workstation or repository is about to be migrated;
4. an existing snapshot no longer covers the current authoritative
   certificate set.

Never overwrite an older snapshot. Use the source commit and date in the
filename, record the file census and SHA-256 here or in a successor report,
and verify the NAS hash after transfer.
