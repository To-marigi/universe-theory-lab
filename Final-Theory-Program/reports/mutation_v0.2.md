# Mutation report v0.2

Eight registered mutations are detected:

1. missing transitive closure;
2. acyclicity violation;
3. isomorphic duplicate;
4. omitted/incorrect automorphism factor;
5. natural labeling counted as a physical state;
6. spectator-set misidentification;
7. precursor-set misidentification;
8. growth order called external physical time.

The first three use explicit malformed relations/catalogs. The automorphism
check verifies orbit–stabilizer equality. The labeling check distinguishes the
one natural labeling of a chain from the six of an antichain while retaining
five unlabeled physical states at `n=3`. Precursor and spectator sets must be
disjoint and partition the source vertices.
