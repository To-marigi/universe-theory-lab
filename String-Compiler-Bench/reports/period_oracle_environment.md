# Period oracle environment

- SageMath: 10.8 Docker image, digest pinned in `source_manifest.json`.
- `lefschetz-family`: 0.1.21 wheel, SHA-256 pinned.
- `ore_algebra`: commit `d234e3d8...`, vendored source.
- Sage source headers: exact 10.8 commit `981d7d71...`.
- Production commit: `afb7a4025e55e667421d7635b9302946a86d525e`.

Sage 10.9 was rejected because the pinned Ore Algebra source still references
legacy Arb Cython paths removed in 10.9. An isolated PassageMath build on 10.8
also produced an ABI mismatch. The accepted environment overlays the exact 10.8
PXDs and builds against Sage itself with `--no-build-isolation`.

Status: `PERIOD_ORACLE_VALIDATED`.
