# Final-Theory Bench v0.3.1 literature-frontier note — 2026-07-28

## Source claims

- Srivastava and Surya, arXiv:2603.25503v1, assume nonsingular transition
  operators. Their TOBC and NTOBC orderings force commutativity; CPOBC yields
  further relations without a general commutative-collapse theorem. A central
  antichain generator forces the full algebra to commute, and the tested
  two-dimensional Pauli ansatz is inconsistent. The paper explicitly leaves a
  general noncommutative realization unresolved.
- Surya and Zalel, arXiv:2003.11311v1 / CQG 37 195030, give an extension
  criterion for scalar Complex Sequential Growth and a large extendible family.
  Dowker, Johnston, and Surya, arXiv:1007.2725v1 / J. Phys. A 43 505305, relate
  extension of a strongly positive decoherence functional to extension of its
  associated histories-Hilbert-space vector measure and give non-extension
  examples.
- Rideout and Sorkin, arXiv:gr-qc/9904062v3, supply the classical
  sequential-growth, general-covariance, precursor/spectator, Bell-causality,
  and normalization framework.
- Gudder's arXiv:1204.5767v1 and arXiv:1303.0433v1 already construct QSGP path
  Hilbert spaces, positive-operator dynamics, and amplitude processes in a
  different formalism.
- Halliwell's arXiv:quant-ph/9902008v3 and Gell-Mann--Hartle's
  arXiv:gr-qc/9509054v4 establish records/decoherence results. These support an
  orthogonal-record regression baseline, not a new coherent-geometry model.
- Quantum Causal Histories, semicausal channels, quantum combs, causal boxes,
  covtree, and quantum causal models all contain relevant causal or
  compositional structures, but none uses the same state space and
  spectator-ordering relation as nonsingular CPOBC sequential growth.

## Independent project inference

The mandatory search used four routes for arXiv:2603.25503: exact ID/title,
both author routes, concept synonyms, and citation tracking. The official
record remained v1 with no journal reference; the exact Ritesh Srivastava
author route and narrow concept queries returned only that paper; INSPIRE
reported zero citations; OpenAlex had no exact-title record. No higher-
dimensional CPOBC representation, complete representation classification, or
general no-go was found.

This supports the bounded repository verdict `FRONTIER_CONFIRMED_OPEN`, not a
global theorem of literature nonexistence. The open target is a finite-
dimensional nonsingular noncommutative CPOBC representation, beginning with
dimension three, or an exact no-go whose assumptions and representation
stratum are explicit.

## Classification consequences

- `LITERATURE_LOCKED`: scalar CSG, its MSR/GC/Bell-causality framework and
  extension criterion; histories Hilbert spaces and amplitude processes;
  records-induced decoherence; QCH/CP maps; semicausal/no-signalling channels;
  combs/causal boxes; classical covtree; TOBC/NTOBC collapse; published CPOBC
  relations, central-antichain collapse, and the stated Pauli-ansatz failure.
- `REGRESSION_ONLY`: an extendible scalar CSG positive control, paper equation
  and ordering fixtures, precursor/spectator conventions, and orthogonal-record
  decoherence checks.
- `OPEN_TARGET`: complete mechanical compilation of the finite CPOBC relation
  scope and an exact higher-dimensional noncommutative representation or
  explicitly scoped no-go.
- `FORMULATION_MISMATCH`: Kraus-channel semicausality, Quantum Causal
  Histories, comb/process causality, causal boxes, classical covtree, and
  quantum causal-model d-separation when offered as CPOBC substitutes.
- `EXTERNAL_RESULT_SUPERSEDES_TASK`: no.

## Unresolved gaps and archive limitation

Semantic Scholar returned HTTP 429, and every negative search remains bounded
by the indexes visible on 2026-07-28. The 17 version-specific primary PDFs were
preserved under `references/papers/` and hashed. The required
`scripts/archive_references.py` run initially failed because `pypdf` was not
installed, then succeeded with `--skip-text` as permitted by `AGENTS.md`.
Consequently the new archive records are `PDF_ONLY`; equations and figures must
be checked in the PDFs, and no new extracted text is treated as evidence.
