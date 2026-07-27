# Assumption audit

## AdS1+1 再現

- 背景は固定された AdS1+1。背景独立な力学の試験ではない。
- 自由な実スカラー場で、相互作用はない。
- 連続 oracle は主値の時間的測地線が定義できる対に限定する。
- 菱形 cutoff を使う。
- 点数を固定するため、Poisson 過程を `N` で条件付けた標本である。
- 論文 Eq. (52) の自由度は `alpha=-1` に固定され、Eq. (56) を使う。
- 曲率を変える保留試験で質量や作用係数を再調整しない。
- 伝播関数の一致は集合平均について評価し、個々の行列要素の一致を要求しない。

## 量子情報模型

- Hilbert 空間は有限次元。
- v0 の channel test は qubit depolarizing channel の既知例。
- 相互情報量からの距離復元は指数 kernel を先に仮定した smoke test。
- `Phi_info` の状態和、測度、収束性は未定義であり、完成した力学ではない。

## 証拠状態

- 行列恒等式と有限半順序の性質: `FORMALLY_DERIVED`
- 有限 seed の収束傾向: `NUMERICALLY_SUPPORTED`
- 一般の連続極限・Hauptvermutung: `CONJECTURAL`
- toy 相互情報量距離: `HEURISTIC`
