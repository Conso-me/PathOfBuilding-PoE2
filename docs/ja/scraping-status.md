# poe2db.tw スクレイピング状況

初回スクレイプで取得した辞書のカバレッジと、今後の改善余地を記録する。

## 取得状況（2026-05-26 時点）

| カテゴリ | 件数 | ソース URL | 状態 |
|---------|-----:|-----------|------|
| Skills | 917 | `/jp/Skill_Gems` `/jp/Support_Gems` `/jp/Spirit_Gems` `/jp/Lineage_Supports` | ✅ 良好 |
| Items | 768 | 20 個の base slot URL（`/jp/Body_Armours` ほか） | ✅ 良好 |
| Tree | 73 | `/jp/Ascendancy_class` `/jp/passive-skill-tree/` | △ 上位職のみ。パッシブツリーノードは未取得 |
| Uniques | 0 | `/jp/Uniques` | ❌ HTML構造が異なる |
| Keywords | 0 | `/jp/Keywords` | ❌ HTML構造が異なる |
| Stats | 0 | `/jp/Stats` (404) | ❌ URL不明 |
| Mods | 0 | `/jp/Modifiers` | ❌ テンプレート形式パース未実装 |

合計: **1,758 件**

## 既知の問題

### URL が 404
- `/jp/Focuses` → 正しくは `/jp/Focus` の可能性
- `/jp/Tablets` → 正しくは `/jp/Map_Tablet` の可能性
- `/jp/Stats` → そもそも別の場所にある可能性

### HTML 構造未解析
- **Uniques**: `class="uniqueitem"` だが、Uniques landing page では item-class ではなくサブカテゴリリンクのみ。各サブカテゴリ（例: `/jp/Unique_Body_Armours`）を探索する必要がある。
- **Keywords**: 単純な `<a>` リストではなく、テーブルや展開可能セクションになっている可能性。
- **Mods**: `(15-25)%` 形式の placeholder 付きテンプレート。EN/JP 並列スクレイプ＋構造マッチが必要。

## 改善タスク（優先度順）

1. **Uniques の正しいサブカテゴリ URL 群を発見** — `/jp/Uniques` ページの `<a>` を全部 GET して subcategory を列挙
2. **Mods スクレイパ実装** — `/us/Modifiers` と `/jp/Modifiers` 並列取得、（N-M）等の placeholder 構造マッチ
3. **Keywords ページ構造解析** — `class="keyword"` 等の CSS class を grep で探索
4. **Stats の代替ソース** — poe2db に無ければ PoB の `Data/StatDescriptions/` から英語抽出 → 手翻訳 or DeepL バッチ
5. **404 URL の修正** — `/jp/Focus` `/jp/Map_Tablet` 等を試行

## 既知のノイズ・揺れ

- `Cast on Shock` → `ショックフラッシュ`（誤訳に見える、本来は「ショック時キャスト」） → glossary.md で override 予定
- `Fireball` → `ファイヤーボール`（一般的な「ファイアボール」と異なる、poe2db 公式表記準拠）

## 運用ルール

- スクレイパ更新後は必ず `git diff src/Locale/ja_JP/` を確認、想定外の項目削除が無いことを目視
- override は `src/Locale/ja_JP/_overrides/<Category>.lua` に追加（仕組みは未実装、TODO）
- 月1回の手動再スクレイプ＋週次 CI 再スクレイプの2系統運用
