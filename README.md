# gerard-custom-skills

Skills for [Claude Code](https://claude.com/claude-code), published as a plugin marketplace.

## Install

```
/plugin marketplace add gerard-castell/gerard-custom-skills
/plugin install png-to-animated-svg@gerard-custom-skills
```

Or drop a single skill in by hand:

```bash
git clone https://github.com/gerard-castell/gerard-custom-skills.git
cp -r gerard-custom-skills/plugins/png-to-animated-svg/skills/png-to-animated-svg ~/.claude/skills/
```

## Skills

### png-to-animated-svg

A PNG is one flat rectangle of pixels: nothing in it can move on its own. This skill turns it into
an SVG made of named groups — a head, an arm, a pair of eyes — that GSAP can pose independently,
and then into an animation on a real page. It is not a redraw and not a sprite sheet: the artwork
is vectorized piece by piece, so it stays sharp at any size.

```
character.png  --grid.py-->    grid.png      read the pieces off a labelled coordinate grid
               --rig.py-->     rigged.svg    each piece traced from its own cut-out, named group
               --preview.py--> preview.html  check the pieces and the pivots in a browser
               + GSAP          the animation (assets/loader.html is a working starting point)
```

What ships with it:

- `scripts/trace.py` — the vectorizer (VTracer at 3x supersampling, alpha cleanup, auto-crop).
- `scripts/grid.py` — the PNG with labelled coordinates, cropped exactly as the tracer crops it.
- `scripts/rig.py` — PNG + `rig.json` → `rigged.svg`. Rect or polygon regions, nested parts,
  pivots, seam patches, bleed.
- `scripts/preview.py` — tint each part, rotate each part around its pivot with a slider.
- `assets/loader.html` — a working loading screen: idle loop, real-progress API, reveal.
- `reference/rigging.md` — where to run cut lines, where pivots go, what to do when it looks wrong.
- `reference/animating.md` — the idle loop, driving it from real loading, the handover, and the
  lens-dive transition (the page arrives *through* a magnifying glass the character is holding).

Requirements: Python 3 with `vtracer` and `pillow`. The PNG needs a transparent background.

Built by reverse-engineering a hand-made Sherlock Holmes loading screen, then validated by
regenerating that same character from its PNG with nothing but the shipped example rig.

## Licence

MIT — see [LICENSE](LICENSE).
