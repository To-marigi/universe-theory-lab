# Handoff — 955 profile track, 2026-08-09/10 session

> **2026-08-10 追補 — 計画の三段階化と jet 梯子の破棄。**
>
> オーナーが `MISSION.md` に**三段階の計画**を固定した。段階A（955 → 721 →
> finite ON lattice）**の完了をもって本プロジェクトを終了**し、その後に段階C
> （検証方法論を独立した成果物にする）、最後に段階B（必須導出目標へ向け標的を
> 変える）へ進む。段階Aの完了は必須導出目標のどれにも到達しないことを承知の
> うえでの決定である。この認識を後から書き換えないこと。
>
> 同時に段階Aの**停止規則**が入った。「次数を1つ上げる作業を、有限の定理への
> 変換経路を示さずに続けない」。これにより第五次 jet preflight
> （候補単項式 4,014,962 本）は**破棄**され、代わりに
> [`reports/v0.4.2_955_upper_stratum.md`](reports/v0.4.2_955_upper_stratum.md)
> の有限ゲートに置き換わった。§12 を読むこと。四次まで沈黙が続いた理由は、
> CSG 基点で左下線形部が rank 107 フルランクであり形式陰関数定理で局所成分が
> upper stratum に入るから、と有限に説明がついた。

これを読む前に `HANDOFF_v0.4.1.md` の冒頭（Paper I v0.4.2 公開済みの注記）を
読むこと。`HANDOFF.md` は v0.3.9 リリースの凍結記録であり、本文書はそれを
置き換えない。

本文書は **955 profile (`strong_GC + reachable_state_MSR`) トラック**の
運用引き継ぎである。このセッションで研究の中心方針が変わり、既存の十九ゲートに
加えて三つの有限監査が追加された。
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
新ゲート7     CSG second order      3,985 compatibility forms全て0、全tangentが二次lift
              Q intrinsic quadratic forms 24/24で0、二次escapeなし
新ゲート8     third-order preflight full二次jet fiber、raw 371,687項、basis 31,761項
              bounded stream 5.67 GB < 8 GiB、dense 47.9 GBは却下
新ゲート9     CSG third order       3,985 compatibility forms全て0、全二次jetが三次lift
              raw Q 6/24非零だがintrinsic 24/24で0、三次escapeなし
新ゲート10    fourth-order preflight full三次jet fiber、raw 1,647,981項、basis 135,396項
              bounded stream 5.73 GB < 8 GiB、dense 682.77 GBは却下
新ゲート11    CSG fourth order      3,985 compatibility forms全て0、全三次jetが四次lift
              raw Q 6/24非零だがintrinsic 24/24で0、四次escapeなし
新ゲート12    無制限チャートの次数付け導出と upper stratum 分解（§12）
              47,298制約でrank 460・不整合0、A:*:01とu:*:0が重み+1
              {A:*:10=0} 上で (1,0)恒等零／(0,1)は123座標に厳密線形／対角は無汚染
              Q可換子6組が各4項の線形形式に崩壊。第五次preflightは破棄
新ゲート13    可換子 row-span 判定（§13）。判定文字列は計測前に固定
              一般結合CSGの検証済み4点すべてで rank(L)=114・ファイバー9・全IN_SPAN
              ただしCSG族は A:*:11 を1に固定するので第二対角は未探索
              WITNESS側の可能性は排除されていない。Q(t)記号消去は放棄
新ゲート14    成長族は core を結合について恒等的に満たす（§14.1）
              QQ(t0..t4) 上で core 4,152成分すべて恒等的に零、timid同一性24/24
              ゲート13の4点抽出が族の言明に格上げ。約16秒（消去せず代入+cancel）
新ゲート15    第二対角を動かした span 判定（§14.2）。ゲート13の限界を解消
              10点すべて core 検証通過・特異0・escape 0、うち4点は β 非定数（最大13値）
              鍵は timid 目標値を「その軌道自身の第二対角値」にすること
新ゲート16    Eq120が6組の可換子を1個のスカラーΛ=c_14に崩壊させる（§15）
              6組全てがΛの厳密スカラー倍（係数はa,dの2x2小行列式のみ）と記号証明
              3点で独立再計算しΛ=0を確認。row-span判定6本→スカラー問い1本に再定義
新ゲート17    非零QファイバーでΛ row-spanを監査（§16）
              4点のQ-visible kernel、ならびに QQ(t,s) の共通第二対角族で残差0
              D=s(t+13)/(2(t+15))、さらに非特異なD=0アンカー1点を直接監査
              ただし全S・D=0枝はopen
新ゲート18    localized row-module preflight（§17）
              scalar 246、非零scalar core 1814（相異1,504）、source localizer 131
              D14/D12/D13のrank-2 coverを固定、finite minor cover required、証明書未発行
新ゲート19    対称性のない独立8点でΛ row-span掃引（§16、自己訂正込み）
              罠: _lambda_at_point は b を常に0にするので数値評価は自明にΛ=0
              正しい row-span 判定で8点全てescape 0、うち7点D!=0
追加監査A      独立 character witness scout（64点）
              全64点がcore 4,152式・source determinant 131個を通過、D14!=0は54点
              54点すべてLambda escape 0、witness candidate 0、full Sはopen
追加監査B      rank-one character branch（93点）
              D12=D13=D14=0の有限格子を全監査、非スカラー12点を含む6可換子escape 0
              L rankは103（スカラー退化81点）または114（非スカラー12点）
追加監査C      localized minor finite preflight（38点）
              非Q119列中107列に構造的monomial matching、D14 sampleは2 minorで覆える
              D12/D13 anchor点も追加したが、I_S・source localizer上の証明書は未発行
計画          段階A（955→721→lattice）で本プロジェクト終了 → 段階C → 段階B
次ゲート      D12/D13/D14のlocalized row-module証明書を作るか、D!=0・Λ!=0のexact core fibreを探す
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

この監査はゲート6として完了し、全first-order escapeがblockされた。後続の二次監査も
ゲート7として完了し、全tangent directionが二次までliftする一方でQ escapeはなかった。

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

## 9. ゲート7: CSG点の二次compatibility・Q escape監査

```
artifact  results/v0.4.2_955_slack_csg_second_order.json
report    reports/v0.4.2_955_slack_csg_second_order.md
module    src/universe_lab/final_theory/source_native_955_slack_csg_second_order_v042.py
digest    2c84fa6af833e320fe9e292a359808a7fcc162e225ce30edf038b5d352ae35f0
verdict   V042_955_SLACK_CSG_SECOND_ORDER_ALL_TANGENTS_LIFT_Q_ESCAPE_BLOCKED_CERTIFIED
```

```powershell
uv run python -m universe_lab.final_theory.source_native_955_slack_csg_second_order_v042
uv run pytest tests/final_theory/test_v042_955_slack_csg_second_order.py -q
```

### 9.1 全tangent directionが二次までliftする

49次元tangent kernel `K` 上で `x=x_CSG+tKz+t^2w` とし、4,412 scalar core jetsの
組 `(J-row, quadratic-form)` をexact `QQ` で同時消去した。Jacobian rankは前ゲートと
同じ427。残る3,985 dependent-Jacobian rowsのcompatibility quadratic formsは**全て0**、
span rankも0。従って任意の一次方向 `z` に対してcoreを `O(t^3)` まで満たす `w` がある。

これはsmoothnessやformal arcの全次数liftを証明しない。三次でobstructionが出る可能性は
残る。

### 9.2 Qは全core lift上で二次まで消える

6可換子・24 scalar entriesを同じjet basisへreduceした。first-order Jacobian remainder 0、
nonzero intrinsic quadratic forms 0、rank modulo core compatibility span 0。よって任意の
core二次lift `(z,w)` で全Q可換子は `O(t^3)`。16 terminal slack blind directionsもcoreと
Qの二次monomial occurrence 0で、二次までsilentである。

### 9.3 実行境界と次ゲート

ambient Hessian tensorとfull scalar manifestは保持していない。Gröbner / saturation / finite
field / numerical / Sageは全て0。full 955は `OPEN`。

三次では `w=w_particular(z)+K a` の49個のfiber変数 `a` を落としてはならない。候補基底は
`C(51,3)=20,825` 個の `z^3` と `49^2=2,401` 個の `z*a`、計23,226。次は疎な三次jetを
直接走らせる前に、full second-order jet fiber上のterm数・basis growth・peak memoryの
versioned preflightを作る。安全なら三次core compatibilityとQ escapeへ進む。安全な8 GiB
budgetを立てられなければ、資源限界終端候補を記録して無理にsolverを走らせない。

このpreflightはゲート8として完了し、fail-closed三次監査が予算内と判定された。

---

## 10. ゲート8: full second-order jet fibre三次preflight

```
artifact  results/v0.4.2_955_slack_csg_third_order_preflight.json
report    reports/v0.4.2_955_slack_csg_third_order_preflight.md
module    src/universe_lab/final_theory/source_native_955_slack_csg_third_order_preflight_v042.py
budget    config/v0.4.2_955_slack_csg_third_order_budget.json
digest    a7cac5ae64b3debdc8c98e5df18ba739b87b37fca91715f9c5236f14b56cf490
verdict   V042_955_SLACK_CSG_THIRD_ORDER_FULL_JET_FIBER_PREFLIGHT_CERTIFIED
```

```powershell
uv run python -m universe_lab.final_theory.source_native_955_slack_csg_third_order_preflight_v042
uv run pytest tests/final_theory/test_v042_955_slack_csg_third_order_preflight.py -q
```

### 10.1 三次で保持すべきfiber

`z` だけを三次へ上げるのは誤り。二次補正は

```text
w = w_particular(z) + K a
```

で、49個のhomogeneous fibre変数 `a` を持つ。weight 3の候補は `z^3` 20,825個と
`z*a` 2,401個、計23,226。canonical `w_particular` は476座標中268 nonzero forms、
総5,111 quadratic terms、最大62項。全4,412 raw core二次式を再検査してfailures 0。

### 10.2 exact streamed census

```text
raw core third forms       2,706 nonzero / 4,412 slots
raw weighted terms         371,687 = 252,521 z^3 + 119,166 z*a
maximum raw terms/form     502
Jacobian basis forms       427
Jacobian basis terms       31,761
conservative basis bytes   18,010,624
predicted dependent visits 1,602,836
raw Q third forms          6 nonzero / 24 slots, 458 terms
```

Qの6 nonzeroは**raw**でありcore reduction前。escapeとは解釈しない。従属3,985行も
compatibility reduceしていないため、本ゲートに三次の科学的結論はない。

### 10.3 budget判定と実行規則

8 GiB hard limitに対し、10,000,000 compatibility-basis-term cap付きstream監査は
保守peak 5,673,132,544 bytes。dense worst caseは47,925,343,232 bytesなので禁止。
単一form 23,226項、source-term visits 200,000,000回、compatibility basis 10,000,000項の
いずれかへ達したらfail closed。予算内なので次の三次exact auditを認可した。

この監査はゲート9として完了し、compatibilityもQ intrinsic formsも全て0だった。

---

## 11. ゲート9: full second-order jet fibre三次exact監査

```
artifact  results/v0.4.2_955_slack_csg_third_order.json
report    reports/v0.4.2_955_slack_csg_third_order.md
module    src/universe_lab/final_theory/source_native_955_slack_csg_third_order_v042.py
digest    53d7818f4bff6e5d3c556cdb137644feeae73a4bde50f74d5cb84feb8db16bfa
verdict   V042_955_SLACK_CSG_THIRD_ORDER_ALL_SECOND_ORDER_JETS_LIFT_Q_ESCAPE_BLOCKED_CERTIFIED
```

```powershell
uv run python -m universe_lab.final_theory.source_native_955_slack_csg_third_order_v042
uv run pytest tests/final_theory/test_v042_955_slack_csg_third_order.py -q
```

### 11.1 全二次jetが三次までliftする

4,412 core third jetsをJacobian basisへ同時消去。427 independent rowsに対する3,985
dependent rowsのcompatibility weighted formsは全て0、span rank 0。従って任意の
`(z,a)`、すなわちfull second-order core jetに対して `Jv+r(z,a)=0` を解く `v` がある。

### 11.2 Qは全core third lift上で三次まで消える

raw Q third formsは6/24 entries非零、458 terms。しかしcore Jacobian third-jet basisへ
reduceするとintrinsic nonzero 0/24、span rank 0、compatibility modulo rank 0。従って
全core-compatible third jets上でQ可換子は `O(t^4)`。16 terminal blind directionsも
raw core/Q・intrinsic Q・remainderの全てでoccurrence 0。

### 11.3 次の四次preflight

三次補正を `v=v_particular(z,a)+K b`, `weight(b)=3` と書く。weight 4候補は

```text
z^4 270,725 + z^2*a 60,025 + a^2 1,225 + z*b 2,401 = 334,376
```

三次候補23,226の14倍超。直ちに四次reduceせず、canonical `v_particular` とraw weight-4
stream、Jacobian basis growth、8 GiB memoryを先にpreflightする。full 955は `OPEN`。
このpreflightとactual監査はゲート10・11として完了した。

---

## 11A. ゲート10: full third-order jet fibre四次preflight

```
artifact  results/v0.4.2_955_slack_csg_fourth_order_preflight.json
report    reports/v0.4.2_955_slack_csg_fourth_order_preflight.md
module    src/universe_lab/final_theory/source_native_955_slack_csg_fourth_order_preflight_v042.py
budget    config/v0.4.2_955_slack_csg_fourth_order_budget.json
digest    688641d2e301d154542ab0296aaff4a1f1d5c5abc32c67f594a679baffd4e6b7
verdict   V042_955_SLACK_CSG_FOURTH_ORDER_FULL_JET_FIBER_PREFLIGHT_CERTIFIED
```

canonical三次補正は268/476 coordinate formsが非零、28,033 weighted terms、最大360項。
`v=v_particular(z,a)+K b` 上でraw weight-4 core streamは1,647,981項、最大2,376項。
427 Jacobian basis jetsは135,396項、保守71,071,744 bytes。従属行の予測visitsは
6,797,996回。10,000,000-term compatibility cap込みの監査見積りは5,726,193,664 bytesで
8 GiB内、dense worst 682,770,911,232 bytesは棄却した。Qはraw 6/24非零、2,374項だが、
本ゲートではintrinsic reductionを行っていない。

---

## 11B. ゲート11: full third-order jet fibre四次exact監査

```
artifact  results/v0.4.2_955_slack_csg_fourth_order.json
report    reports/v0.4.2_955_slack_csg_fourth_order.md
module    src/universe_lab/final_theory/source_native_955_slack_csg_fourth_order_v042.py
digest    f59d46a8d52210fe6b63757b8af10484654fbe8ef1483182dcd14c6fcfe817e4
verdict   V042_955_SLACK_CSG_FOURTH_ORDER_ALL_THIRD_ORDER_JETS_LIFT_Q_ESCAPE_BLOCKED_CERTIFIED
```

3,985 dependent rowsのcompatibility weighted formsは全て0、span rank 0。従って
**対角CSG点の**任意のfull third-order core jet `(z,a,b)` は四次までliftする。raw Qは
6/24 entries非零、2,374項だが、core Jacobian fourth-jet basisへreduceするとintrinsic
nonzero 0/24、rank 0。16 terminal blind directionsもraw core/Q・intrinsic・remainderで
occurrence 0。actual保守メモリは427 form overhead込み607,942,656 bytes。

第五次の候補は `z^5` 2,869,685、`z^3*a` 1,020,425、`z*a^2` 60,025、`z^2*b`
60,025、`a*b` 2,401、`z*c` 2,401、計4,014,962。これはpreflight設計の認可であり、
第五次actual・形式収束・generic solverの認可ではない。full 955は `OPEN`。

---

## 12. 破棄された計画

**「131 patch を構造的基準で選んで exact scout する」は不要になった。**
ゲート2が patch を一つも開かずに探索空間を落としたため。ゲート1の成果物に
`deterministic_scout_schedule`（先頭8件、`executed: false`）が残っているが、
これは当時の予定表であり、現在の推奨経路ではない。

---

## 13. 罠 — 範囲と後続で踏みやすい点

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

## 14. 既存の不具合（本セッション由来ではない）

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

## 15. 検証コマンド（コスト順）

```powershell
uv run ruff check .
uv run pytest tests/final_theory/test_v042_955_symmetry_orbit_reduction.py tests/final_theory/test_v042_955_global_bilinear_reduction.py tests/final_theory/test_v042_955_mixed_branch_closure.py tests/final_theory/test_v042_955_slack_coverage_gap.py tests/final_theory/test_v042_955_slack_term_preflight.py tests/final_theory/test_v042_955_slack_csg_tangent.py tests/final_theory/test_v042_955_slack_csg_second_order.py tests/final_theory/test_v042_955_slack_csg_third_order_preflight.py tests/final_theory/test_v042_955_slack_csg_third_order.py tests/final_theory/test_v042_955_slack_csg_fourth_order_preflight.py tests/final_theory/test_v042_955_slack_csg_fourth_order.py -q
uv run pytest -q
```

十一ゲートの新規テストは 82 件。うち独立検証として、核基底を manifest の生の行と直接
内積で検査するもの（`test_kernel_basis_is_independently_verified_against_the_manifest_rows`）と、
二重次数を成果物を介さず manifest から再計測するもの、一般17パラメータ族で
1,933成分を再代入するもの、timid recurrence から次数 histogram を再構成するもの、
24 timid residualをreachable stateへ再作用して48成分の零を再検査するもの、
3,890 raw core Jacobian rowsへ12 Q-gradient rowsを再reduceするもの、二次形式抽出を
2変数の手計算oracleと照合するもの、weighted三次抽出と三次form reductionを小さな
手計算oracleで照合するものを含む。

---

## 16. AI 開示

ゲート1・2と `MISSION.md` の現行フェーズ節は Anthropic Claude、ゲート3・4・5・6・7・8・9・10・11の
モジュール・テスト・報告・引き継ぎ更新は OpenAI Codex が作成した。Luna は
読み取り専用のブランチ／不要ファイル棚卸しと、ゲート4の数値・digest・適用体境界の
独立再検算、ゲート5で再利用可能な疎多項式・stream・budget実装の探索、ゲート7の
数値・digest・結論範囲の読み取り専用監査、ゲート8で三次helper候補のread-only探索、
ゲート9の数式範囲・全2-jet coverage・三次結論の独立監査、ゲート10の疎性外挿、
ゲート11のwriterなしexact再生成・digest・予算・論理範囲の独立監査を担当した。
人間の著者が範囲を選択し内容に責任を負う。
`CONTRIBUTING.md` の「どのツールがどの部分か」要件に対応する記録である。

`.zenodo.json` と `paper/paper.md` の開示は**触っていない**。両者は凍結
アーカイブのダイジェストに影響するため、次にアーカイブを再構築する版で
まとめて更新すること（`HANDOFF.md` §10）。

---

## 12. ゲート12: 無制限チャートの次数付けと upper stratum 分解（2026-08-10）

```
artifact  results/v0.4.2_955_upper_stratum.json
report    reports/v0.4.2_955_upper_stratum.md
module    src/universe_lab/final_theory/source_native_955_upper_stratum_v042.py
digest    678823e2e663f02c6273d3070698baf7025efd16776694aa9c595830a944ae69
verdict   V042_955_UPPER_STRATUM_SCALAR_TIMES_LINEAR_FIBRE_DECOMPOSITION_CERTIFIED_NONTERMINAL
```

```powershell
uv run python -m universe_lab.final_theory.source_native_955_upper_stratum_v042
uv run pytest tests/final_theory/test_v042_955_upper_stratum.py -q
```

### 12.1 前提（毎回検証すること）

**reachable-state MSR はこのチャートに恒等的に組み込まれている。** slack
compiler の `constraints_after_substitution: 0`、理由は `(J v_c)^T v_c = 0`。
本チャートの core は **CPOBC + strong GC のみ**。rank 427 も本ゲートの全ランクも
その core に対するものである。MSR 行を別途足そうとしないこと。

### 12.2 次数付けは導出した（仮定していない）

47,298 の単項式制約、rank 460、不整合 0、均一性違反 0。

```
A:*:00  0     A:*:01  +1     A:*:10  -1
A:*:11  0     u:*:0   +1     u:*:1    0
```

**罠**: 正の重みを持つのは右上行列成分だけではない。`u:*:0` も +1 を持つ。
仮定していたら分解の記述を誤っていた。ファイバーは `A:*:01`(107) と
`u:*:0`(16) の**合計123座標**に線形である。

解空間の自由度16は、core のどの単項式にも現れない16座標であり、独立に凍結
済みの tangent 監査の `terminal_slack_blind_directions` と**完全一致**する
（成果物に `equals_the_frozen_terminal_slack_blind_directions: true`）。
blind である代数的理由がこれで判明した。

### 12.3 分解（主結果）

upper stratum = `{107個の A:*:10 が全て0}` 上で、4,152 の非零 core 成分すべてに
対し反例0で:

- `(1,0)` ブロックは恒等的に消える
- `(0,1)` ブロックは正重み族に厳密線形、係数は重み付き座標を含まない
- 対角ブロックは重み付き座標を一切含まない

| | 座標 | 成分 | 項数 |
|---|---|---|---|
| スカラー多様体 `S` | `A:*:00`, `A:*:11`, `u:*:1` | 1,814 | 9,673（最大次数9） |
| 正重み線形ファイバー | 123 | 1,038 | 16,004 |

ansatz なし・対角固定なしで、gate 2 の大域双線形簡約と同じパターンが無制限
チャート上に再現した。

### 12.4 可換子は6本の4項線形形式に崩壊

upper stratum 上で、6組すべて対角0・左下0、生き残るのは `(0,1)` のみで
**各4項**。476変数・101,200項の core が、可換性に関しては6本の4項線形形式に
なった。

### 12.5 次のゲートと、そこでの警告

```
DECIDE_THE_SIX_UPPER_RIGHT_COMMUTATOR_FORMS_AGAINST_THE_CORE_ROW_SPAN_ON_S
```

`S` の厳密点で、6形式が正重み線形系の row span に入るかを判定する。厳密線形
代数のみで、Gröbner も予算も不要。

- **span 内** → その点で可換性が強制される（obstruction 側の証拠）
- **span 外** → 線形系を解いて **955 witness 候補**が得られる

**警告 1**: `Q` の対角が自由なので `(a00 - a11)` は一般に非零であり、可換子形式は
generic に非零である。**WITNESS 側に転ぶ可能性を排除していない。** 両終端を
terminal 形に設計し、verdict 文字列を実行前に固定すること。

**警告 2**: mixed ansatz の upper family が可換だったのは対角を `(p_e, 1)` に
凍結していたためである。**その直観をここへ持ち込まないこと。**

**警告 3**: witness 候補が出ても、非特異性、`N != 0`、Eq113/Eq139、そして
**reachable visibility** が別途必要。到達スパン rank 1 の operator-only witness は
SR2 の既知の弱点を再現するだけで、宣言済み三終端には届かない。

**警告 4**: upper stratum は無制限 955 ではない。両非対角族が非零の mixed 点は
open で、ゲージトーラスは片側を膨張させるため退化で落とせない。stratum 上の
obstruction も三終端には届かない。

---

## 13. ゲート13: 可換子形式の row-span 判定（2026-08-10）

```
artifact  results/v0.4.2_955_commutator_span.json
report    reports/v0.4.2_955_commutator_span.md
design    reports/v0.4.2_955_commutator_span_gate_design.md  (計測前に固定、commit 8f900aa)
module    src/universe_lab/final_theory/source_native_955_commutator_span_v042.py
digest    3b95e12a8cfca62f607b559fa215e5dcb34bf3fb494b47490b5a9d25407a5c0e
verdict   V042_955_UPPER_STRATUM_SPAN_POINTWISE_EVIDENCE_ONLY_NONTERMINAL
```

### 13.1 結果

`S` の厳密点は一般結合 `t_0..t_4` の CSG 族から取り、**各点が core の厳密解である
ことを先に検証**した（4,152成分すべて零。非零なら棄却し修復しない）。

| 結合 | rank(L) | ファイバー | 判定 |
|---|---|---|---|
| `(1,1,1,1,1)` 対照 | 114 | 9 | IN_SPAN |
| `(1,2,3,5,7)` | 114 | 9 | IN_SPAN |
| `(2,1,4,1,3)` | 114 | 9 | IN_SPAN |
| `(3,1,1,1,1)` | 114 | 9 | IN_SPAN |

棄却2件（`reachable state became zero` / `lambda(3,0)=0`）を理由付きで保存。
対照は凍結済み131特性の完全再現を機械検査している。

可換子行は評価前4単項式・評価後**2列**。`(a_i-d_i)b_j-(a_j-d_j)b_i` の畳み込みで
あり、事前設計の予測と一致。

### 13.2 これは obstruction の証拠にすぎない

**最重要の限界: CSG 族は `A:*:11` を常に1に固定する。** 結合を変えても第二対角は
動かない。そして可換子形式が generic に非零になるのはまさにその方向である。
**WITNESS 側の可能性は一切排除されていない。** obstruction 本命という方針を
この4点の結果に読み込まないこと。

有限個の点は stratum を決めない。stratum は無制限955ではない。in-span は宣言済み
三終端のどれにも届かない。

### 13.3 `Q(t)` 記号計算の顛末

- **成功（未認証）**: 記号 assignment が core を**恒等的に**満たすと報告された
  （4,412成分すべて `t` の有理関数として零）。事実なら4点抽出より強い。ただし
  **これは補助セッションの報告でリポジトリ未認証**。認証は次のゲート。
- **未完**: `rank(L)` は 1038×123 の `Q(t)` 上疎消去が pivot ごとの `sympy.cancel`
  で詰まり、最初の100行すら抜けなかった。span 判定も因子抽出も未実施。
  浮動小数点にも有限体にも切り替えていない。プロセスは停止済み。**この経路は放棄。**

### 13.4 次のゲート

```
CONSTRUCT_POINTS_OF_S_WITH_A_FREE_SECOND_DIAGONAL_THEN_RERUN_THE_SPAN_DECISION
```

1. `A:*:11 != 1` を持つ `S` の点を構成し、同じ判定を回す（本命）
2. §13.3 の記号 core 同一性をリポジトリで認証する（実行可能な規模）
3. `Q(t)` 上の span 判定を素朴な全体消去で再試行しない。可換子行は `b_Q1..b_Q4` の
   2列しか持たないので、その4列以外を `L` から消去した関係式を見るほうが桁違いに
   小さい。問いは `(p_i - 1) b_j = (p_j - 1) b_i` の形が出るかどうかである。

---

## 14. ゲート14/15: 成長族の恒等性と、第二対角を動かした span 判定（2026-08-10）

### 14.1 ゲート14 — 成長族は core を結合について恒等的に満たす

```
artifact  results/v0.4.2_955_growth_family_identity.json
report    reports/v0.4.2_955_growth_family_identity.md
module    src/universe_lab/final_theory/source_native_955_growth_family_identity_v042.py
digest    d6e1548f13c287377b3f50b2070802e550bf06c334d5501c8bc2ff92be617755
verdict   V042_955_GROWTH_FAMILY_SOLVES_THE_CORE_IDENTICALLY_IN_THE_COUPLINGS_CERTIFIED
```

`QQ(t_0..t_4)` 上で timid first-column 同一性が24 source すべてで成立し、core
4,152成分すべてが恒等的に零。ゲート13の4点抽出が族の言明に格上げされた。
`t_k=1` への特殊化が凍結131特性を再現することを機械検査（不一致なら停止）。

除外軌跡を明示: 結合分母4本と到達状態積の分子22本（既約因子 `t0,t1,t2,t3,t1+t2,
t2+t3,t1+2*t2+t3`）。

**方法の注意**: 消去せず成分ごとに代入して `cancel` するだけ。約16秒。
`Q(t)` 上の疎消去（頓挫した経路）とは別物である。

### 14.2 ゲート15 — 第二対角を動かした span 判定（ゲート13の限界を解消）

```
artifact  results/v0.4.2_955_second_diagonal_span.json
report    reports/v0.4.2_955_second_diagonal_span.md
module    src/universe_lab/final_theory/source_native_955_second_diagonal_span_v042.py
digest    a4ea09f19831dcb2d593e67456b1f020142aa8024c9ec1097ad55b1e6ccfc08b
verdict   V042_955_UPPER_STRATUM_SPAN_POINTWISE_EVIDENCE_ONLY_NONTERMINAL
```

**構成の鍵は timid 目標値の1行である。** `u:c:1` を目標値1に対して解くと失敗する
（42次元核から取った候補は残差5〜21件/4152）。目標値はその timid 軌道自身の第二
対角値でなければならない。**失敗の原因は目標値であって多様体側の obstruction では
なかった。** ここを間違えると「第二対角は動かせない」という誤結論に直行する。

二構成: 定数 `A:*:11 = c`、および二特性（`A:*:00 = p(t)`, `A:*:11 = q(t')`）。

| 点 | β相異値 | rank | ファイバー | escape |
|---|---|---|---|---|
| 定数 c=1 対照 / 2 / 3 / 1/2 / −1 / 5/3 | 1 | 114 | 9 | 0 |
| 二特性 `t'=t`（スカラー退化・対照） | 4 | **103** | **20** | 0 |
| 二特性 3種 | 13 / 12 / 9 | 114 | 9 | 0 |

10点すべて fail-closed の core 検証を通過、特異遷移0、**escape 0**。
スカラー退化点は可換子行が恒等的に零になり rank も落ちる（期待どおりの別挙動）。

**したがってゲート13の最大の限界は解消した。** 第二対角を定数でも非定数でも動かして、
なお6本すべてが row span に入る。

### 14.3 残る限界（変わっていない）

- 掃いたのは定数と第二成長特性だけ。第二対角自由度の全体ではない。
- 有限個の点は stratum を決めない。
- upper stratum は無制限955ではない。mixed 点は open。
- in-span は宣言済み三終端のどれにも届かない。

### 14.4 次のゲート

```
PROVE_THE_SPAN_MEMBERSHIP_UNIFORMLY_ON_S_OR_SWEEP_THE_REMAINING_SECOND_DIAGONAL_FREEDOM
```

残っているのは**量化子**である。一様証明の経路は、`Q(t)` の素朴な全体消去では
なく（頓挫済み）、`L` から4つの `Q` 列以外を消去して
`(p_i - 1) b_j = (p_j - 1) b_i` の形が出るかを見ること。

---

## 15. ゲート16: Eq120 が6組の可換子を1個のスカラーに崩壊させる（2026-08-10）

```
artifact  results/v0.4.2_955_eq120_commutator_collapse.json
report    reports/v0.4.2_955_eq120_commutator_collapse.md
module    src/universe_lab/final_theory/source_native_955_eq120_collapse_v042.py
digest    d6989a56a7fdd896e8dd4f0f8fa3516cdb836649f5a42bf5e15664b7feafdcfe
verdict   V042_955_EQ120_SIX_COMMUTATORS_COLLAPSE_TO_ONE_SCALAR_CERTIFIED
```

### 15.1 発端

ゲート15の点で `L` の非Q列119本を消去し「Q列4本だけの純粋な関係式」を抽出したところ、
**独立な関係式がちょうど3本**（4次元中codim1）現れ、6組の可換子形式が**全て同じ
基底に厳密分解**された。この構造は、**SR3b-A が使った source-native Eq120**
（`results/v0.4.2_eq120_source_provenance.json`）と同一の機構だと判明した。

**罠**: 最初の手計算では Q列とQ生成元段数のラベル対応を取り違え、
`c_12(v)=0` の検証が誤って矛盾した。列インデックスと段数の対応は
`tangent._q_mapping` の戻り値を都度確認すること。

### 15.2 中心の補題

upper stratum上で `Q_i=[[a_i,b_i],[0,d_i]]`。Eq120の `(0,1)` 成分は厳密に
3×3行列式 `det[[a_1,d_1,b_1],[a_m,d_m,b_m],[a_n,d_n,b_n]]` に一致する（記号的に
検証済み）。`E_23,E_24=0` を解くと `E_34=0` が**自動的に**従う（3本のうち独立は
2本のみ）。この代入のもとで **6組すべての可換子が単一のスカラー
`Λ=c_14=(a_1-d_1)b_4-(a_4-d_4)b_1` の厳密なスカラー倍**になる：

```
c_ij = [(a_i d_j - a_j d_i) / (a_1 d_4 - a_4 d_1)] · Λ
```

係数は `a,d` だけの厳密な2×2小行列式（`b` を含まない）。`a_1 d_4-a_4 d_1 != 0`
が必要。

**したがって、6本の row-span 判定は不要になった。全可換性は `Λ=0` という
単一のスカラー条件に完全に同値。**

### 15.3 独立な相互検証

ゲート15で escape 0 と記録された3点（`constant_1_control`, `constant_2`,
`two_character_1_2_3_5_7`）について、**その成果物を信用せず** source-native の
構成から `a_1,d_1,b_1,a_4,d_4,b_4` を独立に再計算し、`Λ` を直接評価。
**3点すべてで `Λ=0` と一致。**

**実装上の罠**: `dict.update()` で整数キー(1,2,3,4)を sympy シンボルキー
(`b[2]`)で上書きしようとすると別エントリが追加されるだけで置換されない
（Python辞書のキー型不一致）。`values[2] = substitution[b[2]]` のように
明示的に書くこと。同様に、`characters()` の辞書は timid 表現元も含む
**全131表現元**を対象にする必要がある。`non_timid` に絞ると timid 漸化式の
目標値取得で `KeyError` になる。

### 15.4 次のゲート（再定義）

これはゲート16時点の履歴であり、現行の次ゲートは §16.1 に更新されている。

```
DECIDE_WHETHER_LAMBDA_C14_IS_FORCED_TO_ZERO_ON_S_OR_EXHIBIT_A_NONSINGULAR_POINT_WHERE_IT_IS_NOT
```

問いは1つ: **`Λ=c_14` は core によって0に強制されるか、それとも
`a_1 d_4-a_4 d_1 != 0` を満たす `S` 上のどこかで `Λ != 0` となるか。**
後者なら955 witness候補（非特異性・`N!=0`・Eq113/Eq139・reachable visibility が
別途必要）。前者ならobstruction証拠がさらに強くなる。

---

## 16. ゲート17: 非零ファイバー上の `Lambda` 監査（2026-08-11）

```
artifact  results/v0.4.2_955_lambda_fibre_audit.json
report    reports/v0.4.2_955_lambda_fibre_audit.md
module    src/universe_lab/final_theory/source_native_955_lambda_fibre_audit_v042.py
test      tests/final_theory/test_v042_955_lambda_fibre_audit.py
verdict   V042_955_LAMBDA_ZERO_ON_CERTIFIED_FIBRE_FAMILY_FULL_S_OPEN
```

前ゲートの `Lambda=0` cross-check は上右ファイバーを全て0にした zero-section だった。
そこで、`L` の非Q列119本を消去し、Q成分が非零の `ker(L)` 方向を4点で再構成した。
各点の会計は `non-Q pivot rank=111`、`pure-Q residual rows=706`、`pure-Q rank=3`。
`D!=0`、`Lambda` の純Q row-module 残差0、Q-visible kernel上の直接評価0を全点で確認した。

さらに第一対角を成長特性 `(1,1,1,1,t)`、第二対角を全遷移で共通値 `s` とする二変数族を
`QQ(t,s)` 上で監査した。4,152 core entriesは恒等的に0、純Q rankは3、`Lambda` の残差も
恒等的に0。`D=s(t+13)/(2(t+15))` なので、`s!=0` と既存の成長分母・`t=-13,-15` を
除く開集合で成立する。`s=2` は前回の一変数監査を再現するが、第二対角131個の独立自由度を
主張するものではない。

これは zero-section を超える一様性だが、`S` 全体の証明ではない。`S` の既約性・稠密性・
全体を覆うpivot minorは未証明である。さらに `D=0` では、`t=-13,s=2` の非特異な
アンカー1点で直接 `Lambda` row-span を確認しただけで、退化枝全体はopenである。
全体判定は `OPEN` のまま。

### 16.1 次のゲート

Sol の監査方針に従い、次は scalar core ideal `I_S` と source determinant localization `Pi`
を含む localized row-module certificate

```
(D*Pi)^N Lambda = r(z)L(z) + sum(f_alpha(z) h_alpha(z)),  f_alpha in I_S
```

を作る。これが閉じなければ、`D!=0` かつ `Lambda!=0` の exact core fibre を探す。
10パラメータ二特性族の全記号消去は式膨張で予算外だったため、今回の成果物には含めない。

### 16.2 `D=0` アンカー点（同日追補）

`D` を割らずに、第一成長結合 `(1,1,1,1,-13)`、第二対角を全遷移で2とする一点を
直接評価した。4,152 core failuresは0、source determinant 131個の失敗は0、
`non-Q rank=111`、`pure-Q rank=3`、`Lambda` 残差0であった。Q-visible kernelの
一例は `(3/56,1/16,15/224,3/56)` で、`Lambda=0`。これは `D=0` 全枝の解決ではなく、
`D!=0` アンカーだけでは覆われない枝に対する非特異な一点の直接監査である。

---

## 17. ゲート18: localized row-module preflight（2026-08-11）

```
artifact  results/v0.4.2_955_localized_row_module_preflight.json
report    reports/v0.4.2_955_localized_row_module_preflight.md
module    src/universe_lab/final_theory/source_native_955_localized_row_module_preflight_v042.py
test      tests/final_theory/test_v042_955_localized_row_module_preflight.py
verdict   V042_955_LOCALIZED_ROW_MODULE_PREFLIGHT_FINITE_MINOR_COVER_REQUIRED_FULL_S_OPEN
```

Solの監査方針に従い、全Sの証明書を直接走らせず、必要な係数環とlocalizerの
manifestをexactに再構成した。scalar座標は246、scalar coreは4,152 entry中
非零1,814・相異なるもの1,504。upper-rightの `L` は1038×123、非Q列119で、
fibreに厳密線形、直接Q-only rowは0。source determinantは131個すべて非零かつ相異なり、
最大145項・次数5である（積は未展開）。

`D14 != 0`、`D14=0,D12 !=0`、`D14=D12=0,D13 !=0` の三つをrank-2 anchor coverとし、
`D12=D13=D14=0`をrank-1閉部分として分離した。既存4点では非Qのpointwise pivot
rank 111、pure-Q rank 3を再確認したが、これは係数環上のminor coverでも
localized row-module certificateでもない。

### 17.1 次のゲート

```
BUILD_OR_FAIL_CLOSED_A_FINITE_LOCALIZED_MINOR_COVER_FOR_D12_D13_D14
OR_FIND_A_D_NONZERO_LAMBDA_NONZERO_CORE_FIBRE
```

有限coverが膨張する場合は、MISSIONの停止規則に従って `RESOURCE_LIMIT_OPEN` に
凍結する。Gröbner、saturation、数値探索はこのゲートで実行していない。

---

## 16. ゲート19: 対称性のない独立点での Λ row-span 掃引（自己訂正込み、2026-08-11）

```
artifact  results/v0.4.2_955_independent_diagonal_sweep.json
report    reports/v0.4.2_955_independent_diagonal_sweep.md
module    src/universe_lab/final_theory/source_native_955_independent_diagonal_sweep_v042.py
digest    714c5e05b3b6357267efcbd988501a3fe62e6e1d2943cacbd66a8f02bc75320e
verdict   V042_955_LAMBDA_IN_SPAN_AT_EIGHT_INDEPENDENT_DIAGONAL_POINTS_FULL_S_OPEN
```

### 16.1 罠：`Λ` を数値評価するのは無意味な場合がある

`source_native_955_eq120_collapse_v042._lambda_at_point` は `A:*:01`（`b` 座標）
を一切設定せず常に0のままである。ここから `Λ=(a1-d1)*b4-(a4-d4)*b1` を直接
評価すると `b=0` により**自明に0**になる。**新しい点で `Λ` を検証したいときに
この関数を使ってはならない**——それは既知の escape=0 点でのクロスチェック
専用である。

**正しい方法**: `Λ` を数値評価せず、`commutator_span`/`second_diagonal_span`
と同じ **row-span 判定**を使う。`L` の対角部分（重み0）だけ数値化し、123個の
正重み座標は列として残したまま、`Λ` に対応する行が `rowspan(L)` に入るかを
判定する。

### 16.2 結果

対称性を共有しない8組の結合対（片側全1・単一自由パラメータ・両側同一公式の
いずれでもない）で正しい方法を適用。全点 fail-closed で core 検証を通過
（対角ブロックのみの検証で全4,152成分の検証と同値——`(0,1)/(1,0)` は正重み
族に定数項なしの厳密線形なので `b=0` で恒等的に0になるため）。

| | |
|---|---|
| 検証点 | 8 |
| `D≠0` の点 | 7 |
| escape | **0** |
| rank(L) | 全点で114 |

Gate 17 の対称性の高い族を超えた独立した8点でも、Eq120 崩壊補題の非退化な
適用範囲で一貫して `Λ` が row-span に入ることを確認した。

### 16.3 次のゲート（不変）

```
BUILD_OR_FAIL_CLOSED_A_FINITE_LOCALIZED_MINOR_COVER_FOR_D12_D13_D14
OR_FIND_A_D_NONZERO_LAMBDA_NONZERO_CORE_FIBRE
```

Gate19時点の15点（Gate17の4+2パラメータ族＋Gate19の8点、対照点を除く）で escape 0 が
続いている。witness 側の可能性は理論上排除されていないが、経験的証拠は
obstruction 側に厚く積み上がっている。

---

## 18. 追加有限監査A: independent-character witness scout（2026-08-11）

```
artifact  results/v0.4.2_955_independent_character_witness_scout.json
report    reports/v0.4.2_955_independent_character_witness_scout.md
module    src/universe_lab/final_theory/source_native_955_independent_character_witness_scout_v042.py
test      tests/final_theory/test_v042_955_independent_character_witness_scout.py
verdict   V042_955_INDEPENDENT_CHARACTER_SCOUT_NO_LAMBDA_ESCAPE_FULL_S_OPEN
```

第一・第二対角の結合を独立に選ぶ8×8=64組を、source-native character construction
からexactに生成した。全64点で4,152 core式と131 source determinantを通過し、
`D14!=0` は54点だった。54点すべてで `Lambda` の純Q row-module残差はゼロで、
escape candidateは0だった。

これは既存の8点 independent sweepを、同じ構成の小さな決定的格子へ広げたもの。
有限scoutなので、witness certificateでも obstructionでもない。単純な character-grid
拡張をこれ以上無制限に続ける根拠は得られなかった。

---

## 19. 追加有限監査B: rank-one diagonal branch（2026-08-11）

```
artifact  results/v0.4.2_955_rank_one_character_audit.json
report    reports/v0.4.2_955_rank_one_character_audit.md
module    src/universe_lab/final_theory/source_native_955_rank_one_character_audit_v042.py
test      tests/final_theory/test_v042_955_rank_one_character_audit.py
verdict   V042_955_RANK_ONE_SOURCE_NATIVE_CHARACTER_AUDIT_NO_ESCAPE_FULL_S_OPEN
```

`D12=D13=D14=0` のrank-one条件を、結合値 `{1,2,3}`（先頭は1に正規化）の
81×81=6,561組で全走査した。条件を満たす93点はすべてcore 4,152式とsource
determinant 131個を通過した。81点は `rank(L)=103` のスカラー退化、残る12点は
非スカラーで `rank(L)=114`。後者を含む全93点で6組の可換子row-span escapeは0だった。

rank-one閉枝全体の証明ではないが、`D14`を割れない枝を単なる自明な
`a_i=d_i`ケースと混同しないための有限監査になっている。

---

## 20. 追加有限監査C: localized minor finite preflight（2026-08-11）

```
artifact  results/v0.4.2_955_minor_cover_preflight.json
report    reports/v0.4.2_955_minor_cover_preflight.md
module    src/universe_lab/final_theory/source_native_955_minor_cover_preflight_v042.py
test      tests/final_theory/test_v042_955_minor_cover_preflight.py
verdict   V042_955_LOCALIZED_MINOR_COVER_PREFLIGHT_FINITE_SAMPLE_NOT_CERTIFIED_FULL_S_OPEN
```

Gate18の係数構造を使い、第一4点×第二9点に`D12`・`D13`を出す2点を追加した
38点で、pivot minorの有限sample coverを測った。全38点がcoreとsource localizerを通過。
非Q119列のうち107列は構造的monomial matchingに入り、残る12列がmulti-termの
Schur/minor部分を担う。

matching edgeの係数は112因子、最大次数3、係数絶対値1で、全て`A:*:00/11`型の
source対角変数だった。131 source determinantをupper stratumへ制限したsupportにも
全因子名が現れた。ただしmatchingは一意でなく、このsupport事実だけではminor
determinantの相殺がないこと、また因子がlocalizer上の単元であることを示さない。

anchor別のsample結果は、`D14`:32点・7 signatures・最小2枚、`D12`:1点・1枚、
`D13`:1点・1枚だった。これは有限sample上の非消滅だけであり、`I_S` と131 source
determinant localizationを含むunit-ideal/row-module証明書ではない。したがって
`unit_minor_certificate_issued=false`を維持する。

## 20.1 現在の最短ルート

次は、sampleで得た候補minorをそのまま全Sの証明とみなさず、scalar core ideal と
source determinant localizationの上で exact row-module certificate に昇格できるかを
fail-closed に判定する。形式は

```
(D_1k * product(delta_e))^N Lambda_1k
  = sum_r p_r(z)L_r(z) + sum_alpha f_alpha(z)h_alpha(z)
```

で、巨大な `product(delta_e)` は展開しない。ここで証明書が膨張して有限の定理へ
変換できない場合は、MISSIONの停止規則に従い `RESOURCE_LIMIT_OPEN` に凍結する。
`D!=0, Lambda!=0` のexact fibreが先に出た場合は、`N`・Eq113/Eq139・reachable
visibilityを追加検査してwitness終端の可否を判定する。

全体判定は引き続き `FINAL_THEORY_OPEN`。上部族・有限sample・rank-one有限格子の
結果をfull 955 profileへ昇格しない。
