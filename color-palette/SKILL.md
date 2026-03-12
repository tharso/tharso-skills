---
name: color-palette
description: Generate professional color palettes using the OKLCH perceptually-uniform color space. Guides the user through visual exploration before producing technical output. Creates complete, accessible palettes with semantic scales, automatic light/dark themes, APCA + WCAG contrast validation, and multi-format export (CSS custom properties, JSON tokens, Tailwind v3/v4, SCSS, Figma Tokens Studio). Use this skill whenever the user mentions color palette, color scheme, color system, color tokens, design tokens for colors, brand colors, theme colors, choosing colors for a project, or needs to generate harmonious color combinations for any interface. Also triggers on "paleta de cores", "esquema de cores", "cores do projeto", "gerar paleta", or when the user has a base color and needs to derive a full system from it. Use proactively when creating any design system, landing page, dashboard, or interface where color decisions are needed, even if the user doesn't explicitly ask for a "palette".
version: 1.0.0
---

# Color Palette Generator

Generate accessible, perceptually-uniform color palettes using OKLCH. The skill has two distinct phases: first it helps the user *see and choose* colors through proportional color boards, then it produces the technical documentation that other tools (and humans) can consume.

## Philosophy

Nobody chooses colors by staring at 168 rectangles in a grid. Colors only make sense in context: a blue that feels corporate on a fintech dashboard might feel serene on a meditation app. The same hex value tells two different stories depending on what surrounds it.

This skill treats palette creation as a two-act process. Act 1 is human: explore, compare, feel, decide. Act 2 is machine: generate the precise, validated, multi-format token system that encodes those decisions for implementation. The technical engine (OKLCH, gamut clamping, contrast validation) runs underneath both acts, but Act 1 speaks the language of the person deciding, and Act 2 speaks the language of the system implementing.

The foundation is OKLCH (Oklab Lightness, Chroma, Hue), a perceptually-uniform color space where equal numeric steps produce equal perceived differences. Unlike HSL, where a yellow at L=50% looks bright and a blue at L=50% looks dark, OKLCH delivers consistent perceived lightness across all hues.

## The Four Phases

### Phase 1 — Context (conversation)

Understand what the colors need to communicate. The depth adapts to how much the user already knows:

**Mode A — Exploration** (no color defined yet): Ask about the project, the audience, the mood. What feeling should the colors carry? Any existing brand elements? References they like or dislike? The goal is to extract enough signal to propose meaningfully different directions.

**Mode B — Derivation** (base color provided): The user gives a hex, RGB, HSL, or OKLCH value. Convert to OKLCH, describe the color's character (warm/cool, saturated/muted). Ask only what's needed: harmony preference, context of use, any existing secondary colors.

**Mode C — Extraction** (reference URL or image): Extract colors from a reference, present findings in OKLCH, ask what to keep and what to change. If the design-dna skill is available, use it.

Keep this phase tight. Don't interrogate; converse. Two or three focused questions are enough for most cases.

### Phase 2 — Visual Proposals (the part that matters for humans)

This is where decisions happen. Generate 2-4 distinct color directions, each rendered as **proportional color boards** where block size reflects visual hierarchy.

The key insight: don't show raw color scales. Show colors at the proportion they'll actually occupy in the design. The dominant color gets the biggest block, secondary gets medium, supporting tones fill the rest. The user should be able to glance at each option and immediately feel the difference. Hex values appear on hover, rendered in the palette's own text color as a live legibility test.

**How to generate proposals:**

```bash
pip install coloraide --break-system-packages -q
python <skill-path>/scripts/generate_proposals.py \
  --base-hue <hue-angle-or-hex> \
  --name "<project-name>" \
  --output-dir "<output-directory>" \
  --num-proposals 3
```

The script generates a single self-contained HTML file with all proposals as **proportional color boards** (large blocks of color, like ColorHunt or Coolors). No fake interfaces or generic mockups. The user sees the actual colors at scale, with the dominant color taking the biggest block, so the visual weight is immediately obvious.

Each proposal shows:

- Proportional color blocks (primary largest, then secondary, supporting tones, neutrals)
- Light and dark theme toggle
- Harmony type and a brief rationale
- Hex values on hover (bold, in the palette's own text color — a live legibility test)

Each proposal uses a genuinely different approach (different harmony, different base hue shift, different chroma strategy), not safe variations of the same idea.

**Present the proposals HTML to the user.** Walk them through each option briefly. Then ask: "Which direction resonates? Or should I combine elements from different options?"

### Phase 3 — Refinement (iteration)

The user picks a direction (or asks to blend elements from multiple proposals). Now refine:

- "Pull the blue more toward cyan" → shift hue
- "The background feels too cold" → warm up neutral tint
- "The accent is too loud" → reduce chroma
- "Can I see it darker?" → regenerate dark theme proposal

For each adjustment, regenerate only the relevant proposal (not all of them). Use the same `generate_proposals.py` script with `--base-hue` set to the refined value. Quick cycles: change → see → decide.

When the user says something equivalent to "this is it", move to Phase 4.

### Phase 4 — Technical Documentation (the machine-readable output)

Now generate the complete token system using the finalized colors:

```bash
python <skill-path>/scripts/generate_palette.py \
  --base-color "<chosen oklch or hex>" \
  --harmony "<chosen harmony>" \
  --tier <1|2|3> \
  --name "<palette-name>" \
  --output-dir "<output-directory>" \
  --formats "css,json,tailwind3,tailwind4,scss,figma"
```

This produces the full technical package: semantic scales, light/dark tokens, contrast validation, multi-format export. This is the artifact that other agents and developers consume.

**Tier selection** happens here, informed by the conversation:

- **Tier 1 — Essential (5 steps):** Landing pages, pitch decks, marketing materials, simple sites. Five colors per hue: bg, surface, border, solid, text. Covers 80% of cases.
- **Tier 2 — Interactive (8 steps):** Web apps with hover/active states, dashboards, forms. Adds bg-subtle, surface-hover, solid-hover.
- **Tier 3 — System (12 steps):** Design systems, component libraries, complex products. Full Radix-style scale. Only recommend when genuinely needed.

Default to Tier 1. It's easier to say "we can add more detail" than to overwhelm someone with 72 colors they don't need.

If the user asks for semantic colors (success, warning, error, info), add them with `--extra-hues`:
```bash
--extra-hues "success:145,warning:85,error:25,info:240"
```

## Palette Architecture (reference for the engine)

### Complexity tiers

**Tier 1 — Essential (5 steps)**

| Step | Name | Purpose | L (light) | L (dark) |
|------|------|---------|-----------|----------|
| 1 | `bg` | Page/section background | 0.97 | 0.13 |
| 3 | `surface` | Cards, wells, elevated areas | 0.91 | 0.20 |
| 7 | `border` | Borders, dividers, focus rings | 0.72 | 0.42 |
| 9 | `solid` | Buttons, badges, primary actions | 0.55 | 0.55 |
| 12 | `text` | Primary text | 0.20 | 0.92 |

**Tier 2 — Interactive (8 steps)**

| Step | Name | Purpose | L (light) | L (dark) |
|------|------|---------|-----------|----------|
| 1 | `bg` | Page background | 0.97 | 0.13 |
| 2 | `bg-subtle` | Subtle background, striped rows | 0.95 | 0.16 |
| 3 | `surface` | Component background | 0.91 | 0.20 |
| 4 | `surface-hover` | Hover state for surfaces | 0.87 | 0.25 |
| 7 | `border` | Default borders | 0.72 | 0.42 |
| 9 | `solid` | Solid backgrounds (buttons) | 0.55 | 0.55 |
| 10 | `solid-hover` | Hover for solid elements | 0.48 | 0.60 |
| 12 | `text` | Primary text | 0.20 | 0.92 |

**Tier 3 — System (12 steps):** Full scale from bg through text with all intermediate states. See `references/oklch-guide.md` for the complete table.

### Chroma strategy

- **Backgrounds**: Very low chroma (0.01-0.03). Just enough tint to feel colored.
- **Surfaces**: Low-medium (0.03-0.06). Visible color without overwhelming.
- **Borders**: Medium (0.05-0.10). Chromatic accent defining structure.
- **Solids**: Maximum viable chroma within sRGB gamut. Where the color lives most vividly.
- **Text**: Medium-low (0.03-0.08). Enough identity, low enough for reading.

### Harmony types

- **Analogous**: Base ± 30°. Calm, cohesive.
- **Complementary**: Base + 180°. High contrast, energetic.
- **Split-complementary**: Base + 150° / + 210°. Contrast with nuance.
- **Triadic**: Base + 120° / + 240°. Balanced, vibrant.
- **Tetradic**: Base + 90° / + 180° / + 270°. Rich, needs careful chroma management.

### Dark theme generation

```
dark_L = 1.0 - light_L  (with adjustments)
dark_C = light_C * 0.85  (Helmholtz-Kohlrausch compensation)
dark_H = light_H          (hue stays constant)
```

### Contrast validation

Every text/background combination is validated against WCAG 2.x (AA: 4.5:1, AAA: 7:1) and APCA (Lc 60+ body, Lc 45+ large, Lc 30+ non-text). A palette that fails accessibility is a broken palette.

## Output formats

Phase 4 generates these formats:

- **CSS Custom Properties**: oklch() values with hex fallbacks via `@supports`
- **JSON Design Tokens**: W3C Design Tokens Community Group format
- **Tailwind v4**: OKLCH native in `@theme` block
- **Tailwind v3**: Hex fallbacks in config JSON
- **SCSS Variables**: Hex with OKLCH in comments
- **Figma Tokens Studio**: JSON compatible with the Figma plugin

## Integration with other skills

- **design-proposition**: Call color-palette first to establish the color system, then use design-proposition with those tokens.
- **design-dna**: Use design-dna to extract colors from a reference, then feed into Phase 1 Mode C.
- **theme-factory**: Tokens from Phase 4 can be consumed by theme-factory.

## Important notes

- Always go through Phase 2 before Phase 4. The technical output is the last step, not the first.
- When the user says "I want it more vibrant/muted/warm/cool", adjust chroma and hue, not lightness. Lightness controls the semantic function of each step.
- If a color goes out of sRGB gamut, clamp to the boundary rather than shifting hue. Explain this when it happens.
- When upgrading tiers, existing steps keep their values. Tier 2 adds to Tier 1, Tier 3 adds to Tier 2.
- For gray/neutral scales, use the base hue at very low chroma (0.005-0.015) for tinted neutrals.

## Reference materials

Read `references/oklch-guide.md` for deeper OKLCH theory, gamut mapping details, and scale generation mathematics.
