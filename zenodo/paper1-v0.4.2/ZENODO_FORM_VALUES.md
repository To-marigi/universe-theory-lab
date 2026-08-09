# Paper I v0.4.2 — Zenodoフォーム入力値

このワークシートは**draftの作成のみ**を完了させるためのものです。publication・DOI予約・manuscript freeze・Git pushを承認するものではありません。`owner_decision.json` の全リリースゲートは、保存済みの外部draftがローカルに記録され、後にオーナー専権の承認が与えられるまで `false` のままです。

Zenodoレコード `21720863`（別の v0.3.9 ソフトウェアレコード）の「new version」ではなく、**新規アップロード**を作成してください。

`2026-08-07T1600Z` predraft文献ゲートは完了済み・現行のものです: 候補
`c112b987…fa2e` に対して切られ、`verify_paper1_bundle.py` に束縛されています。固定submittedDateウィンドウ内で、前身の `2026-08-06T2315Z` ゲート以降に実際のarXivインデックス追いつきが発生していました（722 -> 908件）。すべての差分は個別にレビューされ非重要と判定されており、追跡対象の2レコードは `v1` のままです。`2026-08-06T2315Z` ゲート自体はsupersededのPDF `9f58867d…fd43` に対して切られたもので、現在は歴史的な来歴としてのみ、文書化された前身として保持されています。

**現行PDFバイトのオーナー受諾は記録済みですが、このワークシート単独ではSave draftを承認しません。** 現行バイトの全ページ目視QAは、最後の追記を行ったアシスタントセッションが実施したものであり、オーナー本人によるものではありません。オーナーはこれとは別に、これらの正確なバイトを
`reports/v0.4.2_paper1_owner_decision_amendment_2026-08-07.md` の記録に基づいて受諾しており、builder・verifierの両方がこの記録に対してfail closedしています。ここに記載されている内容は、publication・DOI予約・Git push・manuscript freeze・depositのいずれも承認するものではありません。これらのリリースゲートは `false` のまま、`remote_visibility = NOT_VERIFIED_BY_BUILDER` もオーナー検証待ちのままです。

## 主要項目（Core fields）

| Zenodoフィールド | 最終入力値 |
| --- | --- |
| Resource type | `Publication` → `Preprint` |
| Title | 下記のtitleをそのままコピーする。 |
| Do you already have a DOI? | `No, I need one` |
| Version | `0.4.2` |
| Access right | `Open` |
| License | `CC BY 4.0` |
| Language | `English` |

### Title（原文どおり貼り付け）

```text
Statewise versus operator Bell causality in finite quantum sequential growth: exact separation and recovery at dimension two
```

### Creator

| Creatorフィールド | 最終入力値 |
| --- | --- |
| Person type | `Person` |
| Given name | `Kenichi` |
| Family name | `Osaki` |
| Citation display | `Osaki, Kenichi` |
| ORCID | `0009-0003-9256-7089` |
| Affiliation | `Independent researcher` |

まずORCIDで検索し、一致する `Kenichi Osaki` プロファイルを選択してください。手動入力が必要な場合は、上記のgiven/family名を分割したものを使用してください。`Independent researcher` は承認済みの非所属機関表記です。所属機関を創作しないでください。

### Main public description（原文どおり貼り付け）

これをメインの **Description** フィールドに貼り付けてください。これは一般公開向けの英語アブストラクトであり、内部の完全なclaim ledgerではありません。

```text
We present a bounded analysis of the finite, nonsingular, occurrence-ON quantum sequential-growth presentation at dimension d=2 and source stages n<=4. The preprint records five ledger-bound results: a frozen strong/strong commutativity baseline; an exact rational fixed-vector/general-covariance and reachable-state/martingale witness of noncommutativity; a source-native Eq. (120) lemma; commutativity on a proper reconstruction slice; and conditional statewise-to-operator recovery lemmas. Its purpose is to make the distinction between statewise and operator semantics auditable, rather than to classify all finite semantics. In particular, it does not claim the full 955 or 721 profiles, a complete finite occurrence-ON classification, or a reachable-visible witness. The bounded U2 auxiliary-ideal investigation is retained as a reproducibility and resource-boundary record, not as a unit-ideal theorem.
```

### Additional descriptions

Zenodoの **Additional descriptions** UIで、以下の2つの独立したエントリを追加してください。それぞれ記載のとおりのtypeを選択し、メインのDescriptionフィールドに統合しないでください。

#### Additional description 1

| フィールド | 値 |
| --- | --- |
| Type | `Technical info` |

Zenodoには追加descriptionの見出し欄が別途ないため、descriptionの最初の一文として見出しを貼り付けてください：

```text
Scope and claim boundary. Paper I is a claim-locked archive/submission candidate giving a scoped characteristic-zero interpretation of exact QQ certificates for finite quantum sequential growth at dimension d=2, source stages n<=4, declared nonsingular transitions, and certified occurrence-ON artifacts. C1 is the frozen v0.3.7/v0.3.9 literal strong-GC/strong-MSR comparison baseline, which forces Q1 through Q4 commutativity on its recorded denominator-open 21-chart/S3 certificate and does not use Q5. C2 is an exact rational weak/weak separation: fixed-vector GC plus reachable-state MSR admits a noncommutative witness, but its reachable span has rank one, so the witness is not claimed to be reachable-visible. C3 proves the six raw antichain CPOBC source identities behind Eq. (120) from source nonsingularity alone. C4 proves commutativity only on the proper reconstruction slice P_sGC+rMSR intersect image(Phi_U), not on the full 955 profile or its image complement. C5 gives conditional statewise-to-operator recovery: evaluation injectivity on the declared residual family is necessary and sufficient, with exact same-residual two-probe and non-scalar 2x2 centralizer endpoints; the ordinary single-Omega profile is not claimed to supply those probes. The explicit nonclaims N1--N6 cover the full 955 and 721 profiles, a complete finite ON lattice, reachable-visible weak noncommutativity, a full U2 ideal theorem, occurrence-OFF classification, relation minimality, n>=5, d>=3, singular transitions, and infinite-system conclusions. Scientifically, the global SR2-V status remains SEARCH_OPEN_NO_TERMINAL, U2 remains SOFT_RESOURCE_LIMIT_NONTERMINAL, and u2_is_global_terminal=false. The Paper I editorial disposition is PAPER_I_SCOPED_U2_RESOURCE_OPEN_LIMITATION_ACCEPTED; this is a scoped resource-open limitation, not a QQ theorem or a terminal verdict. The upload excludes third-party reference PDFs/texts and vendored archives; the complete weak electronic ledger remains authoritative, while the compact supplement is an authenticated navigation and selected-witness layer. Full reproduction requires the repository, pinned toolchains, and its exact claim-bound evidence.
```

#### Additional description 2

| フィールド | 値 |
| --- | --- |
| Type | `Other` |

こちらも同様に、別途見出し欄がないためdescription内に見出しを貼り付けてください：

```text
Authorship and AI assistance. The human author is responsible for all claims. OpenAI Codex (Luna/Sol) and Anthropic Claude assisted bounded implementation, audit, and drafting; AI systems are not authors and are not proof authorities.
```

### Keywords（原文どおり貼り付け）

以下を個別のkeywordとして入力してください：

```text
causal sets
quantum sequential growth
finite quantum sequential growth
Bell causality
CPOBC
statewise observability
statewise-to-operator recovery
exact rational certificates
noncommutative matrices
operator semantics
exact symbolic computation
computer-assisted proof
reproducibility
```

## 空欄のままにする項目

| Zenodoフィールド | 最終値 |
| --- | --- |
| Communities | 空（`[]`） |
| Funding | 空（`[]`） |
| Related/alternate identifiers | 空（`[]`） |
| Existing DOI | 空（`null`） |
| Additional titles | 空 |
| Contributors | 空；AIシステムはcontributors/authorsではない |
| Additional dates | 空 |
| References | 空；参考文献リストはPDF内にある |
| Repository URL / Software fields | 空；このレコードはPreprintである |
| Journal / imprint / thesis / conference | 空 |
| Domain-specific fields | 空 |

オーナーが後に明示的な決定を記録しない限り、v0.3.9のconcept DOIやcommit URLをrelationとして追加しないでください。

## 公開日とDOI方針

ローカルワークシートの値は `null` のままです：

```text
publication_date = null
doi = null
```

保存済みdraftに対して、Zenodoが日付を必須にしたり、あらかじめ埋めたりすることがあります。そのUI上の値はpublicationの承認ではなく、ローカルに記録された公開日でもありません。publication前に、オーナーが実際の初回公開Zenodo日を確認し、リリースレコードに記録する必要があります。

**DOIについての指示:** `No, I need one` を選択しますが、「Get a DOI now!」はクリックしないでください。方針は次のとおりです（原文）:

"No draft reservation; Zenodo assigns/registers DOI at publication."

（draft予約は行わない。ZenodoはpublicationのタイミングでDOIを割り当て・登録する。）draftフォームに貼り付けるDOIはありません。

`Publisher = Zenodo`、`Visibility = Public` を維持し、embargoは無効のままにしてください。任意のcopyright欄は空欄のままで構いません。CC BY 4.0が引き続き有効な再利用条件です。

## 正確なコミット値

このリポジトリ管理下のワークシートは、自己参照（循環参照）を作らないよう、意図的に自身のコミットをハードコードしていません。本番supplementの `upload_checksums.json` は `source_commit_binding` にフル40桁16進SHA、正規リポジトリURL、チェック済みソースハッシュ／サイズ、自動witnessを埋め込んでいます。builderは選択済みコミットがpush済みかどうかを検証しないため、`tree_url` は明示的に `null`、`remote_visibility = NOT_VERIFIED_BY_BUILDER` のまま、オーナーがremote状態を検証するまで維持されます。アップロードディレクトリの隣に（内部にではなく）生成される `ZENODO_UPLOAD_RECEIPT.md` から同一の正確なSHAをコピーし、両方の値を比較してください。現行の空関連識別子方針の下では、このSHAはローカル検証のための来歴情報であり、Zenodoのフィールドに貼り付けるものではありません。`/tree/<SHA>` リンクを創作したり、古い候補SHAを使ったり、プレースホルダーをZenodoに入力したりしないでください。

publication直前に、改めて日付付きの文献ゲートを実行してください。それによってリリース対象ファイルに変更が生じた場合は、承認済みの変更をコミットし、`--commit` で新しいフルSHAを使って再ビルドし、アップロード一式とreceiptを一緒に差し替えてください。

## ファイル選択

デフォルトのアップロード構成は、正確に以下の2ファイルです：

```text
paper1_statewise_operator_v0.4.2.pdf
paper1_statewise_operator_v0.4.2_supplement.tar.gz
```

supplementは外部PDFをSHA-256で束縛し、選択済みのsource-commit束縛を埋め込みます。2つ目のPDFや、歴史的な `paper1_statewise_operator_v0.4.2_zenodo.tar.gz` アーカイブを追加しないでください。この歴史的アーカイブは現行のDOI方針より前のもので、PDFの直接プレビューを提供しません。2ファイル構成は、その外部receiptが埋め込まれた `source_commit_binding` と同じ本番コミットを示し、strict検証が通る場合にのみ使用してください。追跡対象ワークシートの `archive_sha256` は `null` のままです；外部receiptは自己参照なしに生成済みsupplementハッシュを保持します。`--unbound-preview` のsupplementは
`status = UNBOUND_PREVIEW`、`commit = null` となり、verifierはこれを拒否します。これはアップロード候補には決してなりません。

両ファイルをアップロードした後、スタンドアロンPDFをZenodoのデフォルトプレビューとして明示的に選択し、draftを保存する前に表示されているサイズ／チェックサムを外部receiptと比較してください。アップロードされたsupplementの `source_commit_binding.commit` が外部receiptのSHAと正確に一致することを確認してください。

## Draft限定のhandoff receipt

オーナーが後にZenodo draftを作成・保存した場合は、（publishせずに）以下をローカルに記録してください: draft URL／レコード識別子、作成タイムスタンプ、表示されたファイル名とSHA-256値、UI上の公開日の値、「Get a DOI now!」を使用しなかったことの確認。そのreceiptを得て初めて、`draft_created` を別途オーナー承認済みの更新として検討可能になります。現時点では `false` のままです。
