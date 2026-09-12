<div align="center">

# png-to-animated-svg

**One flat PNG in. An SVG that waves, blinks and breathes out.**

<table>
<tr>
<td align="center"><img src="assets/demo/robot-before.png" width="330" alt="A cartoon robot as a flat PNG: one rectangle of pixels, nothing in it can move"></td>
<td align="center"><img src="assets/demo/robot-after.gif" width="330" alt="The same robot as a rigged SVG: the head tilts, the eyes blink, one arm waves, the body sways and breathes"></td>
</tr>
<tr>
<td align="center"><code>robot.png</code> — pixels</td>
<td align="center"><code>rigged.svg</code> + a GSAP idle loop</td>
</tr>
</table>

</div>

That is the same drawing on both sides. Nothing was redrawn, and there is no sprite sheet: the PNG
was cut into named pieces, each piece was vectorized from its own cut-out, and the result is an SVG
whose head, eyes, arms and chest light each carry their own transform. It stays sharp at any size,
and it took about fifteen minutes.

## 🎬 How that happened

```
robot.png  --grid.py-->    grid.png      read the pieces off a labelled coordinate grid
           --rig.json-->                 you name the pieces: region, pivot, what's a child of what
           --rig.py-->     rigged.svg    each piece traced from its own cut-out, named group
           --preview.py--> preview.html  tint the pieces, drag a slider, catch bad cuts early
           + GSAP          the animation (assets/loader.html is a working starting point)
```

The robot above is nine pieces: body, head, two arms, two eyes, two antenna bulbs, chest light.
Its rig is checked in as [`assets/demo/robot.rig.json`](assets/demo/robot.rig.json) if you want to
see what a finished one looks like — regions as polygons traced along the shoulder balls, eyes as
ellipses with a socket colour painted underneath so a blink reveals an eyelid rather than a hole.

## 🧩 What's in the box

| | |
|---|---|
| `scripts/grid.py` | The PNG with labelled coordinates, cropped exactly as the tracer crops it. This is how you measure. |
| `scripts/rig.py` | PNG + `rig.json` → `rigged.svg`. Rect or polygon regions, nested parts, pivots, seam patches, bleed. |
| `scripts/preview.py` | Tint each part, rotate each part around its pivot with a slider. Use it before writing any animation. |
| `scripts/trace.py` | The vectorizer — VTracer at 3× supersampling, alpha cleanup, auto-crop. |
| `assets/loader.html` | A working loading screen: idle loop, real-progress API, reveal. |
| `reference/rigging.md` | Where to run cut lines, where pivots go, what to do when it looks wrong. |
| `reference/animating.md` | The idle loop, driving it from real loading, the handover, and the lens-dive transition. |

## ⚡ Try it

```bash
python3 -m venv .venv && .venv/bin/pip install vtracer pillow

.venv/bin/python scripts/grid.py character.png -o grid.png     # measure
$EDITOR rig.json                                                # describe the pieces
.venv/bin/python scripts/rig.py character.png rig.json -o rigged.svg
.venv/bin/python scripts/preview.py rigged.svg rig.json -o preview.html
```

Then paste `rigged.svg` inline into `assets/loader.html` and fill in the ids and pivots that
`rig.py` printed. [`SKILL.md`](SKILL.md) walks the whole thing step by step.

The PNG needs a transparent background — tracing a solid one makes a single giant shape that
swallows the character.

## 🪤 Things that will bite you

- **Small angles.** Idle motion lives at 2–6°. Past that the cuts between pieces open up.
- **Whole-figure motion goes on the root group.** A sibling does not inherit its sibling's
  transform, so swaying the torso alone slides it out from under the head and arms — every seam
  opens at once.
- **A circular cut centred on the pivot is free.** It maps onto itself under rotation, so an arm
  cut around its shoulder ball needs no seam patch at all.
- **The SVG must be inline in the DOM.** `<img src="rigged.svg">` renders it but hides its insides;
  GSAP has nothing to grab.
- **The file is big** — about 1 MB of path data for a detailed character, ~350 KB gzipped. Serve it
  compressed and drop it from the DOM once the loader is gone.

`reference/rigging.md` has the full table of *what you see* → *what it is*.

---
