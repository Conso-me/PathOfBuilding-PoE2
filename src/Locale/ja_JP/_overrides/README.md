# `_overrides/` — translation overrides

このディレクトリのファイルは `src/Locale/ja_JP/<Name>.lua` の翻訳を
**上書き**する。poe2db.tw 由来の自動翻訳が違和感ある／誤訳の場合、
ここに該当エントリを書くと優先される。

## ルール

- ファイル名は対応するベース辞書と同じ: `Skills.lua`, `Items.lua`, `Uniques.lua`,
  `Stats.lua`, `Keywords.lua`, `Tree.lua`, `UI.lua`, `Mods.lua`
- フォーマットも同じ: `return { ["English"] = "日本語", ... }`
- `tools/scrape_poe2db.py` はこのディレクトリを **触らない**（安全）
- 空ファイル不要。override が必要なエントリだけ書けば良い
- ベース辞書にあるキーに対してのみ意味を持つ（新規キーを追加しても表示されない）

## マージ順序

`src/Locale.lua` の `loadDict()` で:

```
1. src/Locale/ja_JP/<Name>.lua          ← ベース（自動 or 手動）
2. src/Locale/ja_JP/_overrides/<Name>.lua ← override（あれば上書き）
```

の順でマージされる。同じキーが両方にあれば override の値が勝つ。

## 例: poe2db 訳の修正

poe2db では `"Cast on Shock"` が `"ショックフラッシュ"` と訳されているが、
PoB ユーザー的には `"ショック時キャスト"` の方が自然。これを修正するには:

```lua
-- src/Locale/ja_JP/_overrides/Skills.lua
return {
    ["Cast on Shock"] = "ショック時キャスト",
}
```

これでスキル選択肢の dropdown で「ショックフラッシュ」が「ショック時キャスト」に
置き換わる。poe2db を再スクレイプしても override は維持される。

## 既知の修正候補（議論中）

- `Fireball` → poe2db: ファイヤーボール / PoE1 慣例: ファイアボール（要決定）
- `Cast on Shock` → poe2db: ショックフラッシュ / 推奨: ショック時キャスト
- `Critical Damage Bonus` → poe2db: クリティカルダメージボーナス / PoE2 表記: 致命的ダメージボーナス（要決定）

詳細は `docs/ja/glossary.md` 参照。
