# HANDOFF: PoB-PoE2 JP 日本語化プロジェクト

最終更新: 2026-05-27 / 引き継ぎ用ドキュメント

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
- **翻訳方式（2026-05-27 変更）**: T() ラッパー方式 → **DrawString フック方式** へ移行。`src/JaText.lua` の `translate()` が描画直前に T_MAP ルックアップ。upstream の素のコードが ~99% 維持される。
- 旧 T()/SkillT/etc ラップカバレッジ指標は obsolete（DrawString フックが call-site 通過後の文字列を翻訳するため、call-site ラップ率は意味を持たない）

---

## 設計判断のサマリ（後で蒸し返さないため）

### なぜオーバーレイ方式か（直接編集ではなく）
upstream は月次リリース、`dev` ブランチで活発に開発中（9,786 commits）。直接編集だと毎週マージ衝突地獄。

### なぜ T() ラッパー方式を捨てて DrawString フック方式に移行したか（2026-05-27）
旧設計は各 call-site で `T("Save")` のようにラップしていたが、これでも upstream の 30+ ファイル / 505 行が変更状態 → rebase で広範囲コンフリクトが続いた。

新設計は `src/JaText.lua` の DrawString/DrawStringWidth フックで描画直前に T_MAP ルックアップ。先頭の色コード（`^N` / `^xRRGGBB`）を剝がしてから body を引くので `"^7" .. "Save"` のような連結も対応。**call-site が upstream とバイト同一** に近づき、rebase コンフリクトが現実的なレベルに減った（残差分 11 ファイル / 50+24- 行）。

トレードオフ:
- 利点: rebase 摩擦激減、JaText の glyph 描画と翻訳ロジックが同じレイヤに集約
- 欠点: 連結中位部品（`"Skill" .. ": " .. skill_name`）は composite で T_MAP に当たらず英語残り。`s_format("^7%s: %s%s", ...)` も同様
- 互換シム: `Locale.T/SkillT/ItemT/StatT/KeywordT` は残置（変数引数版 19 件と Options ロケール切替が globals 経由で呼ぶため）

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
├── Launch.lua                ── Locale ロード＋グローバル T/SkillT/... 登録、
│                                ★ self.jaText.localeGetMap = Locale.GetTMap で
│                                  T_MAP を JaText に注入 (line 100-104)
├── JaText.lua                ── ★ DrawString/DrawStringWidth フック。
│                                CJK glyph atlas 描画 + translate() による
│                                T_MAP ルックアップ + 色コード剝奪
├── FontDiag.lua              ── CJK 文字到達ログ（デバッグ用）
├── Locale.lua                ── ★ T(), SkillT(), ItemT(), StatT(), KeywordT() の
│                                互換シム（変数引数の残置呼び出し用）+
│                                GetTMap() による全カテゴリ統合フラット map +
│                                ModFormat() (mod pattern 翻訳、別 API)
├── Locale/ja_JP/
│   ├── UI.lua                ── 168 件 (手動翻訳)
│   ├── Skills.lua            ── 917 件 (auto scrape)
│   ├── Items.lua             ── 768 件 (auto scrape)
│   ├── Uniques.lua           ── 353 件 (auto scrape)
│   ├── Stats.lua             ── 250 件 (★手動メンテ、scraper 対象外)
│   ├── Keywords.lua          ── 224 件 (auto scrape)
│   ├── Tree.lua              ── 73 件 (auto scrape、上位職のみ)
│   ├── Mods.lua              ── 2053 patterns (auto scrape)
│   ├── GlyphMap.lua          ── ★ JA atlas のグリフ座標マップ
│   │                            （tools/extend_font.py で生成、1560 glyphs）
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

### A. 実機検証（DrawString フック方式の目視確認 — 最優先）
WSL+DISPLAY=:0 で起動確認は通過済（`Engine shutdown complete` 正常終了 / Lua エラーゼロ / atlas 4 枚プリロード OK）。残りは画面巡回チェック:
```bash
cd ~/projects/pob-poe2-jp/runtime && DISPLAY=:0 ./Path\{space\}of\{space\}Building-PoE2.exe
```
チェックリスト:
- メイン Build List → "新規"/"開く"/"コピー"/"名称変更"/"削除"
- Options ポップアップ → "Language:" ラベル翻訳（色コード剝奪パス）
- Skills タブ・ジェム選択 → ジェム名翻訳（SkillT シム + colorCodes.GEM プリフィックス）
- Items タブ・ユニーク tooltip → ユニーク名（Items→Uniques フォールバック）
- Calcs Breakdown → ソースアイテム行
- アイテム mod 行 → ModFormat 経由で従来通り翻訳

### B. ロケール切替 UI ✅ 完了（commit `e0f51ef98`）
Options popup に dropdown 実装済。`main.locale` で永続化、`launch.locale.SetLocale()` で T_MAP もリセット。

### B-2. 変数引数 T() の最終撤廃（小、rebase 摩擦をゼロに）
残った 19 件の `SkillT(self.gemName)` / `ItemT(item.name)` 等を除去すれば src/Classes と src/Modules が upstream とほぼバイト同一になる。
- 検証: `grep -rEn '\b(T|SkillT|ItemT|StatT|KeywordT)\(' src/Classes src/Modules`
- 機能影響: なし（DrawString フックが最終文字列を翻訳）
- 例外: `MinionListControl.lua:73` のような `"^7".."Skill"..": "..SkillT(name)` は連結を `"^7Skill: " .. name` に手動畳み込み必要

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
