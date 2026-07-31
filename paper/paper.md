---
title: "Final-Theory Bench: exact symbolic certificates for finite quantum sequential-growth algebras"
tags:
  - Python
  - SageMath
  - causal sets
  - computer-assisted proof
authors:
  - name: Kenichi Osaki
    orcid: 0009-0003-9256-7089
    affiliation: "1"
affiliations:
  - name: Independent researcher
    index: 1
date: 30 July 2026
bibliography: paper.bib
---

# Summary

Final-Theory Bench is a reproducible symbolic-computation environment for
finite quantum sequential-growth (QSG) algebras. It turns operator relations
into explicit polynomial systems, records the semantic branch used to compile
each relation, stratifies low-dimensional matrix representations, and runs
exact SageMath/Singular calculations under a human-owned resource budget. Its
artifacts retain equation provenance, denominator-open conditions, request
digests, backend versions, peak memory, terminal status, and certificate
hashes.

The v0.3.8 release carries the scientific result established in v0.3.7 and
adds a canonical-LF compatibility bridge for the historical CRLF raw-byte
digests. The result focuses on the causal-past-ordered Bell-causality (CPOBC)
relations studied by @SrivastavaSurya2026. For the repository's frozen
strong-operator compiler through source stage \(n\leq4\), it proves that every
two-dimensional, nonsingular solution of the literal printed-\(Q_{n+1}\)
branch on the explicitly recorded denominator-open locus satisfies
\([Q_i,Q_j]=0\) for \(1\leq i<j\leq4\). The certificates are computed over
\(\mathbb{Q}\); the unit-ideal conclusions persist after extension to any
characteristic-zero field, including \(\mathbb{C}\). This is a finite
computer-assisted theorem, not a classification of the unrestricted CPOBC
algebra or of excluded denominator loci.

# Statement of need

QSG calculations mix noncommutative words, path identities, explicit matrix
inverses, and semantic choices about how statements in a source paper become
operator equations. A plausible-looking Gröbner-basis output is therefore not
enough. The decisive questions are whether the compiled system is the stated
system, whether a chart cover is complete for the predicate being proved,
whether excluded denominators are recorded, whether the exact backend actually
ran, and whether timeouts or finite-field scouts have been promoted to
characteristic-zero proofs.

Final-Theory Bench addresses this audit problem. It keeps literal and
derivation-based interpretations of the source-index ambiguity as separate
branches, freezes compiler products by hash, and distinguishes exact
\(\mathbb{Q}\) proof certificates from modular consistency scouts. Resource
limits come only from `config/v0.3.7_budget.json`; the runtime has no fallback
budget and cannot self-authorise a larger calculation.

# State of the field

Classical sequential growth combines discrete general covariance with a
Bell-causality condition [@RideoutSorkin2000]. Srivastava and Surya formulate
operator-valued Bell-causality orderings for QSG
[@SrivastavaSurya2026]. Their time-ordered and non-time-ordered cases collapse
to commutative transition algebras, while the general CPOBC representation
problem remains open. Their displayed \(d=2\) inconsistency calculation uses a
Pauli-proportional ansatz and is not an arbitrary-\(\mathrm{GL}_2\)
classification.

The `strong-operator` profile is the project's explicit formalisation and
strengthening, not a uniform hypothesis asserted throughout the source paper.
The source first states general covariance on a distinguished initial vector
and invokes reachable-state reasoning, while later atomisation steps use
operator identities. The compiler deliberately adopts the whole-operator
reading and keeps that semantic boundary in every result.

General results on simultaneous similarity and triangularisation of
two-by-two matrix tuples [@Florentino2009] and algorithms for saturation and
colon ideals [@BerthomieuEtAl2023] supply mathematical and computational
context. They do not certify this project's equation inventory, chart cover,
localisation factors, or unit-ideal outputs. The v0.3.7 claims are independent
project derivations with an explicit literature boundary.

# Software design

The pipeline separates compilation, selection, execution, and aggregation.
Canonical numerators preserve structural equality and sign equivalence but are
not advertised as a minimal generating set. Every backend request binds the
selected equation IDs, compiler artifact, chart, coefficient field, budget
file, and memory limit. A completed certificate is proof-eligible only when
these bindings, localisation checks, saturation coverage, and resource gates
all pass.

The decisive v0.3.7 calculation first partitions 2,564 literal canonical
numerators into 2,552 expressions independent of \(Q_5\) and 12 dependent on
it. Every literal solution satisfies the weaker 2,552-expression shared core.
The target predicate involves only \(Q_1,\ldots,Q_4\), so no \(Q_5\) variable
or \(R_5=Q_1^{-1}Q_5\) commutativity assumption is needed. The established
three-stratum cover for \(R_2,R_3,R_4\) yields 12 S1 and 9 S2 charts; S3 is
structurally scalar. All 21 charts resolve over \(\mathbb{Q}\). Matching
computations over \(\mathrm{GF}(32003)\) and \(\mathrm{GF}(32009)\) are
reported only as scouts.

A separate scalar-chain proposition evaluates all 1,001 direct reduced
operator relations exactly over \(\mathbb{Q}\), on the recorded locus where
all specialised inverse and transition factors are nonzero. Exhaustive static
provenance then covers all 2,564 canonical numerators: 979 represented
relations account for 3,916 matrix-entry provenance records, and the remaining
22 relations are exact zero path-consistency identities. These are two proof
components with shared compiler/backend lineage, not two independent
implementations or two actual evaluation routes.

The default v0.3.8 reproduction command verifies the compatibility bridge,
existing semantic and proof gates, and the canonical-LF release manifest
without rerunning expensive algebra. Explicit v0.3.7 flags remain available
for budget-controlled Phase 1 and Phase 2 reruns. The release manifest
enumerates every proof certificate used by the aggregates.

# Research impact statement

The immediate result is a corrected, auditable finite \(d=2\) theorem. An
earlier 49-chart campaign remains numerically unchanged but is now labelled
complete only inside its simultaneous-\(R_5\) ansatz. The replacement proof is
smaller and stronger for the stated predicate because it removes \(Q_5\)
entirely. The software also provides reusable negative-claim controls:
timeouts remain partial, modular runs remain scouts, and a scalar-chain fiber
is not promoted to an arbitrary-base classification.

The global programme verdict remains `FINAL_THEORY_OPEN`. The release does not
resolve the source paper's intended index, the infinite algebra, weak or
occurrence-dependent operator semantics, dimensions \(d\geq3\), or continuum
quantum-measure extension.

# AI usage disclosure

OpenAI Codex assisted with implementation, test scaffolding, exact-run
orchestration, artifact-integrity checks, literature-record maintenance, and
draft prose. Anthropic Claude assisted with research design, the \(Q_5\)-free
proof strategy, symbolic cross-checks, sharpness analysis, and prior-art
review. The human author specified the research questions and claim
boundaries, supplied the computation budget, reviewed the changes and rendered
paper, and remains responsible for the software and scientific claims. The AI
systems are not authors.

# Acknowledgements

The project builds on SageMath, Singular, and the cited causal-set and
computational-algebra literature. No external deposition, DOI assignment, or
JOSS submission is claimed by this draft.

# References
