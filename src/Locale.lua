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
local modCache = { }
local T_MAP = { }
local T_MAP_built = false

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

-- Auto-register "Key:" ↔ "Key" colon variants. Many callsites build labels by
-- concatenating ":" themselves; mirror entries so either form hits the map.
-- Handles ASCII ":" and JA fullwidth "：" on the JA side.
local function endsWithColon(s)
	return s:sub(-1) == ":" or s:sub(-3) == "："
end

local function stripTrailingColon(s)
	if s:sub(-1) == ":" then return s:sub(1, -2) end
	if s:sub(-3) == "：" then return s:sub(1, -4) end
	return s
end

local function bridgeColons(map)
	local additions = { }
	for k, v in pairs(map) do
		if type(k) == "string" and type(v) == "string" and not k:find("\n", 1, true) then
			if endsWithColon(k) then
				local kStrip = stripTrailingColon(k):gsub("%s+$", "")
				if kStrip ~= "" and not map[kStrip] and not additions[kStrip] then
					additions[kStrip] = stripTrailingColon(v)
				end
			else
				local kCol = k .. ":"
				if not map[kCol] and not additions[kCol] then
					additions[kCol] = endsWithColon(v) and v or (v .. ":")
				end
			end
		end
	end
	for k, v in pairs(additions) do
		map[k] = v
	end
end

-- Build a single flat lookup table merging all category dicts.
-- Used by the DrawString hook (JaText) to translate at render time
-- instead of at per-callsite T() wrappers.
-- Iteration order = priority: later entries win on key collision.
-- Items is last to preserve the original ItemT() Items→Uniques fallback.
-- ModTemplates entries use {0}{1}... placeholders so they only collide with
-- runtime strings via the numeric-tokenizer fallback in JaText.translate;
-- listed early so concrete dicts can still override them on the rare event
-- of a literal key collision.
local function buildTMap()
	if T_MAP_built then return T_MAP end
	T_MAP = { }
	for _, name in ipairs({"ModTemplates", "UI", "Skills", "Stats", "Keywords", "Tree", "Uniques", "Items"}) do
		local d = loadDict(current, name)
		for k, v in pairs(d) do
			T_MAP[k] = v
		end
	end
	bridgeColons(T_MAP)
	T_MAP_built = true
	return T_MAP
end

function Locale.GetTMap()
	return buildTMap()
end

function Locale.SetLocale(locale)
	current = locale
	cache[locale] = nil
	modCache[locale] = nil
	T_MAP = { }
	T_MAP_built = false
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

-- Mods.lua merges base + overrides differently from key-value dicts (it's an
-- array-of-pattern-pairs). We cache the merged list with overrides FIRST so
-- they win the linear scan against the bigger base list.
local function loadModPatterns(locale)
	if modCache[locale] ~= nil then return modCache[locale] end
	local merged = { }
	local function append(name)
		local err, mods = PLoadModule("Locale/" .. locale .. "/" .. name)
		if not err and type(mods) == "table" and type(mods.patterns) == "table" then
			for _, p in ipairs(mods.patterns) do
				merged[#merged + 1] = p
			end
		end
	end
	-- Overrides first so they short-circuit the scan ahead of generic patterns.
	append("_overrides/Mods")
	append("Mods")
	modCache[locale] = merged
	return merged
end

-- Numeric tokenizer: replaces literal unsigned numbers (incl. (N-M) ranges,
-- decimals, trailing %) with {0}{1}... placeholders so a runtime string like
-- "+15 to Strength" tokenizes to "+{0} to Strength" (the "+" stays literal,
-- matching how poe2db scrapes mod-value spans). The (N-M) range parser keeps
-- its inner-sign acceptance because parens disambiguate. Existing {N}
-- placeholders in the source pass through. Returns (template, valueList)
-- where valueList[i] is the i-1 token's original literal (1-indexed; tokens
-- are 0-indexed).
local function tokenizeNumbers(s)
	if type(s) ~= "string" or s == "" then return s, { } end
	local out = { }
	local vals = { }
	local idx = 0
	local i = 1
	local n = #s
	while i <= n do
		local placeholder = s:match("^{%d+%%?}", i)
		if placeholder then
			out[#out + 1] = placeholder
			i = i + #placeholder
		else
			local rs, re, a, b, pct = s:find("^%(([%-%+]?%d+%.?%d*)%s*%-%s*([%-%+]?%d+%.?%d*)%)(%%?)", i)
			if rs then
				vals[#vals + 1] = string.format("(%s-%s)", a, b)
				out[#out + 1] = "{" .. idx .. "}" .. pct
				idx = idx + 1
				i = re + 1
			else
				local ns, ne, digits, dec, pct2 = s:find("^(%d+)(%.?%d*)(%%?)", i)
				if ns then
					vals[#vals + 1] = digits .. dec
					out[#out + 1] = "{" .. idx .. "}" .. pct2
					idx = idx + 1
					i = ne + 1
				else
					out[#out + 1] = s:sub(i, i)
					i = i + 1
				end
			end
		end
	end
	return table.concat(out), vals
end

local function applyTokens(template, vals)
	if type(template) ~= "string" or not vals or #vals == 0 then return template end
	return (template:gsub("{(%d+)}", function(n)
		return vals[tonumber(n) + 1] or ("{" .. n .. "}")
	end))
end

function Locale.TokenizeNumbers(s) return tokenizeNumbers(s) end
function Locale.ApplyTokens(t, v) return applyTokens(t, v) end

function Locale.ModFormat(line)
	if type(line) ~= "string" or line == "" then return line end
	local patterns = loadModPatterns(current)
	for i = 1, #patterns do
		local pat = patterns[i]
		local out, count = line:gsub(pat.en, pat.ja)
		if count > 0 then return out end
	end
	return line
end

return Locale
