# poe2db.tw スクレイピング状況

辞書ファイルのカバレッジと改善余地を記録する。

## 取得状況（2026-05-26 時点、Phase 7 完了後）

| カテゴリ | 件数 | ソース | 状態 |
|---------|-----:|--------|------|
| Skills | 917 | `/jp/Skill_Gems` `/jp/Support_Gems` `/jp/Spirit_Gems` `/jp/Lineage_Supports` | ✅ 良好 |
| Items | 768 | 20 個の base slot URL（`/jp/Body_Armours` ほか） | ✅ 良好 |
| **Uniques** | **353** | 同じ 20 個の body-slot URL を `class="uniqueitem"` で抽出（キャッシュ共有） | ✅ **新規** |
| **Keywords** | **224** | `/jp/Keywords` を `class="KeywordPopups"` で抽出 | ✅ **新規** |
| **Stats** | **98** | **手動シード**（poe2db に dedicated page 無し） | ✅ **新規** |
| Tree | 73 | `/jp/Ascendancy_class` `/jp/passive-skill-tree/` | △ 上位職のみ |
| UI | 152 | 手動翻訳 + `tools/extract_strings.py` キュー | ✅ 100% カバレッジ |
| Mods | 0 | `/jp/Modifiers` HTML 構造未解析 | ❌ 後回し |

**合計: 2,585 件**（前回 1,910 件から +675 件）

## 改善履歴

### Phase 7 で追加（このセッション）
1. **Uniques**: 各 body-slot ページに `class="whiteitem"` と `class="uniqueitem"` が同居していることを発見。`tools/scrape_poe2db.py` に fetch キャッシュを追加し、同 URL を 2 カテゴリで再利用。
2. **Keywords**: `/jp/Keywords` ページの `class="KeywordPopups"` 属性で 224 件取得。`class_link_re` を lookahead 化して属性順問わず match できるよう改善。
3. **Stats**: poe2db に該当 URL がないことを確認後（`/jp/Stat` `/jp/Statistics` `/jp/Stat_Descriptions` 等すべて 404）、PoE2 定番ステータス 98 件を手動シード。`CATEGORIES` 辞書から外しスクレイパが上書きしないよう保護。
4. **Locale.ItemT**: Items.lua で見つからない名前を Uniques.lua にフォールバック。同じ ItemT() 経由でユニークアイテム名も日本語化される。

### スクレイパの改善
- **fetch キャッシュ**: 同 URL を複数カテゴリで再利用（Items+Uniques で 22 URL × 1 fetch のみ）
- **lookahead regex**: `class` と `href` の属性順問わず match
- **404 を skip**: 個別 URL の失敗で全体停止しない

## 残課題

### 1. Mods（最難関、未着手）
- `/jp/Modifiers` の `class="explicitMod"` `class="implicitMod"` 内に nested HTML（KeywordPopups, mod-value 等）
- placeholder `(15—25)` の構造マッチが必要（EN/JP 並列取得＋位置合わせ）
- 真っ当な実装には HTML parser（bs4 など）が必要 → 別セッションで取り組む

### 2. Tree 拡張
- パッシブツリーのノード名は 73 件（上位職のみ）
- 通常パッシブノード（数百件）は `/jp/passive-skill-tree/` ページに別構造で存在
- 構造解析が必要

### 3. URL 404 残
- `/jp/Focuses` → 正しくは `/jp/Focus` の可能性（未検証）
- `/jp/Tablets` → 正しくは `/jp/Map_Tablet` の可能性

### 4. 翻訳品質の override
- 例: `["Cast on Shock"] = "ショックフラッシュ"` は誤訳に見える → glossary.md で要レビュー
- `["Fireball"] = "ファイヤーボール"` は poe2db 表記（公式日本語版が出れば変更余地）
- override 仕組み未実装（`src/Locale/ja_JP/_overrides/` 構想）

## 運用ルール（更新）

- `scrape_poe2db.py` 実行後は `git diff src/Locale/ja_JP/` で想定外の項目削除が無いか目視
- `Stats.lua` は手動メンテ専用、スクレイパは触らない設計
- 月1回の手動再スクレイプ＋週次 CI 再スクレイプの2系統運用
