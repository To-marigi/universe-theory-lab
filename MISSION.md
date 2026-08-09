# MISSION

本プロジェクトの最上位目標は、固定背景時空を基礎入力としない量子力学的な
状態空間・観測量・力学を定義し、その巨視的相から時空、重力、物質を導出する
ことである。

## 必須の導出目標

1. 安定した3+1次元ローレンツ時空
2. 質量ゼロ、2偏極、スピン2の重力自由度
3. 全エネルギー運動量への普遍結合
4. 非線形Einstein方程式とEinstein-Hilbert作用
5. 曲がった時空上の量子場理論
6. ブラックホール熱力学、蒸発、ユニタリティー
7. 宇宙論的時空
8. 最終的には標準模型、真空選択、結合定数
9. 既存理論から自動的には出ない反証可能な予言

この9項目は縮小も削除もしない。以下の現行フェーズは、この目標へ到達するための
順序であって、目標の差し替えではない。

## 現行フェーズ（オーナー決定 2026-08-09）

### 決定の理由

Paper I v0.4.2 (`10.5281/zenodo.21861533`) までで、統一理論としての強い新規性は
出ていない。リポジトリ自身の
[`reports/v0.4.2_prior_art_and_related_work_audit.md`](reports/v0.4.2_prior_art_and_related_work_audit.md)
がその根拠を記録している。SR1 は Xu, arXiv:2607.26672 が self-adjoint slice で
より一般であり、SR2 は `reachable_span_rank=1` の到達不可視な分離、SR3b-A は
reconstruction slice 上の補題である。したがって当面の中心は、外部から読める
未解決問題を一つ閉じることに置く。

### 現行フェーズの中心

> **955 profile (strong GC + reachable-state MSR) を、witness ではなく
> obstruction 側を本命として決着させる。**

`955` を選ぶ理由は一つだけである。prior-art audit が、これを Xu が明示的に
open と書いた方向（non-self-adjoint / state-only covariance）との直接の重なり
として分類しているためである。どちらに転んでも「最近の論文が名指しした未解決
問題に答えた」という外部から検証可能な新規性になる。内部証明書の累積では
この可読性は得られない。

obstruction 側を本命とするのは、蓄積データがその方向を指しているためである。
**955 トラック固有の証拠**は、pure-lower ansatz の global no-go 証明と、
mixed-xy tangent scout に witness がないことに加え、
[`reports/v0.4.2_955_mixed_branch_closure.md`](reports/v0.4.2_955_mixed_branch_closure.md)
が宣言済み mixed ansatz の全解を17次元 pure-upper 可換族に分類したことである。
この分類は165個の非特異 occurrence を全検査し、remote / disconnected な
`x!=0,y!=0` 成分が同 ansatz 内に存在しないことまで認証する。
**隣接する SR2-V トラック**
では、bounded full-profile scout が 960 点で escape 0、固定状態 slice が
unit ideal ですべて潰れている。両者は別トラックの結果であり、SR2-V の証拠は
955 の証拠ではない。さらに
[`reports/v0.4.2_955_symmetry_orbit_reduction.md`](reports/v0.4.2_955_symmetry_orbit_reduction.md)
により組合せ的対称群が自明であることが確定したため、patch ごとの witness 探索は
131 個の独立な非線形問題に等しい一方、一様な obstruction 論証は patch 数に鈍感
である。

obstruction 本命という全体方針はなお計画上の賭けであって、full 955 の定理ではない。
mixed ansatz 内の remote / disconnected 成分は閉じたが、無制限 source-native
slack 系はその外側にあり open である。
[`reports/v0.4.2_955_slack_coverage_gap.md`](reports/v0.4.2_955_slack_coverage_gap.md)
は、mixed ansatz が476次元の有効 slack chart から少なくとも214本の独立な対角方向を
捨てることを認証した。したがって mixed 終端を一般 obstruction へ昇格してはならない。
続く
[`reports/v0.4.2_955_slack_term_preflight.md`](reports/v0.4.2_955_slack_term_preflight.md)
は476座標系をstream展開し、4,152非零式・101,200項・実測最大次数9と、core全体から
恒等的に消える16本のterminal slack方向を確定した。さらに
[`reports/v0.4.2_955_slack_csg_tangent.md`](reports/v0.4.2_955_slack_csg_tangent.md)
は既知の非特異CSG点でcore Jacobian rank 427・tangent次元49を得て、Q可換子微分の
core rowspace modulo rankが0、すなわちfirst-order escapeがないことを証明した。さらに
[`reports/v0.4.2_955_slack_csg_second_order.md`](reports/v0.4.2_955_slack_csg_second_order.md)
は49次元kernel上の3,985本の二次compatibility formが全て0で、全一次方向が二次まで
liftし、Q可換子24成分も全core lift上で二次まで消えることを証明した。これはCSG点の
局所formal結果に限り、三次・remote component・full 955はopenである。三次では二次補正の
49自由成分も保持し、20,825個の `z^3` と2,401個の `z*a`、計23,226候補monomialに対する
疎性とメモリをpreflightした。その結果、raw coreは371,687項、独立Jacobian basisは
31,761項・保守保存見積り約18 MB、従属行reduceの予測term visitsは約160万であった。
8 GiB内のfail-closed stream監査を認可し、次は3,985 compatibility formsとQ三次remainderを
実際にreduceする。dense 23,226-column戦略とgeneric solverは使用しない。

### 到達順序

1. **955 を閉じる。** 三終端 —
   `REACHABLE_VISIBLE_NONCOMMUTATIVE_WITNESS_CERTIFIED` /
   `REACHABLE_VISIBLE_NONCOMMUTATIVITY_OBSTRUCTED` /
   `REACHABLE_VISIBILITY_OPEN_RESOURCE_LIMIT` — のいずれかに到達する。
2. **721 profile (fixed-vector GC + strong MSR) を閉じる。**
   Eq. (112) で消去された20生成元を戻す native compiler を先に作る。
3. **`complete finite ON semantics lattice` を名乗る。** これを名乗れるのは
   955 と 721 の双方が profile-native に解決された場合だけである。
4. **その後にスケールアップする。** `n=5`、`d=3`、occurrence-OFF、singular、
   finite-to-infinite lifting。lattice 完成という言い切れる定理を得る前に
   これらへ散らばらない。

### 現行フェーズで名乗らないもの

- 上記1〜3の段階で「最終理論」「統一理論」に接近したとは書かない。
- `d=2`, `n<=4` の可換性補題を、必須導出目標の進捗として数えない。
- OFF、`n>=5`、singular、`d>=3` を含む無限定な complete classification。

## 手段と目的を分離する

- QG-Benchは連続時空回収の検証器であり、最終理論ではない。
- String-Compilerは双対性・UV整合性の検証器であり、最終理論ではない。
- IUT-inspired layerは不正な同一視を防ぐ型安全性機構であり、物理理論ではない。
- 量子因果情報模型は中心候補だが、検証前の仮説である。
- 弦理論、因果集合、ホログラフィー、テンソルネットワーク、スピンフォーム、
  群場理論、漸近的安全性は候補構成と反証の入力である。

## 禁止する近道

- Einstein方程式を入力し、出力として導出したと主張しない。
- 1+1次元のスカラー伝播を重力子の導出と呼ばない。
- 既知のSpin-2射影子を再現しただけで候補模型がSpin-2を創発したと数えない。
- 数値フィットだけでゲージ対称性、2偏極、ゴースト不在を認定しない。
- 低エネルギーGRを再現しただけで最終理論と呼ばない。
- 既知理論の局所的な再現を停止条件なしに続けない。
- bounded ansatz の no-go を一般 obstruction に昇格しない。
- scout の非発見を obstruction の証明として記録しない。

全ゲートが通るまでは、科学的な最終判定を `FINAL_THEORY_OPEN` とする。
現行フェーズの完了はこの判定を動かさない。
