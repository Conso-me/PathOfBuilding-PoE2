# Path of Building (PoE2) 日本語化フォーク

[PathOfBuildingCommunity/PathOfBuilding-PoE2](https://github.com/PathOfBuildingCommunity/PathOfBuilding-PoE2) の非公式日本語化フォーク。

## 設計思想

- **オーバーレイ方式**: upstream の Lua ソースには手を入れず、`T()` 等のグローバル関数経由で表示時のみ日本語化
- **内部は英語維持**: ビルド XML、ModParser、計算ロジックは upstream と完全互換
- **翻訳ソース**: [poe2db.tw/jp](https://poe2db.tw/jp) のスクレイピングを一次ソースとする
- **upstream 同期**: `dev` ブランチに継続的に追随。週次 CI で自動 PR

## ディレクトリ構成

```
src/Locale/                  翻訳インフラ
├── Locale.lua               -- T(), SkillT(), ItemT(), ModFormat() を提供
└── ja_JP/                   -- 日本語辞書
    ├── UI.lua               -- UI chrome (ボタン・ラベル・ダイアログ)
    ├── Skills.lua           -- スキル/ジェム名 (917件 from poe2db)
    ├── Items.lua            -- アイテム/ベース名 (768件 from poe2db)
    ├── Tree.lua             -- パッシブ/上位職 (73件 from poe2db)
    ├── Stats.lua            -- ステータス名 (未取得)
    ├── Keywords.lua         -- キーワード (未取得)
    ├── Mods.lua             -- Mod テンプレート (未取得)
    └── Uniques.lua          -- ユニーク (未取得)

tools/
├── scrape_poe2db.py         -- poe2db.tw から辞書を再生成
└── extract_strings.py       -- src/ から UI 文字列候補を抽出

docs/ja/
├── README-ja.md             -- 本ファイル
├── glossary.md              -- PoE2 用語統一表記
├── scraping-status.md       -- スクレイプの取得状況
└── ui-translation-queue.txt -- UI 翻訳待ちキュー（自動生成）
```

## セットアップ済の安全装置

upstream へ誤って PR や push を送らないよう、3層防御を設定済:

```bash
# Layer 1: upstream への push を物理的に無効化
git remote get-url --push upstream
# → DISABLED

# Layer 2: gh コマンドのデフォルトを fork に固定
gh repo set-default --view
# → Conso-me/PathOfBuilding-PoE2

# Layer 3: ja ブランチの push 先を origin に固定
git config branch.ja.pushRemote
# → origin
```

`gh pr create` 単体ではローカルの fork に PR を作る挙動。本家相手に PR を出すには明示的に `--repo PathOfBuildingCommunity/PathOfBuilding-PoE2` を打たないと不可能。

## 開発フロー

### 翻訳辞書の更新

```bash
# poe2db.tw から最新の翻訳をスクレイプ
python3 tools/scrape_poe2db.py

# 結果を確認
git diff src/Locale/ja_JP/
git add src/Locale/ja_JP/
git commit -m "i18n: refresh translations from poe2db.tw"
```

### UI 文字列の追加翻訳

```bash
# src/ から英語文字列候補を再抽出
python3 tools/extract_strings.py

# docs/ja/ui-translation-queue.txt を見て翻訳したい文字列を選ぶ
# src/Locale/ja_JP/UI.lua に手動で追記:
#   ["Save"] = "保存",

# 再抽出すると翻訳済が queue から消える
python3 tools/extract_strings.py
```

### upstream の取り込み

**自動（推奨）**: `.github/workflows/ja-sync-upstream.yml` が毎週月曜 00:00 UTC に動き、upstream/dev の新規コミットを `ja` ブランチに merge してレビュー用 PR を作る。手動 trigger も `workflow_dispatch` で可能。

**手動の場合**:
```bash
git fetch upstream
git checkout ja
git merge upstream/dev          # rebase ではなく merge
# コンフリクトがあれば解決（Locale/ 以外で発生するはず）
python3 tools/wrap_ui_calls.py      # 新規 UI 呼び出しを T() でラップ
python3 tools/extract_strings.py    # 新規 UI 候補をキュー更新
python3 tools/coverage_report.py    # カバレッジ確認
git add -A
git commit -m "sync: merge upstream/dev @<sha>"
git push origin ja
```

### 翻訳辞書の更新

**自動（推奨）**: `.github/workflows/ja-refresh-translations.yml` が毎週日曜 18:00 UTC に動き、poe2db.tw から再スクレイプして変更があれば PR を作る。

**手動の場合**:
```bash
python3 tools/scrape_poe2db.py
git diff src/Locale/ja_JP/
git add src/Locale/ja_JP/
git commit -m "i18n: refresh translations from poe2db.tw"
```

### テスト

`ja` ブランチへの push / PR で `.github/workflows/ja-test.yml` が動き:
- upstream の Busted テスト suite を実行（翻訳作業で計算ロジックが壊れていないか）
- `luac -p` で全 Locale Lua ファイルの構文チェック
- `coverage_report.py` で UI カバレッジ表示
- `extract_strings.py --dry-run` で抽出ツールがクラッシュしないか確認

### リリースタグ

upstream バージョン + `-ja.N` 形式:
- `v0.15.0-ja.1` — upstream v0.15.0 ベースの初回翻訳パッチ
- `v0.15.0-ja.2` — 同 upstream 上の翻訳修正パッチ
- `v0.16.0-ja.1` — upstream v0.16.0 ベースの新規

## 既知の制約

- **Uniques / Keywords / Stats / Mods 辞書未取得** — poe2db の HTML 構造解析が必要。詳細は [scraping-status.md](scraping-status.md)
- **UI ラップ未配線** — `DrawString(..., "...")` → `DrawString(..., T("..."))` の置換作業は未着手（Phase 5）
- **Mod テンプレート未対応** — `+20 to maximum Life` 等の動的 mod 翻訳は Phase 7+

## 参考

- 上位プラン: `/home/consommex/.claude/plans/https-github-com-pathofbuildingcommunity-eager-fern.md`
- 用語集: [glossary.md](glossary.md)
- スクレイピング状況: [scraping-status.md](scraping-status.md)
- 翻訳キュー: [ui-translation-queue.txt](ui-translation-queue.txt)

## クレジット

- 本家プロジェクト: [Path of Building Community PoE2](https://github.com/PathOfBuildingCommunity/PathOfBuilding-PoE2) (MIT License)
- 翻訳辞書ソース: [poe2db.tw](https://poe2db.tw) コミュニティデータベース
