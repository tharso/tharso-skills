---
name: smry-reader
description: "Leitor limpo de p\u00e1ginas web via smry.ai. Usa quando o usu\u00e1rio quer ler um artigo, not\u00edcia ou p\u00e1gina web sem polui\u00e7\u00e3o visual (an\u00fancios, popups, banners, layouts quebrados). Dispara quando o usu\u00e1rio pede pra 'ler', 'abrir', 'mostrar' ou 'limpar' uma URL, ou quando menciona que um site \u00e9 polu\u00eddo, cheio de an\u00fancios, ou dif\u00edcil de ler. Tamb\u00e9m dispara quando o usu\u00e1rio quer um resumo ou o conte\u00fado principal de uma p\u00e1gina web."
version: 1.0.0
---

# smry-reader

Ferramenta de leitura limpa. Voc\u00ea recebe uma URL, passa ela pelo proxy do smry.ai, e entrega o conte\u00fado sem lixo visual.

## Como funciona

O smry.ai tem um proxy que extrai o conte\u00fado principal de qualquer p\u00e1gina, removendo an\u00fancios, popups, menus de navega\u00e7\u00e3o e todo o ru\u00eddo visual. Basta antepor o prefixo \u00e0 URL original:

```
https://smry.ai/pt/proxy?url=<URL_ORIGINAL>
```

## Workflow

1. O usu\u00e1rio fornece uma URL (ou voc\u00ea identifica uma URL no contexto da conversa)
2. Monte a URL limpa: `https://smry.ai/pt/proxy?url=` + URL original
3. Use a ferramenta `WebFetch` para buscar o conte\u00fado da URL montada
4. Apresente o conte\u00fado de forma organizada ao usu\u00e1rio

Se o WebFetch falhar ou retornar conte\u00fado vazio, informe o usu\u00e1rio que a p\u00e1gina n\u00e3o p\u00f4de ser processada pelo leitor e sugira que ele acesse diretamente.

## Exemplo

Usu\u00e1rio: "Me mostra esse artigo aqui: https://exemplo.com/artigo-interessante"

Voc\u00ea faz:
```
WebFetch("https://smry.ai/pt/proxy?url=https://exemplo.com/artigo-interessante")
```

E entrega o conte\u00fado limpo, sem reproduzir o texto na \u00edntegra (respeite copyright). Forne\u00e7a um resumo \u00fatil e cite trechos curtos quando relevante.

## Regras

- Sempre respeite as restri\u00e7\u00f5es de copyright: n\u00e3o reproduza o conte\u00fado inteiro, fa\u00e7a resumos e cite trechos curtos (menos de 15 palavras entre aspas)
- Se o WebFetch n\u00e3o conseguir acessar a URL montada, n\u00e3o tente m\u00e9todos alternativos (curl, wget, etc.)
- Se o usu\u00e1rio pedir apenas pra "ler" sem mais contexto, pergunte o que ele quer saber sobre o artigo antes de despejar tudo
