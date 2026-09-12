# Animating the rig

All of this is GSAP on an **inline** SVG. `<img src="rigged.svg">` will not work - the pieces are
inside the file, and nothing outside can reach them.

```html
<script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/gsap.min.js"></script>
```

Rotate around a pivot with `svgOrigin`, in viewBox coordinates - the numbers `rig.py` printed:

```js
gsap.to("#head-group", { rotation: -3, svgOrigin: "300 248" });
```

`svgOrigin` beats `transformOrigin` here: it is in the SVG's own coordinates, so it does not move
when the SVG is resized, and it does not care where the element sits in the page.

## What makes an idle loop look alive

A character that waits is not standing still and is not doing one big thing. It is doing four
small things at once, none of them in step.

1. **Sway** - the whole body rocks a couple of degrees, pivoting between the feet.
2. **Breathe** - the chest scales to `1.01` on the vertical, pivoting at the waist. One percent.
3. **Swing** - arms and anything held move on *different* durations from each other (1.1s and
   0.8s, not 1.0s and 1.0s). This is the whole trick: give each piece a duration that shares no
   factor with the others and the loop stops being a loop. Four pieces at 0.8/0.9/1.1/1.0s take
   almost a minute to line up again.
4. **Blink** - the eyes squash on the vertical and open again, with a long pause between.

```js
// a blink has to close AND open inside one cycle. With yoyo + repeatDelay, the eyes hold shut
// through the pause, which reads as a character falling asleep.
gsap.timeline({ repeat: -1, repeatDelay: 2.4, defaults: { svgOrigin: "300 118" } })
  .to("#eyes", { scaleY: 0.1, duration: 0.08, ease: "power1.in" })
  .to("#eyes", { scaleY: 1, duration: 0.1, ease: "power1.out" });
```

Keep every rotation between 2 and 6 degrees, and ease everything `sine.inOut` - that is what
breathing and swaying feel like. `power2` is for things that start and stop.

**Hang it all off one timeline** (`idle.add(tween, 0)`), so that a single `idle.kill()` stops
everything when the loader hands over. Loose tweens keep running against elements another
animation is trying to pose, and the fight is hard to debug.

## Driving it from real loading

A fake progress bar that finishes before the page does is worse than none. Track real work:

```js
const tasks = [];
const track = (p) => tasks.push(Promise.resolve(p).catch(() => {}));  // failures still count

track(document.fonts.ready);
track(fetch("/api/whatever"));
track(new Promise((r) => addEventListener("load", r, { once: true })));

let settled = 0;
for (const t of tasks) t.then(() => Loader.progress(++settled / tasks.length));
Promise.all(tasks).then(Loader.done);
```

Two guards worth having, both in `assets/loader.html`:

- **a floor** (`MIN_SHOW`): if everything is cached the loader would flash for 80ms. Hold it for
  about a second so it reads as intentional.
- **a ceiling**: if a request hangs, reveal anyway after ~10s. Never trap someone behind a loader.

And make it skippable - any key or click - so no one has to sit through it twice.

## Handing over to the page

The simplest handover, and the one to use unless the artwork suggests something better: fade the
loader out while the page fades in, and let the page run its own entrance animation.

```js
function reveal() {
  document.body.classList.remove("loading");
  gsap.from("#page", { opacity: 0, y: 20, duration: 0.6, ease: "power2.out" });
  gsap.to(loader, { opacity: 0, duration: 0.5, onComplete: () => { idle.kill(); loader.remove(); } });
}
```

Start the page's own entrance *while* the loader is still going out. Sequential fades feel like
waiting twice.

Always `idle.kill()` and remove the SVG from the DOM. A few hundred KB of paths that nobody can
see still costs memory, and GSAP keeps ticking tweens on detached-looking elements.

## The lens dive: a transition that uses the artwork

If the character holds something transparent - a magnifier, a keyhole, a window, a mirror - the
page can arrive *through* it: the page appears small inside the lens, then the camera dives in
until it fills the screen. It is the difference between a loading screen and an opening shot.

The shape of it:

1. **Stop the idle** and settle the character into a neutral pose (`rotation: 0`, 0.45s).
2. **Look at it** - eyes widen, head turns towards the object. Half a second, and it is what sells
   the whole move.
3. **Turn the object to camera** - scale the lens on its x-axis until the ellipse reads as a
   circle facing the viewer.
4. **Show the page inside the glass**: make the page container visible and clip it to the lens.
   The lens is moving, so the clip has to follow it every frame:

   ```js
   const clipToLens = () => {
     const m = glass.getScreenCTM();                     // lens group -> screen pixels
     const pts = LENS_POINTS.map(([x, y]) => [m.a*x + m.c*y + m.e, m.b*x + m.d*y + m.f]);
     stage.style.clipPath = `polygon(${pts.map(([x, y]) => `${x}px ${y}px`).join(",")})`;
   };
   gsap.ticker.add(clipToLens);                          // remove it when the dive ends
   ```

   `LENS_POINTS` is 72 points around the lens ellipse, in the lens group's own coordinates - so
   the clip follows the lens through every rotation and scale without extra maths.

5. **Dive**: scale a camera group wrapping the whole SVG, and scale the page with it.

   ```js
   // z = zEnd^u makes the zoom feel like constant speed instead of a sudden rush at the end
   const z = Math.pow(zEnd, u);
   cam.setAttribute("transform", `translate(${cx} ${cy}) scale(${z}) translate(${-cx} ${-cy})`);
   page.style.transform = `scale(${pageScale0 * Math.pow(z, 0.62)})`;  // page is behind the glass
   ```

   Three things make or break this:
   - **exponential zoom.** Linear scale looks like it accelerates into your face. `zEnd^u` is
     perceptually even. Then ease `u` with `sine.inOut` - `power3.in` on top of an exponential
     accelerates twice and truncates at the end, so the dive stops dead instead of landing.
   - **the page moves slower than the lens** (`z^0.62`). It is behind the glass; matching speeds
     kills the depth. Set `pageScale0 = zEnd^-0.62` so the page lands at exactly `scale(1)`.
   - **`zEnd` from the geometry**: the furthest screen corner divided by the lens's smallest
     radius, times ~1.08. Anything less and the lens rim is still on screen when it ends.

6. **Clean up**: remove the ticker callback, clear the inline transforms and clip, kill the
   timeline, drop the SVG.

That is the whole algorithm - the rest is timing. Budget about 3 seconds: 0.5s to settle, 0.5s to
look, 0.5s to turn, 1.3s to dive.

## Reduced motion

```js
const reduced = matchMedia("(prefers-reduced-motion: reduce)").matches;
```

If it is set: skip the idle loop entirely (the character stands still - it still looks good, it is
a drawing), and replace any dive with a plain cross-fade. A zoom through a lens is exactly the
kind of motion that setting exists for. Keep the progress bar; that is information, not decoration.

## In React or another framework

- Load the SVG inline, not as an `<img>`. In a bundler, `?raw` / `dangerouslySetInnerHTML`, or a
  component that inlines it. In Next.js, importing it as a URL and fetching it works too, and it
  keeps the big file out of the JS bundle.
- Use `@gsap/react`'s `useGSAP` so the timelines are scoped and reverted on unmount. Without it a
  hot reload leaves old tweens fighting the new ones.
- Query pieces through a ref to the SVG element, not `document.querySelector` - two loaders on one
  page otherwise pose each other's limbs.
- Look every piece up once, check they are all there, and fall back to the plain fade if any is
  missing. The rig is a build artifact: someone will regenerate it with different ids one day, and
  it should degrade to a working page rather than a crash.
