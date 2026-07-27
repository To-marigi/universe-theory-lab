# String-Compiler Bench v0.3 period oracle

This directory runs `lefschetz-family` as an external SageMath oracle. No oracle
implementation is copied into production Python.

## Frozen environment

- SageMath Docker image: `sagemath/sagemath:10.8`
- Image digest: `sha256:e2e4747b0e1ea8753a9cb5a399314a8b2c25fcefaf69ba85b22ee075829d09ea`
- `lefschetz-family`: PyPI 0.1.21, vendored wheel
- `ore_algebra`: Git commit pinned in `source_manifest.json`, vendored source archive
- Sage 10.8 development headers: exact Sage tag commit, vendored as a PXD archive

The binary Sage image omits development PXD files needed to compile
`ore_algebra`. The runner overlays the exact Sage 10.8 headers, then builds
`ore_algebra` with `--no-build-isolation`, preventing the PassageMath/Sage ABI
mismatch observed with an isolated build.

Sage 10.9 was also tested and rejected for this oracle because that release
removed the legacy `sage.libs.arb` PXD paths still referenced by the pinned
`ore_algebra` source.

## Cases

- `validation`: upstream Shioda K3 documentation example
- `j4-standard`: Equation (3.2) of arXiv:2205.08100v1
- `j4-bfd`: Equation (3.1), related by the symplectic base inversion
- `j4-alternate`: Equation (3.4)
- `j4-maximal`: the maximal specialization/rescaling to Equation (3.4)

Example inside the prepared container:

```sh
sage oracle/sage_periods/run_period_oracle.sage \
  --case j4-standard --nbits 128 \
  --output results/period_oracle_raw/j4-standard-128.json
```

The output stores the full intersection matrix, primary and trivial lattice
bases, certified complex-ball periods, and the Hodge bilinear checks. Numerical
Neron-Severi and Mordell-Weil recovery are intentionally not used as exact
oracles.
