# Narain–period source audit

## 一次資料

- Clingher–Hill–Malmendier,
  [arXiv:2205.08100v1](https://arxiv.org/abs/2205.08100v1):
  two-Wilson-line部分空間、`J2,...,J6`、四つのF-theory fibration、
  heterotic branch対応の主資料。
- Clingher–Hill–Malmendier,
  [arXiv:1908.09578](https://arxiv.org/abs/1908.09578):
  generic K3がちょうど四つの非同値Jacobian elliptic fibrationを持つこと、
  fiber構成とMordell–Weil群の数学的分類。
- Mohaupt,
  [arXiv:hep-th/9209101](https://arxiv.org/abs/hep-th/9209101):
  Dynkin diagramを使ったheterotic toroidal compactificationのcritical Wilson line構成。
- Groot Nibbelink–Vaudrevange,
  [arXiv:1703.05323](https://arxiv.org/abs/1703.05323):
  metric、B-field、Wilson lineを含むNarain moduliとT-duality群のレビュー。

## 導出と引用の境界

| 対象 | v0.2での扱い |
|---|---|
| `E8`、`D16` roots | exact arithmeticで独立生成 |
| `q·A_i ∈ Z` root sector | 局所・zero-winding gauge-root条件として実装 |
| simple roots / Cartan / Dynkin型 | 列挙rootから自動導出 |
| 四branchの目標gauge algebra | `2205.08100v1`から事前登録 |
| MW torsion、B-field、instantons | source-backed metadata。root列挙から導出したとはしない |
| `J2,...,J6` と四Weierstrass模型 | 論文式の独立な記号代入・判別式検査 |
| K3 period integration | 未実装 |
| `O+(L^(2,4))` orbit reduction | 未実装 |
| global gauge-group form | 未再構成 |

`local Wilson representative -> sourceで同定されたfibration` の結合は、同じ
gauge algebraを得ただけでは証明されない。このためbranch certificateは、独立導出した
root dataと、一次資料から付与したMW/B-field/instanton dataを別のevidence文で保持する。

## 許される主張

- `LOCAL_HETEROTIC_LOWERING_PASS`
- `FOUR_F_THEORY_FIBRATIONS_SYMBOLICALLY_CHECKED`
- `GLOBAL_WILSON_COORDINATES_NOT_DEFINED`
- `PERIOD_ORACLE_BLOCKED`

`KNOWN_8D_DUALITY_REPRODUCED` は、独立period oracleとorbit round-tripがないため許されない。
