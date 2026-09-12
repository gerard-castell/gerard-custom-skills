#!/usr/bin/env python3
"""Cut a PNG into named pieces and vectorize each one, producing an SVG you can animate.

    python3 rig.py character.png rig.json -o rigged.svg

Each piece is traced from its own cut-out of the PNG, so the colour layers inside a piece keep
their stacking order and a piece can be rotated without dragging the rest of the drawing with it.

`rig.json` describes the pieces, as regions of the image (run grid.py to measure them):

    {
      "root": "detective",
      "parts": [
        {"id": "coat-group", "rest": true},
        {"id": "head-group", "region": [148, 0, 200, 240], "pivot": [300, 248],
         "children": [{"id": "eyes", "region": [248, 90, 105, 58], "pivot": [300, 118],
                       "under": "#f0d0b0"}]},
        {"id": "arm-group", "region": [[0, 80], [185, 80], [300, 340], [190, 395], [0, 300]],
         "pivot": [285, 355], "joint": [240, 300, 70, 80]}
      ]
    }

  region   [x, y, w, h] or a polygon [[x, y], ...]. Everything inside it becomes this piece and
           is cut out of the piece behind, so the boundary is a visible edge: run it along a line
           the drawing already has (a collar, a cuff, a hairline), not across an open face.
  rest     the piece that gets whatever no region claimed - the body. At most one, list it first.
  children pieces cut out of this one and drawn inside its group, so they inherit its movement
           (eyes in a head, a lens in a hand).
  under    colour painted into the hole a child leaves behind, e.g. skin under the eyes. Without
           it, shrinking the child (a blink) opens a transparent hole.
  pivot    [x, y] the piece turns around: the neck for a head, the shoulder for an arm. Echoed
           back for the animation code; preview.py rotates the piece around it so you can check.
  joint    [x, y, w, h]. A still copy of the piece, clipped to that rectangle, is drawn behind it
           so the seam does not open up when it rotates. Put it over the join, inside the body.

Pieces are drawn in the order listed, so a piece listed later covers the ones before it.

Requires: pip install vtracer pillow
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFilter
except ImportError:  # pragma: no cover
    sys.exit("missing dependency: pip install pillow vtracer")

sys.path.insert(0, str(Path(__file__).parent))
from trace import add_trace_options, load_subject, scaled_group, trace_paths  # noqa: E402


def region_mask(size: tuple[int, int], region: list) -> Image.Image:
    """White inside the region, black outside."""
    mask = Image.new("L", size, 0)
    draw = ImageDraw.Draw(mask)
    if region and isinstance(region[0], (int, float)):
        x, y, w, h = region
        draw.rectangle([x, y, x + w, y + h], fill=255)
    else:
        draw.polygon([(float(px), float(py)) for px, py in region], fill=255)
    return mask


def grow(mask: Image.Image, pixels: int) -> Image.Image:
    """Widen a mask, so the piece in front overlaps the one behind instead of leaving a seam."""
    if pixels <= 0:
        return mask
    return mask.filter(ImageFilter.MaxFilter(2 * pixels + 1))


def keep_only(img: Image.Image, mask: Image.Image) -> Image.Image:
    """The image with everything outside the mask made transparent."""
    out = img.copy()
    alpha = Image.new("L", img.size, 0)
    alpha.paste(img.getchannel("A"), (0, 0), mask)
    out.putalpha(alpha)
    return out


def cut_out(img: Image.Image, mask: Image.Image, fill: str | None) -> Image.Image:
    """The image with the mask removed, optionally repainted with a flat colour."""
    out = img.copy()
    if fill:
        patch = Image.new("RGBA", img.size, fill)
        # only where the piece actually had paint, so the fill cannot spill past the silhouette
        solid = Image.new("L", img.size, 0)
        solid.paste(img.getchannel("A"), (0, 0), mask)
        out.paste(patch, (0, 0), solid)
        return out
    alpha = out.getchannel("A")
    alpha.paste(Image.new("L", img.size, 0), (0, 0), mask)
    out.putalpha(alpha)
    return out


class Part:
    def __init__(self, spec: dict, depth: int = 0):
        self.id: str = spec["id"]
        self.region = spec.get("region")
        self.is_rest = bool(spec.get("rest"))
        self.pivot = spec.get("pivot")
        self.joint = spec.get("joint")
        self.under = spec.get("under")
        self.depth = depth
        self.children = [Part(c, depth + 1) for c in spec.get("children", [])]
        self.paths: list[str] = []
        if not self.region and not self.is_rest:
            sys.exit(f'part "{self.id}" needs either a "region" or "rest": true')
        if self.under and not self.region:
            sys.exit(f'part "{self.id}" has "under" but no region to fill')

    def walk(self):
        yield self
        for child in self.children:
            yield from child.walk()

    def trace(self, img: Image.Image, args: argparse.Namespace) -> None:
        """Trace this piece's cut-out of `img`, then recurse into its children."""
        mask = None if self.is_rest else grow(region_mask(img.size, self.region), args.bleed)
        mine = img if mask is None else keep_only(img, mask)
        for child in self.children:
            child.trace(mine, args)
            mine = cut_out(mine, region_mask(img.size, child.region), child.under)
        self.paths = trace_paths(mine, args)

    def render(self, upscale: float, indent: str = "  ") -> str:
        inner = scaled_group(self.paths, upscale, indent + "  ")
        for child in self.children:
            inner += child.render(upscale, indent + "  ")
        patch = ""
        if self.joint and self.paths:
            x, y, w, h = self.joint
            clip = f"joint-{self.id}"
            patch = (
                f'{indent}<clipPath id="{clip}"><rect x="{x}" y="{y}" width="{w}" height="{h}"/></clipPath>\n'
                f'{indent}<g clip-path="url(#{clip})">\n'
                f"{scaled_group(self.paths, upscale, indent + '  ')}"
                f"{indent}</g>\n"
            )
        return f'{patch}{indent}<g id="{self.id}">\n{inner}{indent}</g>\n'


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("png", type=Path)
    p.add_argument("rig", type=Path, help="rig description (JSON)")
    p.add_argument("-o", "--out", type=Path, required=True)
    p.add_argument("--bleed", type=int, default=2,
                   help="pixels a piece overlaps the one behind it, so cuts do not show as seams (default 2)")
    add_trace_options(p)
    args = p.parse_args()

    spec = json.loads(args.rig.read_text())
    parts = [Part(s) for s in spec["parts"]]
    if sum(part.is_rest for part in parts) > 1:
        sys.exit('only one part can be the "rest"')

    img, origin = load_subject(args.png, args)

    # every region belongs to exactly one piece: cut the claimed ones out of the body
    rest_image = img
    for part in parts:
        if not part.is_rest:
            rest_image = cut_out(rest_image, region_mask(img.size, part.region), None)

    for part in parts:
        part.trace(rest_image if part.is_rest else img, args)

    root_id = spec.get("root", "character")
    body = "".join(part.render(args.upscale) for part in parts)
    args.out.write_text(
        f'<?xml version="1.0" encoding="UTF-8"?>\n'
        f"<!-- rigged by png-to-animated-svg; keep these ids, the animation looks them up -->\n"
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {img.width} {img.height}">\n'
        f'<g id="{root_id}">\n{body}</g>\n</svg>\n'
    )

    print(f"{args.out}: viewBox 0 0 {img.width} {img.height}")
    if origin != (0, 0):
        print(f"  (the PNG was cropped at {origin[0]},{origin[1]}; regions are in the cropped box)")
    for part in parts:
        for node in part.walk():
            note = "  (rest)" if node.is_rest else ""
            empty = "  - EMPTY, is the region in the right place?" if not node.paths else ""
            print(f"  {'  ' * node.depth}#{node.id}: {len(node.paths)} paths{note}{empty}")

    pivots = [(n.id, n.pivot) for part in parts for n in part.walk() if n.pivot]
    if pivots:
        print("\npivots for the animation code (GSAP svgOrigin):")
        for part_id, (x, y) in pivots:
            print(f'  #{part_id}: svgOrigin "{x} {y}"')
    print("\nnext: preview.py, to check the pieces and the pivots in a browser")


if __name__ == "__main__":
    main()
