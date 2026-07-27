# QG-Bench v0.1 独立監査

## 判定

- 小規模・中規模再現: `SMALL_N_REPRODUCTION_PASS`
- 論文規模 \(N=18000\)、30 seeds: `RESOURCE_BLOCKED`
- 総合: `PARTIAL`

この判定は、独立実装で有限サイズの数値収束を支持したという意味に限る。論文規模の
再現、解析的連続極限、量子重力理論の検証ではない。

機械可読な全結果は `results/qgbench_v0.1_audit.json` に保存した。

## 独立性

監査oracleは `src/universe_lab/qgaudit/` にあり、
`universe_lab.qgbench.ads2` および他の `universe_lab.qgbench` モジュールをimport
しない。この禁止はASTを読む試験でも検査している。

- 連続解: Legendre evaluatorを共有せず、
  \(P_\nu(z)={}_2F_1(-\nu,\nu+1;1;(1-z)/2)\) で評価した。
- 離散解: 外部ラベルから決定論的topological orderを独自に求め、
  \(K(I+m^2C/(2\rho))=C/2\) を三角Volterra系として解いた。
- 測地距離: AdS埋込み不変量から主値を計算した。
- sprinkling: AdS体積測度から時間周辺分布と条件付き空間分布の逆CDFを実装した。

これはコード依存の循環を除くが、同じ一次資料の数式を使うため、数式自体の誤植に
対する独立な実験ではない。

## 環境

- Git branch: `master`
- Git commit: なし（`UNBORN_BRANCH_NO_COMMIT`）
- Python: 3.12.10
- NumPy: 2.3.5
- SciPy: 1.18.0
- CPU: AMD64 Family 26 Model 68、6 physical / 12 logical cores
- GPU: NVIDIA GeForce RTX 3090を検出したが、監査計算には不使用
- `uv.lock` SHA-256:
  `25f4d380be075132f2ee669792c5d703fd6de5ffff817023fd7b85712b980591`
- seeds: 30001--30030（各Nで同じ事前固定30 seeds）

コミットが存在しないため、結果を不変なGit objectへ結び付けることはできない。lock
hashと環境値は保存したが、これはcommit hashの代替ではない。

## 独立再計算

固定条件は \(m=4\)、\(L=1\)、\(\epsilon=0.25\)、18 binsである。各行はseedごとに
RMSEを計算してから集約した結果であり、seedを先にpoolした単一RMSEではない。95%区間
はsample標準偏差とStudent-t分布から計算した。

| N | seeds | 平均RMSE | 標準偏差 | 95% CI | 平均因果対数 |
|---:|---:|---:|---:|---:|---:|
| 225 | 30 | 0.039827 | 0.014723 | [0.034330, 0.045325] | 9,025 |
| 450 | 30 | 0.025570 | 0.015090 | [0.019935, 0.031204] | 35,999 |
| 900 | 30 | 0.017163 | 0.008905 | [0.013838, 0.020488] | 143,624 |
| 1800 | 30 | 0.012008 | 0.005551 | [0.009935, 0.014081] | 577,281 |
| 3600 | 30 | 0.009370 | 0.004391 | [0.007731, 0.011010] | 2,310,854 |
| 7200 | 0/30 | — | — | `RESOURCE_BLOCKED` | — |
| 18000 | 0/30 | — | — | `RESOURCE_BLOCKED` | — |

平均RMSEは実行した全レベルで単調に低下した。ただし、95%区間には隣接レベル間の
重なりがあり、単調性を各seedで保証する結果ではない。

## 有限サイズスケーリング

\[
\operatorname{RMSE}(N)=aN^{-p}+b
\]

seedレベル150観測を非線形最小二乗に入力し、各N内でseedを再標本化する500回の
bootstrapを行った。

| parameter | estimate | asymptotic SE | bootstrap 95% CI |
|---|---:|---:|---:|
| \(a\) | 2.2117 | 2.5697 | [0.3427, 10.0000] |
| \(p\) | 0.7671 | 0.2318 | [0.3637, 1.0623] |
| \(b\) | 0.00513 | 0.00441 | [-0.00967, 0.00860] |

\(b\) の区間は0を含むため、観測値は非零floorを要求しない。しかし \(a\) の上側区間が
fit boundへ達しており、\(p\) と \(b\) の識別は弱い。したがって「\(b=0\)を確認した」
または「連続極限を証明した」とは判定しない。

## 資源事前検査

\(N=1800\) の1 seed実測0.2283秒を基準に、時間を \(N^3\)、peak memoryを
\(72N^2\) bytesとして保守的に外挿した。各levelのwall-time予算は180秒、memory予算は
実行時available RAMの25%（約2.27 GB）と事前固定した。

- \(N=7200\), 30 seeds: 推定438秒、推定peak 3.73 GB。`RESOURCE_BLOCKED`
- \(N=18000\), 30 seeds: 推定6,849秒、推定peak 23.33 GB。
  `RESOURCE_BLOCKED`

特に \(N=18000\) は0/30 seedsであり、既存の「全ゲートPASS」と論文規模再現を明確に
区別する。`FULL_PAPER_SCALE_PASS` は付与しない。

## Mutation test

次の全mutationを決定論的に検出した。

| mutation | detector | 結果 |
|---|---|---|
| jump amplitude符号反転 | 非変異Eq. 56 residual | PASS（mutant residual 1.0） |
| 質量係数を2倍 | 非変異Eq. 56 residual | PASS（1.7258） |
| AdS測度の係数を半分に変更 | 解析体積との相対誤差 | PASS（0.5） |
| 長いgeodesic branchを選択 | 局所Minkowski極限 | PASS（誤差6.283） |
| 外部ラベル依存row weight | permutation equivariance | PASS（誤差0.5445） |
| TPだが非CPのChoi行列 | 最小固有値 | PASS（-0.1） |

参照実装側のEq. 56 residualは \(3.4\times10^{-16}\) 以下、ラベル共変性誤差は
\(5.6\times10^{-16}\) 以下だった。mutation testはproduction関数をmonkey-patchせず、
独立oracleへ明示的な誤りを注入してdetectorの感度を試験する。

## 必須コマンド再実行

監査時の観測:

```powershell
uv run qgbench
# exit 0; Knowledge baseと既存6 benchmark gateがPASS

uv run pytest
# exit 0; 43 passed

uv run ruff check .
# exit 0; All checks passed

uv run ruff check src/universe_lab/qgaudit tests/qgaudit
# exit 0; All checks passed
```

並行開発中の中間実行ではString-Compiler側にimport-order I001が1件あったが、統合後の
最終再実行では全体RuffもPASSした。

独立数値監査の再実行:

```powershell
uv run python -m universe_lab.qgaudit.audit
uv run pytest tests/qgaudit -q
uv run ruff check src/universe_lab/qgaudit tests/qgaudit
```

## 主要所見と限界

1. 独立oracleも有限サイズ収束を支持し、critical mutationはすべて検出した。
2. 既存の単一傾向gateより強い30-seed統計を得たが、試した物理パラメータは
   \(m=4,L=1\) の一組だけである。
3. \(N=18000\) は未実行で、論文図のpixel-level reproductionでもない。
4. 固定点数sprinklingであり、点数自体をPoisson抽出する非条件付き過程ではない。
5. binned RMSEはbin数とminimum countに依存する。別binningによる感度分析は未実施。
6. Git commitがないため、現在の成果はcommit-addressableな再現記録ではない。

以上から、既存の小規模再現主張は独立に支持するが、
`FULL_PAPER_SCALE_PASS` または解析的・物理的完成の主張は支持しない。
