# Cutting a drawing into pieces

Everything hard about this step is the same problem: a cut-out piece has an edge that was never
drawn. The original artist drew a head attached to a neck; you are about to draw a line through
it. The craft is in putting that line somewhere the eye already expects one, and in keeping the
motion small enough that what is behind the line never shows.

## Choosing regions

**Run the boundary along a line the drawing already has.** A collar, a cuff, a hairline, the rim
of a hat, the edge of a sleeve. Those are places where the artwork already changes colour, so a
seam there reads as part of the drawing.

**Never cut across an open, smooth area** - the middle of a cheek, a flat expanse of coat. Any
seam there is a scar.

**Cut generously, then hide the overlap.** A region should include a little of what is behind it
(a head region can reach down past the jaw into the collar). `rig.py` also grows every region by
`--bleed` pixels (2 by default) so pieces overlap instead of leaving a hairline gap. Raise it to
3-4 if you still see seams; lower it to 0 if pieces visibly double up.

**Order matters.** Pieces are drawn in the order listed, later on top. Put a piece whose cut is
ugly *behind* the piece that covers it: a head listed before the coat has its neck cut hidden by
the collar. The `rest` piece (the body) goes first.

**Rectangles for compact pieces, polygons for limbs.** An arm that crosses the body diagonally
needs a polygon; a rectangle around it swallows half the torso. Polygon points are
`[[x, y], ...]` in the same coordinates, in order around the shape.

## Choosing pivots

The pivot is the point the piece turns around, and it is almost never the centre of the piece.
Put it where the joint is in the drawing:

| piece        | pivot                                               |
| ------------ | --------------------------------------------------- |
| whole body   | between the feet, at the bottom edge (a sway)        |
| head         | the neck, where it disappears into the collar       |
| arm          | the shoulder                                        |
| held object  | the wrist, not the object's own centre              |
| eyes         | their own middle (they squash, they do not swing)   |
| chest        | the waist, so breathing lifts upwards               |

A pivot in the wrong place shows up immediately in `preview.py`: the piece swings away from the
body instead of turning inside it. Nudge and rebuild - only the JSON changes, so it is cheap.

## Filling holes: `under`

A child piece is cut out of its parent, leaving a hole. That is invisible while the child covers
it - but a blink scales the eyes to nothing, and the hole shows through.

`"under": "#f0d0b0"` paints the hole with a flat colour before the parent is traced: skin behind
the eyes, shadow behind a mouth. Pick the colour from the artwork around the hole (any colour
picker, or read the pixel with Pillow). Leave `under` out for pieces that only rotate.

## Patching seams: `joint`

A piece that rotates pulls away from the body at its join, and a wedge of nothing opens up.
`"joint": [x, y, w, h]` draws a still copy of the piece behind it, clipped to that rectangle, so
there is always something under the seam.

Put the rectangle over the join and slightly *inside* the body - covering the neck, or the
shoulder where the sleeve meets the coat. Keep it small: it does not move, so a large patch
becomes a visible ghost of the piece at rest.

If a piece needs a big patch to look right, the real fix is usually a smaller rotation or a
better-placed cut.

## When it still looks wrong

| what you see                                  | what it is                                              |
| --------------------------------------------- | ------------------------------------------------------- |
| a piece reported as 0 paths                   | the region is off the artwork - re-measure on `grid.png` |
| a straight seam across the drawing            | the cut runs through open artwork; move it to an edge    |
| a hairline gap along a cut                    | raise `--bleed`                                          |
| a hole opening when a piece shrinks           | the child needs `under`                                  |
| a wedge opening when a piece rotates          | add or widen `joint`, or rotate less                     |
| a ghost of the piece standing still behind it | the `joint` rectangle is too big                         |
| the piece swings out of its socket            | the pivot is wrong                                       |
| details lost, shapes look melted              | lower `--speckle`, or raise `--upscale`                  |
| the file is enormous                          | raise `--speckle`; try `--layer-difference 24`           |
| a pale outline around everything              | the PNG's alpha fringe - raise `--alpha-cutoff`          |

## What the tracer is doing

`vtracer` in `stacked` colour mode: it quantizes the image into flat colour layers and emits one
filled path per connected region, back to front. Layers stack, so a path drawn later covers the
one before it.

That stacking is why pieces are traced **separately**, each from its own cut-out of the PNG.
Tracing once and then sorting the paths into groups by position breaks it: a single path often
spans the whole figure (the line art usually does), and moving it into one group puts it behind
shapes that were on top of it. The drawing falls apart. One trace per piece keeps every layer
order intact, at the cost of a second or two per piece.
