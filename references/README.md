# Local research library

このディレクトリは、QG-BenchとString-Compiler Benchで実際に参照した一次資料を
オフラインで再確認するためのローカル資料庫である。

## 構成

```text
references/
  sources.json   書誌、版、取得URL、用途、主張境界
  manifest.json  ローカルPDFのSHA-256、サイズ、ページ数、検索テキスト
  papers/        取得した版指定PDF
  text/          PDFから抽出したUTF-8検索用テキスト
  notes/         このプロジェクトでの読み方と判断履歴
```

## 検索

```powershell
rg -n -i "period|Wilson line|Mordell.Weil|B.field" references/text references/notes
```

PDFと検索テキストは同じstemを使う。正確な数式、図、ページ構造を確認するときはPDFを
正とし、抽出テキストは検索索引としてのみ使う。

## 更新

PDFを追加したら `references/sources.json` に版指定URLとclaim boundaryを登録し、
次を実行する。

```powershell
python scripts/archive_references.py
```

`pypdf` がない環境では `--skip-text` でhash-only manifestを作れる。ネット上の資料を
将来更新版へ差し替える場合も、既存版を上書きせず別ファイルとして保存する。

## 運用原則

- arXiv IDだけでなく `v1`、`v4` など実際に読んだ版を固定する。
- URL、取得日、SHA-256、研究上の用途を残す。
- 論文の主張、プロジェクトの独立導出、未実装部分を分離する。
- 購読制限のある文献はアクセス制御を迂回せず、公式書誌と参照した公開情報だけを残す。
- 今後の調査ではまずこの索引を検索し、追加調査した資料も同じ形式で追記する。
