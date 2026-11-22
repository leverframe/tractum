"""Tractum OG / social-preview image generator.

1280x640 (GitHub social preview spec, also valid og:image).
Seal Amber tokens per the vaulted tractum brand brief
(vault 10_PROJECTS/tractum/brand/BRAND-BRIEF.md — canonical hex lives
there; duplicated here because the brief ships prose, not JSON).
NEWELL green is deliberately absent from this surface.

Usage:
    py scripts/generate_og.py
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

SPACE_GROTESK_DIR = Path.home() / "AppData/Local/Microsoft/Windows/Fonts"
JETBRAINS_DIR = Path.home() / "AppData/Local/Microsoft/Windows/Fonts"

SPACE_GROTESK = {
    "Medium":   SPACE_GROTESK_DIR / "SpaceGrotesk-variable.ttf",  # variable font
    "SemiBold": SPACE_GROTESK_DIR / "SpaceGrotesk-variable.ttf",
    "Bold":     SPACE_GROTESK_DIR / "SpaceGrotesk-Bold.ttf",
}
JETBRAINS = {
    "Regular": JETBRAINS_DIR / "JetBrainsMono-Regular.ttf",
    "Medium":  JETBRAINS_DIR / "JetBrainsMono-Medium.ttf",
    "Bold":    JETBRAINS_DIR / "JetBrainsMono-Bold.ttf",
}

CANVAS_W = 1280
CANVAS_H = 640

EVENT_ID = "3974ebfe688f1639a8534b46bbbfeddf354d18efcd190352da877756d1bac60b"

# Seal Amber tokens — tractum brand brief v0.1 (see module docstring)
BG = "#0A0A0A"
SURFACE = "#101010"
BORDER = "#1F1F1F"
TEXT = "#FFFFFF"
MUTED = "#9E9E9E"
PRIMARY = "#FFB000"  # Seal Amber — the ONE brand color
GRAY = "#3D3D3D"     # non-quorum bars

LOCKUP_PNG = Path("assets/tractum-lockup.png")
VERSION = "v0.6.0"


def parse_hex(s: str) -> tuple[int, int, int]:
    s = s.strip().lstrip("#")
    return int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16)


def font(path: Path, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(path), size)


def grid(n: int) -> int:
    return int(n * 8)


def main() -> int:
    bg = parse_hex(BG)
    text = parse_hex(TEXT)
    primary = parse_hex(PRIMARY)
    muted = parse_hex(MUTED)
    surface = parse_hex(SURFACE)
    border = parse_hex(BORDER)
    gray = parse_hex(GRAY)

    canvas = Image.new("RGB", (CANVAS_W, CANVAS_H), bg)
    draw = ImageDraw.Draw(canvas)

    # Scanline texture (subtle material depth)
    scanline_overlay = (
        min(surface[0] + 6, 255),
        min(surface[1] + 6, 255),
        min(surface[2] + 6, 255),
    )
    for y in range(0, CANVAS_H, 4):
        draw.line([(0, y), (CANVAS_W, y)], fill=scanline_overlay, width=1)

    # Hairline border frame
    inset = grid(2)
    draw.rectangle(
        [inset, inset, CANVAS_W - inset, CANVAS_H - inset],
        outline=border,
        width=1,
    )

    margin_x = grid(8)  # 64px

    # 1. Lockup (amber bars mark + wordmark) — centered top
    lockup = Image.open(LOCKUP_PNG).convert("RGBA")
    lockup_w = 560
    lockup_h = int(lockup.height * lockup_w / lockup.width)  # ~105
    lockup = lockup.resize((lockup_w, lockup_h), Image.Resampling.LANCZOS)
    # Chroma-key the lockup's baked-in #0A0A0A plate so it sits clean on
    # the scanline canvas (mark strokes are amber/white/#3D3D3D — safe).
    px = lockup.load()
    for yy in range(lockup.height):
        for xx in range(lockup.width):
            r, g, b, a = px[xx, yy]
            if abs(r - 10) <= 18 and abs(g - 10) <= 18 and abs(b - 10) <= 18:
                px[xx, yy] = (r, g, b, 0)
    lockup_x = (CANVAS_W - lockup_w) // 2
    lockup_y = grid(7)  # 56px
    canvas.paste(lockup, (lockup_x, lockup_y), lockup)

    # Version chip — sits under the lockup, right-aligned terminal style
    chip_font = font(JETBRAINS["Medium"], 18)
    chip_text = f"tractum {VERSION}"
    chip_pad_x = grid(2)
    chip_pad_y = grid(1)
    chip_bbox = draw.textbbox((0, 0), chip_text, font=chip_font)
    chip_w = chip_bbox[2] - chip_bbox[0] + chip_pad_x * 2
    chip_h = chip_bbox[3] - chip_bbox[1] + chip_pad_y * 2
    chip_x = (CANVAS_W - chip_w) // 2
    chip_y = lockup_y + lockup_h + grid(2)
    draw.rounded_rectangle(
        [chip_x, chip_y, chip_x + chip_w, chip_y + chip_h],
        radius=4,
        fill=surface,
        outline=border,
        width=1,
    )
    draw.text(
        (chip_x + chip_pad_x - chip_bbox[0], chip_y + chip_pad_y - chip_bbox[1]),
        chip_text,
        font=chip_font,
        fill=primary,
    )

    # 2. Terminal session (left-aligned)
    term_font = font(JETBRAINS["Regular"], 20)
    term_lines = [
        ("$ reach_consensus --sign=ed25519 --publish=nostr", primary),
        ("> three agents · debate (round 2)", muted),
        ("> agreement: 34%", muted),
        ("> signing... ✓", text),
        ("> publishing to wss://nos.lol ... ✓", text),
        ("[ok] kind:30078 ed25519 4/7 relays nak verify: 0", primary),
    ]
    term_y = chip_y + chip_h + grid(3)
    line_height = 28
    for line, color in term_lines:
        draw.text((margin_x, term_y), line, font=term_font, fill=color)
        term_y += line_height

    # 3. Hero title — Space Grotesk SemiBold, centered
    title_text = "VERIFIABLE CONSENSUS"
    title_font = font(SPACE_GROTESK["SemiBold"], 84)
    title_bbox = draw.textbbox((0, 0), title_text, font=title_font)
    title_w = title_bbox[2] - title_bbox[0]
    title_h = title_bbox[3] - title_bbox[1]
    title_x = (CANVAS_W - title_w) // 2 - title_bbox[0]
    title_y = grid(53)  # 424px — hero position below terminal
    draw.text((title_x, title_y), title_text, font=title_font, fill=text)

    # Blinking cursor block immediately after title
    cursor_w, cursor_h = 24, title_h - 12
    cursor_x = title_x + title_w + 12
    cursor_y = title_y + 12
    draw.rectangle([cursor_x, cursor_y, cursor_x + cursor_w, cursor_y + cursor_h], fill=primary)

    # 4. Subtitle
    subtitle_text = "signed agreement, on the open wire"
    subtitle_font = font(SPACE_GROTESK["Medium"], 32)
    sub_bbox = draw.textbbox((0, 0), subtitle_text, font=subtitle_font)
    sub_w = sub_bbox[2] - sub_bbox[0]
    sub_x = (CANVAS_W - sub_w) // 2 - sub_bbox[0]
    sub_y = title_y + title_h + grid(3)
    draw.text((sub_x, sub_y), subtitle_text, font=subtitle_font, fill=muted)

    # 5. Footer — event ID hash, bottom-right (tiny mono)
    footer_font = font(JETBRAINS["Regular"], 14)
    footer_text = EVENT_ID
    foot_bbox = draw.textbbox((0, 0), footer_text, font=footer_font)
    foot_w = foot_bbox[2] - foot_bbox[0]
    foot_x = CANVAS_W - margin_x - foot_w - foot_bbox[0]
    foot_y = CANVAS_H - grid(8) - (foot_bbox[3] - foot_bbox[1])
    draw.text((foot_x, foot_y), footer_text, font=footer_font, fill=muted)

    # 6. Tractum mark (5 bars + agreement line) — bottom-left, drawn natively
    # Spec per brand brief: 3 tall amber quorum bars, 2 short gray bars,
    # white base line. Rendered small (~72px tall) as a signature.
    mark_h = 72
    bar_w, bar_gap, bar_r = 12, 12, 6
    tall_h, short_h = int(mark_h * 0.78), int(mark_h * 0.52)
    base_h = 12
    mark_w = 5 * bar_w + 4 * bar_gap
    mx, my = margin_x, CANVAS_H - grid(8) - mark_h
    for i in range(5):
        bx = mx + i * (bar_w + bar_gap)
        if i in (1, 2, 3):
            by = my
            bh = tall_h
            color = primary
        else:
            by = my + (tall_h - short_h)
            bh = short_h
            color = gray
        draw.rounded_rectangle([bx, by, bx + bar_w, by + bh], radius=bar_r, fill=color)
    base_y = my + mark_h - base_h
    draw.rounded_rectangle(
        [mx, base_y, mx + mark_w, base_y + base_h], radius=6, fill=text
    )

    out_path = Path("assets/og/tractum-og.png").resolve()
    canvas.save(out_path, optimize=True)
    print(f"wrote {out_path} ({canvas.width}x{canvas.height})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
