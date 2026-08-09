# Paper I v0.4.2: Zenodo手動アップロード・チェックリスト

**このレコードは既に公開済みです。** オーナーは2026-08-09にZenodo上で本レコードを直接公開しました:
https://zenodo.org/records/21861533 、version DOI `10.5281/zenodo.21861533`、concept DOI `10.5281/zenodo.21861532`、束縛コミット `1ba7a1e3e92d91edaca34f357d7cc6a2a2105ff2`。
三方向の読み戻し検証は `reports/v0.4.2_paper1_zenodo_publication_readback_2026-08-09.md`、それに基づくオーナー決定の記録は `reports/v0.4.2_paper1_owner_decision_amendment_2026-08-09.md` を参照してください。以下のチェックリストは、このバージョンの公開作業そのものはもう完了済みであることを前提に、ローカルでの整合性再検証や次バージョン準備のための参照として残しています。

これはPaper Iの新規プレプリントレコードのためのオーナーゲートです。自動投稿スクリプトではありません。凍結済みのv0.3.9ソフトウェアレコードを編集したり、リポジトリルートの `.zenodo.json` / `CITATION.cff` をこのパッケージにコピーしたりしないでください。

承認済みのオーナー方針は `owner_decision.json` と `reports/v0.4.2_paper1_owner_decision_amendment_2026-08-09.md` に記録されています（後者は前身の2026-08-07記録を保存・参照しています）。要点: 公開済みの最終PDFは18ページ・428286 bytes、SHA-256
`c112b987b4efb76312892481dd033598b939a0a8becfc4ac0e0eca4070dbfa2e`、直接プレビュー可能なPDF＋supplement構成が承認済み、Paper Iのライセンスは CC BY 4.0（リポジトリソフトウェアはMITのまま）、初期の関連識別子は `[]`。公開日は `2026-08-09`、DOIは `10.5281/zenodo.21861533`、最終コミットは `1ba7a1e3e92d91edaca34f357d7cc6a2a2105ff2` として記録済みです。draft作成・submission・deposit・publicationはすべて完了済み（`release_gates` で `true`）。DOIのdraft予約は一度も要求していません（`doi_reserved: false` のまま）。

**文献ゲートは現行のものです。** `2026-08-07T1600Z` predraftゲートは現行候補
`c112b987b4efb76312892481dd033598b939a0a8becfc4ac0e0eca4070dbfa2e` に対して切られ、現行の権威です: `verify_paper1_bundle.py` の `ZENODO_PREDRAFT_*` 束縛はこれを指しています。固定submittedDateウィンドウ内で、`2026-08-06T2315Z` ゲート以降に実際のarXivインデックス追いつきが発生していました（722 -> 908件）。このまだ閉じたウィンドウ内で追加・欠落・版更新・新規ルール該当となったIDはすべて個別にタイトル/アブストラクトでレビューされ、C1--C5に対して非重要と判定されています。詳細は
`reports/v0.4.2_paper1_zenodo_predraft_literature_gate_2026-08-07_20260807T1600Z.md`
を参照してください。superseded（置き換え済み）の `2026-08-06T2315Z` ゲート（取り下げられた `9f58867d…fd43` 候補に対して切られたもの）は、supplement内の歴史的な前身文書としてのみ束縛されています。

**現行PDFバイトのオーナー受諾は記録済みで、本レコードは公開済みです。** 現行バイトの全ページ目視QAは、最後の追記を行ったアシスタントセッションが実施したものであり、オーナー本人によるものではありません。オーナーはこれとは別に、これらの正確なバイト（SHA-256
`c112b987b4efb76312892481dd033598b939a0a8becfc4ac0e0eca4070dbfa2e`）を
`reports/v0.4.2_paper1_owner_decision_amendment_2026-08-09.md` の記録に基づいて受諾しており、`build_paper1_bundle.py`/`verify_paper1_bundle.py` はこの受諾文を必須フラグメントとして束縛しています。**次バージョン**を準備する際には、直前に改めて日付付きの文献ゲートを切る必要があります: 日付付きゲートはその時点限りの証拠であり、恒久的な保証ではありません。ローカルでビルドしたバンドルの `remote_visibility` は `NOT_VERIFIED_BY_BUILDER` のままですが、これはbuilderがGitのremote可視性を検証しない仕様であることによるもので、Zenodo公開そのものとは無関係です（公開はオーナーが直接実施済み）。

## 0. パッケージ化前のオーナー決定事項

- [ ] オーナーが最終ソースコミットと最終検証済みPDFを選定済みである。
- [ ] オーナーが下記の **PDF＋supplement構成**（デフォルト）を承認している。
- [ ] 旧来の単一外側アーカイブは歴史的候補としてのみ保持され、新しいZenodoアップロード構成ではない。
- [ ] 公開日・ライセンス・関連識別子・DOIの扱い・最終publish操作について、オーナー決定がある。
- [ ] 本番ワークシートは `license = CC BY 4.0` を保持している。リポジトリのMITソフトウェアライセンス決定を置き換えないこと。

メタデータワークシートはUIワークシートであり、Zenodo APIペイロードではありません。null になっているオーナー項目は、これらのツールによって黙示的に埋められることはありません。

## 1. デフォルトのPDF＋supplement一式をビルド・検証する

リポジトリルートから、最終生成PDFが存在する状態で:

```powershell
uv run python scripts/normalize_v042_paper1_zenodo_predraft_gate_20260807T1600Z.py --check
uv run python zenodo/paper1-v0.4.2/build_paper1_bundle.py `
  --output-dir ..\paper1-v0.4.2-upload `
  --commit <owner-approved-final-commit>
uv run python zenodo/paper1-v0.4.2/verify_paper1_bundle.py `
  --root ..\paper1-v0.4.2-upload
```

- [ ] builderとverifierの両方が正常終了する。
- [ ] 出力ディレクトリがリポジトリ外にあり、新規または空だった。
- [ ] builderのサマリーとsupplementの `upload_checksums.json` が
      `source_commit_binding.status = PRODUCTION_COMMIT_BOUND`、
      フル40桁16進の選択済みコミット、正規リポジトリURL、
      `tree_url = null` / `remote_visibility = NOT_VERIFIED_BY_BUILDER`（オーナーがremote visibilityを検証するまで）を示している。この束縛のチェック済みソースハッシュ／サイズは `manifest.files` を過不足なくカバーしており、自動追加される
      `results/v0.4.2_paper1_witness_tables.json` witnessも含む。
- [ ] 出力ディレクトリに**ちょうど2ファイル**が存在する:

      `paper1_statewise_operator_v0.4.2.pdf`
      `paper1_statewise_operator_v0.4.2_supplement.tar.gz`

- [ ] builderのサマリーとverifierのワークシートの両方が
      `layout = pdf_and_supplement` を示し、まさにこの2つのZenodoファイルを列挙している。
- [ ] スタンドアロンPDFのSHA-256／バイト数、supplementのSHA-256／バイト数とmanifestのsemantic digest、PDFページ数、選択済みコミットをリリースノートに記録する。
- [ ] builderサマリー内のオーナー決定アーティファクト／レポートのハッシュ、および全リリースゲートがfalseのままであることを確認する。

strict verifierは、決定的なgzip/tarメタデータ、外側・内側両方のmanifest digest、メンバーのハッシュ／サイズ、最終PDFのソース／レポート束縛、メタデータのclaimフラグメント、そして禁止パス・想定外パスが存在しないことをチェックします。

ローカルの非本番プレビュー用途に限り、`--commit <owner-approved-final-commit>` の代わりに `--unbound-preview` を指定できます。この場合supplement manifestは明示的に `status = UNBOUND_PREVIEW`、`commit = null` としてマークされ、strict verificationはこれを拒否します。Git blob束縛を持たないため、アップロードやリリースワークシートとして使用してはいけません。

## 2. Zenodoに投稿する正確なファイル一覧（デフォルト）

**2つ**のファイルを、正確に以下の名前でアップロードしてください:

```text
paper1_statewise_operator_v0.4.2.pdf
paper1_statewise_operator_v0.4.2_supplement.tar.gz
```

supplementの `upload_checksums.json` はソースメンバーを記録し、選択済みソースコミット束縛を埋め込み、スタンドアロンPDFをSHA-256で束縛します。2つ目のPDF、生の参照PDF/テキスト、retrieval receipt、生のAtomレスポンス、リポジトリスナップショットは追加しないでください。

## 3. 歴史的な単一アーカイブの位置づけ

`paper1_statewise_operator_v0.4.2_zenodo.tar.gz` は歴史的なローカル候補にすぎません。現行のZenodoプレプリントレコードにはこれを選択しないでください。単一ファイル形式のためPDFの直接プレビューができず、現行のDOI方針より前のものです。整合性／来歴比較の目的に限り、`verify_paper1_bundle.py --archive` でオフライン検査できます。strictな `--root` 検証は、たとえ整合性が通ったとしても、これを現行アップロード構成として不適格と判定して拒否しなければなりません。レガシーな外側ラッパーは `commit_binding_embedded = false` と報告することがありますが、これはラッパーについてのみ言及したものです。新しい歴史的ラッパーは、本番または明示的な `UNBOUND_PREVIEW` 束縛を内側supplementの `inner_supplement.source_commit_binding` に配置します。その項目を持たない古い内側supplementは、明示的な `--archive` 整合性モードでのみ受け付けられ、現行の来歴や現行アップロード候補としては受け付けられません。

## 4. Zenodo draftのメタデータ

- [ ] **新規アップロード**を作成する（v0.3.9ソフトウェアレコードの「new version」ではない）。
- [ ] Resource type: `Publication / Preprint`。
- [ ] Title: `Statewise versus operator Bell causality in finite quantum
      sequential growth: exact separation and recovery at dimension two`（英語のまま、原文どおり貼り付け）。
- [ ] Creator: `Osaki, Kenichi`；ORCID `0009-0003-9256-7089`；affiliation
      `Independent researcher`（いずれも原文どおり貼り付け）。
- [ ] Language: `English`；version: `0.4.2`；access: `Open`。
- [ ] `ZENODO_FORM_VALUES.md` から公開アブストラクトとキーワードをコピーする。
      詳細スコープテキストは **Additional descriptions → Technical
      info** に、AI開示は **Additional descriptions →
      Other** に追加する。内部的なclaim境界の詳細をメインの公開descriptionには入れないこと。
- [ ] オーナーが明示的に別の判断をしない限り、communities・funding・関連識別子は空のままにする。
- [ ] ローカルワークシートの公開日はnullのままにする。Zenodoは必須のdraft-date欄をあらかじめ埋めることがあるが、その保存済みdraftの日付を公開日として扱わないこと。公開前に、オーナーが実際の初回公開Zenodo日を確認・記録すること。
- [ ] Paper IにはCC BY 4.0を使用する。リポジトリソフトウェアライセンスはMITのまま。
- [ ] DOI方針は**draft予約なし**: DOI欄は空欄のままにし、「Get a DOI
      now!」は**クリックしない**。Zenodoはpublication時にDOIを割り当て・登録する。

## 5. Save draft・プレビュー・publishゲート（このバージョンは完了済み）

- [x] 現行候補に対する文献ゲートが切られ、チェックされ、記録済み
      （`2026-08-07T1600Z`、`verify_paper1_bundle.py` の
      `ZENODO_PREDRAFT_*` 束縛がこれを指している）。
- [x] 現行PDFバイト
      （`c112b987b4efb76312892481dd033598b939a0a8becfc4ac0e0eca4070dbfa2e`）のオーナー受諾は
      `reports/v0.4.2_paper1_owner_decision_amendment_2026-08-09.md` に記録済み。builder・verifierの両方がこのフラグメントに対してfail closedしている。
- [x] オーナーがdraftを作成・保存し、プレビューを確認した（Zenodo UI上で直接実施）。
- [x] 表示されたアップロードファイル一覧・バイト数／チェックサムを記録済み: `paper1_statewise_operator_v0.4.2.pdf`（428286 bytes）、`paper1_statewise_operator_v0.4.2_supplement.tar.gz`（144797 bytes）— `reports/v0.4.2_paper1_zenodo_publication_readback_2026-08-09.md` 参照。
- [x] draft URL、正確なコミット（`1ba7a1e3e92d91edaca34f357d7cc6a2a2105ff2`）、記録済みの全SHA-256値、構成、オーナー専権のメタデータ選択はオーナーに提示済み。
- [x] オーナーがこのdraftをpublishすることを明示的に承認し、実施した。
- [x] 一度だけpublishした。v0.3.9ソフトウェアレコードは上書きしていない。

**次バージョンを準備する場合**は、直前に改めて日付付きの文献ゲートを実行すること。日付付きゲートはその時点限りの証拠であり、恒久的な保証ではない。

## 6. Publication後の読み戻し（完了済み）

- [x] 公開レコードURL・version DOI・concept DOI・公開日・公開タイムスタンプを記録済み:
      https://zenodo.org/records/21861533 、`10.5281/zenodo.21861533`（version DOI）、
      `10.5281/zenodo.21861532`（concept DOI）、公開日 `2026-08-09`。
- [x] 公開ページ／APIから、メタデータと正確なファイル名／バイト数／チェックサム一覧を読み戻し、ローカルワークシートと比較済み。
- [x] 公開済みファイルをダウンロードし、ローカルのSHA-256値と比較済み（完全一致）。ダウンロードした両ファイルに対して
      `verify_paper1_bundle.py --root <directory>` を再実行し、strict verificationが全カテゴリ空でパスした。
- [x] DOIとsupplementのsource-commit束縛、最終外部receiptをリリースノート
      （`reports/v0.4.2_paper1_zenodo_publication_readback_2026-08-09.md`）に保存済み。

後の科学的変更やファイル変更は必ず新しいversionとして扱い、このレコードをその場で書き換えないこと。
