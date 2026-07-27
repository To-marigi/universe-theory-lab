# Global coordinate obstruction

局所chartでは `tau`、`rho`、`A1`、`A2` を使える。一方、大域対象は

```text
[varpi] in D_(2,4) / O+(L^(2,4))
```

であり、arithmetic dualityは幾何moduliとWilson-line成分を混合しうる。
従って異なるlocal chartが同じorbitを表しても、raw coordinate tupleを等値比較しては
ならない。

v0.2では次を型で強制する。

- `LocalNarainChart` はraw coordinate、chart ID、validity domainを持つ。
- `NarainOrbit` はarithmetic group、orbit certificate、monodromy evidenceを持つ。
- 未計算のperiod vectorは `null` とし、local tupleをperiod vectorへコピーしない。
- reverse mapはraw Wilson-line tupleの再現をPASS条件にしない。

現状のorbit certificateは型付きplaceholder hashであり、arithmetic reductionの証明書
ではない。この点を理由に、

`GLOBAL_WILSON_COORDINATES_NOT_DEFINED`

と判定する。これは実装失敗ではなく、大域座標を不当に仮定しないための停止状態である。
