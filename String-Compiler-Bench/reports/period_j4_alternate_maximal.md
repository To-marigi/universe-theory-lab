# J4 alternate / maximal period certificate

After specialization/rescaling, both inputs are exactly Equation (3.4); their
input hashes agree. At 256 bits the marking is:

```text
M = [[-1, 0, 0, 0, 0], [0, -1, 0, 0, 0], [0, 0, -1, 0, 0], [0, 0, 0, -1, 0], [0, 0, 0, 0, -1]]
det(M) = -1
```

The global sign is a cycle-orientation change and does not change the period
line. Exact Gram isometry and certified period overlap recur at 512 and 1024
bits. A 128-bit maximal run was rejected after monodromy integer recognition
failed; it was not promoted.
