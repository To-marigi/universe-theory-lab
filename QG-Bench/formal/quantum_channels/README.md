# quantum_channels

v0 は規格化 Choi 状態を用いて、有限次元チャネルの次を検査します。

- Choi 行列の正半定値性（完全正値性）
- 出力部分トレースが `I/d`（トレース保存性）

実装は `universe_lab.qgbench.quantum`、回帰試験は
`tests/test_qgbench_quantum.py` です。チャネル容量の一般公式や因果集合への
一意な割り当ては未解決で、v0 の証明対象ではありません。
