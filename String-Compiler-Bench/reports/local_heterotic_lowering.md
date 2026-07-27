# Local heterotic lowering

## 方法

`src/universe_lab/stringbench/narain/roots.py` はF-theory moduleをimportせず、次を行う。

1. `E8` の240 rootsと `D16` の480 rootsを `Fraction` で生成する。
2. 分母3までの有理Wilson-line templateを列挙する。
3. 各候補について `q·A_1, q·A_2 ∈ Z` を満たすrootを残す。
4. positive rootsから既約なsimple rootsを抽出する。
5. 内積からCartan行列を作り、connected componentのrank、determinant、graphから
   `A/D/E` 型を分類する。
6. block交換とcolor交換で明らかに同値なtemplateを探索前に正規化する。

答えのroot数を返す分岐や、F-theory側のADE文字列を読み込む処理はない。

## 発見した局所representative

`0` はzero block、`d=(1/3,...,1/3)` はE8 diagonal、
`x=(0^6,1/3,0)`、`y=(0^7,1/3)` とする。

| branch | lattice | 探索で得た色分け | roots | 自動分類 | U(1) rank |
|---|---|---|---:|---|---:|
| standard | `E8xE8` | `(d,d)` と zero second line | 252 | `E7 + E7` | 2 |
| base-fiber-dual | `E8xE8` | one block `0`、other block `(x,y)` | 300 | `D6 + E8` | 2 |
| alternate | `D16` | coordinate colors `12+2+2` | 268 | `A1+A1+D12` | 2 |
| maximal | `D16` | coordinate colors `14+1+1` | 364 | `D14` | 2 |

全ての半単純rankは14である。したがってsourceが表示する「非可換gauge algebra」と、
Cartan全rank 16を混同せず、消失rankを二つのabelian sectorとして記録する。

## 判定

`LOCAL_HETEROTIC_LOWERING_PASS`

ただしこれはsemiclassical local chartのzero-winding gauge-root sectorに限る。
発見したrepresentativeがsourceのglobal Narain orbitを一意に表す、または四つのK3
fibrationと独立に結合できた、という判定ではない。
