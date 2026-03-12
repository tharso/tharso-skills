# Contributing

Thanks for your interest in contributing to tharso-skills.

## Adding a new skill

1. Create a directory with a kebab-case name (e.g., `my-new-skill/`)
2. Add a `SKILL.md` with YAML frontmatter:

```yaml
---
name: my-new-skill
description: >
  Clear description of what it does and when Claude should use it.
  Include trigger phrases so Claude knows when to activate.
version: 1.0.0
---

# My New Skill

Instructions for Claude go here...
```

3. Keep supporting files organized:
   - `references/` for examples and documentation
   - `scripts/` for helper scripts
4. Test the skill by installing it locally and running a few prompts
5. Open a PR with a short description of what the skill does

## Improving an existing skill

- Bug fixes and clarifications are always welcome
- If changing behavior, explain the reasoning in your PR
- Bump the version in the frontmatter

## Guidelines

- Skills should be self-contained and focused on one task
- Write clear trigger descriptions so Claude activates the skill at the right time
- Include examples when the workflow is non-obvious
- Keep instructions concise — Claude works better with clear, direct prompts
