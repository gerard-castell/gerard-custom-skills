#!/usr/bin/env python3
"""Vectorize a transparent PNG into flat colour shapes.

    python3 trace.py character.png -o traced.svg

The output keeps the look of the PNG (one filled path per flat colour region) but is made of
plain <path> elements. Use it to check the settings look right; `rig.py` does the real work,
tracing one piece at a time so that each piece can be animated on its own.

How it works:
  1. clean up the alpha fringe left by background removal (semi-transparent halo -> fully out),
  2. crop to the alpha bounding box so the viewBox hugs the subject,
  3. upscale (default 3x) so the tracer sees smooth edges instead of pixel stairs,
  4. run VTracer,
  5. wrap the paths in <g transform="scale(1/upscale)"> to get back to viewBox coordinates.

Requires: pip install vtracer pillow
"""

from __future__ import annotations

import argparse
import re
import sys
import tempfile
from pathlib import Path

try:
    from PIL import Image
except ImportError:  # pragma: no cover
    sys.exit("missing dependency: pip install pillow vtracer")

PATH_RE = re.compile(r"<path\b[^>]*/?>")

# Tracer settings, shared by trace.py and rig.py so a preview matches the final rig.
DEFAULTS = {
    "upscale": 3.0,
    "alpha_cutoff": 128,
    "pad": 2,
    "speckle": 2,
    "color_precision": 6,
    "layer_difference": 16,
    "corner_threshold": 60,
    "length_threshold": 4.0,
    "precision": 2,
}


def add_trace_options(parser: argparse.ArgumentParser) -> None:
    d = DEFAULTS
    parser.add_argument("--upscale", type=float, default=d["upscale"], help="supersample before tracing (default 3)")
    parser.add_argument("--alpha-cutoff", type=int, default=d["alpha_cutoff"], help="alpha below this is background")
    parser.add_argument("--pad", type=int, default=d["pad"], help="pixels kept around the subject")
    parser.add_argument("--no-crop", action="store_true", help="keep the original canvas instead of cropping")
    parser.add_argument("--speckle", type=int, default=d["speckle"], help="drop specks under N px; raise for fewer, simpler shapes")
    parser.add_argument("--color-precision", type=int, default=d["color_precision"])
    parser.add_argument("--layer-difference", type=int, default=d["layer_difference"], help="higher = fewer, flatter colour layers")
    parser.add_argument("--corner-threshold", type=int, default=d["corner_threshold"])
    parser.add_argument("--length-threshold", type=float, default=d["length_threshold"])
    parser.add_argument("--precision", type=int, default=d["precision"], help="decimals kept in path data")


def clean_alpha(img: Image.Image, cutoff: int) -> Image.Image:
    """Drop pixels below `cutoff` alpha and make the rest opaque.

    Background removal leaves a halo of semi-transparent pixels. A tracer turns that halo into
    its own pale colour layer, which shows up as a dirty outline around every piece.
    """
    img = img.convert("RGBA")
    alpha = img.getchannel("A").point(lambda a: 255 if a >= cutoff else 0)
    img.putalpha(alpha)
    return img


def crop_to_subject(img: Image.Image, pad: int) -> tuple[Image.Image, tuple[int, int]]:
    box = img.getchannel("A").getbbox()
    if box is None:
        return img, (0, 0)
    left = max(0, box[0] - pad)
    top = max(0, box[1] - pad)
    right = min(img.width, box[2] + pad)
    bottom = min(img.height, box[3] + pad)
    return img.crop((left, top, right, bottom)), (left, top)


def load_subject(png: Path, args: argparse.Namespace) -> tuple[Image.Image, tuple[int, int]]:
    """The PNG, cleaned and cropped: the coordinate space every region in rig.json refers to."""
    img = clean_alpha(Image.open(png), args.alpha_cutoff)
    if args.no_crop:
        return img, (0, 0)
    return crop_to_subject(img, args.pad)


def trace_paths(img: Image.Image, args: argparse.Namespace) -> list[str]:
    """Vectorize one RGBA image. Returns <path> tags in coordinates of the upscaled image."""
    import vtracer

    if img.getchannel("A").getbbox() is None:
        return []

    big = img
    if args.upscale != 1:
        big = img.resize((round(img.width * args.upscale), round(img.height * args.upscale)), Image.LANCZOS)
        big = clean_alpha(big, args.alpha_cutoff)  # resampling softens the alpha edge again

    # speckle is an area in pixels of the image actually handed to the tracer, and length is a
    # distance in it, so both have to follow the upscale or the detail explodes at 3x.
    speckle = max(1, round(args.speckle * args.upscale * args.upscale))
    length = args.length_threshold * args.upscale

    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "in.png"
        dst = Path(tmp) / "out.svg"
        big.save(src)
        # NOTE: pass every option POSITIONALLY. The Python binding lists keyword arguments in its
        # signature but segfaults on them with some interpreter builds; positional always works.
        vtracer.convert_image_to_svg_py(
            str(src),
            str(dst),
            "color",  # colormode
            "stacked",  # hierarchical: layers stack back to front, no cutout holes
            "spline",  # mode: curves, not polygons
            speckle,  # filter_speckle
            args.color_precision,  # color_precision: bits per channel
            args.layer_difference,  # layer_difference: merge colours closer than this
            args.corner_threshold,  # corner_threshold: degrees before a corner stays sharp
            length,  # length_threshold
            10,  # max_iterations
            45,  # splice_threshold
            args.precision,  # path_precision: decimals kept in path data
        )
        return PATH_RE.findall(dst.read_text())


def scaled_group(paths: list[str], upscale: float, indent: str = "") -> str:
    """Wrap traced paths so their coordinates read as viewBox units."""
    if not paths:
        return ""
    body = "\n".join(indent + "  " + p for p in paths)
    return f'{indent}<g transform="scale({1 / upscale:.6f})">\n{body}\n{indent}</g>\n'


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("png", type=Path)
    p.add_argument("-o", "--out", type=Path, required=True)
    add_trace_options(p)
    args = p.parse_args()

    img, origin = load_subject(args.png, args)
    paths = trace_paths(img, args)
    if not paths:
        sys.exit("the tracer produced no paths - check the PNG really has an alpha channel")

    args.out.write_text(
        f'<?xml version="1.0" encoding="UTF-8"?>\n'
        f"<!-- traced from {args.png.name} by png-to-animated-svg -->\n"
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {img.width} {img.height}">\n'
        f"{scaled_group(paths, args.upscale)}</svg>\n"
    )

    print(f"{args.out}: {len(paths)} paths, viewBox 0 0 {img.width} {img.height}")
    if origin != (0, 0):
        print(f"cropped at offset {origin[0]},{origin[1]} - regions in rig.json use the cropped box")
    print("next: run grid.py to measure the moving pieces, then rig.py")


if __name__ == "__main__":
    main()
