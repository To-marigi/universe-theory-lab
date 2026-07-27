# Narain–period bridge

## 型付き経路

```text
LocalNarainChart
  -> NarainOrbit
  -> K3PeriodPoint
  -> ModularInvariantPoint
  -> four F-theory fibrations
```

`LocalNarainChart` と `NarainOrbit` は別型である。orbit equality keyに
`tau`、`rho`、二本のraw Wilson lineを使わない。

## forward

quartic coefficientsから

```text
J2 = alpha
J3 = beta
J4 = gamma epsilon
J5 = gamma zeta + delta epsilon
J6 = delta zeta
a^2 = J5^2 - 4 J4 J6
```

をexact symbolicに構成し、既存の独立Weierstrass moduleへ渡す。standard、
base-fiber-dual、alternate、maximalの四presentationは全て判別式を持つ。

判定: `FORWARD_FOUR_FIBRATIONS_PASS`

## reverse

必要なのはWeierstrass modelから正則二形式を作り、production側の `Jk` 代入式を
逆使用せずにcycle periodsを得て、`O+(L^(2,4))` orbitを比較することである。

現在は次のいずれも実装されていない。

- Picard–Fuchs方程式
- K3二cycleの数値積分
- 独立theta/modular-form実装
- monodromy continuation
- arithmetic orbit reduction

従って `K3PeriodPoint.period_vector` は `null` であり、偽の数値精度や積分誤差を
付与しない。

判定: `PERIOD_ORACLE_BLOCKED`

## round trip

raw coordinate一致は要求しない。要求すべき同一orbit判定も、period vectorとorbit
reductionがないため未実行である。

総合: `DUALITY_PARTIAL`
