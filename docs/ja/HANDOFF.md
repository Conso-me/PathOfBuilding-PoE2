# HANDOFF: PoB-PoE2 JP 日本語化プロジェクト

最終更新: 2026-05-26 / 引き継ぎ用ドキュメント

このファイルは「**次のセッションが時間を無駄にしないため**」のもの。
README-ja.md が "what" なら、これは "why" と "次にどう動くか" 。

---

## 1分で状態把握

```bash
cd ~/projects/pob-poe2-jp
git log --oneline 9b201c201..HEAD     # この fork で積んだ 13 コミット
python3 tools/coverage_report.py      # 翻訳カバレッジ
ls src/Locale/ja_JP/                  # 8 辞書ファイル + _overrides/
```

- ブランチ: `ja`（origin/ja に push 済）
- upstream fork-point: `9b201c201` (Add Search and sort to exporter #1147)
- 翻訳ペア合計: **4,790件**
- UI ラップカバレッジ: **99%** (297 中 294 call sites)
- Stats ラップカバレッジ: **100%** (205/205)

---

## 設計判断のサマリ（後で蒸し返さないため）

### なぜオーバーレイ方式か（直接編集ではなく）
upstream は月次リリース、`dev` ブランチで活発に開発中（9,786 commits）。直接編集だと毎週マージ衝突地獄。`T()` 等の関数経由なら upstream ファイルへの変更が極小化される。実測: 27 ファイル × 平均 8 行 = 216 行の変更のみ。

### なぜ「内部は英語、表示時のみ日本語」か
ビルド XML (`Builds/*.xml`) はスキル名・mod・アイテム名を**英語のまま**保存している。内部状態を日本語化すると upstream PoB ユーザーとビルド共有不可能になる。`ModParser` も英語パターンで内部マッチする。だから表示の最後の段階だけ `T()`/`SkillT()`/`ModFormat()` を挟む。

### なぜ poe2db.tw を翻訳ソースに選んだか
- 多言語対応サイト（en/jp/cn/kr/...）。slug が英語、リンクテキストが翻訳済 → 自動ペアリング容易
- robots.txt が `Allow: /` で許可
- コミュニティで広く使われており、用語の権威性がある
- **欠点**: 一部訳が不自然（例: "Cast on Shock" → "ショックフラッシュ"）→ `_overrides/` で対応

### なぜ rebase ではなく merge で upstream 取り込みか
オーバーレイ方式で upstream ファイル変更が極小 → コンフリクトはほぼ Locale 関連だけ → merge コミットの分岐が読みやすい。rebase だと毎週 force-push になり、コミュニティから貢献を受ける時に履歴破壊が起きる。

### なぜ Stats.lua は手動メンテ専用か
poe2db に dedicated stats page が存在しない（`/jp/Stat` `/jp/Statistics` `/jp/Stat_Descriptions` 全部 404）。スクレイパに含めると毎回空ファイルで上書きされる罠 → `CATEGORIES` 辞書から外して保護した。

### なぜ Mods だけ override が array-merge か
他は `["key"] = "value"` の dict（key 衝突で後勝ち）。Mods は `{patterns = {{en=..., ja=...}, ...}}` の配列。dict マージは適用できない。override 側を**配列の先頭**に並べると `ModFormat()` の線形 scan で先勝ちになる → 同じ key-replace セマンティクスを実質的に達成。

---

## 罠と注意事項

### 🚨 本家への誤 push / PR を絶対避ける（3層防御してある）
1. `git remote get-url --push upstream` → `DISABLED`（物理失敗）
2. `gh repo set-default --view` → `Conso-me/PathOfBuilding-PoE2`（gh コマンド fork 優先）
3. `git config branch.ja.pushRemote` → `origin`

新しい branch を切ったら `git config branch.<name>.pushRemote origin` を忘れずに。

### 🚨 Stats.lua は手動編集ファイル — scraper では再生成されない
`tools/scrape_poe2db.py` の `CATEGORIES` に Stats は含まれていない（意図的）。新規 stat 追加は `src/Locale/ja_JP/Stats.lua` を直接編集。

### 🚨 Mods.lua の構造は他と違う
`return { ["en"] = "ja" }` ではなく `return { patterns = { {en=..., ja=...} } }`。
- `tools/coverage_report.py` も別ロジックで count している
- `_overrides/Mods.lua` は array-prepend で merge される（[Locale.lua の loadModPatterns](../../src/Locale.lua)）

### 🚨 `re.escape` は Python regex 用 — Lua パターン用には別関数
Lua の magic chars は `().%+-*?[]^$` で escape 文字は `%`（`\` ではない）。 scrape_poe2db.py の `_lua_escape_pattern()` を必ず使う。

### 🚨 `extract_strings.py` の queue は 5,990 件もある
これは「**もし全文翻訳するなら**」の母数。実用上は `T()` でラップ済の 297 件だけが画面に出る。queue 全件翻訳は不要。

### 🚨 gem ドロップダウンの検索は英語入力前提
表示は日本語化されているが、PoB 内部の filter は英語 name で match する。「ファイア」と打っても "Fireball" は出ない。**逆引き辞書を作るのが次の改善ポイント**だが未実装。

### 🚨 ModFormat の線形 scan は O(N)、N=2,053
実機で hover ごとに 2,053 patterns を走査。理論的に slow だが未測定。lag を観測したら `first-char index` か `length-sorted` で最適化。

---

## ローカル環境の再現

```bash
# 必須
sudo apt install python3-requests  # スクレイパ用（venv 作れないなら apt 経由）
sudo apt install lua5.4            # CI と同じ syntax check したいなら

# 任意（実機テスト用、Windows 側）
# runtime-win32.zip 展開 → src を fork のものに差し替え → Path of Building.exe 起動
```

`python3 -m venv` が動かなかった原因: `python3-venv` が apt 未インストール。
代わりに `python3-requests` を apt で入れて stdlib + apt 依存のみで動かしている。
bs4 は不要（regex で済ませた）。

---

## コード地図

```
src/
├── Launch.lua                ── Locale ロード＋グローバル T/SkillT/... 登録 (line 67-83)
├── Locale.lua                ── ★ T(), SkillT(), ItemT(), StatT(), KeywordT(),
│                                ModFormat() を提供。base + _overrides の merge ロジック
├── Locale/ja_JP/
│   ├── UI.lua                ── 168 件 (手動翻訳)
│   ├── Skills.lua            ── 917 件 (auto scrape)
│   ├── Items.lua             ── 768 件 (auto scrape)
│   ├── Uniques.lua           ── 353 件 (auto scrape)
│   ├── Stats.lua             ── 250 件 (★手動メンテ、scraper 対象外)
│   ├── Keywords.lua          ── 224 件 (auto scrape)
│   ├── Tree.lua              ── 73 件 (auto scrape、上位職のみ)
│   ├── Mods.lua              ── 2053 patterns (auto scrape)
│   └── _overrides/           ── 翻訳上書き
│       ├── README.md         ── 仕組みの説明 ★必読
│       ├── Skills.lua        ── 例: "Cast on Shock" 上書き
│       ├── Mods.lua          ── 例: "Monster Level: (%d+)" 汎用化
│       └── UI.lua            ── 空placeholder
├── Modules/
│   ├── ItemTools.lua         ── formatModLine() で ModFormat 中央配線 (line 335)
│   ├── BuildDisplayStats.lua ── 205 個の StatT() ラップ
│   ├── Main.lua              ── 17 個の T() ラップ
│   └── ...
└── Classes/
    └── ...                   ── 26 ファイルで T()/SkillT()/ItemT() 散布

tools/
├── scrape_poe2db.py          ── ★ メインスクレイパ。CATEGORIES + MOD_SOURCES + 重要関数群
├── wrap_ui_calls.py          ── ★ DrawString/ButtonControl/OpenPopup/tooltip:AddLine
│                                を自動ラップ (5 種類のパターン)
├── extract_strings.py        ── UI 候補抽出 → docs/ja/ui-translation-queue.txt
├── coverage_report.py        ── 4 種類のラッパー＋ Mods array count
└── regenerate_all.sh         ── 1コマンドで全部回す（scrape→wrap→extract→coverage）

docs/ja/
├── HANDOFF.md                ── ★ このファイル
├── README-ja.md              ── プロジェクト総合 README
├── glossary.md               ── PoE2 用語統一表記（議論用）
├── scraping-status.md        ── poe2db 取得状況詳細
└── ui-translation-queue.txt  ── 自動生成（5,990 件、参考情報）

.github/workflows/
├── ja-sync-upstream.yml      ── 月曜 0:00 UTC: upstream/dev → ja の PR
├── ja-refresh-translations.yml── 日曜 18:00 UTC: poe2db 再スクレイプ PR
└── ja-test.yml               ── push/PR: Busted テスト + Lua syntax + coverage 確認
```

---

## 次の作業 — 優先度別

### A. 実機検証（最優先 — まだ未実行）
PoB-PoE2 を Windows で実際に起動して JP 表示を目視確認。
- `runtime-win32.zip` を C:\PoB あたりに展開
- `src/` フォルダを fork クローンで上書き
- `Path of Building.exe` 起動
- 各タブ巡回（Tree/Skills/Items/Calcs/Notes/Configuration/Party/Trade）
- popup（Options/About/build save/delete confirmation）も確認
- **観測**: 翻訳されている / 未翻訳箇所がある / クラッシュする / 文字化け
- **期待**: 翻訳済は日本語、未翻訳は英語にフォールバック、計算結果は upstream と完全一致

### B. ロケール切替 UI（中、ユーザビリティ向上）
現在 `Locale.lua:24` に `current = "ja_JP"` ハードコード。Options popup に dropdown を追加して `en_US` / `ja_JP` 選択可能に。
- 設定の永続化: `main:SaveSettings()` で Settings.xml に保存
- 切替時の挙動: Locale.SetLocale() でキャッシュ無効化＋ UI 再描画
- en_US "辞書" は不要（全 dict が miss → 英語フォールバックで足りる）

### C. Mods generalization（中、品質向上）
`Mods.lua` の 2,053 patterns には "Monster Level: 83" 等の具体値混じりが多数。
`_overrides/Mods.lua` に `(%d+)` テンプレで汎用パターンを足していくと品質向上。
1パターン書いて override 動作確認 → 残りパターンを優先度順に追加。

### D. 逆引き gem 検索（小〜中、UX 向上）
GemSelectControl の filter が英語前提。「ファイア」と打って「Fireball」を探せるように:
- 起動時に Skills.lua から JA→EN マップを構築
- `BuildList(filter)` で filter を EN/JA 両方で search
- 表示は今まで通り日本語

### E. Tree 通常パッシブノード取得（大、量が多い）
現在 Tree.lua 73 件は上位職のみ。通常パッシブノードは `/jp/passive-skill-tree/` ページに別構造で存在。HTML 解析次第。

### F. UI queue を翻訳して 100% を目指す（小、地道）
`docs/ja/ui-translation-queue.txt` に 5,990 件の候補。実質的に UI に出るのは数百件程度。よく使われる順で `UI.lua` に追加していく。

---

## CI が動くまでの確認チェックリスト

GitHub Actions が fork で初回動かない可能性。次セッションでこれを確認:
1. https://github.com/Conso-me/PathOfBuilding-PoE2/actions を開く
2. "I understand my workflows, go ahead and enable them" を押す
3. `ja-test.yml` を手動 dispatch して通るか試す
4. `ja-refresh-translations.yml` も手動 dispatch（poe2db 取得テスト）

---

## ハマりやすいポイントの再掲

1. **wrap_ui_calls.py を実行した後は必ず `coverage_report.py --missing` を見る** — 新規ラップで未翻訳キーが増えている可能性
2. **新規ファイル翻訳追加時は `tools/regenerate_all.sh` を回す前後で `git diff --stat` 確認** — スクレイパが想定外の項目を削除していないか
3. **`luac -p` で syntax 確認可能だが apt install lua5.4 が必要** — 普段は Edit ツールが構文壊しを防いでくれる前提
4. **upstream sync 時は merge コンフリクトが Locale 以外に出たら要注意** — オーバーレイ方式の前提が崩れている兆候

---

## 連絡・参考

- 上位プラン（最初の設計時）: `/home/consommex/.claude/plans/https-github-com-pathofbuildingcommunity-eager-fern.md`
- 上流リポジトリ: https://github.com/PathOfBuildingCommunity/PathOfBuilding-PoE2
- 翻訳ソース: https://poe2db.tw/jp
- このフォーク: https://github.com/Conso-me/PathOfBuilding-PoE2 (branch: ja)
