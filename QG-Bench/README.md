# QG-Bench v0.1

量子重力の「候補を作る」前に、既知結果を再現し、仮定の混線と数値的な
過学習を検出するための実行可能な基盤です。この版は新しい量子重力理論を
主張しません。

## 実行

リポジトリ直下で次を実行します。

```powershell
uv run python -m universe_lab.qgbench.cli --quick
uv run python -m universe_lab.qgbench.cli
```

前者は CI 用の smoke test、後者は固定 seed の v0.1 再現実験です。結果は既定で
`results/qgbench_v0.1.json` に保存されます。Atlas と Claim Graph だけを検査する場合:

```powershell
uv run python -m universe_lab.qgbench.cli --validate-only
```

## 収録する成果物

- A — `schema/theory_card.schema.json` と `atlas/*.yaml`
- B — `schema/claim.schema.json` と `claims/*.jsonl`
- C — 実行可能なベンチマーク群
- D — `ads2_scalar_propagator` の独立実装
- E — 密度収束、seed、保留曲率、ラベル不変性を含む反証・誤差分析
- F — `models/causal_information_v0/spec.json`

`.yaml` は JSON 互換 YAML 1.2 とし、環境依存の YAML パーサーなしで読めるように
しています。

## 学習・検証・保留の分離

| 分割 | 内容 | 係数調整 |
|---|---|---|
| calibration | AdS1+1、自由スカラー、固定された解析式 | 解析式から固定 |
| validation | seed と点密度を変更した収束 | 禁止 |
| held out | 曲率半径 0.7 と 1.4 | 禁止 |
| future holdout | 2+1 次元、BTZ、相互作用場 | v0.1 では未開封 |

## 合格が意味すること

`ads2_scalar_propagator` の合格は、有限の指定範囲で、集合平均した離散値の
ビン平均誤差が密度とともに減ったことだけを意味します。連続極限の解析的証明、
背景独立な力学、量子重力、あるいは時空創発の証明ではありません。

`geometry_reconstruction` は、明示的に与えた
`I=I0 exp(-d/xi)` を逆変換できるかだけの smoke test です。相互情報量から自然界の
距離が創発するという証拠ではありません。

## 直ちに不合格にする条件

- 同じ試験で seed を変えると結論が反転し、集合平均でも安定しない
- 密度を増やしても誤差が減らない
- 曲率半径を変えるために質量・作用係数・ビン規則を再調整する
- ラベル変更で抽象的に同じ因果集合の結果が変わる
- Choi 行列に負固有値が出る、またはトレース保存性を破る
- toy 幾何だけを合わせ、場の伝播を同じ微視的規則で再現しない

## 主要一次資料

- A. Kastrati and H. Hinrichsen, “Retarded Causal Set Propagator in 2D
  Anti-de-Sitter Spacetime,” [arXiv:2504.12919v1](https://arxiv.org/abs/2504.12919v1).

論文は 2025-04-17 付の preliminary version です。そのため本ベンチは論文の
「excellent agreement」という表現をそのまま採用せず、式、seed、誤差指標、
合否条件を固定して再評価します。
