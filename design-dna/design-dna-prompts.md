# Prompts para extração de Design DNA via Claude

Copie o prompt relevante, substitua `[URL]` pela URL do site, e cole numa conversa com o Claude (não o Cowork). Depois, copie a resposta inteira e me passe aqui no Cowork pra eu salvar na biblioteca de referências.

---

## Prompt 1: Extração completa (sites complexos, ricos em detalhes)

Use pra sites com identidade visual forte, animações, glassmorphism, sistemas de design elaborados.

```
Analise o site [URL] e extraia o Design DNA completo: todas as decisões visuais que dão personalidade ao site.

Preciso de uma análise profunda e técnica, com valores CSS reais (não resumos genéricos). O output deve seguir exatamente este formato markdown:

# Design DNA: [Nome do Site]

**Source:** [URL]
**Extracted:** [Data de hoje]
**Extraction mode:** Claude direct analysis
**Atmosphere:** [Uma frase capturando o "feeling" geral do site]

## Typography [confidence: measured]

**Font stack:**
- Display/Headings: [nome da fonte] ([pesos usados]) — [observação sobre personalidade]
- Body: [nome da fonte] ([pesos usados])
- Code/Labels: [se houver]
- Fallback chain: [sequência completa]

**Hierarquia:**
- H1: font-family, tamanho exato (mobile/desktop se responsivo), weight, line-height, letter-spacing, text-transform
- H2: mesmos detalhes
- Body: mesmos detalhes
- Small/UI: se houver

**Size ratio:** [proporção entre body e H1, com valores]

**Fonts:** [como são carregadas: Google Fonts, self-hosted, CDN? URLs se visíveis]

## Color palette [confidence: measured]

**Core:**
- Background (light/dark): valor hex/rgb exato + descrição
- Foreground (light/dark): valor exato
- Accent primário: valor exato + onde é usado
- Accent secundário: se houver

**Neutrals:** [escala completa se visível: 100, 200, 300... 900]

**Accent colors:** [cada cor com hex e contexto de uso]

**CSS variables encontradas:** [lista das mais relevantes com nome e valor]

**Palette character:** [descrição da estratégia cromática]

## Backgrounds and surfaces [confidence: measured]

**Primary background:** [sólido/gradiente/textura — descreva com precisão]
**Surface treatment:** [como cards/containers diferem do fundo]
**Notable effects:** [gradientes, noise, blur, mix-blend-mode, etc. com valores CSS]

## Depth strategy [confidence: measured]

**Approach:** [estratégia geral]
**Box shadows:** [valores completos de multi-layer shadows, incluindo inset]
**Borders:** [valores, incluindo técnicas como conic-gradient borders]
**Border radius:** [valores e onde são usados]
**Backdrop filter:** [se houver, valor exato]
**Hover/active states:** [transformações no hover e click]

## Spacing [confidence: measured]

**Base unit:** [valor em px/rem]
**Density:** [tight/moderate/generous + onde cada uma é usada]
**Notable:** [gaps entre seções, paddings responsivos, qualquer decisão de spacing que defina ritmo]

## Motion [confidence: measured]

**Approach:** [Minimal/Purposeful/Orchestrated/Heavy]
**Libraries detected:** [GSAP, Framer Motion, Lenis, AOS, etc.]
**Key patterns:** [scroll animations, hover transitions, page transitions, loading states]
**Transition timing:** [duração + easing function com valores cubic-bezier exatos]
**@keyframes:** [animações nomeadas relevantes, com valores]
**CSS @property:** [se usado pra animações de custom properties]

## Visual style [confidence: measured/interpreted]

**Illustrations:** [estilo preciso — flat, 3D, hand-drawn, etc. Descreva como se fosse um prompt de geração de imagem]
**Photography:** [tratamento se houver]
**Iconography:** [estilo, tamanho, cor]
**Layout personality:** [grid/orgânico, denso/arejado, simétrico/assimétrico]

## Signature elements

[Liste 3-5 decisões de design que tornam este site memorável. Seja específico e técnico.]

## Dark mode [confidence: measured]

[Se existir: como funciona, quais valores mudam, duração da transição]

## Tech stack [confidence: measured]

[Framework, CSS approach, animation libraries, fonts delivery, monitoring]

## How to use this reference

**Elementos mais transferíveis:** [o que funciona fora do contexto original]
**Cuidados ao adaptar:** [o que precisa de licença, o que é difícil de replicar, o que não escala]

---

REGRAS IMPORTANTES:
1. Use valores CSS REAIS sempre que possível (hex, rgb, px, rem, cubic-bezier). Nada de "azul escuro" quando você pode dizer #191919.
2. Multi-layer shadows: liste CADA camada separadamente.
3. Gradientes: sintaxe CSS completa (direção, color stops).
4. Não resuma — detalhe. Se um botão tem 6 propriedades CSS interessantes, liste as 6.
5. Confidence indicators: [measured] pra dados extraídos do código, [interpreted] pra inferências, [estimated] pra palpites educados.
6. Se o site tem dark mode, documente ambos os modos.
7. Output como um único bloco markdown, pronto pra copiar.
```

---

## Prompt 2: Extração rápida (sites mais simples ou quando vc quer só o essencial)

Use pra sites mais limpos, ou quando vc quer capturar só a essência sem ir fundo em cada detalhe.

```
Extraia o Design DNA do site [URL]. Foco nos elementos que definem a identidade visual.

Formato do output:

# Design DNA: [Nome]

**Source:** [URL]
**Extracted:** [Data]
**Extraction mode:** Claude direct analysis
**Atmosphere:** [uma frase]

## Typography [confidence: measured]
Font stack completo (nomes, pesos, fontes de carregamento). Hierarquia com tamanhos reais. Size ratio body-to-H1.

## Color palette [confidence: measured]
Background, foreground, accents com valores hex exatos. CSS variables relevantes. Descrição da estratégia cromática.

## Depth + Surfaces [confidence: measured]
Shadows (valores completos), borders, border-radius, backdrop-filter. Como cards/surfaces se diferenciam do fundo.

## Motion [confidence: measured]
Libraries detectadas. Timing (duração + easing). Padrões principais (scroll, hover, page transitions).

## Signature elements
3 decisões de design que tornam o site memorável. Seja técnico e específico.

## How to use this reference
O que é transferível e o que exige cuidado.

REGRAS: valores CSS reais (hex, px, cubic-bezier), não descrições vagas. Output como markdown único.
```

---

## Dica de uso

Pra sites com muito CSS custom (glassmorphism, scroll animations, sistemas de cor complexos), use o Prompt 1. Pra landing pages mais limpas ou sites onde vc quer só capturar a vibe geral, o Prompt 2 resolve.

Quando o Claude devolver a extração, copie tudo e me envie aqui no Cowork (pode colar direto ou salvar num .txt e fazer upload). Eu processo, valido o formato, e salvo na biblioteca `.design-references/`.
