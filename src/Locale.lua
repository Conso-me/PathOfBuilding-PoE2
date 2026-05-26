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

local function loadDict(locale, name)
	cache[locale] = cache[locale] or { }
	if cache[locale][name] == nil then
		local errMsg, dict = PLoadModule("Locale/" .. locale .. "/" .. name)
		if errMsg or type(dict) ~= "table" then
			cache[locale][name] = { }
		else
			cache[locale][name] = dict
		end
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
