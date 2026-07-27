# 宇宙理論計算研究所

宇宙の統一理論を、**記号導出 → 数値化 → 独立検算 → 記録**の順で育てるための
オープンソース計算環境です。現時点では「理論そのもの」ではなく、理論を安全に
組み立てる実験台を提供します。

## すぐ始める

PowerShellで次を実行します。

```powershell
.\scripts\bootstrap.ps1
.\scripts\lab.ps1
```

ブラウザに表示されたURLを開き、`notebooks/00_environment_check.ipynb` を実行します。
環境を再検査するときは次の1行です。

```powershell
.\scripts\check.ps1
```

## 二層の計算基盤

| 層 | 主な道具 | 用途 |
|---|---|---|
| Python 3.12 | SymPy, python-flint, gmpy2, SymEngine, mpmath | 厳密式、任意精度、代数 |
| Python 3.12 | NumPy, SciPy, Numba, numexpr | 数値線形代数、ODE、最適化、高速化 |
| Python 3.12 | Dask, Joblib, xarray, HDF5, Zarr | 並列化、大規模配列、結果保存 |
| 物理 | QuTiP, EinsteinPy, Astropy, Pint | 量子系、一般相対論、定数・単位 |
| SageMath 10.9 | Maxima, GAP, PARI/GP, FLINT, Singularほか | 重いCAS、群論、数論、独立検算 |

SageMathは大きいためDockerに隔離しています。Docker Desktopを起動した後、次を実行します。

```powershell
.\scripts\sage.ps1 pull
.\scripts\sage.ps1 start
```

既定のURLは <http://localhost:8889>、トークンは `.env` の `SAGE_TOKEN` です。
停止は `.\scripts\sage.ps1 stop`、Sageの対話シェルは
`.\scripts\sage.ps1 shell` で開きます。

## ディレクトリ

```text
notebooks/          仮説、導出、可視化
src/universe_lab/   再利用する検算・計算コード
tests/              数学的不変量と回帰テスト
data/               入力データ（Git管理外）
results/            計算結果と環境レポート（Git管理外）
scripts/            導入、起動、検査
compose.yaml        SageMath 10.9
uv.lock             Python依存関係の厳密な固定
```

## 計算を信頼するための原則

1. 浮動小数点の一致ではなく、まず記号的に残差がゼロか調べる。
2. 重要な結論はSymPyとSage/FLINTなど、独立した実装で再計算する。
3. 次元解析、保存量、対称性、極限、既知解を自動テストにする。
4. 桁落ちが疑われる計算はmpmath/FLINTの精度を段階的に増やし、収束を見る。
5. ノートブックだけにロジックを閉じ込めず、確定した処理は`src/`と`tests/`へ移す。
6. 式、仮定、単位、ソフトウェア版、乱数seed、許容誤差を結果と一緒に残す。

`results/environment.json` には実際に使ったPython・OS・各バックエンドの版と
検算結果が保存されます。

## 理論開発の入口

最初の理論モデルは次の順で定義すると比較可能になります。

1. 基礎対象: 時空、場、状態空間
2. 対称性: Lorentz/Poincaré、ゲージ群、離散対称性
3. 作用または生成原理: ラグランジアン、ハミルトニアン、量子振幅
4. 変分から運動方程式と拘束条件を自動導出
5. 一般相対論・標準模型・量子力学が現れる極限を検証
6. 無次元の新規予言を作り、観測値または公開データと比較

「あらゆる式を一つの巨大式にする」ことより、仮定と反証条件を機械可読にすることを
優先します。これにより、理論が変わっても同じ検算基盤を使い続けられます。

## QG-Bench v0.1

量子重力理論の機械可読 Atlas、Claim Graph、AdS1+1 因果集合スカラー伝播の
独立再現、量子チャネル検査、保留曲率試験を `QG-Bench/` に収録しています。

```powershell
uv run qgbench --quick
uv run qgbench
```

詳細な証拠範囲、仮定、未達項目は
[`QG-Bench/README.md`](QG-Bench/README.md) と `QG-Bench/reports/` にあります。

## String-Compiler Bench v0.1 / v0.2

F-theory/heterotic双対性を、生の座標比較ではなく型付き中間表現で検査する別トラックを
`String-Compiler-Bench/` に収録しています。

```powershell
uv run stringbench --suite all
uv run stringbench --suite v0.2
uv run stringbench iut-bridge
```

四つのF-theory K3ファイブレーションは記号計算済みですが、heterotic側の四分岐
Wilson-line loweringと物理的round tripは `BLOCKED` のため、総合判定は `PARTIAL` です。
IUTの判定は `IUT_TYPE_SYSTEM_ONLY` で、物理的制約の追加は主張しません。

v0.2では局所heterotic root loweringを四branchについて独立再現した。一方、
独立K3 period oracleとNarain orbit round-tripは `BLOCKED` のため、科学的総合判定は
引き続き `PARTIAL` です。

## 性能を上げるとき

- まずSymPyで導出し、`lambdify`でNumPy関数に変換します。
- ループが支配的ならNumba、配列がRAMを超えるならDask/Zarrを使います。
- 多項式・整数・有理数が巨大ならFLINTまたはSageMathへ渡します。
- 32 GB RAMを超える問題は式の疎性、対称性、ブロック構造を先に利用します。
- GPU計算はモデルが固まった段階で別プロファイルとして追加します。
