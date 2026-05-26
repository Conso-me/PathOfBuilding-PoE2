-- Manual overrides for src/Locale/ja_JP/Mods.lua.
-- Entries here are checked FIRST by ModFormat() — useful for replacing
-- over-specific scraped patterns with generalized templates.
--
-- Same shape as Mods.lua: { patterns = { { en = <Lua pattern>, ja = <repl> } } }
return {
	patterns = {
		-- Example: scraped "Monster Level: 83" → generalize to any level
		{ en = "^Monster Level: (%d+)$", ja = "モンスターレベル: %1" },
	},
}
