-- Manual overrides for src/Locale/ja_JP/Skills.lua.
-- Entries here win over the poe2db-scraped base. See ./README.md.
return {
	-- poe2db: "ショックフラッシュ" — looks like a translation slip (should be
	-- "ショック時キャスト" to mirror "Cast on Critical" / "Cast on Freeze" etc.)
	["Cast on Shock"] = "ショック時キャスト",
}
