# causal_orders

実行仕様は `universe_lab.qgbench.causal` にあります。

- 非反射性
- 非対称性
- 推移性
- 推移簡約
- ラベル変更の共変性

を `tests/test_qgbench_ads2.py` とベンチマーク `label_invariance` で検査します。
これは Lean による形式証明ではなく、有限行列上の executable specification です。
