# String-Compiler Bench v0.1

既知の八次元 F-theory / heterotic 双対性を、フレーム固有座標を直接比較せず、
型付き `VacuumIR` と `DualityLinkCertificate` を介して検査する研究用ベンチです。

この版は超弦理論の完成、現実宇宙の選択、4次元標準模型の導出を主張しません。

## コマンド

```powershell
uv run stringbench audit
uv run stringbench duality --suite f-heterotic-8d
uv run stringbench iut-bridge
uv run stringbench report
uv run stringbench --suite all
```

## v0.1の対象

一次資料 [arXiv:2205.08100](https://arxiv.org/abs/2205.08100) が分類する
`H ⊕ E7(-1) ⊕ E7(-1)` 偏極 K3 の四つの非同値なJacobian楕円ファイブレーション:

| ID | Generic singular fibers | MW | 論文が対応させる8D gauge algebra |
|---|---|---|---|
| standard | `2 III* + 6 I1` | trivial | `e7 + e7` |
| alternate | `I8* + 2 I2 + 6 I1` | `Z/2Z` | `so(24) + su(2)^2` |
| base-fiber-dual | `II* + I2* + 6 I1` | trivial | `e8 + so(12)` |
| maximal | `I10* + 8 I1` | trivial | `so(28)` |

F-theory側ではWeierstrass式から判別式と消失次数を計算します。heterotic側について、
論文は一般の非幾何学的Narainモジュライを扱い、通常の意味で分離された二本の
Wilson線ベクトルを全四分岐について入力データとして与えていません。このため、
独立なWilson線root enumerationを実行できない分岐は `BLOCKED` とし、論文の対応表を
独立計算と偽ってハードコードしません。

## 証拠状態

`EXACT_SYMBOLIC` は有限の代数式を記号計算で確認したことだけを表します。
`NUMERICALLY_REPRODUCED` は任意精度評価の再現です。双対性の物理的正しさや
非摂動的完成を自動的に意味しません。

IUTについては型安全設計と物理bridgeを分離し、明示的なinitial theta dataへの写像が
なければ `IUT_TYPE_SYSTEM_ONLY` または `IUT_NOT_APPLICABLE` と判定します。
