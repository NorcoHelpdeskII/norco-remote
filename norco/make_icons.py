#!/usr/bin/env python3
"""Regenerate the Norco Remote Android launcher and notification icons.

    python norco/make_icons.py <square-logo.png> [--background "#000000"] [--badge 0.86]

<square-logo> is a square image with the round badge centred in it. --badge is the badge's
diameter as a fraction of the image width. Needs Pillow (pip install pillow).

Writes into flutter/android/app/src/main/res:
  mipmap-*/ic_launcher.png, ic_launcher_round.png   legacy icons (Android 7 and older)
  mipmap-*/ic_launcher_foreground.png               adaptive icon foreground (Android 8+)
  mipmap-*/ic_stat_logo.png                         status-bar icon (white on transparent)
  values/ic_launcher_background.xml                 adaptive icon background colour
"""
import argparse
import os
import sys

from PIL import Image, ImageChops, ImageDraw, ImageFilter

RES = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "..", "flutter", "android", "app", "src", "main", "res")
DENSITIES = {"mdpi": 1.0, "hdpi": 1.5, "xhdpi": 2.0, "xxhdpi": 3.0, "xxxhdpi": 4.0}
SS = 4  # supersampling for smooth edges


def circle_mask(size, diameter, feather=0):
    mask = Image.new("L", (size, size), 0)
    off = (size - diameter) / 2
    ImageDraw.Draw(mask).ellipse((off, off, off + diameter, off + diameter), fill=255)
    return mask.filter(ImageFilter.GaussianBlur(feather)) if feather else mask


def badge(logo, badge_fraction):
    """The round badge cut out of the logo, as a square RGBA image."""
    side = min(logo.size)
    left, top = (logo.width - side) // 2, (logo.height - side) // 2
    square = logo.crop((left, top, left + side, top + side)).convert("RGBA")
    d = int(side * badge_fraction)
    off = (side - d) // 2
    cut = square.crop((off, off, off + d, off + d))
    cut.putalpha(circle_mask(d, d - 2, feather=1))
    return cut


def stat_icon(px):
    """Status-bar icon: a ring with a slanted N, white on transparent."""
    s = px * SS * 4
    img = Image.new("L", (s, s), 0)
    draw = ImageDraw.Draw(img)
    w = s * 0.085
    draw.ellipse((w / 2, w / 2, s - w / 2, s - w / 2), outline=255, width=int(w))
    x0, x1, y0, y1, t, slant = s * 0.31, s * 0.69, s * 0.27, s * 0.73, s * 0.115, s * 0.05
    draw.polygon([(x0, y1), (x0 + slant, y0), (x0 + slant + t, y0), (x0 + t, y1)], fill=255)
    draw.polygon([(x1 - t - slant, y1), (x1 - t, y0), (x1, y0), (x1 - slant, y1)], fill=255)
    draw.polygon([(x0 + slant, y0), (x0 + slant + t, y0), (x1 - slant, y1), (x1 - slant - t, y1)],
                 fill=255)
    alpha = img.resize((px, px), Image.LANCZOS)
    out = Image.new("RGBA", (px, px), (255, 255, 255, 0))
    out.putalpha(alpha)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("logo")
    ap.add_argument("--background", default="#000000")
    ap.add_argument("--badge", type=float, default=0.86)
    args = ap.parse_args()

    art = badge(Image.open(args.logo), args.badge)
    bg = args.background

    for name, scale in DENSITIES.items():
        out = os.path.join(RES, f"mipmap-{name}")
        os.makedirs(out, exist_ok=True)

        # Adaptive foreground: 108dp canvas, artwork inside the 66dp safe zone.
        fg_px = round(108 * scale)
        fg = Image.new("RGBA", (fg_px, fg_px), (0, 0, 0, 0))
        d = round(66 * scale)
        fg.alpha_composite(art.resize((d, d), Image.LANCZOS), ((fg_px - d) // 2,) * 2)
        fg.save(os.path.join(out, "ic_launcher_foreground.png"), optimize=True)

        # Legacy icons: the badge on a filled circle.
        px = round(48 * scale)
        big = px * SS
        disc = Image.new("RGBA", (big, big), (0, 0, 0, 0))
        fill = Image.new("RGBA", (big, big), bg)
        disc.paste(fill, (0, 0), circle_mask(big, big - SS))
        d = round(big * 0.94)
        disc.alpha_composite(art.resize((d, d), Image.LANCZOS), ((big - d) // 2,) * 2)
        legacy = disc.resize((px, px), Image.LANCZOS)
        legacy.save(os.path.join(out, "ic_launcher.png"), optimize=True)
        legacy.save(os.path.join(out, "ic_launcher_round.png"), optimize=True)

        stat_icon(round(24 * scale)).save(os.path.join(out, "ic_stat_logo.png"), optimize=True)

    with open(os.path.join(RES, "values", "ic_launcher_background.xml"), "w", newline="\n") as f:
        f.write('<?xml version="1.0" encoding="utf-8"?>\n<resources>\n'
                f'    <color name="ic_launcher_background">{bg}</color>\n</resources>\n')
    print("icons written to", os.path.normpath(RES))


if __name__ == "__main__":
    sys.exit(main())
