# Handoff — 955 profile track, 2026-08-09/10 session

これを読む前に `HANDOFF_v0.4.1.md` の冒頭（Paper I v0.4.2 公開済みの注記）を
読むこと。`HANDOFF.md` は v0.3.9 リリースの凍結記録であり、本文書はそれを
置き換えない。

本文書は **955 profile (`strong_GC + reachable_state_MSR`) トラック**の
運用引き継ぎである。このセッションで研究の中心方針が変わり、六つのゲートが
閉じた。`HANDOFF_v0.4.1.md` の後半にある「次は 131 patch を symmetry で
reduce してから scout する」という趣旨の記述は、本文書が上書きする。

---

## 1. まず結論

```
方針転換      オーナー決定 2026-08-09。MISSION.md に現行フェーズ節を追加済み
中心          955 を obstruction 側本命で決着させる → 721 → finite ON lattice
新ゲート1     対称性・軌道簡約   NEGATIVE TERMINAL（対称群は自明、patch 削減 0）
新ゲート2     大域双線形簡約     262 → 46 パラメータ、局所化なし solver なし
新ゲート3     mixed枝閉包         46 → 43 → 厳密17次元 pure-upper 全解族
              Q可換子24成分は0、非特異165 occurrence全通過、mixed ansatz終端
新ゲート4     slack coverage gap  572 → 476、mixedがdirect rank 214方向を捨てる
              導来obligation 48、構文次数上限11、full 955はopen
新ゲート5     streamed term count  4,152非零entry、101,200項、exact degree 9
              exact linear式0、terminal slack blind direction 16本
新ゲート6     CSG tangent audit     core rank 427、tangent dim 49
              Q gradient raw rank 6 / modulo core rank 0、first-order escapeなし
次ゲート      49次元kernel上の二次compatibility obstruction + Q二次escape
全体判定      FINAL_THEORY_OPEN（不変。更新禁止）
```

---

## 2. 方針転換の内容と根拠

オーナーが Paper I v0.4.2 の新規性不足を認識し、`MISSION.md` の書き換えを
承認した。9つの必須導出目標と「禁止する近道」は保持したまま、現行フェーズ節を
追加してある。

中心を 955 に置く理由は一つだけである。
`reports/v0.4.2_prior_art_and_related_work_audit.md` が、955 を **Xu,
arXiv:2607.26672 が明示的に open と書いた方向**（non-self-adjoint / state-only
covariance）との直接の重なりと分類している唯一の項目だからである。どちらに
転んでも外部から読める新規性になる。

obstruction 側を本命とするのは蓄積データがその方向を指すためだが、**これは
賭けであって定理ではない**。証拠の帰属を混同しないこと:

- **955 トラック固有**: pure-lower ansatz の global no-go 証明、mixed-xy tangent
  scout の witness 不在、本セッションの対称群自明性。
- **隣接 SR2-V トラック**: bounded full-profile scout 960点 escape 0、固定状態
  slice の unit ideal。**これは 955 の証拠ではない。**

witness が出た場合はそちらを終端として受け入れる。

---

## 3. ゲート1: 対称性・軌道簡約（否定的終端）

```
artifact  results/v0.4.2_955_symmetry_orbit_reduction.json
report    reports/v0.4.2_955_symmetry_orbit_reduction.md
module    src/universe_lab/final_theory/source_native_955_symmetry_orbit_reduction_v042.py
digest    df2103fd7a4c7c62b525df8cf1ec0e37ae5d394454706a8f1250606d6f8fa05b
verdict   V042_955_SYMMETRY_GROUP_TRIVIAL_NO_PATCH_REDUCTION_CERTIFIED
          V042_955_MIXED_GAUGE_TORUS_GRADING_CERTIFIED
```

```powershell
uv run python -m universe_lab.final_theory.source_native_955_symmetry_orbit_reduction_v042
uv run pytest tests/final_theory/test_v042_955_symmetry_orbit_reduction.py -q
```

### 3.1 ゲージトーラス（確定・再利用可能）

`g_t = diag(t,1)` の共役が mixed ansatz `A_e=[[p_e,x_[e]],[y_[e],1]]` を保つ。
機械証明書は `deg_x - deg_y` の `Z`-次数付けで、成分 `(i,j)` が次数 `j-i`、
到達状態ベクトル残差の成分 `i` が次数 `-i`。行列3ブロック 22,180 項、
ベクトル 986 項、Q可換子 48 項を検査して**違反 0**。

ベクトル側の均一性が、同時に「準備ベクトル `= e_1`」の機械検査になっている。

**この次数付けが後続の全ての土台である。** ゲート2はここから出た。

再利用時の注意:

- 縮約効果は**大域パラメータ1個だけ**。辺ごとではない。
- **トーラスが ansatz の完全な安定化群とは主張していない。**
- **トーラス退化で pure 族には落ちない。** 重みが `x:+1 / y:-1` なので
  `t→0` で `x→0` かつ `y→∞`。pure-lower の global no-go を退化で mixed へ
  延長する近道は存在しない。

### 3.2 組合せ的対称群（自明）

131 orbit / 1,127 方程式の二部接続構造を equitable refinement した結果、
初期23色が1ラウンドで131色に離散化し安定。彩色は真の対称軌道の粗化なので、
離散 ⟹ 対称群は自明。

**したがって 131 patch は互いに非互換で、対称性による削減は 0。**

健全性の境界:

- 認証したのは**単語レベルの組合せ的対称性のみ**。多項式レベル・非線形な
  多様体自己同型は分類していない。
- 非離散だった場合はクラスは軌道ではなく上界にすぎない。今回は離散なので
  明示置換証明書は不要（発行数 0）。

---

## 4. ゲート2: 大域双線形簡約（本セッションの主成果）

```
artifact  results/v0.4.2_955_global_bilinear_reduction.json  (4.1 MB, 縮約多項式を全収録)
report    reports/v0.4.2_955_global_bilinear_reduction.md
module    src/universe_lab/final_theory/source_native_955_global_bilinear_reduction_v042.py
digest    38b648b62ad893768285aa17ff282d60e35d26fea03798ccb56f7593b2a5e7d5
verdict   V042_955_GLOBAL_BILINEAR_REDUCTION_262_TO_46_CERTIFIED_NONTERMINAL
```

```powershell
uv run python -m universe_lab.final_theory.source_native_955_global_bilinear_reduction_v042
uv run pytest tests/final_theory/test_v042_955_global_bilinear_reduction.py -q
```

### 4.1 中心的な構造事実

トーラス次数より細かい**二重次数** `(deg_x, deg_y)` を凍結済み manifest 上で
実測すると、CPOBC ブロックは次の通り:

| CPOBC 成分 | 二重次数 | 項数 |
|---|---|---|
| `00` | `(1,1)` のみ | 1,642 |
| `01` 右上 | `(1,0)` のみ | 2,831 |
| `10` 左下 | `(0,1)` のみ | 2,831 |
| `11` | `(1,1)` のみ | 1,642 |

**CPOBC の非対角ブロックは mixed ansatz 全体で厳密に線形**である。右上は `x` の
定数係数線形形式で `y` を含まず、左下は `y` の定数係数線形形式で `x` を含まない。
基点まわりの線形化ではなく恒等式であることを間違えないこと。

両係数行列は `783 × 131`、rank 108、nullity 23。これは凍結済み
`v0.4.2_955_mixed_xy_tangent_scout.json` の
`exact_linear_blocks.{upper,lower}.ranks.CPOBC = 108` と一致する（成果物に
照合フィールドあり）。

### 4.2 帰結

**CPOBC だけで、局所化も patch 分割も solver も使わず、大域的に
`x ∈ K_x (23次元)`, `y ∈ K_y (23次元)` が強制される。**

```
262 パラメータ → 46（s0..s22, t0..t22）→ ゲージを法として 45
```

自己検査: 得た核へ代入すると CPOBC 非対角の **1,566 成分が全て恒等的に消える**
（failures 0）。核が正しいことの独立検査になっている。
トーラス次数も縮約座標 `s:+1 / t:-1` で保たれる（違反 0）。

### 4.3 縮約系の実測サイズ

| ブロック | 残存成分 | 総項数 | 最大項数/成分 | 次数分布 |
|---|---|---|---|---|
| CPOBC | 954 | 1,814 | 3 | 2:954 |
| strong_GC | 932 | 7,150 | 19 | 1:2, 2:30, 3:464, 4:436 |
| reachable_MSR_vector | 47 | 593 | 28 | 1:3, 2:7, 3:21, 4:16 |
| **合計** | **1,933** | **9,557** | 28 | 最大次数 4 |

簡約前の source-native manifest は 262 変数・29,994 項。

**Q 可換子（標的）は 24 成分 / 60 項。恒等的に零ではない。**
したがって本簡約から可換性は従わない。しかし標的が 46 変数・60 項まで縮んだ
ことが、obstruction 論証の実装可能性を変えた。

### 4.4 副産物: 1次部分は rank 3

縮約系に斉次1次形式が5本あり、厳密ランク3。変数は `s19, s21, t19, t21` のみ:

```
strong_GC 01           :  2*s19 - 6*s21 = 0
strong_GC 10           : -1/2*t19 + 6*t21 = 0
reachable_MSR_vector 1 :  t19 + 4*t21 = 0
reachable_MSR_vector 1 :  7/2*t19 + 6*t21 = 0
reachable_MSR_vector 1 :  1/2*t19 + 26*t21 = 0
```

`t` 側4本は2変数に対して rank 2（第1・第2式の行列式 `-8`）→ **`t19 = t21 = 0`**。
`s` 側 → `s19 = 3*s21`。残りパラメータの上界 **43**。

**この消去は実行していない**（`eliminated_here: false`）。測定として記録した
だけである。

---

## 5. ゲート3: rank 3 消去・CPOBC枝閉包・非特異条件（mixed ansatz終端）

```
artifact  results/v0.4.2_955_mixed_branch_closure.json
report    reports/v0.4.2_955_mixed_branch_closure.md
module    src/universe_lab/final_theory/source_native_955_mixed_branch_closure_v042.py
digest    9316c624c589131120447e5399d8b77603f73d99c0b71258f8da1c197958a867
verdict   V042_955_MIXED_ANSATZ_17D_PURE_UPPER_COMMUTATIVE_TERMINAL_CERTIFIED
```

```powershell
uv run python -m universe_lab.final_theory.source_native_955_mixed_branch_closure_v042
uv run pytest tests/final_theory/test_v042_955_mixed_branch_closure.py -q
```

### 5.1 46 → 43 と可換子の消滅

保留されていた rank 3 を実際に消去した。

```
s19 = 3*s21,  t19 = 0,  t21 = 0
```

この代入だけで、前段のQ可換子 **24成分 / 60項は全て恒等的に0**。したがって
宣言済み mixed ansatz の955解は全て可換であり、CPOBC枝分けはこの可換性結論には
不要である。

### 5.2 CPOBCは5単項式だけ

954本の対角式は870本が恒等的に消え、残る84本は次の5式の非零スカラー倍だけ:

```
s21*t11 = s21*t15 = s21*t16 = s21*t18 = s21*t22 = 0
```

出現数は順に16, 13, 13, 30, 12。各単項式に元のCPOBC選択式を束縛済み。

### 5.3 全解分類

`s21!=0` 枝ではCPOBCが上の5個の`t`を消し、残る63本は全て1次式、rank 21。
`s21=0` 枝では結合1次rank 26。二枝は次の単一17次元 pure-upper 線形族に合流する:

```
all t = 0
(s11,s15,s16,s18,s21,s22) = (15,12,12,14,1,12)*u
free: s0,s1,s2,s3,s4,s5,s6,s7,s8,s9,s10,s12,s13,s14,s17,s20,u
```

`s21=0` 枝は `u=0` の16次元超平面。一般17パラメータ点で縮約系1,933成分を
全検査して failures 0。これにより tangent scout が open とした
remote/disconnected `x!=0,y!=0` mixed component は**存在しない**と確定した。

### 5.4 非特異条件

131因子を43変数へ実際に再コンパイル。rank 3 消去だけで88因子が定数非零、
43因子（元の50 occurrence、異なる多項式26個）が可変のまま残る。しかし最終族は
全 `y=0` なので、全因子は `p_e in {1/16,1/8,1/4,1/2}` に戻る。
**165 source occurrence 全て通過、failures 0。**

### 5.5 ゲート4へ引き渡した手順

mixed ansatz をさらに解く作業は不要。`CURRENT_RESEARCH_STATE.json` の次ゲートは
無制限 source-native slack 系へ戻し、次の順に固定した。

1. mixed ansatz が捨てた自由度と coverage gap を明示する。
2. 無制限系の次数分布と厳密線形ブロックを solver なしで測る。
3. source-profile coverage certificate と版付き budget artifact が揃った場合だけ
   solver 実行を再検討する。

heavy solver は引き続き凍結（`solver_run_permitted: false`）。ここまでの三ゲートは
Gröbner 0、saturation 0、有限体 0、数値 0、Sage 0 で完了。

---

## 6. ゲート4: 無制限 slack coverage gap と次数上限

```
artifact  results/v0.4.2_955_slack_coverage_gap.json
report    reports/v0.4.2_955_slack_coverage_gap.md
module    src/universe_lab/final_theory/source_native_955_slack_coverage_gap_v042.py
digest    19ec4466745981dc1fa1d91b945b81212f2215aa7be924b9857368f46c7b4f71
verdict   V042_955_SLACK_COVERAGE_GAP_214_NORMALS_DEGREE11_CEILING_CERTIFIED
```

```powershell
uv run python -m universe_lab.final_theory.source_native_955_slack_coverage_gap_v042
uv run pytest tests/final_theory/test_v042_955_slack_coverage_gap.py -q
```

### 6.1 572 → 476 の厳密 slack chart

131個の一般 `2x2` quotient matrix は524 scalar entries。reachable-state MSR の
二次元 annihilator parameterisation `R=u(Jv)^T` が48 slack coordinates を加えるため、
出発点は572座標。24個の timid definition は互いに異なる matrix を monic triangular
に定義し、96 entries を厳密に消去する。したがって有効 chart は **476座標**である。

非特異 source transition と `Omega!=0` により全到達状態は非零なので、`v0!=0` と
`v1!=0` の二 patch が reachable-state MSR locus を覆う。これは局所線形化ではない。

### 6.2 mixed ansatz が捨てた自由度

timid 24個を除く107個の独立 matrix に mixed 対角 `(p_e,1)` を課すと、異なる自由
座標 `00/11` を固定する214本になる。よって **direct exact rank 214**、
`476-214=262` で mixed manifest の `x/y` ambient 数と一致する。

消去された24 timid matrix の対角形は、さらに48本の導来 obligation として残る。
この48本のランクは測っていない。従って mixed locus は少なくとも余次元214であり、
mixed 終端を稠密性で無制限系へ昇格できない。適用体を混同しないこと: この coverage
gap の構造計数は標数0、引用する前段 mixed terminal verdict は **`QQ` 限定**である。

### 6.3 streamed expansion 前の次数上限

timid recurrence を非循環順に伝播した構文的上限は、state 7、timid matrix 8、
raw CPOBC 5、strong GC 11。相殺後の厳密次数ではない。scalar polynomial expansion は
0回で term count は未測定、solver も全種0回。

### 6.4 新しい次ゲート

次は **476座標 timid-eliminated 系の streamed term-count-only preflight**。式全体を
保持せず、block別 scalar equation / nonzero term 数、実測次数、係数 bit 長、項数分位点、
peak memory 見積りだけを出す。その後に版付き expansion budget を作る。この二つが
揃うまで heavy solver を開始しない。full 955 は `OPEN` のまま。

このpreflightはゲート5として完了した。版付き予算より先に、そこで見つかった16本の
blind directionを含むCSG基点tangent auditへ進む。

---

## 7. ゲート5: 476座標 streamed term-count preflight

```
artifact  results/v0.4.2_955_slack_term_preflight.json
report    reports/v0.4.2_955_slack_term_preflight.md
module    src/universe_lab/final_theory/source_native_955_slack_term_preflight_v042.py
digest    b61d611830ff89815b9046b8df3a8b284f6716cdeb687c4d2bb7bb960e5190ab
verdict   V042_955_SLACK_STREAMED_TERM_PREFLIGHT_CERTIFIED_NO_SOLVER
```

```powershell
uv run python -m universe_lab.final_theory.source_native_955_slack_term_preflight_v042
uv run pytest tests/final_theory/test_v042_955_slack_term_preflight.py -q
```

### 7.1 exact scalar census

`Omega=e1` を unrestricted `GL_2` chart の基底正規化として用いた。24 timid matrixと
24 stateだけを保持し、783 CPOBC + 320 strong-GCを1 blockずつ展開・hash・破棄した。

```text
matrix blocks       1,103
scalar slots        4,412
nonzero entries     4,152
zero entries          260
exact terms       101,200
max terms/entry      3,723
exact max degree         9
```

CPOBCは3,132 entryすべて非零、18,836 terms、最大24 terms、degree 4。strong GCは
1,020非零 / 260 zero、82,364 terms、最大3,723 terms、degree 9。前ゲートの構文上限
5 / 11より実測4 / 9まで下がった。full polynomial manifestは保持していない。

完全に次数1以下の非零式は0本。全式の次数1成分だけは772 rows / rank 304だが、
これは非特異でない原点のJacobian planning dataにすぎず、exact eliminationではない。

### 7.2 16本のterminal slack blind direction

476座標中460だけがcoreに現れる。残る16本は

```text
p4-0000, p4-000e, p4-00cc, p4-00ce,
p4-0888, p4-088e, p4-08cc, p4-08ce
```

の各 `u:c:0`, `u:c:1`。CPOBCとstrong GCの全多項式supportから恒等的に消える。
ただしこれらはterminal timid slackであり、別のgregarious matrixから定義される
`Q1,...,Q4` の非可換性を単独では証明しない。

### 7.3 非特異条件と資源判断

131 determinantは全て非零多項式、合計6,250 terms、最大986 terms、degree 5。
別inverse座標によるlocaliserは131座標・131式・6,381 terms、degree 6。入力全保持の
portable compact modelは3,376,080 bytesだが、degree 9 / 476変数のsolver basis growthは
予測できない。stream expansion 1回、full manifest 0、全solver 0。

### 7.4 新しい次ゲート

既知の非特異対角CSG解を476 slack coordinatesへ逆写像し、その点でcore Jacobian
kernelと6個のQ可換子微分を同時に測る。16 blind directionも明示的に含める。
Q tangent escapeがあればformal deformation候補へ進み、なければ高次の局所obstruction
を設計する。generic solverと版付きbudgetはその判断まで凍結。

この監査はゲート6として完了し、全first-order escapeがblockされた。次は二次監査。

---

## 8. ゲート6: 非特異CSG点のQ tangent escape監査

```
artifact  results/v0.4.2_955_slack_csg_tangent.json
report    reports/v0.4.2_955_slack_csg_tangent.md
module    src/universe_lab/final_theory/source_native_955_slack_csg_tangent_v042.py
digest    3182718cc0424dcc7837c8f2cc3dd03e6b27c0c106f9dbbb378b936c5e50e382
verdict   V042_955_SLACK_CSG_Q_TANGENT_ESCAPE_FIRST_ORDER_BLOCKED_CERTIFIED
```

```powershell
uv run python -m universe_lab.final_theory.source_native_955_slack_csg_tangent_v042
uv run pytest tests/final_theory/test_v042_955_slack_csg_tangent.py -q
```

### 8.1 CSG点のslack inverse image

全source matrixを `diag(p_e,1)` にする476座標を厳密に再構成。24 sourceすべてで
`u:c:0=0`, `u:c:1!=0`、特に `u:p1-0=(0,1)`。よって基点は `N!=0` open上。
全131 determinantは `p_e in {1/16,1/8,1/4,1/2}` でfailures 0。

### 8.2 core Jacobian

```text
CPOBC       2,870 nonzero rows, rank 381
strong GC   1,020 nonzero rows, rank 180
combined    3,890 nonzero rows, rank 427
tangent dimension = 476 - 427 = 49
```

全4,412 scalar slotのCSG点評価はfailures 0。前ゲートのpolynomial stream digestとも一致。

### 8.3 Q可換子の一次 obstruction

6可換子・24 entriesのうちgradient非零は12 rows、raw rank 6。しかしcore Jacobian
echelonへ全12 rowsをreduceするとremainders 0、追加rank 0。従って49次元kernelの
全方向で `d[Qi,Qj]=0`。16 terminal blind directionも全てQ-silent。

これは**一次だけ**。`[Qi,Qj]=O(t^2)` のcurveを否定しない。exact witnessや局所
obstructionへ昇格してはならない。

### 8.4 新しい次ゲート

49次元kernel `K` 上で `x=x_CSG+tKz+t^2w` を代入し、二次core compatibility
`Jw + H[Kz,Kz]/2=0` とQ可換子の二次項をstream計算する。left-kernel obstructionを
先に取り、full Hessian tensorは保持しない。二次Q escapeがcompatibilityを通る場合だけ
higher-order liftingへ進む。generic solverは凍結。

---

## 9. 破棄された計画

**「131 patch を構造的基準で選んで exact scout する」は不要になった。**
ゲート2が patch を一つも開かずに探索空間を落としたため。ゲート1の成果物に
`deterministic_scout_schedule`（先頭8件、`executed: false`）が残っているが、
これは当時の予定表であり、現在の推奨経路ではない。

---

## 10. 罠 — 範囲と後続で踏みやすい点

- **ゲート2の46変数系だけには非特異条件が入っていない。** ただしゲート3は
  `det(A_e) = p_e - x_[e]*y_[e] != 0` を131因子・165 occurrence 全て持ち込み、
  最終17次元族で failures 0 を認証した。ゲート3まで引用する場合、この穴は
  mixed ansatz 内では閉じている。無制限 slack 系へ自動転用してはならない。
- **`Eq113` / `Eq139` の分岐は縮約系に入っていない。** 955 profile の
  common core（CPOBC + strong_GC + reachable_state_MSR）だけである。
  full witness には別途必要（`mixed_xy_tangent_scout` の
  `full_witness_gates_not_run` を参照）。ただし mixed ansatz 内では common core
  だけで既に全Q可換なので、追加分岐が非可換 witness を復活させることはない。
- **`reachable_MSR_operator` と `reachable_MSR_vector` を取り違えないこと。**
  955 は **vector**（到達状態上）。operator ブロックは強い意味論のもので、
  こちらは mixed でも `(0,1)` のみ＝厳密線形だが、955 では使えない。
  この取り違えは「955 も CPOBC+MSR で rank 131 になる」という誤結論を生む。
- **`mixed ansatz` は宣言された族であって一般 `GL_2` ではない。** 無制限の
  source-native slack 系（572 スカラー）は本簡約の外側にある。
- ゲート1の verdict 文字列 `NO_PATCH_REDUCTION_CERTIFIED` は無条件に見えるが、
  §3.2 の通り単語レベル限定である。引用時は範囲を付けること。

---

## 11. 既存の不具合（本セッション由来ではない）

```
5 failed, 8 errors — tests/final_theory/test_line_ending_bridge_v038.py
                     tests/final_theory/test_reproduce_v037.py
                     tests/final_theory/test_reproduce_v038.py
                     tests/final_theory/test_reproduce_v039.py
根本原因  references/manifest.json: recorded current_raw_sha256 does not match
          repository bytes   (src/universe_lab/artifact_migration_v038.py:491)
```

`git stash -u` したクリーンツリーでも同一件数で再現することを確認済み。
本セッションの変更由来ではない。おそらく 2026-08-01 の prior-art audit で
14 PDF を追加した際に bridge を再ビルドしていない
（`HANDOFF.md` §8 の既知トラップ「manifest-tracked file を編集して manifest を
再ビルドしない」）。

**凍結成果物の中の digest を書き換えて通してはならない**（`HANDOFF.md` §7-1）。
`results/v0.3.8_line_ending_bridge.json` の設計は legacy hash を保ったまま
bridge する方式である。

`MISSION.md`, `CURRENT_RESEARCH_STATE.json`, `HANDOFF*.md` は v0.3.9 リリース
マニフェストに**含まれない**ことを確認済み（`references/manifest.json` と
`README.md` は含まれる）。本セッションの編集はマニフェストを動かしていない。

---

## 12. 検証コマンド（コスト順）

```powershell
uv run ruff check .
uv run pytest tests/final_theory/test_v042_955_symmetry_orbit_reduction.py tests/final_theory/test_v042_955_global_bilinear_reduction.py tests/final_theory/test_v042_955_mixed_branch_closure.py tests/final_theory/test_v042_955_slack_coverage_gap.py tests/final_theory/test_v042_955_slack_term_preflight.py tests/final_theory/test_v042_955_slack_csg_tangent.py -q
uv run pytest -q
```

六ゲートの新規テストは 48 件。うち独立検証として、核基底を manifest の生の行と直接
内積で検査するもの（`test_kernel_basis_is_independently_verified_against_the_manifest_rows`）と、
二重次数を成果物を介さず manifest から再計測するもの、一般17パラメータ族で
1,933成分を再代入するもの、timid recurrence から次数 histogram を再構成するもの、
24 timid residualをreachable stateへ再作用して48成分の零を再検査するもの、
3,890 raw core Jacobian rowsへ12 Q-gradient rowsを再reduceするものを含む。

---

## 13. AI 開示

ゲート1・2と `MISSION.md` の現行フェーズ節は Anthropic Claude、ゲート3・4・5・6の
モジュール・テスト・報告・引き継ぎ更新は OpenAI Codex が作成した。Luna は
読み取り専用のブランチ／不要ファイル棚卸しと、ゲート4の数値・digest・適用体境界の
独立再検算、ゲート5で再利用可能な疎多項式・stream・budget実装の探索を担当した。
人間の著者が範囲を選択し内容に責任を負う。
`CONTRIBUTING.md` の「どのツールがどの部分か」要件に対応する記録である。

`.zenodo.json` と `paper/paper.md` の開示は**触っていない**。両者は凍結
アーカイブのダイジェストに影響するため、次にアーカイブを再構築する版で
まとめて更新すること（`HANDOFF.md` §10）。
