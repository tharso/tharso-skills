---
name: youtube-extractor
description: >
  Extracts metadata and full transcript from YouTube videos, saving everything
  as a structured Markdown file in pt-BR. Use this skill whenever the user
  shares a YouTube URL and wants to extract, transcribe, summarize, or save
  the video content as text. Also triggers when the user mentions "transcrever
  vídeo", "extrair conteúdo do YouTube", "salvar vídeo como texto", or any
  variation of wanting to get text content from a YouTube video. Works with
  any YouTube URL format (youtube.com, youtu.be, shorts, embeds).
version: 1.0.0
---

# YouTube Extractor

Extrai metadados e transcrição completa de vídeos do YouTube, gerando um
arquivo Markdown estruturado em pt-BR.

## Arquitetura (pipeline de 3 estágios)

O processo combina ferramentas mecânicas pra extração com inteligência do
Claude pra tradução e formatação. Cada estágio tem um papel claro:

**Estágio 1 — Extração mecânica** (script Python, sem IA):
`yt-dlp` captura metadados (título, canal, data, views, descrição, tags).
`youtube-transcript-api` puxa a transcrição/legendas direto do YouTube.
Resultado: dados brutos em JSON, tipicamente no idioma original do vídeo.

**Estágio 2 — Tradução e formatação** (Claude):
Se a transcrição veio em idioma diferente de pt-BR, Claude traduz o texto
mantendo terminologia técnica correta (especialmente termos de áreas como
medicina, engenharia, finanças, esporte, etc.). Claude também organiza o
texto em parágrafos naturais, corrige artefatos de speech-to-text, e monta
o Markdown final com todos os metadados.

**Estágio 3 — Fallback** (Gemini, só quando necessário):
Se o vídeo não tiver legenda nenhuma (nem manual, nem auto-gerada), o
script usa a API do Gemini pra processar o vídeo diretamente e extrair o
conteúdo falado. Requer GEMINI_API_KEY como variável de ambiente.

Essa separação importa porque: a API do YouTube é rápida, gratuita e
captura 100% do conteúdo falado, mas entrega texto cru no idioma original.
O Claude traduz com precisão terminológica que o Gemini sozinho não
consegue (vide comparativo em references/). E o Gemini só entra quando
não existe outra fonte de transcrição.

## Workflow passo a passo

Quando o usuário compartilha uma URL do YouTube:

### Passo 1: Instalar dependências (se necessário)

```bash
pip install yt-dlp youtube-transcript-api google-genai
```

### Passo 2: Extrair dados brutos

Use o modo `--raw-json` pra obter todos os dados estruturados:

```bash
python scripts/extract.py "<youtube_url>" --raw-json
```

Isso retorna um JSON com dois blocos: `metadata` e `transcript`.
O campo `transcript.language` indica o idioma da transcrição obtida.
O campo `transcript.success` indica se a extração funcionou.

### Passo 3: Processar o conteúdo

Com o JSON em mãos, Claude faz o trabalho inteligente:

**Se a transcrição veio em pt ou pt-BR:** Apenas organize em parágrafos
naturais, corrija artefatos de speech-to-text (palavras cortadas, repetições
de fala como "um", "é", "tipo"), e monte o Markdown.

**Se a transcrição veio em outro idioma:** Traduza o texto completo pra
pt-BR. Pontos de atenção na tradução:
- Mantenha nomes próprios no original (pessoas, marcas, lugares)
- Use terminologia técnica correta em português (ex: "stroke volume" →
  "volume sistólico", não "volume de golpe"; "cardiac output" → "débito
  cardíaco", não "produção cardíaca")
- Preserve o tom e estilo do falante
- Não resuma nem condense; traduza tudo

**Se a transcrição falhou (success: false):** Verifique se existe
GEMINI_API_KEY configurada e rode novamente sem --raw-json e com
--gemini-key. Se não houver key, informe o usuário.

### Passo 4: Montar o Markdown final

O arquivo MD deve seguir esta estrutura:

```
# [Título do vídeo]

## Informações do vídeo

| Campo | Valor |
| --- | --- |
| **Canal** | [Nome](URL) |
| **Data de publicação** | DD/MM/AAAA |
| **Duração** | XhYmin Zs |
| **Visualizações** | N |
| **Likes** | N |
| **URL** | link |
| **Idioma original** | xx |

**Tags:** `tag1`, `tag2`, ...

**Categorias:** Cat1, Cat2

## Descrição original

[Descrição do vídeo como veio do YouTube]

## Conteúdo do vídeo (transcrição)

*Fonte: [tipo de legenda] | Traduzido de [idioma] para pt-BR por Claude*

[Texto completo organizado em parágrafos naturais]

---
*Extraído em DD/MM/AAAA às HH:MM via youtube-extractor skill*
```

### Passo 5: Salvar e entregar

Salve o arquivo MD no workspace do usuário. Use o título do vídeo como
nome do arquivo (slugificado). Informe ao usuário: título, canal, duração,
quantidade de palavras, e idioma original.

## Modo direto (sem tradução do Claude)

Se o usuário quiser o output rápido sem passar pela tradução do Claude,
o script gera o Markdown completo sozinho:

```bash
python scripts/extract.py "<url>" --output-dir <dir>
```

Útil quando o vídeo já está em português ou quando o usuário não precisa
de tradução.

## Opções do script

```
python scripts/extract.py <url> [options]

Argumentos:
  url                    URL do YouTube ou video ID

Opções:
  --output, -o PATH      Caminho do arquivo de saída
  --output-dir, -d DIR   Diretório de saída (default: dir atual)
  --gemini-key KEY       API key do Gemini (ou var GEMINI_API_KEY)
  --lang LANG            Idioma preferido pra transcrição (default: pt)
  --timestamps           Incluir timestamps na transcrição
  --json                 Salvar JSON com dados brutos junto do Markdown
  --raw-json             Retornar apenas JSON no stdout (pra Claude processar)
```

## Dependências

```bash
pip install yt-dlp youtube-transcript-api google-genai
```

`google-genai` só é necessário pro fallback Gemini.

## Edge cases

- **Shorts:** Funciona normalmente com URLs de YouTube Shorts
- **Live streams:** Metadados OK, transcrição pode não existir
- **Vídeos com restrição de idade:** yt-dlp pode falhar; informar usuário
- **Vídeos privados/deletados:** Script vai dar erro; informar usuário
- **Sem legenda nenhuma:** Tentar fallback Gemini ou informar usuário
- **Vídeos muito longos (>2h):** Transcrição pode ser grande; considerar
  quebrar em seções ou oferecer resumo
