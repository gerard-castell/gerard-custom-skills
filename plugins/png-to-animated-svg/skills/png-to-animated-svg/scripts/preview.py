#!/usr/bin/env python3
"""Build a self-contained page for checking a rig: tint the parts, drag them around their pivots.

    python3 preview.py rigged.svg rig.json -o preview.html

Open preview.html in a browser.
  - "tint parts" colours each group, so you can see exactly which shapes ended up where. Anything
    that is the wrong colour belongs to the wrong region: fix rig.json and run rig.py again.
  - one slider per part rotates it around the pivot you picked. If the piece tears away from the
    body, the pivot is off, or the part needs a `joint` patch in rig.json.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

TEMPLATE = """<!doctype html>
<meta charset="utf-8">
<title>rig preview</title>
<style>
  :root { color-scheme: light dark; }
  body { margin: 0; font: 14px system-ui, sans-serif; display: flex; min-height: 100vh; }
  main { flex: 1; display: grid; place-items: center; padding: 16px; background: #14100c; }
  svg { width: min(80vw, 70vh); height: auto; }
  aside { width: 300px; padding: 16px; overflow-y: auto; background: Canvas; color: CanvasText; }
  h1 { font-size: 15px; margin: 0 0 12px; }
  label { display: block; margin: 10px 0 2px; font-weight: 600; }
  input[type=range] { width: 100%; }
  .val { float: right; font-weight: 400; opacity: .7; font-variant-numeric: tabular-nums; }
  .no-pivot { opacity: .55; font-weight: 400; font-size: 12px; }
  button { margin-top: 12px; width: 100%; padding: 6px; }
  @media (max-width: 700px) { body { flex-direction: column; } aside { width: auto; } }
</style>
<main>__SVG__</main>
<aside>
  <h1>rig preview</h1>
  <label><input type="checkbox" id="tint"> tint parts</label>
  <div id="controls"></div>
  <button id="reset">reset pose</button>
</aside>
<script>
const PARTS = __PARTS__;
const PIVOTS = __PIVOTS__;
const svg = document.querySelector("svg");
const COLORS = ["#e2574c","#4c9fe2","#4ce28a","#e2c84c","#b04ce2","#4ce2d8","#e28a4c","#8ae24c"];

// tinting: one CSS rule per part, so it can be toggled without touching the paths
const sheet = document.createElement("style");
sheet.textContent = PARTS.map((p, i) =>
  `.tinted #${p.id} path { fill: ${COLORS[i % COLORS.length]} !important; }`).join("\\n");
document.head.append(sheet);
tint.onchange = () => document.body.classList.toggle("tinted", tint.checked);

const state = new Map();
function pose(id, deg) {
  const el = svg.querySelector("#" + id);
  const pivot = PIVOTS[id];
  if (!el) return;
  state.set(id, deg);
  el.setAttribute("transform",
    pivot ? `rotate(${deg} ${pivot[0]} ${pivot[1]})` : `rotate(${deg})`);
}

for (const part of PARTS) {
  const row = document.createElement("div");
  const pivot = PIVOTS[part.id];
  row.innerHTML = `<label for="s-${part.id}">${part.id}
      ${pivot ? "" : '<span class="no-pivot">(no pivot: spins around 0,0)</span>'}
      <span class="val" id="v-${part.id}">0&deg;</span></label>
    <input type="range" id="s-${part.id}" min="-30" max="30" step="0.5" value="0">`;
  controls.append(row);
  const slider = row.querySelector("input");
  slider.oninput = () => {
    pose(part.id, +slider.value);
    document.getElementById("v-" + part.id).textContent = slider.value + "\\u00b0";
  };
}

reset.onclick = () => {
  for (const input of controls.querySelectorAll("input")) { input.value = 0; input.oninput(); }
};
</script>
"""


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("rigged", type=Path, help="output of rig.py")
    p.add_argument("rig", type=Path, help="the same rig description rig.py used")
    p.add_argument("-o", "--out", type=Path, required=True)
    args = p.parse_args()

    svg = args.rigged.read_text()
    svg = re.sub(r"<\?xml[^>]*\?>\s*", "", svg)
    svg = re.sub(r"<!--.*?-->\s*", "", svg, flags=re.DOTALL)

    spec = json.loads(args.rig.read_text())

    parts: list[dict] = []
    pivots: dict[str, list[float]] = {}

    def collect(specs: list[dict]) -> None:
        for s in specs:
            parts.append({"id": s["id"]})
            if s.get("pivot"):
                pivots[s["id"]] = s["pivot"]
            collect(s.get("children", []))

    collect(spec["parts"])

    args.out.write_text(
        TEMPLATE.replace("__SVG__", svg.strip())
        .replace("__PARTS__", json.dumps(parts))
        .replace("__PIVOTS__", json.dumps(pivots))
    )
    missing = [p["id"] for p in parts if p["id"] not in pivots]
    print(f"{args.out}: {len(parts)} parts")
    if missing:
        print('  no "pivot" in rig.json for: ' + ", ".join(missing))


if __name__ == "__main__":
    main()
