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

### [png-to-animated-svg](plugins/png-to-animated-svg/skills/png-to-animated-svg/)

Turns a flat PNG character into a rigged SVG with named, independently animatable
parts, plus a GSAP animation to drive it.

## Licence

MIT — see [LICENSE](LICENSE).
