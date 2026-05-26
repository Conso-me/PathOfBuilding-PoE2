-- Stat name dictionary.
-- poe2db.tw has no dedicated stats page, so this is seeded manually with
-- canonical PoE2 stat names. Order matters for diff readability; keep
-- alphabetical within each section.
return {
	-- ライフ・マナ・エネルギーシールド
	["Life"] = "ライフ",
	["Maximum Life"] = "最大ライフ",
	["Life Regeneration"] = "ライフ自然回復",
	["Life Leech"] = "ライフリーチ",
	["Mana"] = "マナ",
	["Maximum Mana"] = "最大マナ",
	["Mana Regeneration"] = "マナ自然回復",
	["Mana Leech"] = "マナリーチ",
	["Energy Shield"] = "エナジーシールド",
	["Maximum Energy Shield"] = "最大エナジーシールド",
	["Energy Shield Recharge"] = "エナジーシールド再充填",
	["Spirit"] = "スピリット",

	-- 防御
	["Armour"] = "アーマー",
	["Evasion Rating"] = "回避レーティング",
	["Evasion"] = "回避力",
	["Block Chance"] = "ブロック率",
	["Spell Block Chance"] = "スペルブロック率",
	["Dodge Roll Distance"] = "ドッジロール距離",

	-- 耐性
	["Fire Resistance"] = "火耐性",
	["Cold Resistance"] = "冷気耐性",
	["Lightning Resistance"] = "雷耐性",
	["Chaos Resistance"] = "カオス耐性",
	["Maximum Fire Resistance"] = "最大火耐性",
	["Maximum Cold Resistance"] = "最大冷気耐性",
	["Maximum Lightning Resistance"] = "最大雷耐性",
	["Maximum Chaos Resistance"] = "最大カオス耐性",
	["Elemental Resistance"] = "元素耐性",
	["All Elemental Resistances"] = "全元素耐性",

	-- ダメージ
	["Physical Damage"] = "物理ダメージ",
	["Fire Damage"] = "火ダメージ",
	["Cold Damage"] = "冷気ダメージ",
	["Lightning Damage"] = "雷ダメージ",
	["Chaos Damage"] = "カオスダメージ",
	["Elemental Damage"] = "元素ダメージ",
	["Spell Damage"] = "スペルダメージ",
	["Attack Damage"] = "アタックダメージ",
	["Melee Damage"] = "近接ダメージ",
	["Projectile Damage"] = "投射物ダメージ",
	["Area Damage"] = "範囲ダメージ",
	["Minion Damage"] = "ミニオンダメージ",

	-- クリティカル
	["Critical Strike"] = "クリティカル",
	["Critical Strike Chance"] = "クリティカル発生率",
	["Critical Damage Bonus"] = "クリティカルダメージボーナス",
	["Critical Hit Chance"] = "クリティカル発生率",

	-- 速度
	["Attack Speed"] = "攻撃速度",
	["Cast Speed"] = "詠唱速度",
	["Movement Speed"] = "移動速度",
	["Accuracy"] = "命中率",
	["Accuracy Rating"] = "命中レーティング",

	-- アトリビュート
	["Strength"] = "ストレングス",
	["Dexterity"] = "デクスタリティ",
	["Intelligence"] = "インテリジェンス",
	["All Attributes"] = "全アトリビュート",

	-- 状態異常
	["Stun Threshold"] = "スタン閾値",
	["Stun Duration"] = "スタン持続時間",
	["Ailment Threshold"] = "状態異常閾値",
	["Ignite Chance"] = "発火付与率",
	["Freeze Chance"] = "凍結付与率",
	["Shock Chance"] = "感電付与率",
	["Chill Effect"] = "冷却効果",
	["Bleed Chance"] = "出血付与率",
	["Poison Chance"] = "毒付与率",
	["Damage over Time"] = "継続ダメージ",
	["Damage over Time Multiplier"] = "継続ダメージ倍率",

	-- レベル・経験値
	["Level"] = "レベル",
	["Experience"] = "経験値",
	["Required Level"] = "必要レベル",

	-- ジェム
	["Gem Level"] = "ジェムレベル",
	["Quality"] = "品質",
	["Skill Effect Duration"] = "スキル効果持続時間",
	["Area of Effect"] = "効果範囲",
	["Cooldown Recovery Rate"] = "クールダウン回復速度",
	["Skill Mana Cost"] = "スキルマナコスト",
	["Skill Cost"] = "スキルコスト",
	["Reservation"] = "リザーブ",

	-- チャージ
	["Endurance Charge"] = "エンデュランスチャージ",
	["Frenzy Charge"] = "フレンジーチャージ",
	["Power Charge"] = "パワーチャージ",
	["Maximum Endurance Charges"] = "最大エンデュランスチャージ",
	["Maximum Frenzy Charges"] = "最大フレンジーチャージ",
	["Maximum Power Charges"] = "最大パワーチャージ",

	-- レイス
	["Rarity of Items"] = "アイテムレアリティ",
	["Quantity of Items"] = "アイテム個数",
	["Item Rarity"] = "アイテムレアリティ",
	["Item Quantity"] = "アイテム個数",

	-- アタック・スペル属性
	["Attack"] = "アタック",
	["Spell"] = "スペル",
	["Melee"] = "近接",
	["Projectile"] = "投射物",
	["Area"] = "範囲",
	["Aura"] = "オーラ",
	["Curse"] = "カース",
	["Mark"] = "マーク",
	["Minion"] = "ミニオン",
	["Totem"] = "トーテム",
	["Trap"] = "トラップ",
	["Mine"] = "マイン",
	["Brand"] = "ブランド",
}
