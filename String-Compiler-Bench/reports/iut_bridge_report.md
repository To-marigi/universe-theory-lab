# IUT bridge report — skeptical v0.1 track

## Result

| Layer | Result | Scope |
|---|---|---|
| A: frame/type discipline (H-IUT0) | `IUT_TYPE_SYSTEM_ONLY` | Implemented and negatively tested |
| B: IUT-native arithmetic/physics bridge | `IUT_NOT_APPLICABLE` | No defined domain map |

This result is intentionally independent of whether the wider String-Compiler
Bench passes. Failure or non-applicability of Layer B does not invalidate the
ordinary F-theory/heterotic benchmark.

## What the primary IUT sources establish for this audit

Mochizuki's IUT I abstract defines the starting domain as *initial Θ-data*,
including an elliptic curve over a number field and a prime \(\ell\ge 5\), plus
further technical data and conditions. It constructs Θ-Hodge theaters and says
that theaters are isomorphic while a Θ-link relates selected
Frobenioid-theoretic portions in a way that is not compatible with their
ordinary ring/scheme structures. IUT II describes the Θ-link as
non-scheme-theoretic and develops multiradiality. IUT III studies log-links,
log-shells, and log-volume estimates. IUT IV applies those estimates to claimed
Diophantine consequences and discusses a set-theoretic notion of species.

Primary sources:

- S. Mochizuki, [IUT I: Construction of Hodge Theaters](https://doi.org/10.4171/PRIMS/57-1-1),
  *PRIMS* 57 (2021), 3–207.
- S. Mochizuki, [IUT II: Hodge–Arakelov-Theoretic Evaluation](https://doi.org/10.4171/PRIMS/57-1-2),
  *PRIMS* 57 (2021), 209–401.
- S. Mochizuki, [IUT III: Canonical Splittings of the Log-Theta-Lattice](https://doi.org/10.4171/PRIMS/57-1-3),
  *PRIMS* 57 (2021), 403–626.
- S. Mochizuki, [IUT IV: Log-Volume Computations and Set-Theoretic Foundations](https://doi.org/10.4171/PRIMS/57-1-4),
  *PRIMS* 57 (2021), 627–723.

None of these source descriptions supplies a map from an F-theory or heterotic
compactification to valid initial Θ-data, nor a definition identifying an IUT
log-volume with energy, action, a vacuum weight, or another physical observable.
The bridge code consequently requires such a map explicitly and does not
manufacture one by analogy.

## Published dispute context

The four IUT papers are published, but their claimed ABC/Szpiro consequence is
disputed. Scholze and Stix's 2018 report, written after discussions at RIMS,
argues that the proof has a severe problem at the use of IUT III,
Corollary 3.12. Their report also gives a skeptical reconstruction in which
important structures are equivalent to more conventional data. Mochizuki
rejects that criticism in his response and maintains that the critics collapse
structures that IUT requires one to keep separate.

Sources recording the opposing positions:

- P. Scholze and J. Stix,
  [Why abc is still a conjecture](https://www.math.uni-bonn.de/people/scholze/WhyABCisStillaConjecture.pdf)
  (2018).
- S. Mochizuki,
  [Comments on the manuscript by Scholze–Stix](https://www.kurims.kyoto-u.ac.jp/~motizuki/Cmt2018-05.pdf)
  (2018).

This benchmark does not adjudicate that deep mathematical dispute. It records
the relevant conclusions as `DISPUTED` and forbids them as trusted oracles.
Publication is evidence of publication, not independent resolution of the
objection.

## Executable gates

The implementation separates the following gates:

1. **H-IUT0 / isolation:** raw cross-frame equality and ordering raise an
   exception. Transport requires an allowed, directional morphism certificate.
2. **I1 / domain:** require a fully specified map from a physical frame to
   initial Θ-data, including the further technical conditions. A shared phrase
   such as “elliptic fibration” is insufficient.
3. **I2 / model independence:** require invariance under presentation and
   coordinate changes.
4. **I3 / duality:** require compatibility across the independently implemented
   F-theory and heterotic frames.
5. **I4 / non-redundancy:** reject anything reconstructible from discriminant
   valuations, reduction type, \(j\)-data, Mordell–Weil data, heights, local
   Galois data, conductor-like data, or other declared conventional fields.
6. **I5 / prediction:** require a preregistered held-out prediction with no
   post-hoc coefficient fitting.
7. **Evidence:** a physical bridge pass additionally requires proof-grade
   independent verification and an explicit dispute audit.

## Negative-control findings

- Equal Python values in different universe/frame/model addresses cannot be
  compared directly.
- A morphism not listed in the source object's permissions is rejected.
- Relabeling standard arithmetic fields with IUT vocabulary is classified
  `IUT_ADDS_NO_NEW_CONSTRAINT`.
- Hashing the conventional fingerprint is also classified
  `IUT_ADDS_NO_NEW_CONSTRAINT`; a checksum is not a prediction.
- Without the domain map, Layer A remains useful but Layer B is
  `IUT_NOT_APPLICABLE`.

## Claim boundary

The implementation is an IUT-*inspired* runtime type discipline. It is not a
formalization of Hodge theaters, Θ-links, log-links, or multiradial algorithms.
It establishes no IUT theorem and no physics. Its positive result is limited to
preventing a concrete class of software errors: accidental identification of
values that belong to different frames.
