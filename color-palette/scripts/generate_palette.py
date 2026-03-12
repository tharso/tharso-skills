#!/usr/bin/env python3
"""
Color Palette Generator — OKLCH-based, accessible, multi-format export.

Generates 12-step semantic color scales using the OKLCH perceptually-uniform
color space, with automatic light/dark theme generation and contrast validation.

Usage:
    python generate_palette.py \
        --base-color "#2563EB" \
        --harmony analogous \
        --name "my-palette" \
        --output-dir ./output \
        --formats css,json,tailwind4

Dependencies:
    pip install coloraide --break-system-packages
"""

import argparse
import json
import math
import os
import sys
from dataclasses import dataclass, field
from typing import Optional

try:
    from coloraide import Color
except ImportError:
    print("Installing coloraide...")
    os.system(f"{sys.executable} -m pip install coloraide --break-system-packages -q")
    from coloraide import Color


# ─── Configuration ───────────────────────────────────────────────────────────

# Full 12-step scale (Tier 3)
ALL_STEPS = [
    {"name": "bg",             "light_l": 0.97, "dark_l": 0.13, "chroma_mult": 0.08},
    {"name": "bg-subtle",      "light_l": 0.95, "dark_l": 0.16, "chroma_mult": 0.10},
    {"name": "surface",        "light_l": 0.91, "dark_l": 0.20, "chroma_mult": 0.15},
    {"name": "surface-hover",  "light_l": 0.87, "dark_l": 0.25, "chroma_mult": 0.20},
    {"name": "element-active", "light_l": 0.83, "dark_l": 0.29, "chroma_mult": 0.25},
    {"name": "border-subtle",  "light_l": 0.78, "dark_l": 0.34, "chroma_mult": 0.32},
    {"name": "border",         "light_l": 0.72, "dark_l": 0.42, "chroma_mult": 0.40},
    {"name": "border-strong",  "light_l": 0.63, "dark_l": 0.53, "chroma_mult": 0.55},
    {"name": "solid",          "light_l": 0.55, "dark_l": 0.55, "chroma_mult": 1.00},
    {"name": "solid-hover",    "light_l": 0.48, "dark_l": 0.60, "chroma_mult": 0.90},
    {"name": "text-secondary", "light_l": 0.35, "dark_l": 0.75, "chroma_mult": 0.35},
    {"name": "text",           "light_l": 0.20, "dark_l": 0.92, "chroma_mult": 0.20},
]

# Tier definitions: which step indices to include
TIER_INDICES = {
    1: [0, 2, 6, 8, 11],           # bg, surface, border, solid, text
    2: [0, 1, 2, 3, 6, 8, 9, 11],  # + bg-subtle, surface-hover, solid-hover
    3: list(range(12)),              # all 12
}

def get_tier_steps(tier: int) -> list:
    """Return the step definitions for a given tier."""
    indices = TIER_INDICES.get(tier, TIER_INDICES[1])
    return [ALL_STEPS[i] for i in indices]

def get_tier_l_curves(tier: int):
    """Return (light_L, dark_L, chroma_mult, names) for a tier."""
    steps = get_tier_steps(tier)
    return (
        [s["light_l"] for s in steps],
        [s["dark_l"] for s in steps],
        [s["chroma_mult"] for s in steps],
        [s["name"] for s in steps],
    )

# Dark theme chroma reduction (Helmholtz-Kohlrausch compensation)
DARK_CHROMA_FACTOR = 0.85


# ─── Data Structures ─────────────────────────────────────────────────────────

@dataclass
class ColorStep:
    step: int
    name: str
    oklch: tuple  # (L, C, H)
    hex: str
    rgb: tuple
    in_gamut: bool

@dataclass
class ColorScale:
    hue_name: str
    hue_angle: float
    steps: list  # list of ColorStep

@dataclass
class Palette:
    name: str
    harmony: str
    base_oklch: tuple
    light_scales: list   # list of ColorScale
    dark_scales: list    # list of ColorScale
    neutral_light: Optional[ColorScale] = None
    neutral_dark: Optional[ColorScale] = None
    contrast_report: dict = field(default_factory=dict)


# ─── Core Functions ──────────────────────────────────────────────────────────

def parse_color(color_str: str) -> tuple:
    """Parse any color format to OKLCH (L, C, H) tuple."""
    color_str = color_str.strip()

    try:
        if color_str.startswith("oklch("):
            # Direct OKLCH input
            inner = color_str.replace("oklch(", "").rstrip(")")
            parts = inner.split()
            l_val = float(parts[0].rstrip("%")) / 100 if "%" in parts[0] else float(parts[0])
            c_val = float(parts[1])
            h_val = float(parts[2])
            return (l_val, c_val, h_val)
        else:
            # Use coloraide to parse hex, rgb, hsl, etc.
            c = Color(color_str)
            oklch = c.convert("oklch")
            return (oklch["lightness"], oklch["chroma"], oklch["hue"] or 0)
    except Exception as e:
        print(f"Error parsing color '{color_str}': {e}")
        sys.exit(1)


def oklch_to_hex(l: float, c: float, h: float) -> tuple:
    """Convert OKLCH to hex string and RGB tuple. Returns (hex, rgb, in_gamut)."""
    try:
        color = Color("oklch", [l, c, h])
        in_gamut = color.in_gamut("srgb")
        if not in_gamut:
            color = color.fit("srgb", method="oklch-chroma")
        rgb = color.convert("srgb")
        r, g, b = [max(0, min(255, round(v * 255))) for v in [rgb["red"], rgb["green"], rgb["blue"]]]
        hex_str = f"#{r:02x}{g:02x}{b:02x}"
        return (hex_str, (r, g, b), in_gamut)
    except Exception:
        return ("#000000", (0, 0, 0), False)


def max_chroma_for_hue(l: float, h: float, max_c: float = 0.4) -> float:
    """Find the maximum in-gamut chroma for a given L and H in sRGB."""
    low, high = 0.0, max_c
    for _ in range(32):  # binary search
        mid = (low + high) / 2
        color = Color("oklch", [l, mid, h])
        if color.in_gamut("srgb"):
            low = mid
        else:
            high = mid
    return low


def generate_harmony(base_h: float, harmony_type: str) -> list:
    """Generate harmony hue angles from base hue."""
    harmonies = {
        "analogous":          [base_h, (base_h + 30) % 360, (base_h - 30) % 360],
        "complementary":      [base_h, (base_h + 180) % 360],
        "split":              [base_h, (base_h + 150) % 360, (base_h + 210) % 360],
        "triadic":            [base_h, (base_h + 120) % 360, (base_h + 240) % 360],
        "tetradic":           [base_h, (base_h + 90) % 360, (base_h + 180) % 360, (base_h + 270) % 360],
    }
    return harmonies.get(harmony_type, [base_h])


def generate_scale(hue_name: str, hue_angle: float, l_curve: list,
                   chroma_mults: list, step_names: list,
                   chroma_factor: float = 1.0) -> ColorScale:
    """Generate a scale for a single hue at the given tier."""
    steps = []

    for i, (l_val, c_mult, s_name) in enumerate(zip(l_curve, chroma_mults, step_names)):
        max_c = max_chroma_for_hue(l_val, hue_angle)
        target_c = max_c * c_mult * chroma_factor

        hex_str, rgb, in_gamut = oklch_to_hex(l_val, target_c, hue_angle)

        steps.append(ColorStep(
            step=i + 1,
            name=s_name,
            oklch=(round(l_val, 4), round(target_c, 4), round(hue_angle, 2)),
            hex=hex_str,
            rgb=rgb,
            in_gamut=in_gamut
        ))

    return ColorScale(hue_name=hue_name, hue_angle=hue_angle, steps=steps)


# Neutral chroma per step (all 12); we'll pick by tier index
_NEUTRAL_CHROMA_ALL = [0.005, 0.006, 0.008, 0.009, 0.010, 0.012, 0.013, 0.015, 0.020, 0.018, 0.012, 0.008]

def generate_neutral_scale(base_hue: float, l_curve: list, step_names: list,
                           tier: int, chroma_factor: float = 1.0) -> ColorScale:
    """Generate a tinted neutral scale at the given tier."""
    steps = []
    indices = TIER_INDICES[tier]
    neutral_chromas = [_NEUTRAL_CHROMA_ALL[i] for i in indices]

    for i, (l_val, nc, s_name) in enumerate(zip(l_curve, neutral_chromas, step_names)):
        c_val = nc * chroma_factor
        hex_str, rgb, in_gamut = oklch_to_hex(l_val, c_val, base_hue)

        steps.append(ColorStep(
            step=i + 1,
            name=s_name,
            oklch=(round(l_val, 4), round(c_val, 4), round(base_hue, 2)),
            hex=hex_str,
            rgb=rgb,
            in_gamut=in_gamut
        ))

    return ColorScale(hue_name="neutral", hue_angle=base_hue, steps=steps)


# ─── Contrast Validation ────────────────────────────────────────────────────

def relative_luminance(r: int, g: int, b: int) -> float:
    """Calculate relative luminance per WCAG 2.x."""
    def linearize(v):
        v = v / 255
        return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
    return 0.2126 * linearize(r) + 0.7152 * linearize(g) + 0.0722 * linearize(b)


def wcag_contrast(rgb1: tuple, rgb2: tuple) -> float:
    """Calculate WCAG 2.x contrast ratio."""
    l1 = relative_luminance(*rgb1)
    l2 = relative_luminance(*rgb2)
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


def apca_contrast(text_rgb: tuple, bg_rgb: tuple) -> float:
    """
    Simplified APCA contrast calculation.
    Returns Lc value (positive = dark text on light bg, negative = light text on dark bg).
    """
    def to_y(r, g, b):
        def lin(v):
            v = v / 255
            return v ** 2.4  # simplified sRGB linearization
        return 0.2126729 * lin(r) + 0.7151522 * lin(g) + 0.0721750 * lin(b)

    y_text = to_y(*text_rgb)
    y_bg = to_y(*bg_rgb)

    # SAPC power curve (simplified)
    if y_bg > y_text:  # dark text on light bg
        sapc = (y_bg ** 0.56 - y_text ** 0.57) * 1.14
    else:  # light text on dark bg
        sapc = (y_bg ** 0.65 - y_text ** 0.62) * 1.14

    if abs(sapc) < 0.1:
        return 0
    elif sapc > 0:
        return (sapc - 0.027) * 100
    else:
        return (sapc + 0.027) * 100


def _find_step(scale, name):
    """Find a step by name in a scale, returns None if not present."""
    for s in scale.steps:
        if s.name == name:
            return s
    return None


def validate_contrast(palette: Palette) -> dict:
    """Validate contrast for key text/background combinations."""
    report = {"light": [], "dark": []}

    bg_names = ["bg", "bg-subtle", "surface", "surface-hover", "element", "element-hover"]

    for theme, scales in [("light", palette.light_scales), ("dark", palette.dark_scales)]:
        neutral = palette.neutral_light if theme == "light" else palette.neutral_dark
        if not neutral:
            continue

        for scale in scales:
            text_step = _find_step(scale, "text")
            if not text_step:
                continue

            # Text on background steps from neutral scale
            for bg_name in bg_names:
                bg_step = _find_step(neutral, bg_name)
                if not bg_step:
                    continue
                wcag = wcag_contrast(text_step.rgb, bg_step.rgb)
                lc = apca_contrast(text_step.rgb, bg_step.rgb)

                report[theme].append({
                    "combination": f"{scale.hue_name}-text on neutral-{bg_name}",
                    "text_hex": text_step.hex,
                    "bg_hex": bg_step.hex,
                    "wcag_ratio": round(wcag, 2),
                    "wcag_aa": wcag >= 4.5,
                    "wcag_aaa": wcag >= 7.0,
                    "apca_lc": round(abs(lc), 1),
                    "apca_body": abs(lc) >= 75,
                    "apca_large": abs(lc) >= 60,
                })

            # Solid with white/black text
            solid_step = _find_step(scale, "solid")
            if not solid_step:
                continue

            white_rgb = (255, 255, 255)
            black_rgb = (0, 0, 0)

            for label, txt_rgb in [("white", white_rgb), ("black", black_rgb)]:
                wcag = wcag_contrast(txt_rgb, solid_step.rgb)
                lc = apca_contrast(txt_rgb, solid_step.rgb)
                report[theme].append({
                    "combination": f"{label}-text on {scale.hue_name}-solid",
                    "text_hex": "#ffffff" if label == "white" else "#000000",
                    "bg_hex": solid_step.hex,
                    "wcag_ratio": round(wcag, 2),
                    "wcag_aa": wcag >= 4.5,
                    "wcag_aaa": wcag >= 7.0,
                    "apca_lc": round(abs(lc), 1),
                    "apca_body": abs(lc) >= 75,
                    "apca_large": abs(lc) >= 60,
                })

    return report


# ─── Export Functions ────────────────────────────────────────────────────────

def export_css(palette: Palette, output_dir: str):
    """Export CSS custom properties."""
    lines = ["/* Generated by Color Palette Generator (OKLCH) */", ""]

    # Light theme
    lines.append(":root {")
    for scale in palette.light_scales:
        lines.append(f"  /* {scale.hue_name} (H: {scale.hue_angle}°) */")
        for step in scale.steps:
            l, c, h = step.oklch
            lines.append(f"  --color-{scale.hue_name}-{step.name}: oklch({l} {c} {h});")
        lines.append("")
    if palette.neutral_light:
        lines.append("  /* neutral */")
        for step in palette.neutral_light.steps:
            l, c, h = step.oklch
            lines.append(f"  --color-neutral-{step.name}: oklch({l} {c} {h});")
    lines.append("}")
    lines.append("")

    # Dark theme
    lines.append('[data-theme="dark"] {')
    for scale in palette.dark_scales:
        lines.append(f"  /* {scale.hue_name} (H: {scale.hue_angle}°) */")
        for step in scale.steps:
            l, c, h = step.oklch
            lines.append(f"  --color-{scale.hue_name}-{step.name}: oklch({l} {c} {h});")
        lines.append("")
    if palette.neutral_dark:
        lines.append("  /* neutral */")
        for step in palette.neutral_dark.steps:
            l, c, h = step.oklch
            lines.append(f"  --color-neutral-{step.name}: oklch({l} {c} {h});")
    lines.append("}")

    # Hex fallback
    lines.append("")
    lines.append("/* Hex fallbacks for browsers without OKLCH support */")
    lines.append("@supports not (color: oklch(0 0 0)) {")
    lines.append("  :root {")
    for scale in palette.light_scales:
        for step in scale.steps:
            lines.append(f"    --color-{scale.hue_name}-{step.name}: {step.hex};")
    if palette.neutral_light:
        for step in palette.neutral_light.steps:
            lines.append(f"    --color-neutral-{step.name}: {step.hex};")
    lines.append("  }")
    lines.append('  [data-theme="dark"] {')
    for scale in palette.dark_scales:
        for step in scale.steps:
            lines.append(f"    --color-{scale.hue_name}-{step.name}: {step.hex};")
    if palette.neutral_dark:
        for step in palette.neutral_dark.steps:
            lines.append(f"    --color-neutral-{step.name}: {step.hex};")
    lines.append("  }")
    lines.append("}")

    path = os.path.join(output_dir, f"{palette.name}-tokens.css")
    with open(path, "w") as f:
        f.write("\n".join(lines))
    return path


def export_json(palette: Palette, output_dir: str):
    """Export W3C Design Tokens format."""
    tokens = {"$description": f"Color tokens for {palette.name}", "color": {}}

    for theme_name, scales, neutral in [
        ("light", palette.light_scales, palette.neutral_light),
        ("dark", palette.dark_scales, palette.neutral_dark)
    ]:
        tokens["color"][theme_name] = {}
        for scale in scales:
            tokens["color"][theme_name][scale.hue_name] = {}
            for step in scale.steps:
                l, c, h = step.oklch
                tokens["color"][theme_name][scale.hue_name][step.name] = {
                    "$type": "color",
                    "$value": f"oklch({l} {c} {h})",
                    "hex": step.hex,
                    "rgb": f"rgb({step.rgb[0]}, {step.rgb[1]}, {step.rgb[2]})"
                }
        if neutral:
            tokens["color"][theme_name]["neutral"] = {}
            for step in neutral.steps:
                l, c, h = step.oklch
                tokens["color"][theme_name]["neutral"][step.name] = {
                    "$type": "color",
                    "$value": f"oklch({l} {c} {h})",
                    "hex": step.hex,
                    "rgb": f"rgb({step.rgb[0]}, {step.rgb[1]}, {step.rgb[2]})"
                }

    path = os.path.join(output_dir, f"{palette.name}-tokens.json")
    with open(path, "w") as f:
        json.dump(tokens, f, indent=2)
    return path


def export_tailwind4(palette: Palette, output_dir: str):
    """Export Tailwind v4 CSS theme (uses OKLCH natively)."""
    lines = ["/* Tailwind v4 — OKLCH native */", "@import 'tailwindcss';", "", "@theme {"]

    for scale in palette.light_scales:
        for step in scale.steps:
            l, c, h = step.oklch
            lines.append(f"  --color-{scale.hue_name}-{step.name}: oklch({l} {c} {h});")
    if palette.neutral_light:
        for step in palette.neutral_light.steps:
            l, c, h = step.oklch
            lines.append(f"  --color-neutral-{step.name}: oklch({l} {c} {h});")

    lines.append("}")
    lines.append("")
    lines.append("/* Dark theme overrides */")
    lines.append("@variant dark {")
    lines.append("  @theme {")
    for scale in palette.dark_scales:
        for step in scale.steps:
            l, c, h = step.oklch
            lines.append(f"    --color-{scale.hue_name}-{step.name}: oklch({l} {c} {h});")
    if palette.neutral_dark:
        for step in palette.neutral_dark.steps:
            l, c, h = step.oklch
            lines.append(f"    --color-neutral-{step.name}: oklch({l} {c} {h});")
    lines.append("  }")
    lines.append("}")

    path = os.path.join(output_dir, f"{palette.name}-tailwind4.css")
    with open(path, "w") as f:
        f.write("\n".join(lines))
    return path


def export_tailwind3(palette: Palette, output_dir: str):
    """Export Tailwind v3 config (hex values, no OKLCH support)."""
    config = {"theme": {"extend": {"colors": {}}}}

    for scale in palette.light_scales:
        config["theme"]["extend"]["colors"][scale.hue_name] = {}
        for step in scale.steps:
            config["theme"]["extend"]["colors"][scale.hue_name][step.name] = step.hex

    if palette.neutral_light:
        config["theme"]["extend"]["colors"]["neutral"] = {}
        for step in palette.neutral_light.steps:
            config["theme"]["extend"]["colors"]["neutral"][step.name] = step.hex

    # Add dark variants as separate keys
    config["theme"]["extend"]["colors"]["dark"] = {}
    for scale in palette.dark_scales:
        config["theme"]["extend"]["colors"]["dark"][scale.hue_name] = {}
        for step in scale.steps:
            config["theme"]["extend"]["colors"]["dark"][scale.hue_name][step.name] = step.hex

    path = os.path.join(output_dir, f"{palette.name}-tailwind3.config.json")
    with open(path, "w") as f:
        json.dump(config, f, indent=2)
    return path


def export_scss(palette: Palette, output_dir: str):
    """Export SCSS variables."""
    lines = ["// Generated by Color Palette Generator (OKLCH)", "// Hex values with OKLCH originals in comments", ""]

    lines.append("// Light theme")
    for scale in palette.light_scales:
        for step in scale.steps:
            l, c, h = step.oklch
            lines.append(f"${scale.hue_name}-{step.name}: {step.hex}; // oklch({l} {c} {h})")
    if palette.neutral_light:
        for step in palette.neutral_light.steps:
            l, c, h = step.oklch
            lines.append(f"$neutral-{step.name}: {step.hex}; // oklch({l} {c} {h})")

    lines.append("")
    lines.append("// Dark theme")
    for scale in palette.dark_scales:
        for step in scale.steps:
            l, c, h = step.oklch
            lines.append(f"${scale.hue_name}-dark-{step.name}: {step.hex}; // oklch({l} {c} {h})")
    if palette.neutral_dark:
        for step in palette.neutral_dark.steps:
            l, c, h = step.oklch
            lines.append(f"$neutral-dark-{step.name}: {step.hex}; // oklch({l} {c} {h})")

    path = os.path.join(output_dir, f"{palette.name}-tokens.scss")
    with open(path, "w") as f:
        f.write("\n".join(lines))
    return path


def export_figma(palette: Palette, output_dir: str):
    """Export Figma Tokens Studio format."""
    tokens = {}

    for theme_name, scales, neutral in [
        ("light", palette.light_scales, palette.neutral_light),
        ("dark", palette.dark_scales, palette.neutral_dark)
    ]:
        tokens[theme_name] = {}
        for scale in scales:
            tokens[theme_name][scale.hue_name] = {}
            for step in scale.steps:
                tokens[theme_name][scale.hue_name][step.name] = {
                    "value": step.hex,
                    "type": "color",
                    "description": f"oklch({step.oklch[0]} {step.oklch[1]} {step.oklch[2]})"
                }
        if neutral:
            tokens[theme_name]["neutral"] = {}
            for step in neutral.steps:
                tokens[theme_name]["neutral"][step.name] = {
                    "value": step.hex,
                    "type": "color",
                    "description": f"oklch({step.oklch[0]} {step.oklch[1]} {step.oklch[2]})"
                }

    path = os.path.join(output_dir, f"{palette.name}-figma-tokens.json")
    with open(path, "w") as f:
        json.dump(tokens, f, indent=2)
    return path


# ─── HTML Preview ────────────────────────────────────────────────────────────

def generate_preview(palette: Palette, output_dir: str) -> str:
    """Generate an HTML preview of the palette."""

    def scale_to_html(scale, neutral, theme):
        rows = ""
        for step in scale.steps:
            l, c, h = step.oklch
            text_color = "#000" if l > 0.5 else "#fff"
            gamut_badge = "" if step.in_gamut else ' <span style="color:red;font-size:10px;">⚠ clamped</span>'
            rows += f"""
            <div style="background:{step.hex};color:{text_color};padding:8px 12px;display:grid;grid-template-columns:140px 1fr;align-items:center;gap:8px;font-size:13px;font-family:'SF Mono',SFMono-Regular,Consolas,'Liberation Mono',Menlo,monospace;line-height:1.4;white-space:nowrap;">
                <span style="font-weight:600;overflow:hidden;text-overflow:ellipsis;">{step.step}. {step.name}{gamut_badge}</span>
                <span style="text-align:right;opacity:0.8;">{step.hex} · oklch({l} {c} {h})</span>
            </div>"""
        return rows

    # Build scales HTML
    light_scales_html = ""
    for scale in palette.light_scales:
        light_scales_html += f"""
        <div style="flex:1;min-width:360px;">
            <h3 style="margin:0 0 8px;font-size:14px;font-family:system-ui;">{scale.hue_name} (H: {scale.hue_angle}°)</h3>
            <div style="border-radius:8px;overflow:hidden;border:1px solid #e0e0e0;">
                {scale_to_html(scale, palette.neutral_light, "light")}
            </div>
        </div>"""

    if palette.neutral_light:
        light_scales_html += f"""
        <div style="flex:1;min-width:360px;">
            <h3 style="margin:0 0 8px;font-size:14px;font-family:system-ui;">neutral (tinted)</h3>
            <div style="border-radius:8px;overflow:hidden;border:1px solid #e0e0e0;">
                {scale_to_html(palette.neutral_light, None, "light")}
            </div>
        </div>"""

    dark_scales_html = ""
    for scale in palette.dark_scales:
        dark_scales_html += f"""
        <div style="flex:1;min-width:360px;">
            <h3 style="margin:0 0 8px;font-size:14px;font-family:system-ui;color:#ccc;">{scale.hue_name} (H: {scale.hue_angle}°)</h3>
            <div style="border-radius:8px;overflow:hidden;border:1px solid #333;">
                {scale_to_html(scale, palette.neutral_dark, "dark")}
            </div>
        </div>"""

    if palette.neutral_dark:
        dark_scales_html += f"""
        <div style="flex:1;min-width:360px;">
            <h3 style="margin:0 0 8px;font-size:14px;font-family:system-ui;color:#ccc;">neutral (tinted)</h3>
            <div style="border-radius:8px;overflow:hidden;border:1px solid #333;">
                {scale_to_html(palette.neutral_dark, None, "dark")}
            </div>
        </div>"""

    # Contrast report
    contrast_html = ""
    if palette.contrast_report:
        for theme in ["light", "dark"]:
            if theme in palette.contrast_report:
                contrast_html += f'<h3 style="font-family:system-ui;margin-top:24px;">{theme.title()} theme</h3>'
                contrast_html += '<table style="width:100%;border-collapse:collapse;font-family:monospace;font-size:12px;">'
                contrast_html += '<tr style="background:#f0f0f0;"><th style="padding:6px;text-align:left;">Combination</th><th>WCAG</th><th>AA</th><th>AAA</th><th>APCA Lc</th><th>Body</th><th>Large</th></tr>'
                for item in palette.contrast_report[theme]:
                    aa = "✅" if item["wcag_aa"] else "❌"
                    aaa = "✅" if item["wcag_aaa"] else "❌"
                    body = "✅" if item["apca_body"] else "❌"
                    large = "✅" if item["apca_large"] else "❌"
                    swatch = f'<span style="display:inline-block;width:12px;height:12px;background:{item["text_hex"]};border:1px solid #ccc;vertical-align:middle;"></span> on <span style="display:inline-block;width:12px;height:12px;background:{item["bg_hex"]};border:1px solid #ccc;vertical-align:middle;"></span>'
                    contrast_html += f'<tr style="border-bottom:1px solid #eee;"><td style="padding:6px;">{swatch} {item["combination"]}</td><td style="text-align:center;">{item["wcag_ratio"]}</td><td style="text-align:center;">{aa}</td><td style="text-align:center;">{aaa}</td><td style="text-align:center;">{item["apca_lc"]}</td><td style="text-align:center;">{body}</td><td style="text-align:center;">{large}</td></tr>'
                contrast_html += '</table>'

    # Sample components using name-based lookup
    primary = palette.light_scales[0] if palette.light_scales else None
    neutral = palette.neutral_light

    def _get(scale, name, fallback_hex="#888"):
        """Get hex from a scale step by name."""
        if not scale:
            return fallback_hex
        step = _find_step(scale, name)
        return step.hex if step else fallback_hex

    components_html = ""
    if primary and neutral:
        components_html = f"""
        <div style="margin-top:32px;">
            <h2 style="font-family:system-ui;margin-bottom:16px;">Sample components (light theme)</h2>
            <div style="display:flex;gap:16px;flex-wrap:wrap;">
                <!-- Button -->
                <button style="background:{_get(primary, 'solid')};color:#fff;border:none;padding:10px 24px;border-radius:6px;font-size:14px;cursor:pointer;font-family:system-ui;">Primary button</button>
                <button style="background:{_get(neutral, 'surface')};color:{_get(primary, 'text')};border:1px solid {_get(neutral, 'border')};padding:10px 24px;border-radius:6px;font-size:14px;cursor:pointer;font-family:system-ui;">Secondary button</button>
                <!-- Card -->
                <div style="background:{_get(neutral, 'bg')};border:1px solid {_get(neutral, 'border')};border-radius:8px;padding:16px;max-width:300px;">
                    <div style="font-size:16px;font-weight:600;color:{_get(neutral, 'text')};font-family:system-ui;">Card title</div>
                    <p style="font-size:14px;color:{_get(neutral, 'text-secondary', _get(neutral, 'text'))};margin:8px 0 12px;font-family:system-ui;">Some descriptive text using the secondary text color.</p>
                    <div style="background:{_get(primary, 'surface')};border:1px solid {_get(primary, 'border')};border-radius:4px;padding:8px;font-size:12px;color:{_get(primary, 'text')};font-family:monospace;">Highlighted element</div>
                </div>
                <!-- Badge -->
                <div style="display:flex;gap:8px;align-items:start;">
                    <span style="background:{_get(primary, 'surface')};color:{_get(primary, 'text')};padding:4px 10px;border-radius:12px;font-size:12px;font-family:system-ui;">Default</span>
                    <span style="background:{_get(primary, 'solid')};color:#fff;padding:4px 10px;border-radius:12px;font-size:12px;font-family:system-ui;">Solid</span>
                </div>
            </div>
        </div>"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{palette.name} — Color Palette</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: system-ui, -apple-system, sans-serif; padding: 32px; background: #fafafa; }}
    </style>
</head>
<body>
    <h1 style="font-size:24px;margin-bottom:4px;">{palette.name}</h1>
    <p style="color:#666;margin-bottom:24px;font-size:14px;">Harmony: {palette.harmony} | Base: oklch({palette.base_oklch[0]} {palette.base_oklch[1]} {palette.base_oklch[2]})</p>

    <h2 style="font-size:18px;margin-bottom:12px;">Light theme</h2>
    <div style="display:flex;gap:16px;flex-wrap:wrap;margin-bottom:32px;">
        {light_scales_html}
    </div>

    <h2 style="font-size:18px;margin-bottom:12px;">Dark theme</h2>
    <div style="display:flex;gap:16px;flex-wrap:wrap;margin-bottom:32px;background:#111;padding:20px;border-radius:12px;">
        {dark_scales_html}
    </div>

    {components_html}

    <div style="margin-top:32px;">
        <h2 style="font-size:18px;margin-bottom:12px;">Contrast validation</h2>
        {contrast_html}
    </div>

    <p style="margin-top:32px;color:#999;font-size:12px;">Generated with OKLCH Color Palette Generator</p>
</body>
</html>"""

    path = os.path.join(output_dir, f"{palette.name}-preview.html")
    with open(path, "w") as f:
        f.write(html)
    return path


# ─── Main Pipeline ───────────────────────────────────────────────────────────

def generate_palette(base_color: str, harmony: str, name: str,
                     output_dir: str, formats: list,
                     tier: int = 1,
                     extra_hues: dict = None) -> dict:
    """Main palette generation pipeline."""

    os.makedirs(output_dir, exist_ok=True)

    # Parse base color
    base_l, base_c, base_h = parse_color(base_color)
    print(f"Base color: oklch({base_l:.4f} {base_c:.4f} {base_h:.1f})")
    print(f"Tier: {tier} ({len(TIER_INDICES[tier])} steps per hue)")

    # Get tier curves
    light_l, dark_l, chroma_mults, step_names = get_tier_l_curves(tier)

    # Generate harmony hues
    hue_angles = generate_harmony(base_h, harmony)
    hue_names = _name_hues(hue_angles, name)

    # Add extra hues if specified
    if extra_hues:
        for hue_name, hue_angle in extra_hues.items():
            hue_angles.append(float(hue_angle))
            hue_names.append(hue_name)

    print(f"Harmony ({harmony}): {', '.join(f'{n} ({a:.0f}°)' for n, a in zip(hue_names, hue_angles))}")

    # Generate scales
    light_scales = []
    dark_scales = []

    for hue_name, hue_angle in zip(hue_names, hue_angles):
        light_scales.append(generate_scale(hue_name, hue_angle, light_l, chroma_mults, step_names))
        dark_scales.append(generate_scale(hue_name, hue_angle, dark_l, chroma_mults, step_names, DARK_CHROMA_FACTOR))

    # Generate neutral scales
    neutral_light = generate_neutral_scale(base_h, light_l, step_names, tier)
    neutral_dark = generate_neutral_scale(base_h, dark_l, step_names, tier, DARK_CHROMA_FACTOR)

    # Build palette
    palette = Palette(
        name=name,
        harmony=harmony,
        base_oklch=(round(base_l, 4), round(base_c, 4), round(base_h, 2)),
        light_scales=light_scales,
        dark_scales=dark_scales,
        neutral_light=neutral_light,
        neutral_dark=neutral_dark,
    )

    # Validate contrast
    print("Validating contrast...")
    palette.contrast_report = validate_contrast(palette)

    # Export
    exported = {}

    format_exporters = {
        "css": export_css,
        "json": export_json,
        "tailwind4": export_tailwind4,
        "tailwind3": export_tailwind3,
        "scss": export_scss,
        "figma": export_figma,
    }

    for fmt in formats:
        fmt = fmt.strip().lower()
        if fmt in format_exporters:
            path = format_exporters[fmt](palette, output_dir)
            exported[fmt] = path
            print(f"Exported {fmt}: {path}")

    # Always generate preview
    preview_path = generate_preview(palette, output_dir)
    exported["preview"] = preview_path
    print(f"Preview: {preview_path}")

    # Summary
    steps_per_hue = len(TIER_INDICES[tier])
    total_colors = len(hue_angles) * steps_per_hue * 2 + steps_per_hue * 2  # scales + neutrals, light + dark
    failures = sum(
        1 for theme in palette.contrast_report.values()
        for item in theme if not item["wcag_aa"]
    )

    print(f"\nSummary:")
    print(f"  Colors generated: {total_colors}")
    print(f"  Hues: {len(hue_angles)} + neutral")
    print(f"  Contrast failures (WCAG AA): {failures}")
    print(f"  Formats exported: {', '.join(exported.keys())}")

    return exported


def _name_hues(hue_angles: list, base_name: str) -> list:
    """Generate names for harmony hues."""
    if len(hue_angles) == 1:
        return [base_name]

    suffixes = ["primary", "secondary", "tertiary", "quaternary"]
    return [f"{base_name}-{suffixes[i]}" if i < len(suffixes) else f"{base_name}-{i+1}"
            for i in range(len(hue_angles))]


# ─── CLI ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Generate OKLCH color palettes")
    parser.add_argument("--base-color", required=True, help="Base color (hex, oklch, hsl)")
    parser.add_argument("--harmony", default="analogous",
                       choices=["analogous", "complementary", "split", "triadic", "tetradic"],
                       help="Harmony type")
    parser.add_argument("--name", default="palette", help="Palette name")
    parser.add_argument("--output-dir", default="./palette-output", help="Output directory")
    parser.add_argument("--tier", type=int, default=1, choices=[1, 2, 3],
                       help="Complexity tier: 1=essential (5 steps), 2=interactive (8 steps), 3=system (12 steps)")
    parser.add_argument("--formats", default="css,json,tailwind4",
                       help="Export formats (comma-separated: css,json,tailwind3,tailwind4,scss,figma)")
    parser.add_argument("--extra-hues", default=None,
                       help='Extra named hues as "name:angle,name:angle" (e.g., "success:145,error:25")')

    args = parser.parse_args()

    extra = None
    if args.extra_hues:
        extra = {}
        for pair in args.extra_hues.split(","):
            n, a = pair.split(":")
            extra[n.strip()] = float(a.strip())

    generate_palette(
        base_color=args.base_color,
        harmony=args.harmony,
        name=args.name,
        output_dir=args.output_dir,
        formats=args.formats.split(","),
        tier=args.tier,
        extra_hues=extra,
    )


if __name__ == "__main__":
    main()
