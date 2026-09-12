# AGENTS.md

Entry point for coding agents (Codex, Cursor, Aider, or anything else that reads this file by
convention) landing in this repo.

Each skill lives at `plugins/<skill>/skills/<skill>/` and is self-contained: a `SKILL.md`
describing what it does and how to run it, `scripts/` to run directly from a shell, and
`reference/` docs for the parts that need judgment rather than a flag.

To use a skill:

1. Read its `SKILL.md` — it doubles as plain documentation, no agent required to make sense of it.
2. Install the few Python dependencies it names.
3. Run its scripts from the terminal, following the pipeline the `SKILL.md` lays out.

If `SKILL.md` has a section marked for agent runtimes, that's the only agent-specific wiring —
everything above it applies equally to a human running the same commands by hand.

Claude Code additionally discovers these skills as a plugin marketplace; see the root
[README](README.md) for that path. It is one consumer among several, not a requirement.
