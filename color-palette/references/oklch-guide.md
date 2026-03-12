# OKLCH Color Theory Reference

## Table of contents

1. What OKLCH is and why it matters
2. The three axes: L, C, H
3. Gamut boundaries and sRGB constraints
4. Lightness curves for palette scales
5. Chroma behavior across hues
6. Converting between color spaces
7. Contrast algorithms: WCAG vs APCA
8. Common pitfalls

## 1. What OKLCH is and why it matters

OKLCH is a cylindrical representation of the Oklab color space, created by Bjorn Ottosson in 2020. "OK" stands for the optimization method used to create it. It solves the core problem of older color spaces: perceptual non-uniformity.

In HSL, the same numeric lightness produces different perceived brightness depending on the hue. Yellow at hsl(60, 100%, 50%) looks bright; blue at hsl(240, 100%, 50%) looks dark. This makes systematic palette generation unreliable because you can't trust the numbers.

OKLCH fixes this. Equal L values produce equal perceived lightness regardless of hue. Equal C values produce equal perceived colorfulness. Equal H values produce the same perceived hue at different lightness levels (no hue shift as you darken or lighten).

CSS syntax: `oklch(L C H)` where L is 0-1 (or 0%-100%), C is 0-0.4 (roughly), H is 0-360 degrees.

## 2. The three axes

### L (Lightness): 0 to 1
- 0 = pure black
- 1 = pure white
- 0.5 = mid-gray (and it actually LOOKS like mid-gray, unlike HSL)
- Perceptually linear: the step from 0.3 to 0.4 looks the same as 0.7 to 0.8

### C (Chroma): 0 to ~0.37
- 0 = no color (gray)
- Higher = more colorful/saturated
- Maximum depends on the specific L and H combination (the gamut is not a simple shape)
- sRGB gamut caps chroma much lower than the theoretical maximum
- Typical usable range in sRGB: 0 to ~0.25 depending on hue

### H (Hue): 0 to 360 degrees
- 0/360 = pinkish-red
- 30 = orange
- 90 = yellow-green
- 145 = green
- 180 = cyan
- 240 = blue
- 270 = purple/violet
- 330 = magenta/pink

Note: OKLCH hue values don't perfectly match HSL hue values. Red in HSL is 0°, in OKLCH it's closer to 25-30°. Always work in OKLCH hue space when using this skill.

## 3. Gamut boundaries and sRGB constraints

The visible gamut of OKLCH is much larger than what sRGB displays can show. When you specify an OKLCH color with high chroma, it may fall outside the sRGB gamut. Browsers handle this by clamping to the nearest in-gamut color, but the result may not be what you intended.

Key facts:
- Every hue has a different maximum chroma at each lightness level
- Yellow-green hues can achieve higher chroma than blue-purple hues in sRGB
- At very high or very low lightness, all hues have reduced maximum chroma (approaching gray at the extremes)
- P3 displays have a larger gamut (about 25% more colors than sRGB)

Strategy for this skill:
- Always generate colors within sRGB gamut for maximum compatibility
- Optionally generate P3 variants for wider-gamut displays using `@media (color-gamut: p3)`
- When clamping, reduce chroma while keeping L and H constant (never shift hue to fit gamut)

## 4. Lightness curves for palette scales

The 12-step scale uses a non-linear lightness distribution. Steps are not evenly spaced because:
- Background steps (1-2) cluster near white (light) or black (dark) for minimal visual interference
- Element steps (3-5) need enough contrast with backgrounds to be visible but not distracting
- Solid steps (9-10) sit at the perceptual "sweet spot" where colors look most vivid
- Text steps (11-12) need maximum contrast with all lighter steps

Light theme curve (approximate L values):
```
Step:  1     2     3     4     5     6     7     8     9     10    11    12
L:     0.98  0.95  0.91  0.87  0.83  0.78  0.72  0.63  0.55  0.48  0.35  0.20
```

Dark theme curve (inverted with adjustments):
```
Step:  1     2     3     4     5     6     7     8     9     10    11    12
L:     0.13  0.16  0.20  0.25  0.29  0.34  0.42  0.53  0.55  0.60  0.75  0.92
```

Note: Steps 9-10 share similar L values between themes. This is intentional — the "brand color" should look consistent whether in light or dark mode.

## 5. Chroma behavior across hues

Not all hues can reach the same chroma at a given lightness. The OKLCH gamut has an irregular shape.

Approximate maximum sRGB chroma by hue at L=0.55:
- Red (H≈25): C ≈ 0.22
- Orange (H≈55): C ≈ 0.18
- Yellow (H≈95): C ≈ 0.15
- Green (H≈145): C ≈ 0.17
- Cyan (H≈190): C ≈ 0.12
- Blue (H≈260): C ≈ 0.18
- Purple (H≈300): C ≈ 0.20
- Pink (H≈350): C ≈ 0.22

This means: when generating a multi-hue palette, you can't use the same chroma value for all hues and expect equal perceived saturation. The script handles this by finding the maximum in-gamut chroma for each hue at each lightness level and scaling proportionally.

## 6. Converting between color spaces

The script handles conversions, but for reference:

- **Hex → OKLCH**: Via sRGB → linear RGB → Oklab → OKLCH (cylindrical conversion)
- **HSL → OKLCH**: Via sRGB → same path as hex
- **OKLCH → Hex**: OKLCH → Oklab → linear RGB → sRGB → hex (with gamut clamping if needed)

The `coloraide` Python library handles all these conversions correctly, including gamut mapping.

## 7. Contrast algorithms

### WCAG 2.x
Uses relative luminance ratio. Simple formula:
- Ratio = (L1 + 0.05) / (L2 + 0.05) where L1 > L2
- AA normal text: 4.5:1
- AA large text: 3:1
- AAA normal text: 7:1
- AAA large text: 4.5:1

Known weakness: doesn't account for polarity (light-on-dark vs dark-on-light) or spatial frequency.

### APCA (Accessible Perceptual Contrast Algorithm)
More accurate perceptual contrast. Uses different formulas for light-on-dark vs dark-on-light (because human vision is asymmetric). Returns a contrast value Lc (Lightness Contrast):
- Body text (16px): Lc 75+
- Large text (24px+): Lc 60+
- Headlines: Lc 45+
- Non-text elements: Lc 30+

The script validates against both standards and flags failures.

## 8. Common pitfalls

**"My yellow looks washed out compared to my blue"**
This happens when you use the same chroma for both. Yellow reaches its max chroma at higher lightness, blue at lower. Adjust chroma per hue to maintain equal perceived vividness.

**"The dark theme looks neon"**
Keeping the same chroma in dark mode makes colors appear more vivid (Helmholtz-Kohlrausch effect). Reduce chroma by 10-20% in dark theme to compensate.

**"Steps 6-8 look too similar"**
The lightness curve in the border range is intentionally compressed. If more distinction is needed, increase chroma differentiation between these steps rather than lightness.

**"The palette feels cold/warm despite neutral hues"**
Likely caused by chroma in the neutral scale. Even C=0.01 tints grays visibly. Check the neutral/gray scale's chroma values and adjust or remove the tint.
