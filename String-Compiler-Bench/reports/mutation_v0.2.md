# Mutation v0.2

## 結果

12/12 detected。要求されたcritical gate 8/8を満たす。

| mutation | detector |
|---|---|
| E8 root欠落 | parent root count 240 |
| massless conditionの符号/offset破壊 | exact surviving-root set比較 |
| U(1) rank無視 | `16 - semisimple_rank` |
| orbitとraw coordinateの同一視 | distinct type / identifier policy |
| `a=±sqrt(...)` の統合 | sign branch比較 |
| MW `Z/2Z` 無視 | alternate certificate |
| B-field branch反転 | alternate/maximal metadata inequality |
| standard/base-fiber-dual交換 | independently derived root systems |
| alternate/maximal交換 | independently derived root systems |
| validity domain外inverse | local-only domain gate |
| weighted-projective scale固定 | weighted equivalence test |
| period cycle basis誤変換 | intersection-form preservation |

これはsoftware mutation coverageのPASSであり、period bridgeの科学的PASSではない。
特にsource-backed B-field metadataのmutationを検出できても、そのB-field classを
root enumerationから独立導出したことにはならない。
