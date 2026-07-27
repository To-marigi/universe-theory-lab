# Hypothesis Space v0.1

## 探索変数

中心候補は、有限DAG、辺Hilbert空間、頂点CPTP写像、境界状態からなる。探索対象は
グラフの同型類、有限次元、CPTP写像、状態、最大4個の作用演算子とその係数である。

巨大なニューラルネットに作用を直接生成させない。各候補は、どの演算子がどの結果に
寄与したかを追跡可能でなければならない。

## v0.1演算子

| 演算子 | 種類 | 現在の証拠 |
| --- | --- | --- |
| order interval vector | 因果順序 | 有限対象で厳密 |
| discrete curvature | 因果順序 | 次元・連続近似条件に依存 |
| graph spectrum | 因果順序 | heuristic |
| mutual information | 有限量子状態 | 厳密 |
| conditional mutual information | 有限量子状態 | 厳密 |
| channel information | 有限量子チャネル | bound/proxyを明記 |
| local causal defect | 因果順序 | 有限対象で厳密 |

## 事前に禁止する入力

- 目標の背景計量
- 3+1次元という答えを固定する埋め込み座標
- Einstein方程式またはFierz-Pauli作用
- Spin-2射影子を含む損失関数だけによる認定
- 保留集合を見た後の演算子追加・係数再調整

## 比較候補

`causal_set_amplitude_family` と `quantum_channel_network_family` を同じゲートで比較する。
候補間で異なる用語を使っても、合格条件は緩めない。
