# tharso-skills

A collection of practical skills for [Claude Code](https://docs.anthropic.com/en/docs/claude-code) — the AI coding agent by Anthropic.

Each skill is a self-contained set of instructions that teaches Claude how to perform a specific task with depth and precision.

## Skills

| Skill | What it does | Language |
|-------|-------------|----------|
| [**design-dna**](./design-dna/) | Extracts the visual DNA from any website — typography, colors, spacing, depth, motion — and saves it as a structured design reference | EN |
| [**feature-forge**](./feature-forge/) | Thinking partner for planning features before creating GitHub issues. Goes from vague idea to structured issue | PT-BR |
| [**pdf-like-a-boss**](./pdf-like-a-boss/) | Professional PDF generation pipeline via HTML+CSS with validation at every step | EN |
| [**smry-reader**](./smry-reader/) | Clean web page reader via smry.ai proxy. Strips ads, popups, and visual noise | PT-BR |
| [**youtube-extractor**](./youtube-extractor/) | Extracts metadata and full transcript from YouTube videos into structured Markdown | PT-BR |

## Installation

### Install a single skill

```bash
claude skills add /path/to/tharso-skills/design-dna
```

### Install from GitHub (clone first)

```bash
git clone https://github.com/tharso/tharso-skills.git
claude skills add ./tharso-skills/design-dna
```

### Manual installation

Copy the skill folder into your project's `.claude/skills/` directory:

```bash
cp -r design-dna /your-project/.claude/skills/
```

## Skill format

Each skill follows the [Claude Code skills spec](https://docs.anthropic.com/en/docs/claude-code/skills):

```
skill-name/
├── SKILL.md          # Instructions + YAML frontmatter (required)
├── references/       # Supporting docs, examples (optional)
└── scripts/          # Helper scripts (optional)
```

The `SKILL.md` frontmatter includes:

```yaml
---
name: skill-name
description: What it does and when to trigger it
version: 1.0.0
---
```

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines on adding or improving skills.

## License

[MIT](./LICENSE)
