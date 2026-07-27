# Exact finite-causet enumerator

The production algorithm adjoins one maximal element above every down-set,
canonicalizes every result under all vertex permutations, and deduplicates by
the minimal row-major relation code.

Exact unlabeled counts are:

| cardinality | count |
|---:|---:|
| 0 | 1 |
| 1 | 1 |
| 2 | 2 |
| 3 | 5 |
| 4 | 16 |
| 5 | 63 |

An independent oracle enumerates all forward relation masks, rejects
non-transitive relations, and canonicalizes the survivors. It agrees with the
production set through `n=4`.

Each move records precursor and spectator sets, automorphism orbit size,
stabilizer order, the exact orbit/automorphism factor as a `Fraction`, and the
target unlabeled history. Natural-label multiplicity is metadata, not a count
of physical states.

The declared completeness limit is `n=5`; larger exact enumeration is
`RESOURCE_BLOCKED`, not silently truncated.
