# CPOBC 研究・出版ロードマップ v0.4--v0.7

決定日: 2026-08-01
位置づけ: v0.3.9 以後の研究順序と論文化判断を固定する作業文書

Current scientific facts and cross-version proof rules are indexed in
[`KNOWLEDGE_BASE_v0.4.md`](../KNOWLEDGE_BASE_v0.4.md). Read it before starting
or resuming any SR3--SR6 implementation. Tools should also read the compact
mutable index [`CURRENT_RESEARCH_STATE.json`](../CURRENT_RESEARCH_STATE.json);
it is navigation metadata, not a proof certificate.

The post-literature strategic authority is
[`v0.4.2_post_literature_strategy_review.md`](v0.4.2_post_literature_strategy_review.md).
It supersedes the earlier ordering where the two one-sided profiles and `n=5`
were treated as mandatory Paper I gates; it does not supersede any certified
theorem, scope correction, or frozen artifact.

## 1. 出版方針の決定

個々の計算結果を独立した査読論文として細分化せず、まず版付きの短報として
証拠・未解決点・再現手順を固定し、それらを二本の主論文へ統合する。

1. **第一論文（数学的中核）**
   - 第一目標誌: *Journal of Mathematical Physics*（JMP）
   - 主題: 有限 CPOBC において、状態上の GC/MSR がどの作用素関係を観測・分離し、
     どの追加条件で `d=2` の作用素恒等式と可換性を回復するか
   - 必要成果: SR1、SR2、SR2-V observability audit、SR3b-M、SR3b-A。
     full SR3 と SR4 は classification/robustness upgrade であり、scoped manuscript の
     絶対 gate にはしない。
2. **第二論文（次元境界と無限系への橋）**
   - 条件付き第一目標誌: *Classical and Quantum Gravity*（CQG）
   - 主題: `d=3` の次元閾値と、有限段階の結果を無限 CPOBC へ移す
     restriction/lifting 問題
   - 必要短報: SR5--SR6
   - CQG を選ぶのは、有限行列分類を越える物理的・構造的意義が得られた
     場合に限る。

JOSS は数学・数理物理の主論文の代替にはしない。コンパイラと証明成果物の
基盤が独立利用可能な研究ソフトウェアへ成熟した場合だけ、別のソフトウェア
論文として検討する。

## 2. 第一論文へ統合する短報

### SR1 -- v0.3.9: strong/strong `d=2` 可換性

- 状態: **完了・公開済み**
- 内容: `n<=4`、非特異、occurrence identification ON、strong GC と
  strong MSR のもとで `Q_1,...,Q_4` の可換性を証明。
- 公開基準: Zenodo v0.3.9 を固定基準とし、凍結済み成果物は改変しない。
- 第一論文での役割: 強い作用素意味論における rigidity 側の定理。
- 文献境界: Xu, arXiv:2607.26672v1（2026-07-29）は self-adjoint finite CPOBC と
  複数の二次元 triangular/extension branch により広い rigidity theorem を持つ。
  v0.3.9 の arbitrary `GL_2`, `n<=4` exact certificate scope は同一ではないが、
  `first d=2 CPOBC rigidity` や self-adjoint/triangular 領域の priority は主張しない。

### SR2 -- v0.4: fixed-vector/reachable-state の厳密反例

- 状態: **研究結果完成、短報・公開版の整備は未完**
- 判定: `WEAK_D2_NONCOMMUTATIVE_WITNESS_CERTIFIED`
- 内容: `n<=4`、`d=2`、非特異、有理係数の厳密な非可換解。
- 必須証拠:
  - CPOBC、GC、MSR、Eq. (113) の両分岐、Eq. (139) の両被覆への直接代入
  - 全遷移行列の行列式非零
  - 全六個の `Q_1,...,Q_4` の交換子非零
  - occurrence identification ON/OFF の両方への適用範囲
  - 独立 oracle による再検算
- 第一論文での役割: source-native な弱い意味論では rigidity が破れるという
  separation theorem。
- prior-art 判定: 2026-08-01 までの bounded audit で同一の exact rational
  weak/weak witness は発見されず、`DISTINCT_CONTRIBUTION_IDENTIFIED`。ただし
  bibliographic absence の絶対主張は行わない。
- 限界: 現反例の reachable subspace は一次元であり、非可換性は初期状態から
  到達する ray 上では観測されない。この点を物理的非可換性として誇張しない。

### SR2-V -- v0.4-V: reachable observability strengthening

- 状態: **文献調査後に新規登録。exact audit と counterexample-first search は未実装**
- 現 SR2 witness を `operator_noncommutative=true`, `reachable_span_rank=1`,
  `reachable_visible=false` と machine-readable に固定する。
- 将来の witness では reachable-span rank と、stage/source-compatible reachable state 上の
  `[Q_i,Q_j]` の作用を別々に検証する。
- 第一目標は、rank two かつ reachable-visible な exact rational weak/weak witness。
  見つからない場合は、完全被覆を持つ exact obstruction のみを一般 no-go と呼ぶ。
- 終端判定:
  - `REACHABLE_VISIBLE_NONCOMMUTATIVE_WITNESS_CERTIFIED`
  - `REACHABLE_VISIBLE_NONCOMMUTATIVITY_OBSTRUCTED`
  - `REACHABLE_VISIBILITY_OPEN_RESOURCE_LIMIT`
- 強い witness または一般 obstruction が得られた場合だけ独立短報候補に昇格する。
  単なる audit または bounded no-go は SR2/Paper I の補助moduleとする。

### SR3a -- v0.4.1: ON 片側強化プロファイルと最小回復条件

- 状態: **証明解釈を撤回。両 profile の真偽は未解決**
- 対象:
  1. fixed-vector GC x strong MSR
  2. strong GC x reachable-state MSR
  3. occurrence identification ON の完全分類。OFF は SR3c へ分離
- 主要課題:
  - 一般 `GL_2` で非可換反例を先に探索する。
  - 反例がなければ、全チャートを被覆した `QQ` 上の
    saturation/unit-ideal 証明を行う。
  - strong GC と strong MSR のどちらが単独で可換性を回復するかを決める。
  - reachable vectors の spanning 条件、および residual space に対する
    separating-vector 条件を定理化する。
  - 可換性を強制する最小関係群を、任意の `GL_2` に対する大域結果と
    ansatz 内の局所結果に分けて記録する。
- 許容される終端:
  - 厳密反例
  - 完全消去による可換性証明
  - 明記した資源上限による未解決
- 禁止事項: triangular scout のランク結果を一般 `GL_2` の完全分類へ昇格しない。
- occurrence identification OFF は、v0.3.2 の165件を独立化する操作ではない。
  自然ラベル付きDAGの406遷移を用いる別 compiler とし、ON の131 quotient
  variables と混同しない。
- 現在の静的仕様と実行ゲート:
  [v0.4.1 research protocol](v0.4.1_one_sided_research_protocol.md)
- scope correction:
  [v0.4.1 ON semantics lattice](v0.4.1_on_semantics_lattice.md)
- soundness audit:
  [v0.4.1 reachable-MSR soundness audit](v0.4.1_reachable_msr_soundness_audit.md)
- owner decision packet:
  [v0.4.1 scope-break decision packet](v0.4.1_scope_break_decision_packet.md)
- 42/42 exact QQ chart と独立 oracle の算術は保持するが、入力座標は
  `PAPER_STRONG_OPERATOR_PROFILE` 由来の restricted locus である。Eq. (108) の
  strong-MSR 依存と Eq. (112) の strong-GC 依存が relation filtering より先に
  埋め込まれていたため、one-sided profile への forward implication は無効。
- 強/強と弱/弱の両端だけが確定し、二つの one-sided corner は `OPEN` に戻る。

### SR3b -- v0.4.2: profile-native ON compiler と one-sided 再判定

- 状態: **owner 承認済み。SR3b-A theorem certified、mixed manifest/tangent scout と pure-lower bounded no-go 完了、一般955 profileは未解決**
- triangular scout が候補化した `msr:p1-0`, `msr:p2-0`, `msr:p2-2` は
  source-stage constraint ID であり、既存 source-to-Q lift では三本とも exact zero
  residual になる。したがって `700 + 1 = 701` direct-relation campaign は実行しない。
- 第一段階: live driver/oracle の撤回済み forward rule をscope-correctし、既存955系が
  `P intersect image(Phi)` を被覆するか、localisationを含めて機械検証する。
- scope fix は完了。将来の成果物は restricted-locus 専用 path/verdict を使い、旧3 JSON
  と42 certificate は read-only historical arithmetic input として固定した。
- 955 pullback は 783 -> 83 identity + 700 residual、strong-GC basis は
  320 -> 65 identity + 255 residual と exact に閉じ、165 transition predicate と
  4 Q + 22 B inverse site の source nonsingularity binding も閉じた。
- 六つの raw antichain CPOBC Eq. (103) と source nonsingularity だけから三つの
  `k=1` Eq. (120) を source-native に導出した。MSR、GC、Eq. (108)、Eq. (112) は
  不使用であり、この証明は将来の reachable-MSR slack にも再利用できる。
- 以上を `R_2`--`R_4` 分割と 21 exact QQ certificates に独立再結合し、
  `P_sGC+rMSR intersect image(Phi_U)` 上の可換性を `PROVED_PARTIAL_SLICE` として
  確定した。一般 one-sided profile、特に `P minus image(Phi_U)` は未解決である。
- この proper-slice theorem は一般 SR3b の解決を待たず、独立短報
  **SR3b-A** として固定する。状態は
  **`THEOREM_CERTIFIED / SHORT_REPORT_SLOT_CONFIRMED / PRIOR_ART_AUDIT_COMPLETE /
  DISTINCT_TECHNICAL_CONTRIBUTION_IDENTIFIED / DRAFT_RECOMMENDED /
  DEPOSIT_NOT_AUTHORIZED`**。
  scope、構成、図表、付録、公開前 gate は
  [SR3b-A partial-slice short-report plan](v0.4.2_partial_slice_short_report_plan.md)
  に固定した。deposit・投稿は manuscript/reproducibility gate と fresh owner approval
  まで行わない。
- novelty/priority audit は
  [audit report](v0.4.2_prior_art_and_related_work_audit.md) として2026-08-01に完了した。
  Xu, arXiv:2607.26672v1 を material adjacent theorem として追加し、source Eq. (120)
  自体は先行関係、project contribution は有限 provenance、pullback/localisation、proper
  slice、21 exact charts の合成であると固定した。一般955/721は引き続き open。
- 第二段階: reachable-MSR 側は24 sourceそれぞれに
  `N_c=u_c(Jv_c)^T` を導入する最小 de-elimination（合計+48 scalar）を行い、既に
  閉じた `N=0` slice ではなく `N!=0` を反例探索の主対象にする。
- この +48 は局所的には exhaustive と証明済み。ただし frozen Eq. (107) recursion と
  Eq. (112) の B factor は Eq. (108) を展開済みなので、旧 Q presentation へ48変数を
  後付けすることはできない。source-native global compiler が必要である。
- source-native structured inventory は完成した。165 occurrence / 131 orbit、783 CPOBC、
  320 strong-GC basis、24 timid definition、48 slack、131 determinant localisation、48
  `N!=0` open patch を保持する。407 path / 87 endpoint fibre が320辺の連結木となり、
  1,529 same-endpoint pair 全体を張ることも独立再計算した。ただし scalar-polynomial
  manifest そのものではなく、global chart cover も主張しない。
- Eq. (113) は25/25、Eq. (139) は4/10を分離した validation-only gate として台帳化し、
  Eq. (112) 由来の座標定義を弱意味論へ逆流させない。
- 第一の exact `N!=0` scout は `A_e=[[p_e,x_[e]],[0,1]]` を調べた。全24
  reachable-MSR と非特異性を満たし、`p1-0` で operator residual の右下成分が1なので
  強 MSR slice 外にある。CPOBC rank 108、CPOBC+strong-GC rank 114/nullity 17だが、
  六 Q commutator は全て rank increment 0 であり、この族に非可換 witness はない。
  一般結論ではない。
- 次の mixed source-native ansatz
  `A_e=[[p_e,x_[e]],[y_[e],1]]` は131 orbit上の262変数へexactに展開済みで、verdict は
  `V042_955_MIXED_SOURCE_NATIVE_SCALAR_MANIFEST_READY_NO_SOLVER_RUN`。783 CPOBC、
  320 strong-GC basis、24 reachable-state MSR vector residual、165 determinant predicate
  `p_e-x_[e]y_[e]!=0` を保持し、`p1-0` の定数 residual により ansatz 全体で
  `N!=0` である。旧21 chart idealsは再利用せず、solver runも行っていない。
- 同 manifest の対角点における exact QQ tangent scout はschema v2、semantic digest
  `d7a4f6dba63d17cd1107ce173fb829a60af0bbf044bb02b7ccca262c70b029d5`、verdict
  `V042_955_MIXED_XY_SCOUT_NO_WITNESS_OPEN`。upper blockはrank 114/nullity 17、lower
  blockはCPOBC+reachable-MSRだけでrank 131となる。後者には108 CPOBC行+23
  reachable-MSR行のexact QQ pivot certificateがある。lower Jacobianはupper-familyの
  `x` に依存しないため、全upper-family点を通る局所枝は `y=0` に限られ、その局所枝は
  可換である。
- さらに `x=0` の pure lower ansatz では783 CPOBC、320 strong-GC、24
  reachable-state-MSRの全方程式がexactに`y`-linearである。108 CPOBC行+23
  reachable-MSR行のQQ rank-131 certificateから唯一解は `y=0`、四つのQは対角で
  可換、かつ `D_p1=diag(0,1)` なので `N!=0`。bounded verdict は
  `V042_955_PURE_LOWER_TRIANGULAR_GLOBAL_NO_GO_PROVED`、非依存oracle verdict は
  `V042_955_PURE_LOWER_ORACLE_CERTIFIED`（semantic digest
  `809f1931c2274b0b57a3bdedf73ca1997a3115030af11437f6c1f1793c20f5ba`）である。
  独立検証のscopeと再現境界は
  [pure-lower oracle report](v0.4.2_955_pure_lower_oracle.md) に固定した。
  これは新短報ではなくSR3bの補助定理であり、SR3b-Aのscopeを変更しない。
- 残る対象はpure upper/lower lociから離れた remote/disconnected
  `x!=0,y!=0` mixed componentsとfull 955 profileであり、いずれも `OPEN` である。
- fixed-vector-GC 側は Eq. (112) で消去した20個の非-antichain generatorを独立に戻す。
- 721側では exact diagonal escape point が完成し、CPOBC 783/783、inverse 712/712、
  strong MSR 24/24、fixed-vector GC 1,529/1,529 を満たしながら strong GC と
  Eq. (112) を破る。これは旧座標の非被覆を直接証明するが、Q は可換なので一般721
  可換性問題は未解決のままである。
- 131 orbit matrices / 165 aliases の compiler は assumption ledger と source coverage
  certificate の検証器として構築し、既定の Gröbner 座標系にはしない。
- 現在の soundness 判定は `PROFILE MISREPRESENTATION; THE CLAIMED PROFILE PROOF IS
  INVALID`。定理の真偽は `UNRESOLVED`。
- 監査記録:
  [v0.4.2 source-to-direct provenance audit](v0.4.2_source_to_direct_provenance_audit.md)
- 次の探索 gate は131 patchesの総当たりではない。まず残る `x!=0,y!=0` mixed
  componentsに対する対称性/orbit reductionを行い、少数の自然な principal-open
  patchをexact scoutする。solver campaign は、その結果をprofile coverage
  certificate と版付き budget artifactへ結合した後にだけ許可する。
- 数学文献監査から、scout前に common-invariant-line/simultaneous-triangularisable branch
  と irreducible branch を exact に分離する。`det[A,B]=0` は可換性ではなく前者の判定に
  使う。residual family 上の `D -> D Omega` injectivity、同一 residual に対する
  sourcewise multi-probe rank two、
  一つの non-scalar `Q_k` の centralizer `F[I,Q_k]` を最小回復条件・証明終点候補として
  compiler/test planへ追加する。

#### SR3b-M -- minimal semantic recovery lemma module

- 状態: **新規にロードマップ登録。軽量な数学補題track、独立短報にはしない**
- reachable-state MSR residual が同一 source の二つの独立 probe vectors を消すなら
  `d=2` で strong MSR が回復することを multi-probe sourcewise theorem として形式化する。
- fixed-vector equality は full transition algebra ではなく profile-specific residual space
  `R` に対する evaluation `D -> D Omega` の injectivity が必要十分であることを証明する。
- cyclicityだけでは不十分、`C^2` 上で full `M_2` separating vector は存在しない、という
  nonclaim/counterexampleを併記する。
- single-`Omega` GC は各 source に一つの state しか与えないため、異なる source を通じた
  global reachable rank two だけでは各 source residual の strong identity は従わないことを
  明記する。通常の reachability と multi-preparation recovery を混同しない。
- この module を SR3b の「最小追加仮定」回答に使い、full one-sided commutativityが未解決でも
  条件付き recovery theorem として Paper I に収録可能にする。

### SR3c -- v0.4.3: 406-occurrence OFF semantics

- 状態: **未実装。ON 結果と混同しない独立 compiler track**
- 自然ラベル付き50 source nodes・406 transition occurrences に対する labelled
  CPOBC/MSR/Eq. (113)/Eq. (139) lifts を作る。
- v0.4 の orbit-constant witness transfer は候補に留め、406 residual の直接 exact
  verification 後にのみ OFF witness へ昇格する。
- ON の21 chart cover は自動再利用しない。

### SR3d -- v0.4.4: relation-level minimal forcing core

- 状態: **profile-native compiler 完成まで延期**
- direct relation minimality と source-constraint minimalityを分離する。
- 既存の21本の非零 direct MSR residual を調べる場合、その結論は強 profile の
  presentation 内 redundancy と明記する。
- one-sided semantics の最小関係群は、SR3b の修復座標上でのみ再開する。

### SR4 -- v0.5: genuine source-stage `n=5` と `Q_6`-free 安定性

- 状態: **Paper I の scoped draft を妨げない downstream robustness track**
- 主要課題:
  - 真正な source-stage `n=5` 関係を生成する。
  - Eq. (113) の literal/derived 分岐を統合しない。
  - Eq. (139) の printed-strict/Eq. (145)-completed 被覆を統合しない。
  - `Q_6` に依存しない部分系を抽出し、低段階の結論が外部自由変数による
    見かけの効果でないことを証明する。
  - strong/weak の主要結論が `n<=4` の打切りに固有か、`n=5` でも安定かを
    厳密に判定する。
- 第一論文での役割: 得られれば有限カットオフ依存への強い回答になるが、SR2-V と
  SR3b-M より後に置き、scoped Paper I の投稿準備 gate にはしない。

## 3. 第一論文の投稿ゲート

文献調査後の仮題:

> *Statewise versus operator Bell causality in finite quantum sequential
> growth: exact separation and recovery at dimension two*

当初の中心命題は scope audit により未証明へ戻った。sharp threshold を中心命題に
戻すには SR3b の再判定が必要である。当面の sound な対比は次である。

> 有限 ON `d=2` 系では strong/strong profile が可換である一方、両方を
> source-native vector equality に弱めると非特異な有理非可換解が存在する。
> 一側だけを strong にした二つの境界は profile-native 座標で再判定する。

補助定理として、raw CPOBC と非特異性だけによる dimension-independent Eq. (120)
lemma、および strong-GC/reachable-MSR の `P intersect image(Phi_U)` 上の可換性を
収録できる。後者は独立短報 **SR3b-A** として
`THEOREM_CERTIFIED / SHORT_REPORT_SLOT_CONFIRMED / PRIOR_ART_AUDIT_COMPLETE /
DISTINCT_TECHNICAL_CONTRIBUTION_IDENTIFIED / DRAFT_RECOMMENDED /
DEPOSIT_NOT_AUTHORIZED` に固定したが、一般 one-sided corner の解決として要旨へ
格上げしない。pure-lower bounded global no-go は一般SR3bの補助定理としてのみ
収録し、SR3b-Aのscopeや独立短報数を変更しない。

Paper I は Xu, arXiv:2607.26672v1 の self-adjoint/triangular rigidity と仮定を明示的に
比較する。元論文・2024講演資料に既にある strong operator formulation を project の
導入として売らず、arbitrary non-self-adjoint finite `GL_2` certificates、弱意味論の
exact separation、statewise equality の observability と minimal recovery を中心に置く。

JMP への投稿準備開始条件は次の全項目とする。

- SR1 と SR2 の theorem/witness を一つの定義体系で記述できる。
- SR2-V audit が現 witness の reachable rank one と全 commutator の off-ray 性を exact に
  固定し、manuscript freeze 前に承認予算内の visible-witness/obstruction campaign が
  三終端のいずれかへ到達している。
- SR3b-M が residual-family injectivity、single-source multi-probe rank two、cyclicity の
  非十分性、および centralizer endpoint を profile assumptions と結合している。
- sharp classification を掲げる場合、SR3b で二つの ON 片側プロファイルが
  profile-native に解決されている。未解決のままなら完全分類とは書かない。
- OFF=406、relation-level minimality、`n=5` が本文で未解決 extension として明確に
  分離されている。これらは ON finite theorem の投稿準備を妨げない。
- 全主張が exact characteristic-zero certificate を持つ。
- 数値解・有限体計算は scout と明記され、証明に使用されていない。
- 独立実装による主要定理・反例の再検算がある。
- source claim、project derivation、open problem が本文と成果物で分離されている。

題名・要旨で **complete classification** と書けるのは、SR3b が両 one-sided
corner を profile-native に解決した後に限る。その場合も必ず `finite ON semantics
lattice` と限定する。OFF、relation-level minimum、`n>=5` を含む無限定な完全分類は
主張しない。

## 4. 第二論文へ統合する短報

### SR5 -- v0.6: `d=3` の次元閾値

- 状態: **第一論文の投稿準備後に実施**
- 研究順序: 反例探索を先行し、数値解・有限体解は scout のみに使う。
- 主要課題:
  - v0.4.2 で得た dimension-independent な source-native Eq. (120) free-word
    lemma をそのまま再利用し、`d=2` 固有なのは後段の chart rigidity だけであることを
    分離する。
  - strong/weak のどの意味論で真正な非可換 `d=3` 解が初めて現れるか。
  - 見つかった解が非特異で、全関係を満たし、単なる自由ファイバーでないか。
  - reachable subspace が全空間を張る例、またはそれが不可能であるという
    obstruction を得られるか。
- 許容される終端: 厳密 witness、厳密 no-go、または資源上限付き open。

### SR6 -- v0.7: 有限系から無限 CPOBC への restriction/lifting

- 状態: **SR5 の後に実施**
- 主要課題:
  - 無限表現から各有限 source-stage 系への restriction が、現在の関係 inventory
    と意味論プロファイルを保存する条件を定式化する。
  - 整合する有限解族から無限表現を構成できるための compatibility、compactness、
    inverse/direct-limit 条件を特定する。
  - lifting が一般には偽なら、厳密な obstruction theorem または反例を与える。
  - occurrence-wise operator identification と Eq. (113)/(139) の分岐が極限でどう
    振る舞うかを明記する。

## 5. 第二論文の投稿ゲート

仮題:

> *Finite-dimensional operator Bell causality in quantum sequential growth:
> dimension thresholds and infinite-stage extension*

CQG を第一目標とするには、次の少なくとも一つに加えて、有限系と量子逐次成長の
物理的解釈を明確にする必要がある。

- full-span または同等に非退化な reachable-state 非可換表現
- 有限段階の rigidity/noncommutativity を無限 CPOBC に移す restriction/lifting 定理
- そのような移行を妨げる、物理的意味を持つ obstruction theorem

これらが得られず、結果が有限行列方程式の分類に留まる場合は、CQG を機械的に
選ばず、JMP 系の第二論文または数学寄りの投稿先として再評価する。

## 6. 実施順序

```text
v0.3.9 strong/strong theorem       DONE
          |
v0.4 weak/weak rational witness    RESULT COMPLETE
          |
post-literature refocus             STATEWISE OBSERVABILITY / RECOVERY
          |
SR2-V exact audit + SR3b-M lemmas   NEW FIRST PRIORITY
          |
reachable-visible witness or exact obstruction campaign
          |
955 non-self-adjoint state-only repair, then 721 repair
          |
Paper I scoped assembly and submission-strength review
          |
parallel writing: SR3b-A scoped technical draft
          |
downstream: OFF / relation minimum / n=5 / d=3 / finite-to-infinite
          |
Paper II assembly and conditional CQG submission decision
```

## 7. 短報共通の完成条件

各短報は最低限、次を含む。

- 固定した問題定義、意味論スイッチ、段階範囲、基礎体、非特異条件
- 文献から採った関係と project 固有の強化の区別
- Eq. (113) と Eq. (139) の分岐別 inventory
- exact certificate と独立 oracle
- 再現コマンド、機械可読結果、semantic digest
- 成功判定、失敗判定、未解決範囲
- 既存公開版を上書きしない版管理と provenance

短報は原則として Zenodo/arXiv 上の技術報告として蓄積し、査読誌への細切れ投稿は
行わない。ただし、単独で閉じた強い定理または反例が得られ、統合論文を待つことが
新規性確認を不必要に遅らせる場合は例外を再検討する。

## 8. 現時点の最優先作業

1. SR2-V の stage/source-compatible visibility domain、exact metrics、verdict schema を
   固定し、現 witness の rank-one/off-reachable-sector 性を独立 verifier で成果物化する。
2. SR3b-M を source-bound residual spaces 上の injectivity theorem、single-source
   multi-probe theorem、cyclicity counterexample、centralizer endpoint として形式化する。
3. weak/weak で rank-two かつ reachable-visible な exact rational witness を反例先行で
   探索する。完全被覆がない bounded no-go は一般 obstruction と呼ばない。
4. その後に955の `x!=0,y!=0` mixed componentsを reducible/irreducible と symmetry/orbit
   で分け、少数の自然なprincipal-open patchをexact scoutする。131 patchesを総当たりしない。
5. coverage certificateと版付きbudget artifactが揃った場合だけsolver campaignを判断する。
   955のterminal後に721 native compilerへ進む。
6. SR3b-A は短報scopeを保って並行執筆できるが、deposit・投稿はfresh owner approvalまで
   行わない。pure-lower bounded no-goをSR3b-Aへ混入させない。
7. Paper I は observability/recovery を中心にscopedに構成し、sharp semantic threshold や
   complete classification を書かない。406-occurrence OFF、relation minimality、`n=5`、
   `d=3` はdownstreamへ分離する。
8. manuscript freeze 前に 2026-08-01 からの literature delta search を行い、新規PDFを
   `references/` と NAS へ版付き・SHA-256照合で保存する。

## 9. 研究拡張と破綻時の判断規則

- 標準計算予算は、1 chart 3,600秒、総計43,200秒、8 GiB とする。2026-08-01
  にプロジェクト所有者が今後の同種キャンペーンにも承認した。各版で独立した
  budget artifact を作り、上限変更時のみ再承認を得る。
- 想定外の結果が exact certificate を持ち、既存 SR より大幅に強い定理、新しい
  obstruction、または自然な拡張でより強い結果へ到達する場合は、元の SR を曖昧に
  せず追加研究線としてロードマップへ登録する。
- 定義の不整合、source-stage lift の不成立、chart cover の欠落、証明 verifier の
  破綻などが主要主張を脅かす場合は、その系統の計算を停止する。失敗成果物、最小
  再現手順、影響する主張、維持できる成果、修復案、必要資源、推奨判断を一つの
  decision packet にまとめて所有者へ連絡する。
- timeout や resource limit は破綻ではなく `OPEN_RESOURCE_LIMIT` として扱い、完了・
  空集合・反例不存在へ読み替えない。
- source code、tests、tracked result JSON、reports は Git commit + push を正本・バックアップ
  とし、NAS に unpacked worktree を複製しない。NAS は papers と高コストな non-Git
  artifacts の cold backup に限定し、そこで実行・展開・build・solver runを行わない。
  現行snapshotと復旧規則は
  [backup policy](cpobc_backup_policy_2026-08-01.md) に固定する。

## 10. 根拠と見直し条件

- 公開済み基準: [Zenodo v0.3.9](https://zenodo.org/records/21720863)
- 現在の弱意味論結果: [v0.4 classification](v0.4_weak_d2_classification.md)
- Eq. (139) 監査: [v0.4 coverage audit](v0.4_eq139_coverage.md)
- JMP の公式 scope:
  <https://publishing.aip.org/publications/journals/special-topics/jmp/>
- CQG の公式 scope/article types:
  <https://publishingsupport.iopscience.iop.org/journals/classical-and-quantum-gravity/about-classical-quantum-gravity/>

投稿先の記述は 2026-08-01 時点の暫定判断であり、採択可能性の保証ではない。
scope、article type、投稿規定は各投稿直前に公式ページで再確認し、このロードマップを
必要に応じて版更新する。
