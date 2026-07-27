# Mutation report

次のmutationは正常系と同じコード経路で検出されなければなりません。

- lattice signatureの反転
- Wilson lineの欠落
- discriminantの符号または次数変更
- Mordell–Weil torsionの欠落
- validity domain外へのmap適用
- raw座標のframe間直接比較
- ADE/gauge algebraの誤対応
- branch tagの不正な同一視

未実装または一次資料不足で注入できないmutationをPASS扱いにせず、結果JSONに
`BLOCKED` として残します。

## v0.1実行結果

検出 `4/8`、総合 `PARTIAL`。

| mutation | 結果 |
|---|---|
| lattice signature反転 | DETECTED |
| discriminant次数変更 | DETECTED |
| Mordell–Weil torsion欠落 | DETECTED |
| validity domain外入力 | DETECTED |
| Wilson line一本欠落 | BLOCKED |
| raw座標直接比較 | IUT型安全層ではDETECTED、物理round-tripではBLOCKED |
| gauge algebra誤対応 | BLOCKED |
| branch不正同一視 | 型安全層ではDETECTED、四分岐round-tripではBLOCKED |

全critical mutation検出というv0.1 PASS条件は満たしていない。
