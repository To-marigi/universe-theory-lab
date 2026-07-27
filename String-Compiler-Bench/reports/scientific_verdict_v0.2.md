# Scientific verdict v0.2

## 判定

| 領域 | 状態 |
|---|---|
| v0.1 freeze | `bench-v0.1-partial` |
| schemas / software | `ENGINEERING_PASS` |
| local heterotic root lowering | `LOCAL_HETEROTIC_LOWERING_PASS` |
| four F-theory presentations | `EXACT_SYMBOLIC` |
| local/global type separation | PASS |
| global orbit reduction | `GLOBAL_WILSON_COORDINATES_NOT_DEFINED` |
| independent K3 periods | `PERIOD_ORACLE_BLOCKED` |
| reverse orbit round-trip | `PERIOD_ORACLE_BLOCKED` |
| held-out | `PARTIAL` |
| mutations | 12/12 |
| IUT | `IUT_TYPE_SYSTEM_ONLY` |
| scientific overall | `PARTIAL` |
| final | `DUALITY_PARTIAL` |

## 到達点

四つのsource-classified gauge algebraについて、F-theoryコードから独立したE8/D16
root moduleが有理Wilson-line representativeを探索し、Cartan/Dynkin型を再現した。
これはv0.1の `heterotic lowering: BLOCKED` を局所範囲で解消する。

## 未到達点

局所representativeをglobal Narain orbitへ同定し、K3から独立計算したperiodで同じ
orbitへ戻す閉路は完成していない。MW torsion、B-field、pointlike instantonのbranch
情報も、現段階では一次資料で束縛したmetadataであり、heterotic計算から全て導出した
ものではない。

従って、

`KNOWN_8D_DUALITY_REPRODUCED`

とは判定しない。許される最終表現は、

> local heterotic gauge-root lowering reproduced; Narain–K3 period
> round-trip remains blocked.

である。
