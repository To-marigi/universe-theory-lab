# Handoff — 955 profile track, 2026-08-09/10 session

これを読む前に `HANDOFF_v0.4.1.md` の冒頭（Paper I v0.4.2 公開済みの注記）を
読むこと。`HANDOFF.md` は v0.3.9 リリースの凍結記録であり、本文書はそれを
置き換えない。

本文書は **955 profile (`strong_GC + reachable_state_MSR`) トラック**の
運用引き継ぎである。このセッションで研究の中心方針が変わり、二つのゲートが
閉じた。`HANDOFF_v0.4.1.md` の後半にある「次は 131 patch を symmetry で
reduce してから scout する」という趣旨の記述は、本文書が上書きする。

---

## 1. まず結論

```
方針転換      オーナー決定 2026-08-09。MISSION.md に現行フェーズ節を追加済み
中心          955 を obstruction 側本命で決着させる → 721 → finite ON lattice
新ゲート1     対称性・軌道簡約   NEGATIVE TERMINAL（対称群は自明、patch 削減 0）
新ゲート2     大域双線形簡約     262 → 46 パラメータ、局所化なし solver なし
次ゲート      縮約座標での 1次消去 → 双線形形式解析 → 非特異条件の持ち込み
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

## 5. 次のゲート（この順で）

`CURRENT_RESEARCH_STATE.json` の `affected_campaign.next_gate` に固定済み。

1. **1次部分 rank 3 の消去。** 46 → 43 変数。純粋な厳密線形代数。
2. **CPOBC 対角の 954 個の双線形形式の構造解析。** 全て次数2・最大3項。
   `s^T M_k t = 0` の形なので、行列式的／階数的な扱いが自然。
3. **非特異条件を縮約座標へ持ち込む。** これは**必須**であり、後回しにしては
   ならない。§7 を読むこと。

heavy solver は従来どおり coverage certificate と版付き budget artifact が
揃うまで凍結（`solver_run_permitted: false`）。今回の二ゲートは Gröbner 0、
saturation 0、有限体 0、数値 0、Sage 0 で完了している。

---

## 6. 破棄された計画

**「131 patch を構造的基準で選んで exact scout する」は不要になった。**
ゲート2が patch を一つも開かずに探索空間を落としたため。ゲート1の成果物に
`deterministic_scout_schedule`（先頭8件、`executed: false`）が残っているが、
これは当時の予定表であり、現在の推奨経路ではない。

---

## 7. 罠 — 未処理の落とし穴

- **縮約系は非特異条件を含まない。** `det(A_e) = p_e - x_[e]*y_[e] != 0` は
  46変数系に課していない。縮約系の解が自動的に許容点になるわけではない。
  成果物の `claim_boundary` に明記してある。obstruction を主張する前に
  必ず localisation を持ち込むこと。逆に witness を主張する場合も、
  165 occurrence 全ての非特異性を別途検査しなければならない。
- **`Eq113` / `Eq139` の分岐は縮約系に入っていない。** 955 profile の
  common core（CPOBC + strong_GC + reachable_state_MSR）だけである。
  full witness には別途必要（`mixed_xy_tangent_scout` の
  `full_witness_gates_not_run` を参照）。
- **`reachable_MSR_operator` と `reachable_MSR_vector` を取り違えないこと。**
  955 は **vector**（到達状態上）。operator ブロックは強い意味論のもので、
  こちらは mixed でも `(0,1)` のみ＝厳密線形だが、955 では使えない。
  この取り違えは「955 も CPOBC+MSR で rank 131 になる」という誤結論を生む。
- **`mixed ansatz` は宣言された族であって一般 `GL_2` ではない。** 無制限の
  source-native slack 系（572 スカラー）は本簡約の外側にある。
- ゲート1の verdict 文字列 `NO_PATCH_REDUCTION_CERTIFIED` は無条件に見えるが、
  §3.2 の通り単語レベル限定である。引用時は範囲を付けること。

---

## 8. 既存の不具合（本セッション由来ではない）

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

## 9. 検証コマンド（コスト順）

```powershell
uv run ruff check .
uv run pytest tests/final_theory/test_v042_955_symmetry_orbit_reduction.py tests/final_theory/test_v042_955_global_bilinear_reduction.py -q
uv run pytest -q
```

新規テストは 19 件。うち独立検証として、核基底を manifest の生の行と直接
内積で検査するもの（`test_kernel_basis_is_independently_verified_against_the_manifest_rows`）と、
二重次数を成果物を介さず manifest から再計測するものを含む。

---

## 10. AI 開示

本セッションのモジュール、テスト、報告、`MISSION.md` の現行フェーズ節は
Anthropic Claude が作成し、人間の著者が範囲を選択し内容に責任を負う。
`CONTRIBUTING.md` の「どのツールがどの部分か」要件に対応する記録である。

`.zenodo.json` と `paper/paper.md` の開示は**触っていない**。両者は凍結
アーカイブのダイジェストに影響するため、次にアーカイブを再構築する版で
まとめて更新すること（`HANDOFF.md` §10）。
