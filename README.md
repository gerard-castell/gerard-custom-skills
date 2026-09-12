# gerard-custom-skills

A collection of reusable skills — each one a self-contained folder of scripts and reference docs
that solves one concrete problem. They don't depend on any particular agent or framework: read the
skill's docs, run its scripts from a terminal, get the same output whether or not an agent is
involved. Claude Code is one consumer, wired up as a plugin marketplace; it is not the intended
reader.

## Use it plainly (no agent required)

Every skill is just a folder. Clone the repo, copy the folder wherever you're working, install its
dependencies, and run its scripts directly:

```bash
git clone https://github.com/gerard-castell/gerard-custom-skills.git
cp -r gerard-custom-skills/plugins/png-to-animated-svg/skills/png-to-animated-svg ./my-project/
cd my-project/png-to-animated-svg
python3 -m venv .venv && .venv/bin/pip install vtracer pillow
.venv/bin/python scripts/grid.py character.png -o grid.png
```

Each skill's `SKILL.md` is written to be read as plain documentation — the pipeline, the setup, the
commands — with any agent-specific wiring called out in its own section at the bottom.

## Use it with an agent

Any agent that can read a folder of docs and run shell commands can follow a skill the same way a
human would — point it at the skill's folder and its `SKILL.md`. Some agent runtimes have their own
convention for this (for example, an `AGENTS.md` entry point); see [AGENTS.md](AGENTS.md).

### Claude Code

Claude Code discovers skills through a plugin marketplace:

```
/plugin marketplace add gerard-castell/gerard-custom-skills
/plugin install png-to-animated-svg@gerard-custom-skills
```

## Skills

### [png-to-animated-svg](plugins/png-to-animated-svg/skills/png-to-animated-svg/)

Turns a flat PNG character into a rigged SVG with named, independently animatable
parts, plus a GSAP animation to drive it.

## Licence

MIT — see [LICENSE](LICENSE).
