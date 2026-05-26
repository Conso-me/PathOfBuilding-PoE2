-- Path of Building PoE2 — Japanese Localization
-- Overlay-based i18n. Internal state stays English (build XML / ModParser
-- compatibility); translation applied only at render time.
--
-- Globals registered by Launch.lua:
--   T(key)             UI string lookup
--   SkillT(name)       Skill/gem name lookup
--   ItemT(name)        Item/base name lookup
--   StatT(name)        Stat name lookup
--   KeywordT(name)     Keyword/buff lookup
--   ModFormat(line)    Mod template pattern translation
--
-- All lookups fall back to the original English on miss.

local Locale = { }
local current = "ja_JP"
local cache = { }

-- loadDict merges two sources for the given category:
--   1. src/Locale/<locale>/<name>.lua          — base dictionary (auto-scraped
--                                                from poe2db or manually
--                                                maintained; do not hand-edit
--                                                if scraped — scrape will
--                                                clobber changes)
--   2. src/Locale/<locale>/_overrides/<name>.lua — optional user overrides
--                                                that win when present.
--                                                Safe to hand-edit; scraper
--                                                never touches this dir.
local function loadDict(locale, name)
	cache[locale] = cache[locale] or { }
	if cache[locale][name] == nil then
		local merged = { }
		local err1, base = PLoadModule("Locale/" .. locale .. "/" .. name)
		if not err1 and type(base) == "table" then
			for k, v in pairs(base) do merged[k] = v end
		end
		local err2, overrides = PLoadModule("Locale/" .. locale .. "/_overrides/" .. name)
		if not err2 and type(overrides) == "table" then
			for k, v in pairs(overrides) do merged[k] = v end
		end
		cache[locale][name] = merged
	end
	return cache[locale][name]
end

function Locale.SetLocale(locale)
	current = locale
	cache[locale] = nil
end

function Locale.GetLocale()
	return current
end

function Locale.T(key)
	if type(key) ~= "string" then return key end
	return loadDict(current, "UI")[key] or key
end

function Locale.SkillT(name)
	if type(name) ~= "string" then return name end
	return loadDict(current, "Skills")[name] or name
end

function Locale.ItemT(name)
	if type(name) ~= "string" then return name end
	local v = loadDict(current, "Items")[name]
	if v then return v end
	return loadDict(current, "Uniques")[name] or name
end

function Locale.StatT(name)
	if type(name) ~= "string" then return name end
	return loadDict(current, "Stats")[name] or name
end

function Locale.KeywordT(name)
	if type(name) ~= "string" then return name end
	return loadDict(current, "Keywords")[name] or name
end

function Locale.ModFormat(line)
	if type(line) ~= "string" or line == "" then return line end
	local mods = loadDict(current, "Mods")
	local patterns = mods.patterns
	if type(patterns) ~= "table" then return line end
	for i = 1, #patterns do
		local pat = patterns[i]
		local out, count = line:gsub(pat.en, pat.ja)
		if count > 0 then return out end
	end
	return line
end

return Locale
