#!/usr/bin/env python3
"""Draw a labelled coordinate grid over the PNG, in the coordinates trace.py produces.

    python3 grid.py character.png -o grid.png

Look at grid.png and read off the boxes for rig.json: head, arm, whatever moves. The grid uses
the same crop as trace.py, so a rectangle measured here is a `region` in the traced viewBox.

Requires: pip install pillow
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw
except ImportError:  # pragma: no cover
    sys.exit("missing dependency: pip install pillow")

sys.path.insert(0, str(Path(__file__).parent))
from trace import clean_alpha, crop_to_subject  # noqa: E402


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("png", type=Path)
    p.add_argument("-o", "--out", type=Path, required=True)
    p.add_argument("--step", type=int, default=50, help="grid spacing in viewBox units (default 50)")
    p.add_argument("--zoom", type=float, default=2.0, help="scale the preview up so labels stay readable")
    p.add_argument("--alpha-cutoff", type=int, default=128)
    p.add_argument("--pad", type=int, default=2)
    p.add_argument("--no-crop", action="store_true")
    args = p.parse_args()

    img = clean_alpha(Image.open(args.png), args.alpha_cutoff)
    if not args.no_crop:
        img, _ = crop_to_subject(img, args.pad)
    width, height = img.size

    canvas = Image.new("RGB", (round(width * args.zoom), round(height * args.zoom)), "white")
    subject = img if args.zoom == 1 else img.resize(canvas.size, Image.LANCZOS)
    canvas.paste(subject, (0, 0), subject)

    draw = ImageDraw.Draw(canvas, "RGBA")
    for x in range(0, width + 1, args.step):
        sx = x * args.zoom
        draw.line([(sx, 0), (sx, canvas.height)], fill=(220, 30, 30, 110), width=1)
        draw.text((sx + 3, 3), str(x), fill=(180, 0, 0))
    for y in range(0, height + 1, args.step):
        sy = y * args.zoom
        draw.line([(0, sy), (canvas.width, sy)], fill=(30, 80, 220, 110), width=1)
        draw.text((3, sy + 3), str(y), fill=(0, 0, 180))

    canvas.save(args.out)
    print(f"{args.out}: viewBox 0 0 {width} {height}, grid every {args.step} units, drawn at {args.zoom}x")


if __name__ == "__main__":
    main()
