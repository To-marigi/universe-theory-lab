# F-theory / heterotic duality report

## 判定欄

機械可読な最終結果は `results/stringbench_v0.1.json` に生成済みです。

v0.1では次を別判定にします。

- 四つのF-theory Weierstrass模型の記号検査
- Kodaira/ADE導出
- Mordell–Weil既知データとの整合
- 型付きVacuum IRへのlowering
- heterotic側の独立root enumeration
- round trip
- held-out / mutation

F-theory側だけがPASSし、heterotic側の独立入力が一次資料に不足する場合、総合判定は
`PARTIAL` または `BLOCKED` であり、`KNOWN_8D_DUALITY_REPRODUCED` とはしません。

## v0.1実行結果

- 四つのWeierstrass係数写像: `EXACT_SYMBOLIC`
- 四つの判別式の全次数: すべて24
- 基底上の主要消失次数:
  - standard: `(3,5,9)` を二箇所、`III* / E7`
  - alternate: `(2,3,14)`、`I8* / D12`
  - base-fiber-dual: `(2,3,8)` と `(4,5,10)`、`I2* / D6` と `II* / E8`
  - maximal: `(2,3,16)`、`I10* / D14`
- `H⊕E7(-1)^2`: rank 16、signature `(1,15)`、discriminant order 4
- Narain格子: rank 20、signature `(2,18)`、even unimodular
- heterotic zero-Wilson-line sanity: 480 roots
- 四分岐の明示的Wilson-line lowering: `BLOCKED`
- 双方向round trip: `BLOCKED`
- 総合: `PARTIAL`

したがって許される主張は
`FOUR_F_THEORY_FIBRATIONS_SYMBOLICALLY_CHECKED` までです。
