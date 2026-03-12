#!/usr/bin/env python3
"""
Color Palette Proposals Generator — Visual color boards for human decision-making.

Generates 2-5 distinct color directions as proportional color boards
(inspired by color palette sites like Coolors/ColorHunt). Each board
shows the palette colors as large blocks with proportional sizing
reflecting visual hierarchy: primary gets the biggest block, secondary
gets a medium block, supporting colors fill the rest.

Usage:
    python generate_proposals.py \
        --base-hue 250 \
        --name "Silêncio" \
        --output-dir ./proposals \
        --num-proposals 3

    # Can also accept hex/oklch:
    --base-hue "#2563EB"
    --base-hue "oklch(0.55 0.15 250)"

Dependencies:
    pip install coloraide --break-system-packages
"""

import argparse
import json
import math
import os
import sys
from dataclasses import dataclass

try:
    from coloraide import Color
except ImportError:
    os.system(f"{sys.executable} -m pip install coloraide --break-system-packages -q")
    from coloraide import Color


# ─── Color Engine ────────────────────────────────────────────────────────────

def parse_to_hue(color_str: str) -> float:
    """Parse any color input to an OKLCH hue angle."""
    color_str = color_str.strip()
    try:
        return float(color_str) % 360
    except ValueError:
        pass
    try:
        if color_str.startswith("oklch("):
            inner = color_str.replace("oklch(", "").rstrip(")")
            parts = inner.split()
            return float(parts[2]) % 360
        else:
            c = Color(color_str)
            oklch = c.convert("oklch")
            return (oklch["hue"] or 0) % 360
    except Exception as e:
        print(f"Error parsing color '{color_str}': {e}")
        sys.exit(1)


def oklch_to_hex(l: float, c: float, h: float) -> str:
    """Convert OKLCH to hex, clamping to sRGB gamut."""
    try:
        color = Color("oklch", [l, c, h])
        if not color.in_gamut("srgb"):
            color = color.fit("srgb", method="oklch-chroma")
        rgb = color.convert("srgb")
        r, g, b = [max(0, min(255, round(v * 255))) for v in [rgb["red"], rgb["green"], rgb["blue"]]]
        return f"#{r:02x}{g:02x}{b:02x}"
    except Exception:
        return "#888888"


def max_chroma_for_hue(l: float, h: float, max_c: float = 0.4) -> float:
    """Binary search for max in-gamut chroma at given L and H."""
    low, high = 0.0, max_c
    for _ in range(32):
        mid = (low + high) / 2
        color = Color("oklch", [l, mid, h])
        if color.in_gamut("srgb"):
            low = mid
        else:
            high = mid
    return low


def text_color_on(hex_bg: str) -> str:
    """Return black or white text depending on background lightness."""
    try:
        c = Color(hex_bg).convert("oklch")
        return "#1a1a2e" if c["lightness"] > 0.6 else "#ffffff"
    except Exception:
        return "#ffffff"


# ─── Proposal Color Sets ────────────────────────────────────────────────────

@dataclass
class ProposalColors:
    """Colors for a single proposal board."""
    name: str
    harmony: str
    rationale: str
    base_hue: float
    # The board colors (largest block to smallest)
    primary: str           # dominant color
    primary_light: str     # lighter variant
    secondary: str         # accent
    neutral_warm: str      # tinted neutral
    neutral_cool: str      # supporting neutral
    # Dark variant board
    dark_primary: str
    dark_primary_light: str
    dark_secondary: str
    dark_neutral_warm: str
    dark_neutral_cool: str
    # OKLCH reference strings
    oklch_primary: str
    oklch_secondary: str


def generate_proposal_colors(base_hue: float, harmony: str, rationale: str,
                              name: str, chroma_boost: float = 1.0) -> ProposalColors:
    """Generate a color set for a single proposal."""
    h1 = base_hue

    # Determine secondary hue based on harmony
    harmony_offsets = {
        "analogous": 30,
        "complementary": 180,
        "split-complementary": 150,
        "triadic": 120,
        "warm-shift": 25,
        "cool-shift": 195,
        "monochromatic": 0,
    }
    offset = harmony_offsets.get(harmony, 120)
    h2 = (base_hue + offset) % 360

    if harmony == "warm-shift":
        h1 = (base_hue - 15) % 360
    elif harmony == "cool-shift":
        h1 = (base_hue + 15) % 360

    # Primary at peak saturation
    max_c1 = max_chroma_for_hue(0.55, h1)
    c1 = min(max_c1 * 0.85 * chroma_boost, max_c1)

    # Secondary
    max_c2 = max_chroma_for_hue(0.55, h2)
    c2 = min(max_c2 * 0.7 * chroma_boost, max_c2)

    # For monochromatic, secondary differs in lightness, not hue
    if harmony == "monochromatic":
        secondary_hex = oklch_to_hex(0.72, c1 * 0.5, h1)
        dark_secondary_hex = oklch_to_hex(0.35, c1 * 0.4, h1)
    else:
        secondary_hex = oklch_to_hex(0.55, c2, h2)
        dark_secondary_hex = oklch_to_hex(0.62, c2 * 0.85, h2)

    return ProposalColors(
        name=name,
        harmony=harmony,
        rationale=rationale,
        base_hue=h1,
        # Light board
        primary=oklch_to_hex(0.55, c1, h1),
        primary_light=oklch_to_hex(0.78, c1 * 0.4, h1),
        secondary=secondary_hex,
        neutral_warm=oklch_to_hex(0.92, 0.015, h1),
        neutral_cool=oklch_to_hex(0.85, 0.02, (h1 + 180) % 360),
        # Dark board
        dark_primary=oklch_to_hex(0.62, c1 * 0.85, h1),
        dark_primary_light=oklch_to_hex(0.30, c1 * 0.3, h1),
        dark_secondary=dark_secondary_hex,
        dark_neutral_warm=oklch_to_hex(0.18, 0.012, h1),
        dark_neutral_cool=oklch_to_hex(0.22, 0.015, (h1 + 180) % 360),
        # Reference
        oklch_primary=f"oklch(0.55 {c1:.3f} {h1:.0f})",
        oklch_secondary=f"oklch(0.55 {c2:.3f} {h2:.0f})",
    )


def create_proposals(base_hue: float, num: int = 3) -> list:
    """Create N distinct color proposals from a base hue."""
    strategies = [
        {
            "harmony": "analogous",
            "hue_shift": 0,
            "rationale": (
                u"Harmonia an\u00e1loga: cores vizinhas no c\u00edrculo crom\u00e1tico "
                u"(\u00b130\u00b0). Produz coes\u00e3o visual natural porque o olho humano "
                u"percebe transi\u00e7\u00f5es suaves de matiz como pertencentes a um mesmo "
                u"sistema. \u00c9 a escolha mais segura para interfaces que precisam "
                u"de unidade sem monotonia. Funciona especialmente bem em landing "
                u"pages e apps onde a hierarquia vem mais da satura\u00e7\u00e3o que do contraste."
            ),
            "chroma": 1.0,
        },
        {
            "harmony": "complementary",
            "hue_shift": 0,
            "rationale": (
                u"Harmonia complementar: a cor principal e seu oposto crom\u00e1tico "
                u"(+180\u00b0). Gera o m\u00e1ximo contraste poss\u00edvel entre duas matizes, "
                u"o que a torna ideal para call-to-actions, alertas e pontos focais "
                u"que precisam saltar da p\u00e1gina. O risco \u00e9 a tens\u00e3o visual em excesso. "
                u"Aqui, a chave \u00e9 usar o complementar com modera\u00e7\u00e3o: reserv\u00e1-lo para "
                u"destaques (bot\u00f5es, badges, links ativos) e deixar o neutro dominar "
                u"a \u00e1rea total."
            ),
            "chroma": 0.9,
        },
        {
            "harmony": "split-complementary",
            "hue_shift": 0,
            "rationale": (
                u"Split-complementar: em vez do oposto direto, usa os dois vizinhos "
                u"do complementar (+150\u00b0 e +210\u00b0). Mant\u00e9m o contraste alto, mas "
                u"distribui a tens\u00e3o em duas dire\u00e7\u00f5es, o que suaviza o resultado. "
                u"Na pr\u00e1tica, d\u00e1 mais versatilidade que o complementar puro: voc\u00ea "
                u"ganha duas cores de acento que podem servir fun\u00e7\u00f5es diferentes "
                u"(ex: uma para sucesso, outra para aten\u00e7\u00e3o) sem parecer arbitr\u00e1rio."
            ),
            "chroma": 0.95,
        },
        {
            "harmony": "triadic",
            "hue_shift": 0,
            "rationale": (
                u"Tri\u00e1dica: tr\u00eas cores equidistantes no c\u00edrculo (+120\u00b0 e +240\u00b0). "
                u"\u00c9 a harmonia mais vibrante e diversa. Cada cor carrega personalidade "
                u"pr\u00f3pria, e juntas criam riqueza visual sem competi\u00e7\u00e3o. O segredo "
                u"\u00e9 reduzir a satura\u00e7\u00e3o das cores secund\u00e1rias para que a prim\u00e1ria "
                u"mantenha o protagonismo. Muito usada em dashboards e sistemas que "
                u"precisam de m\u00faltiplas categorias visuais distintas."
            ),
            "chroma": 0.85,
        },
        {
            "harmony": "warm-shift",
            "hue_shift": -15,
            "rationale": (
                u"Varia\u00e7\u00e3o quente: desloca a base 15\u00b0 em dire\u00e7\u00e3o ao vermelho/laranja "
                u"e aplica harmonia an\u00e1loga. A mesma estrutura coesa, mas com um toque "
                u"mais humano e acolhedor. Cores quentes ativam associa\u00e7\u00f5es com "
                u"proximidade, energia e urg\u00eancia (moderada). Boa op\u00e7\u00e3o quando o "
                u"projeto precisa parecer acess\u00edvel e convidativo sem perder a "
                u"personalidade da matiz original."
            ),
            "chroma": 1.0,
        },
        {
            "harmony": "cool-shift",
            "hue_shift": 15,
            "rationale": (
                u"Varia\u00e7\u00e3o fria: desloca a base 15\u00b0 em dire\u00e7\u00e3o ao azul/ciano "
                u"e aplica harmonia an\u00e1loga. O resultado \u00e9 mais t\u00e9cnico, sereno e "
                u"profissional. Cores frias recuam visualmente, o que cria sensa\u00e7\u00e3o "
                u"de espa\u00e7o e clareza. Ideal para produtos que querem transmitir "
                u"confian\u00e7a, estabilidade e compet\u00eancia (fintech, sa\u00fade, analytics)."
            ),
            "chroma": 1.0,
        },
        {
            "harmony": "monochromatic",
            "hue_shift": 0,
            "rationale": (
                u"Monocrom\u00e1tica: uma \u00fanica matiz explorada em diferentes n\u00edveis "
                u"de luminosidade e satura\u00e7\u00e3o. A mais elegante e a mais segura. "
                u"Imposs\u00edvel criar conflito crom\u00e1tico quando s\u00f3 existe uma cor. "
                u"O desafio \u00e9 evitar que fique mon\u00f3tono: por isso, o neutro aquecido "
                u"ganha import\u00e2ncia extra, e a hierarquia vem inteiramente do "
                u"contraste de luminosidade (OKLCH brilha aqui, literalmente)."
            ),
            "chroma": 1.1,
        },
    ]

    selected = [strategies[0], strategies[1]]
    remaining = strategies[2:]
    for s in remaining:
        if len(selected) >= num:
            break
        selected.append(s)

    proposals = []
    for i, strat in enumerate(selected):
        shifted_hue = (base_hue + strat["hue_shift"]) % 360
        p = generate_proposal_colors(
            base_hue=shifted_hue,
            harmony=strat["harmony"],
            rationale=strat["rationale"],
            name=f"Proposta {chr(65 + i)}",
            chroma_boost=strat["chroma"],
        )
        proposals.append(p)

    return proposals


# ─── Color Board Rendering ──────────────────────────────────────────────────

def render_color_board(colors: list, height: int = 320) -> str:
    """
    Render a proportional color board (vertical blocks, like ColorHunt).

    colors: list of (hex, proportion) tuples.
            proportions are relative weights (e.g., 5, 3, 3, 2, 2).

    Hex value appears on hover, rendered in the palette's own text color
    on each block — doubles as a live legibility test.
    """
    total = sum(p for _, p in colors)
    blocks = ""
    for hex_color, proportion in colors:
        pct = (proportion / total) * 100
        txt = text_color_on(hex_color)
        blocks += f"""<div style="
            background:{hex_color};
            height:{pct}%;
            display:flex;
            align-items:center;
            justify-content:center;
            cursor:pointer;
        " class="board-block" data-hex="{hex_color}">
            <span style="
                font-family:'SF Mono',SFMono-Regular,Consolas,'Liberation Mono',monospace;
                font-size:30px;
                font-weight:700;
                letter-spacing:0.04em;
                color:{txt};
                opacity:0;
                transition:opacity 0.2s;
                pointer-events:none;
            " class="hex-label">{hex_color.upper()}</span>
        </div>"""

    return f"""<div style="
        height:{height}px;
        border-radius:14px;
        overflow:hidden;
        display:flex;
        flex-direction:column;
        box-shadow:0 2px 8px rgba(0,0,0,0.06);
    ">{blocks}</div>"""


def render_proposal_card(p: ProposalColors, index: int) -> str:
    """Render a full proposal card with light and dark boards."""
    light_colors = [
        (p.primary, 5),
        (p.primary_light, 3),
        (p.secondary, 3),
        (p.neutral_warm, 2),
        (p.neutral_cool, 2),
    ]
    dark_colors = [
        (p.dark_primary, 5),
        (p.dark_primary_light, 3),
        (p.dark_secondary, 3),
        (p.dark_neutral_warm, 2),
        (p.dark_neutral_cool, 2),
    ]

    light_board = render_color_board(light_colors, height=380)
    dark_board = render_color_board(dark_colors, height=380)

    return f"""
    <div class="proposal-card" id="proposal-{index}">
      <div class="proposal-header">
        <div style="display:flex;align-items:center;gap:10px;">
          <span class="proposal-letter" style="background:{p.primary};color:{text_color_on(p.primary)};">{chr(65 + index)}</span>
          <div>
            <div class="proposal-harmony">{p.harmony}</div>
            <div class="proposal-meta">{p.oklch_primary}</div>
          </div>
        </div>
      </div>
      <div class="proposal-rationale">{p.rationale}</div>

      <div class="theme-toggle">
        <button class="toggle-btn active" onclick="showTheme(this, 'light', {index})">Light</button>
        <button class="toggle-btn" onclick="showTheme(this, 'dark', {index})">Dark</button>
      </div>

      <div id="board-light-{index}">
        {light_board}
      </div>
      <div id="board-dark-{index}" style="display:none;">
        {dark_board}
      </div>
    </div>"""


# ─── HTML Page ───────────────────────────────────────────────────────────────

def generate_proposals_html(proposals: list, project_name: str, output_dir: str) -> str:
    """Generate the full proposals HTML page."""

    cards_html = "".join(render_proposal_card(p, i) for i, p in enumerate(proposals))

    # JSON summary for programmatic use
    summary = []
    for p in proposals:
        summary.append({
            "name": p.name,
            "harmony": p.harmony,
            "rationale": p.rationale,
            "base_hue": p.base_hue,
            "oklch_primary": p.oklch_primary,
            "oklch_secondary": p.oklch_secondary,
            "light": {
                "primary": p.primary,
                "primary_light": p.primary_light,
                "secondary": p.secondary,
                "neutral_warm": p.neutral_warm,
                "neutral_cool": p.neutral_cool,
            },
            "dark": {
                "primary": p.dark_primary,
                "primary_light": p.dark_primary_light,
                "secondary": p.dark_secondary,
                "neutral_warm": p.dark_neutral_warm,
                "neutral_cool": p.dark_neutral_cool,
            }
        })

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{project_name} — Propostas de cor</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
    background: #f5f5f7;
    color: #1d1d1f;
    padding: 40px 32px;
    max-width: 1200px;
    margin: 0 auto;
  }}
  h1 {{ font-size: 26px; font-weight: 700; margin-bottom: 4px; letter-spacing: -0.02em; }}
  .subtitle {{ font-size: 14px; color: #86868b; margin-bottom: 40px; }}

  .proposals-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 28px;
  }}

  .proposal-card {{
    background: #fff;
    border-radius: 20px;
    padding: 20px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
    transition: box-shadow 0.2s, transform 0.2s;
  }}
  .proposal-card:hover {{
    box-shadow: 0 8px 24px rgba(0,0,0,0.1);
    transform: translateY(-2px);
  }}

  .proposal-header {{
    margin-bottom: 8px;
  }}
  .proposal-letter {{
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 32px;
    height: 32px;
    border-radius: 10px;
    font-size: 15px;
    font-weight: 700;
  }}
  .proposal-harmony {{
    font-size: 14px;
    font-weight: 600;
    color: #1d1d1f;
    text-transform: capitalize;
  }}
  .proposal-meta {{
    font-size: 11px;
    font-family: 'SF Mono', SFMono-Regular, Consolas, monospace;
    color: #86868b;
  }}
  .proposal-rationale {{
    font-size: 13px;
    color: #6e6e73;
    line-height: 1.45;
    margin-bottom: 14px;
  }}

  .theme-toggle {{
    display: flex;
    gap: 4px;
    margin-bottom: 14px;
    background: #f0f0f2;
    border-radius: 10px;
    padding: 3px;
    width: fit-content;
  }}
  .toggle-btn {{
    padding: 5px 16px;
    border: none;
    border-radius: 8px;
    font-size: 12px;
    cursor: pointer;
    background: transparent;
    color: #6e6e73;
    transition: all 0.15s;
    font-weight: 500;
  }}
  .toggle-btn.active {{
    background: #fff;
    color: #1d1d1f;
    font-weight: 600;
    box-shadow: 0 1px 3px rgba(0,0,0,0.08);
  }}

  .board-block:hover .hex-label {{
    opacity: 1 !important;
  }}

  footer {{
    margin-top: 48px;
    font-size: 11px;
    color: #aeaeb2;
    text-align: center;
  }}
</style>
</head>
<body>

<h1>{project_name}</h1>
<div class="subtitle">{len(proposals)} propostas de paleta · Passe o mouse sobre os blocos para ver os hex</div>

<div class="proposals-grid">
  {cards_html}
</div>

<footer>
  Gerado com OKLCH Color Palette Generator
</footer>

<script>
function showTheme(btn, theme, idx) {{
  const card = document.getElementById('proposal-' + idx);
  card.querySelectorAll('.toggle-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  document.getElementById('board-light-' + idx).style.display = theme === 'light' ? 'block' : 'none';
  document.getElementById('board-dark-' + idx).style.display = theme === 'dark' ? 'block' : 'none';
}}

// Click to copy hex
document.querySelectorAll('.board-block').forEach(block => {{
  block.addEventListener('click', () => {{
    const hex = block.dataset.hex;
    navigator.clipboard.writeText(hex).catch(() => {{}});
    const label = block.querySelector('.hex-label');
    const orig = label.textContent;
    label.textContent = 'copiado!';
    label.style.opacity = '1';
    setTimeout(() => {{ label.textContent = orig; }}, 800);
  }});
}});
</script>

</body>
</html>"""

    os.makedirs(output_dir, exist_ok=True)
    safe_name = project_name.lower().replace(" ", "-").replace("ê", "e").replace("ã", "a").replace("ç", "c").replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u")
    path = os.path.join(output_dir, f"{safe_name}-proposals.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)

    # Save summary JSON
    json_path = os.path.join(output_dir, f"{safe_name}-proposals.json")
    with open(json_path, "w") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    return path


# ─── CLI ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Generate color palette visual proposals")
    parser.add_argument("--base-hue", required=True,
                       help="Base hue angle (0-360), hex color, or oklch() value")
    parser.add_argument("--name", default="Projeto", help="Project name")
    parser.add_argument("--output-dir", default="./proposals", help="Output directory")
    parser.add_argument("--num-proposals", type=int, default=3,
                       help="Number of proposals to generate (2-5)")

    args = parser.parse_args()

    base_hue = parse_to_hue(args.base_hue)
    num = max(2, min(5, args.num_proposals))

    print(f"Base hue: {base_hue:.0f}°")
    print(f"Generating {num} proposals...")

    proposals = create_proposals(base_hue, num)
    path = generate_proposals_html(proposals, args.name, args.output_dir)

    print(f"\nProposals saved to: {path}")
    print("Open in a browser to compare.")


if __name__ == "__main__":
    main()
