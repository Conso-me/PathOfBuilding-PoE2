-- FontDiag.lua: Font rendering diagnostic logger for Japanese localization.
-- Detects non-ASCII codepoints in strings before DrawString, logs them once.
-- Enable via: FONT_DIAG=1 (set in FontDiag itself or via ConExecute from console)

local FontDiag = {}

FontDiag.enabled = true
FontDiag.logFile = nil
FontDiag.seen = {}       -- avoid log spam for repeated strings
FontDiag.stats = { total = 0, japanese = 0, missing = 0 }

-- U+3000..U+9FFF covers CJK symbols, hiragana, katakana, CJK unified ideographs
local function isJapanese(cp)
	return cp >= 0x3000 and cp <= 0x9FFF
end

-- U+FF01..U+FF9F fullwidth/halfwidth forms
local function isFullwidth(cp)
	return cp >= 0xFF01 and cp <= 0xFF9F
end

local function needsJaFont(cp)
	return isJapanese(cp) or isFullwidth(cp)
end

-- Decode UTF-8 string into codepoints (returns iterator)
local function codepoints(s)
	local i = 1
	local len = #s
	return function()
		if i > len then return nil end
		local b = s:byte(i)
		local cp, advance
		if b < 0x80 then
			cp, advance = b, 1
		elseif b < 0xC0 then
			-- continuation byte at start = invalid
			cp, advance = 0xFFFD, 1
		elseif b < 0xE0 then
			local b2 = s:byte(i + 1) or 0x80
			cp = ((b - 0xC0) * 64) + (b2 - 0x80)
			advance = 2
		elseif b < 0xF0 then
			local b2 = s:byte(i + 1) or 0x80
			local b3 = s:byte(i + 2) or 0x80
			cp = ((b - 0xE0) * 4096) + ((b2 - 0x80) * 64) + (b3 - 0x80)
			advance = 3
		else
			local b2 = s:byte(i + 1) or 0x80
			local b3 = s:byte(i + 2) or 0x80
			local b4 = s:byte(i + 3) or 0x80
			cp = ((b - 0xF0) * 262144) + ((b2 - 0x80) * 4096) + ((b3 - 0x80) * 64) + (b4 - 0x80)
			advance = 4
		end
		i = i + advance
		return cp
	end
end

function FontDiag.analyzeString(s, context)
	if not FontDiag.enabled then return end
	if type(s) ~= "string" or #s == 0 then return end

	FontDiag.stats.total = FontDiag.stats.total + 1

	local hasCJK = false
	local missingCPs = {}

	for cp in codepoints(s) do
		if needsJaFont(cp) then
			hasCJK = true
			if not FontDiag.seen[cp] then
				FontDiag.seen[cp] = true
				missingCPs[#missingCPs + 1] = cp
			end
		end
	end

	if hasCJK then
		FontDiag.stats.japanese = FontDiag.stats.japanese + 1
		if #missingCPs > 0 then
			FontDiag.stats.missing = FontDiag.stats.missing + #missingCPs
			local preview = s:sub(1, 40) .. (#s > 40 and "..." or "")
			local cpList = {}
			for _, cp in ipairs(missingCPs) do
				cpList[#cpList + 1] = string.format("U+%04X", cp)
			end
			ConPrintf("[FontDiag] CJK chars without glyph in %s: %s | text: %s",
				context or "?", table.concat(cpList, " "), preview)
		end
	end
end

function FontDiag.printSummary()
	ConPrintf("[FontDiag] Summary: %d strings checked, %d had Japanese, %d unique missing codepoints",
		FontDiag.stats.total, FontDiag.stats.japanese, FontDiag.stats.missing)
end

-- Install a thin wrapper around the global DrawString.
-- Call FontDiag.installHook() once at startup (after RenderInit).
function FontDiag.installHook()
	local _real = DrawString
	if not _real then
		ConPrintf("[FontDiag] WARNING: DrawString global not found, hook not installed")
		return
	end
	DrawString = function(x, y, align, height, font, text, ...)
		FontDiag.analyzeString(text, string.format("DrawString(font=%s,h=%s)", tostring(font), tostring(height)))
		return _real(x, y, align, height, font, text, ...)
	end
	ConPrintf("[FontDiag] DrawString hook installed. CJK chars will be logged once each.")
end

return FontDiag
