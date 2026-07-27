# Research log — 2026-07-28

## String-Compiler Bench

`arXiv:2205.08100v1` を主資料、`arXiv:1908.09578v4` を四fibrationの数学的分類資料
として使用した。

確認・実装した範囲:

- `J2,...,J6` と `a^2 = J5^2 - 4 J4 J6`
- standard、base-fiber-dual、alternate、maximalの四Weierstrass presentation
- generic fiber/ADE dataとMordell–Weil metadata
- `E8`、`D16` root生成
- 有理Wilson-line候補探索
- `E7+E7`、`E8+D6`、`D12+A1+A1`、`D14` の局所root lowering

確認できなかった範囲:

- K3正則二形式の独立cycle integration
- Picard–Fuchsまたは独立theta実装
- `O+(L^(2,4))` arithmetic orbit reduction
- K3から同一Narain orbitへ戻るreverse certificate
- global gauge-group formの独立再構成

従って科学判定は `DUALITY_PARTIAL`、periodは `PERIOD_ORACLE_BLOCKED`。

## QG-Bench

`arXiv:2504.12919v1` をAdS1+1 causal-set retarded propagatorの再現対象として使用した。
小さいNと固定seed群で有限サイズ数値再現を得たが、論文規模の全実行、複数収束モデル、
解析的連続極限は未達である。

判定は `SMALL_N_REPRODUCTION_PASS` と
`NUMERICALLY_SUPPORTED_AT_SMALL_N` を越えない。

## IUT

EMS PressのIUT I公式ページで公開されている書誌・abstractから、initial Theta-dataが
数体上の楕円曲線、素数 `l >= 5`、その他の技術条件を要求することを確認した。

現在のcomplex K3/Narain period dataから、その算術データへの自然で物理的不変な写像は
見つかっていない。従って `IUT_TYPE_SYSTEM_ONLY` を維持し、IUT固有の物理bridgeとは
呼ばない。
