# tharso-skills

Uma coleção de skills práticas para o [Claude Code](https://docs.anthropic.com/en/docs/claude-code) — o agente de IA da Anthropic.

Cada skill é um conjunto autocontido de instruções que ensina o Claude a executar uma tarefa específica com profundidade e precisão.

> **Sobre o idioma:** Sim, eu escolhi criar todas as skills em português... porque... porque as features são minhas e eu faço no idioma que eu bem entender. Dito isso, se precisar em inglês, basta pedir pro seu modelo favorito traduzir que ele fará o job sem reclamar. Muak!

## Skills

| Skill | O que faz |
|-------|-----------|
| [**brainstorm**](./brainstorm/) | Facilitador de brainstorming com 36 técnicas criativas em 7 categorias. Da divergência à convergência |
| [**color-palette**](./color-palette/) | Gera paletas de cores profissionais em OKLCH. Exploração visual com boards proporcionais, temas light/dark, validação APCA + WCAG, export multi-formato |
| [**decisã**](./decisa/) | Facilitadora de tomada de decisão. Não dá respostas — faz as perguntas que você está evitando |
| [**design-dna**](./design-dna/) | Extrai o DNA visual de qualquer site — tipografia, cores, espaçamento, profundidade, motion — e salva como referência estruturada |
| [**feature-forge**](./feature-forge/) | Parceiro de pensamento pra planejar features antes de criar issues no GitHub. Da ideia vaga à issue estruturada |
| [**pdf-like-a-boss**](./pdf-like-a-boss/) | Pipeline profissional de geração de PDF via HTML+CSS com validação em cada etapa |
| [**smry-reader**](./smry-reader/) | Leitor limpo de páginas web via proxy smry.ai. Remove anúncios, popups e ruído visual |
| [**youtube-extractor**](./youtube-extractor/) | Extrai metadados e transcrição completa de vídeos do YouTube em Markdown estruturado |

## Instalação

### Instalar uma skill

```bash
claude skills add /caminho/para/tharso-skills/design-dna
```

### Instalar via GitHub (clone primeiro)

```bash
git clone https://github.com/tharso/tharso-skills.git
claude skills add ./tharso-skills/design-dna
```

### Instalação manual

Copie a pasta da skill para o diretório `.claude/skills/` do seu projeto:

```bash
cp -r design-dna /seu-projeto/.claude/skills/
```

## Formato das skills

Cada skill segue a [spec de skills do Claude Code](https://docs.anthropic.com/en/docs/claude-code/skills):

```
nome-da-skill/
├── SKILL.md          # Instruções + frontmatter YAML (obrigatório)
├── references/       # Docs de apoio, exemplos (opcional)
└── scripts/          # Scripts auxiliares (opcional)
```

O frontmatter do `SKILL.md` inclui:

```yaml
---
name: nome-da-skill
description: O que faz e quando deve ser ativada
version: 1.0.0
---
```

## Contribuindo

Veja [CONTRIBUTING.md](./CONTRIBUTING.md) para guidelines de contribuição.

## Licença

[MIT](./LICENSE)
