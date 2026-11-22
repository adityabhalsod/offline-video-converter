"""Generate the app icon (PNG, Windows .ico and macOS .icns) with Pillow.

    pip install pillow
    python packaging/icons/make_icon.py

To use your own artwork instead, replace the three files in this folder
(icon.png 1024x1024, icon.ico, icon.icns) and keep the same names.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

HERE = Path(__file__).resolve().parent
SIZE = 1024
SS = 4  # supersampling factor for smooth edges

TOP = (99, 102, 241)  # indigo
BOTTOM = (14, 165, 233)  # sky blue


def _gradient(size: int) -> Image.Image:
    grad = Image.new("RGB", (1, size))
    for y in range(size):
        t = y / (size - 1)
        grad.putpixel((0, y), tuple(round(a + (b - a) * t) for a, b in zip(TOP, BOTTOM)))
    return grad.resize((size, size))


def render() -> Image.Image:
    s = SIZE * SS
    margin = round(s * 0.06)
    radius = round(s * 0.22)

    # Rounded-square background with a vertical gradient.
    mask = Image.new("L", (s, s), 0)
    ImageDraw.Draw(mask).rounded_rectangle((margin, margin, s - margin, s - margin), radius, fill=255)
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    img.paste(_gradient(s), (0, 0), mask)

    d = ImageDraw.Draw(img)
    white = (255, 255, 255, 255)
    cx, cy = s / 2, s / 2

    # Two circular "convert" arrows around the centre.
    r = s * 0.29
    w = round(s * 0.055)
    # PIL draws arc strokes inward from the box edge; offset so the stroke is centred on r.
    ro = r + w / 2
    box = (cx - ro, cy - ro, cx + ro, cy + ro)
    d.arc(box, 200, 326, fill=white, width=w)
    d.arc(box, 20, 146, fill=white, width=w)

    def head(angle_deg: float, clockwise: bool = True) -> None:
        import math

        a = math.radians(angle_deg)
        px, py = cx + r * math.cos(a), cy + r * math.sin(a)
        tx, ty = -math.sin(a), math.cos(a)  # tangent (clockwise direction in screen coords)
        if not clockwise:
            tx, ty = -tx, -ty
        nx, ny = math.cos(a), math.sin(a)  # outward normal
        L, H = s * 0.085, s * 0.07
        tip = (px + tx * L, py + ty * L)
        b1 = (px + nx * H, py + ny * H)
        b2 = (px - nx * H, py - ny * H)
        d.polygon([tip, b1, b2], fill=white)

    head(324)
    head(144)

    # Play triangle in the middle.
    t = s * 0.15
    d.polygon(
        [(cx - t * 0.75, cy - t), (cx - t * 0.75, cy + t), (cx + t * 1.05, cy)],
        fill=white,
    )

    img = img.resize((SIZE, SIZE), Image.LANCZOS)

    # Soft drop shadow underneath.
    shadow = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    sm = mask.resize((SIZE, SIZE), Image.LANCZOS).point(lambda v: v * 0.35)
    shadow.putalpha(sm)
    shadow = shadow.filter(ImageFilter.GaussianBlur(SIZE * 0.012))
    out = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    out.alpha_composite(shadow, (0, round(SIZE * 0.012)))
    out.alpha_composite(img)
    return out


def main() -> None:
    img = render()
    img.save(HERE / "icon.png")
    img.save(HERE / "icon.ico", sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    img.save(HERE / "icon.icns")
    print("Wrote icon.png, icon.ico, icon.icns to", HERE)


if __name__ == "__main__":
    main()
