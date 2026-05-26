#!/usr/bin/env python3
"""
Generate Japanese font atlas (TGA + TGF) for SimpleGraphic/PoB.

Format: RGBA TGA (white glyphs on transparent background),
        TGF with sequential glyph entries (index = codepoint).

Usage:
    python3 tools/gen_ja_font.py [--sizes 10,12,14] [--font /path/to/font.ttf]
"""

import os
import sys
import struct
import argparse
from pathlib import Path

try:
    from PIL import Image, ImageFont, ImageDraw
except ImportError:
    print("ERROR: Pillow not found. Run: uv pip install pillow")
    sys.exit(1)

FONT_PATH = "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf"
OUTPUT_DIR = Path(__file__).parent.parent / "runtime" / "SimpleGraphic" / "Fonts"
FONT_NAME = "JA"

# Sizes must match exactly what PoB requests via DrawString
SIZES = [10, 12, 14, 16, 18, 20, 24, 28, 32]

# Character ranges to include in the atlas
# These are also the codepoints that need REAL glyph entries in TGF.
GLYPH_RANGES = [
    (0x0020, 0x007F),  # ASCII printable
    (0x3000, 0x303F),  # CJK symbols & punctuation (。、「」 etc.)
    (0x3041, 0x3097),  # Hiragana
    (0x30A1, 0x3100),  # Katakana
    (0xFF01, 0xFF5F),  # Fullwidth Latin (！～ etc.)
    (0xFF61, 0xFF9F),  # Halfwidth Katakana
]

MAX_CODEPOINT = 0xFF9F  # End of halfwidth katakana (ranges above)
MAX_CODEPOINT_CJK = 0x9FFF  # End of CJK unified ideographs

# Extra individual codepoints (e.g. kanji used in translation) — loaded at runtime
EXTRA_CODEPOINTS = []


def build_charset():
    """Return sorted list of codepoints to actually render."""
    cps = set()
    for start, end in GLYPH_RANGES:
        for cp in range(start, end):
            cps.add(cp)
    for cp in EXTRA_CODEPOINTS:
        cps.add(cp)
    return sorted(cps)

def make_atlas(size, font_path, charset):
    """
    Render all characters in charset onto an RGBA atlas.
    Returns (Image, dict[codepoint -> (x, y, w, xoff, advance)]).
    """
    try:
        pil_font = ImageFont.truetype(font_path, size)
    except Exception as e:
        print(f"  ERROR loading font at size {size}: {e}", file=sys.stderr)
        return None, {}

    # --- Measure all glyphs to plan atlas layout ---
    measurements = {}
    for cp in charset:
        ch = chr(cp)
        try:
            bbox = pil_font.getbbox(ch)
            # bbox = (left, top, right, bottom) relative to origin
            if bbox is None or bbox[2] <= bbox[0]:
                # Zero-width or unmeasurable
                measurements[cp] = None
                continue
            w = bbox[2] - bbox[0]
            h = bbox[3] - bbox[1]
            xoff = -bbox[0]          # shift so leftmost pixel is at x
            yoff = -bbox[1]          # shift so topmost pixel is at y
            try:
                adv = int(pil_font.getlength(ch) + 0.5)
            except Exception:
                adv = w
            measurements[cp] = (w, h, xoff, yoff, adv)
        except Exception:
            measurements[cp] = None

    # --- Pack glyphs into atlas rows ---
    PAD = 2  # pixels of padding between glyphs
    row_height = size + PAD * 2

    atlas_width = 2048
    # First pass: compute total area to size the atlas
    cursor_x = PAD
    cursor_y = PAD
    glyph_positions = {}  # cp -> (x, y)

    for cp in charset:
        m = measurements.get(cp)
        if m is None:
            continue
        w, h, xoff, yoff, adv = m
        cell_w = w + PAD * 2

        if cursor_x + cell_w > atlas_width:
            cursor_x = PAD
            cursor_y += row_height + PAD

        glyph_positions[cp] = (cursor_x, cursor_y)
        cursor_x += cell_w

    # atlas height = next power-of-two >= (cursor_y + row_height + PAD)
    needed_h = cursor_y + row_height + PAD
    atlas_height = 1
    while atlas_height < needed_h:
        atlas_height *= 2
    atlas_height = max(atlas_height, 128)

    atlas = Image.new("RGBA", (atlas_width, atlas_height), (255, 255, 255, 0))
    draw = ImageDraw.Draw(atlas)

    glyph_map = {}  # cp -> (atlas_x, atlas_y, glyph_w, xoff, extra_advance)

    for cp in charset:
        m = measurements.get(cp)
        if m is None:
            continue
        w, h, xoff, yoff, adv = m
        ax, ay = glyph_positions[cp]

        # Draw the character at (ax + xoff, ay + yoff) so the bounding box
        # lines up with (ax, ay).
        try:
            draw.text((ax + xoff, ay + yoff), chr(cp), font=pil_font,
                      fill=(255, 255, 255, 255))
        except Exception:
            continue

        extra_adv = adv - w  # SimpleGraphic "advance" field = extra space beyond width
        glyph_map[cp] = (ax, ay, w, xoff, extra_adv)

    return atlas, glyph_map


def save_tga(img, path):
    """Save Pillow Image as uncompressed RGBA TGA."""
    img.save(str(path), format="TGA")
    print(f"  Saved TGA: {path} ({img.size[0]}x{img.size[1]})")


def build_tgf_section(size, glyph_map, placeholder_advance):
    """
    Build a HEIGHT section of the TGF file.
    Returns list of lines (strings, without newline).
    """
    lines = [f"HEIGHT {size};"]

    # Placeholder for codepoints with no glyph: width=1 px, no visual content
    placeholder = (0, 0, 1, 0, placeholder_advance)

    for cp in range(MAX_CODEPOINT + 1):
        if cp in glyph_map:
            ax, ay, w, xoff, extra_adv = glyph_map[cp]
            w = max(w, 1)  # minimum width = 1
            lines.append(
                f"GLYPH {ax:4d} {ay:4d} {w:2d} {xoff:2d} {extra_adv:2d};"
                f"\t// {cp}"
                + (f" ({chr(cp)})" if 0x20 <= cp < 0x7F else "")
            )
        else:
            ax, ay, w, xoff, adv = placeholder
            lines.append(
                f"GLYPH {ax:4d} {ay:4d} {w:2d} {xoff:2d} {adv:2d};"
                f"\t// {cp}"
            )
    return lines


def log(msg):
    print(msg, flush=True)


def main():
    parser = argparse.ArgumentParser(description="Generate Japanese font atlas for PoB SimpleGraphic")
    parser.add_argument("--font", default=FONT_PATH, help="Path to Japanese TTF/OTF font")
    parser.add_argument("--sizes", default=",".join(str(s) for s in SIZES),
                        help="Comma-separated list of sizes to generate")
    parser.add_argument("--out", default=str(OUTPUT_DIR), help="Output directory")
    parser.add_argument("--name", default=FONT_NAME, help="Font family name")
    parser.add_argument("--luamap", default=None,
                        help="Path to output Lua glyph map (for JaText.lua image renderer)")
    parser.add_argument("--extra-codepoints", default=None,
                        help="File with one decimal codepoint per line to add to charset")
    parser.add_argument("--scan-src", default=None,
                        help="Scan this directory for .lua files and add all CJK codepoints found")
    args = parser.parse_args()

    sizes = [int(s) for s in args.sizes.split(",")]
    out_dir = Path(args.out)
    font_name = args.name

    # Load extra codepoints
    global EXTRA_CODEPOINTS
    if args.extra_codepoints:
        with open(args.extra_codepoints, encoding="utf-8") as f:
            EXTRA_CODEPOINTS = [int(line.strip()) for line in f if line.strip()]
        log(f"Extra codepoints from file: {len(EXTRA_CODEPOINTS)}")
    if args.scan_src:
        found = set()
        for root, _, files in os.walk(args.scan_src):
            for fname in files:
                if not fname.endswith(".lua"):
                    continue
                try:
                    text = open(os.path.join(root, fname), encoding="utf-8", errors="replace").read()
                except Exception:
                    continue
                for ch in text:
                    cp = ord(ch)
                    if (0x4E00 <= cp <= 0x9FFF) or (0x3400 <= cp <= 0x4DBF):
                        found.add(cp)
        EXTRA_CODEPOINTS = sorted(set(EXTRA_CODEPOINTS) | found)
        log(f"Extra codepoints from scan: {len(EXTRA_CODEPOINTS)} total")

    if not os.path.exists(args.font):
        print(f"ERROR: Font file not found: {args.font}")
        import subprocess
        r = subprocess.run(["fc-list", ":lang=ja"], capture_output=True, text=True)
        print(r.stdout[:1000])
        sys.exit(1)

    log(f"Font: {args.font}")
    log(f"Sizes: {sizes}")
    log(f"Output: {out_dir}")
    log(f"Font name: {font_name}")
    log(f"Max codepoint: U+{MAX_CODEPOINT:04X}")

    charset = build_charset()
    log(f"Characters to render: {len(charset)} (U+0020..U+{MAX_CODEPOINT:04X})")

    all_sections = []
    all_glyph_maps = {}  # size -> glyph_map

    for size in sizes:
        log(f"\n[Size {size}]")
        atlas, glyph_map = make_atlas(size, args.font, charset)
        if atlas is None:
            log(f"  SKIP size {size} (font load failed)")
            continue

        log(f"  Glyphs mapped: {len(glyph_map)} / {len(charset)}")
        all_glyph_maps[size] = glyph_map

        # Save TGA
        tga_path = out_dir / f"{font_name}.{size}.tga"
        w_atlas, h_atlas = atlas.size
        save_tga(atlas, tga_path)

        # Build TGF section
        placeholder_adv = max(2, size // 2)
        section = build_tgf_section(size, glyph_map, placeholder_adv)
        all_sections.extend(section)
        all_sections.append("")  # blank line between sections
        log(f"  TGF section: {len(section)} lines")

        # Store atlas dimensions in glyph_map for Lua output
        all_glyph_maps[size]["__atlas_w"] = w_atlas
        all_glyph_maps[size]["__atlas_h"] = h_atlas

    # Write combined TGF
    tgf_path = out_dir / f"{font_name}.tgf"
    with open(str(tgf_path), "w", encoding="utf-8") as f:
        f.write("\n".join(all_sections))
    log(f"\nWrote TGF: {tgf_path} ({len(all_sections)} lines)")

    # Optionally write Lua glyph map for DrawImage-based rendering
    if args.luamap:
        lua_path = Path(args.luamap)
        lua_path.parent.mkdir(parents=True, exist_ok=True)
        with open(str(lua_path), "w", encoding="utf-8") as f:
            f.write("-- Auto-generated by gen_ja_font.py — do not edit by hand.\n")
            f.write("-- Glyph positions in JA.{size}.tga for each codepoint.\n")
            f.write("-- Format: [cp] = {x, y, w, xoff, adv}\n")
            f.write("-- adv = advance beyond width (extra right spacing)\n\n")
            f.write("local M = {}\n\n")
            for size, gm in sorted(all_glyph_maps.items()):
                aw = gm.pop("__atlas_w", 2048)
                ah = gm.pop("__atlas_h", 128)
                f.write(f"M[{size}] = {{\n")
                f.write(f"  atlasW = {aw}, atlasH = {ah},\n")
                f.write(f"  g = {{\n")
                for cp in sorted(gm.keys()):
                    ax, ay, w, xoff, extra_adv = gm[cp]
                    adv_total = w + extra_adv
                    if 0x20 <= cp < 0x7F:
                        comment = f" -- {chr(cp)}"
                    elif cp >= 0x3000:
                        try:
                            comment = f" -- {chr(cp)}"
                        except Exception:
                            comment = ""
                    else:
                        comment = ""
                    f.write(f"    [{cp}]={{{ax},{ay},{w},{xoff},{adv_total}}},{comment}\n")
                f.write(f"  }},\n")
                f.write(f"}}\n\n")
            f.write("return M\n")
        log(f"Wrote Lua glyph map: {lua_path}")

    log("\nDone.")


if __name__ == "__main__":
    main()
