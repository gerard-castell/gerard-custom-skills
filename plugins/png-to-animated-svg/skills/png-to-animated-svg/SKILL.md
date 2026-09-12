---
name: png-to-animated-svg
description: Turn a flat PNG (a character, mascot, logo, illustration - typically background-removed or AI-generated) into a rigged SVG whose pieces move independently, and into a real web animation such as a loading screen or an intro. Use when someone wants to animate a still image, make a character wave/blink/breathe, build an animated loader from artwork, or vectorize a PNG into animatable parts.
---

# PNG to animated SVG

A PNG is one flat rectangle of pixels: nothing in it can move on its own. This skill turns it
into an SVG made of named groups - a head, an arm, a pair of eyes - that GSAP can pose
independently, and then into an animation on a real page.

The result still looks like the original drawing. It is not a redraw, and not a sprite sheet:
the artwork is vectorized piece by piece, so it stays sharp at any size and every piece keeps its
own transform.

## The pipeline

```
character.png  --grid.py-->   grid.png     you (or the user) read the pieces off the image
               --rig.py-->    rigged.svg   each piece traced from its own cut-out, named group
               --preview.py--> preview.html check the pieces and the pivots in a browser
               + GSAP          the animation (assets/loader.html is a working starting point)
```

### 0. Set up

```bash
python3 -m venv .venv && .venv/bin/pip install vtracer pillow
```

The PNG needs a transparent background. If it has a solid one, remove it first (`rembg`, a
background-removal tool, or the user's own file) - tracing a background makes one giant shape
that swallows the character.

### 1. See the image, and measure it

**Look at the PNG yourself** (read the image file) before anything else. You are deciding what
moves; that is an artistic call, not a mechanical one. Then:

```bash
.venv/bin/python scripts/grid.py character.png -o grid.png
```

Read `grid.png` (it is the image with labelled coordinates, cropped exactly the way the tracer
will crop it) and write down a box for each piece that should move.

Decide with the user, or propose: what moves, and what kind of motion? A loading loop usually
wants 3-5 pieces. More pieces means more seams to hide, not more life - a body that sways, an
arm that swings, a head that tilts and blinks already reads as alive.

### 2. Describe the rig

Write `rig.json`: one entry per piece, back to front.

```json
{
  "root": "detective",
  "parts": [
    { "id": "coat-group", "rest": true, "pivot": [200, 517] },
    {
      "id": "head-group",
      "region": [148, 0, 200, 240],
      "pivot": [300, 248],
      "joint": [230, 215, 130, 30],
      "children": [
        { "id": "eyes", "region": [248, 90, 105, 58], "pivot": [300, 118], "under": "#f0d0b0" }
      ]
    },
    {
      "id": "arm-group",
      "region": [[0, 80], [185, 80], [300, 340], [190, 395], [0, 300]],
      "pivot": [285, 355],
      "joint": [240, 300, 70, 80]
    }
  ]
}
```

`python3 scripts/rig.py --help` documents every field. The two that decide whether this looks
good: **where the region boundary runs** (along a collar, a cuff, a hairline - never across an
open face) and **where the pivot sits** (a real joint: neck, shoulder, wrist).
See `reference/rigging.md` before guessing.

### 3. Build and check

```bash
.venv/bin/python scripts/rig.py character.png rig.json -o rigged.svg
.venv/bin/python scripts/preview.py rigged.svg rig.json -o preview.html
```

`rig.py` prints how many shapes each piece got and the pivots in GSAP's `svgOrigin` format.
A piece with 0 paths means its region is in the wrong place.

Open `preview.html`: tint the parts to see what ended up where, and drag each slider to rotate a
piece around its pivot. **Do this before writing any animation** - a wrong pivot or a bad cut is
obvious here and invisible in a diff. Screenshot it if you want to look at it yourself.

Then go back to step 2 and adjust. Two or three rounds is normal.

### 4. Animate it

Copy `assets/loader.html` next to the artwork, paste `rigged.svg` inline into it, and fill in the
ids and pivots at the top of its script. That gives a working loading screen: an idle loop, a
progress bar, and a reveal.

`reference/animating.md` covers what to do from there - what makes an idle loop look alive rather
than mechanical, how to drive it from real loading progress, how to hand over to the page, the
lens-dive transition, reduced motion, and how to wire this into React or another framework.

## Hard-won details

- **The SVG must be inline in the DOM.** `<img src="rigged.svg">` renders it but hides its
  insides; GSAP has nothing to grab.
- **Keep the ids.** The animation looks pieces up by id. If you re-run the tracer or push the file
  through SVGO, keep them (`svgo --config` with `cleanupIds: false`).
- **Small angles.** Idle motion lives at 2-6 degrees. Past that the cut lines between pieces open
  up, and `joint` patches start to show.
- **The file is big.** A detailed character runs about 1 MB of path data, ~350 KB gzipped - every
  piece is traced separately, so it costs more than a single trace. Serve it compressed, and drop
  it from the DOM once the loader is gone. To shrink it, raise `--speckle` (3 or 4 gives fewer,
  simpler shapes with the same silhouette) and run it through SVGO.
- **`vtracer`'s Python binding segfaults on keyword arguments** on some builds. `trace.py` calls it
  positionally; keep it that way.
