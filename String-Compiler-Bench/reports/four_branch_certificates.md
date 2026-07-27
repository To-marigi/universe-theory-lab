# Four branch certificates

| fibration | parent | independently derived roots | nonabelian algebra | MW | B-field / instanton evidence |
|---|---|---|---|---|---|
| standard | `E8xE8` | `E7+E7` | `e7+e7` | trivial | double-cover/signとpointlike-instanton関係はsource-backed |
| base-fiber-dual | `E8xE8` | `D6+E8` | `so(12)+e8` | trivial | fixed `II*` とgeneric avoidanceはsource-backed |
| alternate | `Spin32_Z2` | `A1+A1+D12` | `su(2)^2+so(24)` | `Z/2Z` | non-trivial quantized B-fieldはsource-backed |
| maximal | `Spin32_Z2` | `D14` | `so(28)` | trivial | alternateと異なるbranchであることはsource-backed |

各certificateには次を同時に保存する。

- exact Wilson representative
- search certificate
- root count
- Cartan matrix
- Dynkin components
- abelian rank
- local validity domain
- global-form、MW、B-field、instantonsの証拠境界

alternateとmaximalは低エネルギーgauge algebra文字列だけで同一視しない。特に
`Z/2Z` torsionとB-field記録を落とすmutationは失敗として検出する。

global gauge groupそのものはroot latticeとMW文字列だけから再構成していないため、
certificateの該当欄は `not independently reconstructed` を明記する。
