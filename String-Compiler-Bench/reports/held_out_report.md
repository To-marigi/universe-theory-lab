# Held-out report

## 固定方針

- maximal fibrationを少なくとも一つの構造保留対象とする。
- `J4=0` と `J4=J5=0` のenhancement locusは実装時の汎用式から導出する。
- ランダム有効点はseedを固定し、少なくとも25%を保留する。
- 保留点で閾値、係数、規約を再調整しない。

保留対象を実装式やfixtureへ写した場合はデータ漏洩としてFAILにします。

## v0.1判定

`BLOCKED`。

maximal fibration自体の係数・判別式・主要消失次数は記号計算できたが、heterotic側の
四分岐 lowering が未確定なため、フレーム横断の保留fibration/locusをデータ漏洩なしに
構成できない。F-theory側だけの成功をheld-out duality PASSへ格上げしない。
