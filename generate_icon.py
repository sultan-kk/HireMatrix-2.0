"""
generate_icon.py  (Style C — network/matrix motif)
-----------------------------------------------------
The THIRD distinct HireMatrix brand identity, built for this fresh
redesign. Concept: a grid of connected nodes forming a subtle "H" —
literally illustrating the "Matrix" half of the name (a network/graph),
while the highlighted node + connecting lines suggest "matching" data
points, which is what the app actually does (matching resume text to
structured fields). Flat, geometric, modern — a deliberately different
mark from the document+magnifier and "HM" monogram versions used before.

Produces:
    assets/icon.png / assets/icon.ico  — square app icon
    assets/logo_banner.png             — wide header banner

Run once:
    python generate_icon.py
"""

import os
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
FONTS_DIR = os.path.join(ASSETS_DIR, "fonts")
os.makedirs(ASSETS_DIR, exist_ok=True)

ICON_PATH = os.path.join(ASSETS_DIR, "icon.png")
ICON_ICO_PATH = os.path.join(ASSETS_DIR, "icon.ico")
BANNER_PATH = os.path.join(ASSETS_DIR, "logo_banner.png")

BOLD_FONT_PATH = os.path.join(FONTS_DIR, "BricolageGrotesque-Bold.ttf")
REGULAR_FONT_PATH = os.path.join(FONTS_DIR, "InstrumentSans-Regular.ttf")

# ---------------------------------------------------------------------------
# Brand palette (Style C) — deep indigo + coral accent. Keep in sync with
# theme.py's CSS variables.
# ---------------------------------------------------------------------------
INDIGO_DARK = (30, 27, 75)     # near-black indigo, icon/sidebar bg
INDIGO = (49, 46, 129)
CORAL = (251, 113, 133)        # warm accent for the "matched" node
WHITE = (255, 255, 255)
DIM_NODE = (99, 102, 241)      # unmatched nodes (soft indigo-violet)
INK = (226, 232, 240)


def _font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()


def _rounded_mask(size, radius):
    mask = Image.new("L", size, 0)
    d = ImageDraw.Draw(mask)
    d.rounded_rectangle([0, 0, size[0] - 1, size[1] - 1], radius=radius, fill=255)
    return mask


# 4x4 grid node positions (normalized 0..1) that trace an "H" shape when
# connected: two vertical strokes + a horizontal crossbar.
_H_NODES = {
    (0, 0), (0, 1), (0, 2), (0, 3),         # left vertical stroke
    (3, 0), (3, 1), (3, 2), (3, 3),         # right vertical stroke
    (1, 1), (2, 1),                          # crossbar (row 1, between the strokes)
}
_H_EDGES = [
    ((0, 0), (0, 1)), ((0, 1), (0, 2)), ((0, 2), (0, 3)),
    ((3, 0), (3, 1)), ((3, 1), (3, 2)), ((3, 2), (3, 3)),
    ((0, 1), (1, 1)), ((1, 1), (2, 1)), ((2, 1), (3, 1)),
]
_HIGHLIGHT_NODE = (2, 1)  # the "matched data point" — drawn in coral


def _draw_network(draw, origin_x, origin_y, cell, node_r, line_w):
    def pos(gx, gy):
        return origin_x + gx * cell, origin_y + gy * cell

    for a, b in _H_EDGES:
        draw.line([pos(*a), pos(*b)], fill=DIM_NODE, width=line_w)

    for node in _H_NODES:
        x, y = pos(*node)
        r = node_r
        color = CORAL if node == _HIGHLIGHT_NODE else WHITE
        draw.ellipse([x - r, y - r, x + r, y + r], fill=color)
        if node == _HIGHLIGHT_NODE:
            # soft outer ring to draw the eye to the "matched" node
            draw.ellipse([x - r - 10, y - r - 10, x + r + 10, y + r + 10], outline=CORAL, width=4)


def build_icon():
    size = 512
    icon = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    flat = Image.new("RGB", (size, size), INDIGO_DARK)
    icon.paste(flat, (0, 0), _rounded_mask((size, size), radius=100))
    draw = ImageDraw.Draw(icon)

    _draw_network(draw, origin_x=146, origin_y=116, cell=93, node_r=17, line_w=7)

    icon.save(ICON_PATH)
    print(f"Saved {ICON_PATH}")
    icon.save(ICON_ICO_PATH, format="ICO", sizes=[(16, 16), (32, 32), (48, 48), (256, 256)])
    print(f"Saved {ICON_ICO_PATH}")


def build_banner(tagline="AI-Assisted Resume Intelligence for HR Teams"):
    w, h = 1600, 300
    banner = Image.new("RGB", (w, h), INDIGO_DARK)
    draw = ImageDraw.Draw(banner)

    if os.path.exists(ICON_PATH):
        mark = Image.open(ICON_PATH).convert("RGBA")
    else:
        build_icon()
        mark = Image.open(ICON_PATH).convert("RGBA")
    mark_size = 190
    mark = mark.resize((mark_size, mark_size), Image.LANCZOS)
    banner.paste(mark, (56, (h - mark_size) // 2), mark)

    title_font = _font(BOLD_FONT_PATH, 86)
    tagline_font = _font(REGULAR_FONT_PATH, 30)

    text_x = 56 + mark_size + 46
    draw.text((text_x, 68), "Hire", font=title_font, fill=WHITE)
    hire_w = draw.textlength("Hire", font=title_font)
    draw.text((text_x + hire_w, 68), "Matrix", font=title_font, fill=CORAL)
    draw.text((text_x + 4, 168), tagline, font=tagline_font, fill=INK)

    # a few faint background network dots on the right, echoing the icon
    import random
    random.seed(7)
    for _ in range(22):
        x = random.randint(int(w * 0.72), w - 40)
        y = random.randint(30, h - 30)
        r = random.choice([3, 4, 5])
        draw.ellipse([x - r, y - r, x + r, y + r], fill=DIM_NODE)

    banner.save(BANNER_PATH)
    print(f"Saved {BANNER_PATH}")


if __name__ == "__main__":
    build_icon()
    build_banner()
