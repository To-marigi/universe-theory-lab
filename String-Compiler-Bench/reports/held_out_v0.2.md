# Held-out v0.2

実行前に固定したexact fixturesを使い、scale、符号branch、許容誤差を再調整しない。

| case | 状態 | 結果 |
|---|---|---|
| generic point | exact rational/integer | PASS |
| `J4=0` | exact | PASS |
| `J4=J5=0` | exact | PASS |
| `a=0` | `a_squared=0` としてexact | PASS |
| branch singularity nearby | `gamma=1/1000` を固定 | PASS |
| `J30=0` | independent `J30` 未実装 | BLOCKED |

weighted-projective scalingはweights `(2,3,4,5,6)` による同値として検査し、
代表値の単純な数値一致を要求しない。

5/6 fixturesはPASSしたが、`J30` とperiod-oracle側held-outがないため、held-out全体は
`PARTIAL` とする。これによりv0.2全体のscientific statusをPASSへ引き上げない。
