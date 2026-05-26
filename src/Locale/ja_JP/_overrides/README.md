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

### Dict 系（UI / Skills / Items / Uniques / Stats / Keywords / Tree）

`src/Locale.lua` の `loadDict()` で:

```
1. src/Locale/ja_JP/<Name>.lua          ← ベース（自動 or 手動）
2. src/Locale/ja_JP/_overrides/<Name>.lua ← override（あれば上書き）
```

の順でマージされる。同じキーが両方にあれば override の値が勝つ。

### Mods（配列構造）

`Mods.lua` は `{ patterns = { {en=, ja=}, ... } }` の配列形式。
`Locale.lua` の `loadModPatterns()` で:

```
1. _overrides/Mods.lua の patterns     ← 先に並ぶ → 線形 scan で先勝ち
2. Mods.lua の patterns                 ← 後ろに並ぶ
```

`ModFormat()` は最初に match した pattern で打ち切るので、override の汎用
パターン（例: `Monster Level: (%d+)`）でスクレイプ起源の具体パターン（例:
`Monster Level: 83`）を実質的に上書きできる。同じ pattern を base 側で
maintain 不要 — override が先勝ちするだけ。

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
