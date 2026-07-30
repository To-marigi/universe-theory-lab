# Contributing

Thanks for looking at this repository. It is a research environment for
exact symbolic computation on finite quantum sequential-growth algebras, so
the contribution rules are shaped by one requirement: **a claim is only as
good as the artifact that certifies it.**

## Reporting a problem

Open a GitHub issue. The most valuable reports are:

- **A wrong result.** Give the artifact path, the field or verdict token you
  believe is wrong, and why. A counterexample or a failing assertion is
  ideal.
- **A reproduction failure.** Follow `REPRODUCING_v0.3.7.md` first, then
  report the step that diverged, with your OS, Python version, and
  `uv run finaltheory --help` output.
- **A scope overreach.** If a report, docstring, or metadata field claims
  more than its certificate supports, that is a bug. Say which sentence and
  which artifact.

## Seeking support

Use GitHub issues for questions about running the code or reading the
artifacts. There is no private support channel and no service-level
expectation: this is a single-author research repository, and replies are
best-effort.

## Contributing changes

1. Open an issue before a substantial change so the scope can be agreed.
2. Branch from the current working branch, not from a frozen release tag.
3. Keep the following invariants:
   - **Frozen artifacts are immutable.** Files under `results/` belonging to
     an already-released version are not edited. Corrections are added as a
     new version plus an addendum that names what it supersedes; the earlier
     digests must stay valid.
   - **Exact over numeric.** No floating-point value is admitted as a
     certificate. Finite-field runs are scouts; only characteristic-zero
     results are proof-bearing.
   - **No silent capability downgrade.** If a required backend is missing,
     fail loudly. Never fall back to a weaker solver and report success.
   - **Resource budgets are human-owned.** Timeouts and memory limits are
     read from `config/*_budget.json`. Code must not invent defaults.
   - **Claims stay separated** into known literature, independent derivation,
     and unresolved. Unresolved components are listed, never emptied for
     tidiness.
   - **Sources are recorded.** See the research-source preservation rules in
     `AGENTS.md` before citing anything external.
4. Add or extend tests. New proof-bearing code needs a test that would fail
   if the claim were wrong, not only one that pins current output.
5. Run the portable checks locally:

   ```bash
   uv sync --frozen
   uv run ruff check .
   uv run pytest -ra
   ```

   `uv run mypy` currently reports pre-existing errors in
   `src/universe_lab/final_theory/d2_sage_backend_v035.py`; the CI mypy job is
   advisory for that reason. Do not add new type errors.
6. Exact SageMath/Singular reruns need the container in `compose.yaml` and a
   budget file. They are not part of CI. If your change affects a certificate,
   say in the pull request which campaign you reran and attach the digests.

## AI-assisted contributions

They are welcome, and they must be disclosed in the pull request: which tool,
and for which part. The submitter takes full responsibility for every line
regardless of how it was produced. Unverified AI output — fabricated
references, invented citations, plausible-looking numbers with no artifact
behind them — is the one thing this repository cannot absorb.

## License

By contributing you agree that your contribution is licensed under the MIT
License, as stated in `LICENSE`.
