---
name: pdf-like-a-boss
description: >
  Professional PDF generation pipeline via HTML+CSS with validation at every step.
  Use this skill whenever the user asks to create, generate, or produce a new PDF
  (reports, proposals, one-pagers, corporate documents, technical sheets, invoices).
  Also triggers on "generate PDF", "create document", "build a report",
  "make a nice PDF", "PDF with my branding", or any variation of PDF creation
  with visual control. Supports any language including pt-BR with full accent/unicode support.
  Do NOT use for operations on existing PDFs (merge, split, extract, fill forms) —
  use the standard "pdf" skill for those.
version: 1.0.0
---

# Professional PDF generation

You generate reliable, good-looking PDFs through a 5-step pipeline. The core idea: HTML+CSS is your layout engine (you're fluent in it), and WeasyPrint converts everything to PDF with high fidelity. Each step has a validation checkpoint before moving on.

## The pipeline

```
[1. Content] → [2. Visual identity] → [3. HTML + TOC] → [4. PDF] → [5. Verification]
```

Don't skip steps. The temptation to jump straight to code is real, but each step prevents rework in the next one.

## Step 1: Structure the content

Before writing any code, organize the content into semantic blocks. Think of this as the document's skeleton.

Validate with the user:
- Which sections the document will have (and in what order)
- What data/text goes in each section
- Whether there are tables, lists, quotes, highlights
- Whether there are images that need to be included
- Metadata: title, author, date, version (if applicable)

If the user already provided all the content, assemble the skeleton and confirm: "The document will have these sections in this order: [...]. Does that work?"

If information is missing, ask. Never invent data.

## Step 2: Visual identity

This step is critical because it's the difference between a generic PDF and one that looks intentional. Before generating anything, ask the user about these three things explicitly. Use the AskUserQuestion tool to gather this efficiently in one shot.

### What to ask

**Logo**: Ask if the user has a logo file to include. If they uploaded one or have one in the workspace folder, use it. If they don't have one, that's fine — skip it. But always ask. Place the logo on the cover page and optionally in the header/footer.

**Colors**: Suggest a palette based on the document type and ask the user to confirm or override. Present 2-3 options with hex codes so they can visualize what you're proposing. If the user provides brand colors, use those instead.

**Fonts**: Suggest a Google Fonts pairing (one for headings, one for body) and ask for confirmation. Default suggestion: Inter for body, Inter for headings (clean and versatile). For more personality, suggest alternatives like Source Serif 4 + Source Sans 3, or Merriweather + Open Sans.

**Table of contents**: Ask if the user wants a table of contents. For documents with 3+ sections, suggest yes. For short documents (1-2 pages), suggest no. The TOC is built as a styled HTML page (not auto-generated), so it gives full control over formatting but must be manually kept in sync with the content.

### Suggested palettes

When suggesting colors, pick based on the document's tone:

**Corporate** (default for reports, formal docs):
- Primary: #1a365d, Secondary: #2d3748, Accent: #3182ce
- Highlight bg: #ebf4ff, Text: #1a202c, Light text: #718096

**Modern neutral** (proposals, one-pagers):
- Primary: #111827, Secondary: #374151, Accent: #6366f1
- Highlight bg: #f0f0ff, Text: #111827, Light text: #6b7280

**Warm professional** (materials with personality):
- Primary: #7c2d12, Secondary: #44403c, Accent: #ea580c
- Highlight bg: #fff7ed, Text: #1c1917, Light text: #78716c

### Layout defaults

Unless the user specifies otherwise:
- Page size: A4 portrait
- Margins: 2cm top/bottom, 2.5cm left/right
- Footer: page number (centered, "page X / Y" format)
- First page: no footer (cover page)

## Step 3: Generate the HTML

This is where the document takes shape. Generate a self-contained HTML file.

### Base template

Use this as your starting point. Replace color/font placeholders with the choices from Step 2. Set the `lang` attribute to match the document language (e.g., `pt-BR`, `en`, `es`).

```html
<!DOCTYPE html>
<html lang="LANG_CODE">
<head>
<meta charset="UTF-8">
<meta name="author" content="AUTHOR_NAME">
<title>DOCUMENT_TITLE</title>
<style>
/* ===== FONTS ===== */
@import url('https://fonts.googleapis.com/css2?family=HEADING_FONT:wght@400;500;600;700&family=BODY_FONT:wght@400;500;600;700&display=swap');

/* ===== PAGE SETUP ===== */
@page {
    size: A4;
    margin: 2cm 2.5cm;
    @bottom-center {
        content: counter(page) " / " counter(pages);
        font-family: "BODY_FONT", sans-serif;
        font-size: 8pt;
        color: COLOR_LIGHT_TEXT;
    }
}

/* Cover uses a named page with zero margins for full-bleed background */
@page cover {
    margin: 0;
    @bottom-center { content: none; }
}

/* ===== GLOBALS ===== */
body {
    font-family: "BODY_FONT", sans-serif;
    font-size: 10.5pt;
    line-height: 1.65;
    color: COLOR_TEXT;
}

/* ===== TYPOGRAPHY ===== */
h1 { font-family: "HEADING_FONT", sans-serif; font-size: 22pt; font-weight: 700; margin-top: 0; color: COLOR_PRIMARY; }
h2 {
    font-family: "HEADING_FONT", sans-serif; font-size: 14pt; font-weight: 600; color: COLOR_PRIMARY;
    margin-top: 1.5em; border-bottom: 2px solid COLOR_ACCENT; padding-bottom: 4px;
}
h3 { font-family: "HEADING_FONT", sans-serif; font-size: 11pt; font-weight: 600; color: COLOR_SECONDARY; margin-top: 1.2em; }

p { margin: 0.6em 0; text-align: justify; }

/* ===== TABLES ===== */
table { width: 100%; border-collapse: collapse; margin: 1em 0; font-size: 9.5pt; }
thead { display: table-header-group; } /* repeats header on page breaks */
thead th {
    background: COLOR_PRIMARY; color: white;
    padding: 8px 10px; text-align: left; font-weight: 600;
}
tbody td { padding: 7px 10px; border-bottom: 1px solid #e2e8f0; }
tbody tr:nth-child(even) { background: #f7fafc; }

/* ===== CALLOUTS ===== */
.callout {
    background: COLOR_HIGHLIGHT_BG;
    border-left: 4px solid COLOR_ACCENT;
    padding: 12px 16px; margin: 1em 0; font-size: 10pt;
}

/* ===== PAGE BREAK CONTROL ===== */
h1, h2, h3 { page-break-after: avoid; }
table, figure, .callout { page-break-inside: avoid; }
.page-break { page-break-before: always; }

/* ===== COVER (optional) ===== */
/* The cover uses a named @page rule (defined above) to get zero margins.
   This makes the background color/image fill the entire page edge-to-edge.
   All spacing is handled via padding on the inner container. */
.cover-page {
    page: cover;
    page-break-after: always;
    width: 100%; height: 100vh;
    background: COLOR_PRIMARY;
    color: white;
    display: flex; flex-direction: column;
    padding: 0; box-sizing: border-box;
}
.cover-inner {
    flex: 1;
    display: flex; flex-direction: column; justify-content: center;
    padding: 4cm;
}
.cover-page h1 { font-size: 28pt; color: white; margin: 0 0 0.4em 0; line-height: 1.2; }
.cover-page .logo { height: 48px; margin-bottom: 2em; }
.cover-bottom {
    padding: 16px 4cm;
    border-top: 2px solid COLOR_ACCENT;
    font-size: 8.5pt; color: #555;
}
</style>
</head>
<body>
<!-- Document content here -->
</body>
</html>
```

### Table of contents (if requested)

If the user wants a TOC, build it as a manually crafted HTML section placed right after the cover page. Use a dedicated `@page toc` rule if you want different margins or styling for the TOC page.

The TOC should list all major sections with their key metadata (estimates, risk levels, etc. — whatever is relevant for the document type). Use dotted borders between the label and the metadata to create a clean, scannable layout.

```html
<div class="toc-page">
    <div class="toc-title">Table of Contents</div>
    <div class="toc-phase">Section group label</div>
    <div class="toc-item">
        <span class="toc-label">Section name</span>
        <span class="toc-meta">Relevant metadata</span>
    </div>
    <!-- More items... -->
</div>
```

Style the TOC items with `display: flex; justify-content: space-between;` and a `border-bottom: 1px dotted #ddd;` for the classic TOC look. The TOC page should have `page-break-after: always;` to separate it from the main content.

WeasyPrint does not support automatic TOC generation, so the TOC must be built by hand in the HTML. This means extra work, but it also means total control over formatting and content. Keep the TOC in sync with the actual document sections.

### Important rules for the HTML

**Images and logos**: Always embed as base64 or use absolute URLs. Relative paths break during conversion.

```python
import base64
with open("logo.png", "rb") as f:
    b64 = base64.b64encode(f.read()).decode()
img_tag = f'<img src="data:image/png;base64,{b64}" alt="Logo" class="logo">'
```

**Long tables**: The `thead { display: table-header-group; }` in the base template ensures headers repeat across page breaks.

**Explicit page breaks**: Use `<div class="page-break"></div>` between sections that should start on a new page.

**Fonts**: Google Fonts @import works in WeasyPrint. If the connection fails, the sans-serif fallback kicks in. For mission-critical documents where offline is a risk, embed the font as base64 via @font-face.

**Unicode/accents**: WeasyPrint handles UTF-8 natively. Content in any language (pt-BR, es, fr, etc.) works out of the box as long as `<meta charset="UTF-8">` is present and the chosen font supports the required glyphs (all Google Fonts in the suggestions above do).

### Save the HTML

Always save the generated HTML as a file. This lets the user make manual tweaks later without regenerating everything from scratch.

```python
html_path = "document.html"
with open(html_path, "w", encoding="utf-8") as f:
    f.write(html_content)
```

Tell the user the HTML was saved and can be edited directly for future adjustments.

## Step 4: Convert HTML → PDF

Use WeasyPrint for conversion. If not installed, run `pip install weasyprint`.

```python
from weasyprint import HTML

HTML(filename=html_path).write_pdf(pdf_path)
```

If WeasyPrint throws warnings (missing fonts, unsupported CSS properties), log them and assess whether they're critical. Font fallbacks are usually acceptable; ignored CSS properties may affect layout.

### CSS that works well in WeasyPrint

- Flexbox (most properties)
- @page rules with counters and named margins
- Google Fonts via @import
- background, border, box-shadow, border-radius
- Full table styling
- CSS custom properties (variables)

### CSS that does NOT work or has partial support

- CSS Grid (partial support — avoid for complex layouts, prefer flexbox)
- position: fixed (doesn't work in paginated context)
- JavaScript (obviously)
- Complex transforms

When in doubt between flexbox and grid, pick flexbox.

## Step 5: Verify the PDF

This step separates a "generated" PDF from a "finished" one. Render each page as an image and visually inspect it.

```python
import pypdfium2 as pdfium

pdf = pdfium.PdfDocument(pdf_path)
print(f"Total pages: {len(pdf)}")

for i, page in enumerate(pdf):
    bitmap = page.render(scale=2.0)
    img = bitmap.to_pil()
    preview_path = f"preview_page_{i+1}.png"
    img.save(preview_path)
    # Examine each image using the Read tool
```

### Verification checklist

Examine EVERY rendered page and check:

1. **Text**: Is all content present? Nothing cut off?
2. **Layout**: Elements aligned? Consistent margins?
3. **Tables**: Headers visible? Rows not split awkwardly across pages?
4. **Images/logos**: Correct size? No distortion? Logo present where expected?
5. **Fonts**: Expected font rendered? No "square" glyphs?
6. **Pagination**: Correct page number in footer?
7. **Page breaks**: Orphaned headings? Sections starting where they should?
8. **Colors**: Palette applied consistently throughout?

If you find problems, go back to Step 3 (edit the HTML) and reconvert. That's exactly why the intermediate HTML exists.

### Metadata validation

```python
from pypdf import PdfReader

reader = PdfReader(pdf_path)
meta = reader.metadata
print(f"Title: {meta.title}")
print(f"Author: {meta.author}")
print(f"Pages: {len(reader.pages)}")
```

WeasyPrint automatically picks up `<title>` and `<meta name="author">` from the HTML.

## Troubleshooting

**"Font didn't load"**: Check the Google Fonts URL. Use a font stack with fallbacks: `font-family: "Inter", "Helvetica Neue", Arial, sans-serif;`

**"Table got cut between pages"**: If the table is too large for a single page, make sure `thead { display: table-header-group; }` is active. For very long tables (2+ pages), remove `page-break-inside: avoid` from the table and let the header repeat naturally.

**"Image doesn't show"**: Convert to base64 if it's a local file. Remote URLs must be accessible during conversion.

**"Layout looks wrong"**: Most common cause is CSS Grid. Switch to flexbox. Second most common is `position: fixed` — use @page margins instead.

**"Different header/footer per section"**: Use named @page rules:
```css
@page chapter { @top-center { content: "Chapter X"; } }
.chapter { page: chapter; }
```

## Common sense

If the user asks for something simple ("generate a PDF with this table"), don't run through the full process with questions at every step. Use the corporate palette, generate the HTML, convert, and verify. Only ask when there's real ambiguity.

The pipeline exists to ensure quality, not to bureaucratize trivial tasks.
