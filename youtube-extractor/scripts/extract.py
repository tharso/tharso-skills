#!/usr/bin/env python3
"""
YouTube Video Extractor
Extracts metadata and transcript from a YouTube video URL.
Outputs a structured Markdown file in pt-BR.

Usage:
    python extract.py <youtube_url> [--output <path>] [--gemini-key <key>] [--lang <lang>]

Dependencies:
    pip install yt-dlp youtube-transcript-api google-genai
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path


def parse_youtube_url(url: str) -> str | None:
    """Extract video ID from various YouTube URL formats."""
    patterns = [
        r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/|youtube\.com/v/|youtube\.com/shorts/)([a-zA-Z0-9_-]{11})',
        r'^([a-zA-Z0-9_-]{11})$',  # bare video ID
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def extract_metadata(url: str) -> dict:
    """Extract video metadata using yt-dlp (no download)."""
    import yt_dlp

    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'skip_download': True,
        'no_check_certificates': True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)

    # Parse upload date
    upload_date_raw = info.get('upload_date', '')
    if upload_date_raw:
        try:
            upload_date = datetime.strptime(upload_date_raw, '%Y%m%d').strftime('%d/%m/%Y')
        except ValueError:
            upload_date = upload_date_raw
    else:
        upload_date = 'Desconhecida'

    # Format duration
    duration_secs = info.get('duration', 0)
    if duration_secs:
        hours, remainder = divmod(int(duration_secs), 3600)
        minutes, seconds = divmod(remainder, 60)
        if hours > 0:
            duration = f'{hours}h {minutes}min {seconds}s'
        else:
            duration = f'{minutes}min {seconds}s'
    else:
        duration = 'Desconhecida'

    # Format view count
    view_count = info.get('view_count', 0)
    if view_count:
        if view_count >= 1_000_000:
            views_str = f'{view_count/1_000_000:.1f}M visualizações'
        elif view_count >= 1_000:
            views_str = f'{view_count/1_000:.1f}K visualizações'
        else:
            views_str = f'{view_count} visualizações'
    else:
        views_str = 'Desconhecido'

    return {
        'title': info.get('title', 'Sem título'),
        'channel': info.get('channel', info.get('uploader', 'Desconhecido')),
        'channel_url': info.get('channel_url', info.get('uploader_url', '')),
        'upload_date': upload_date,
        'upload_date_raw': upload_date_raw,
        'duration': duration,
        'duration_secs': duration_secs,
        'view_count': view_count,
        'views_str': views_str,
        'like_count': info.get('like_count', 0),
        'description': info.get('description', ''),
        'tags': info.get('tags', []),
        'categories': info.get('categories', []),
        'language': info.get('language', ''),
        'thumbnail': info.get('thumbnail', ''),
        'video_id': info.get('id', ''),
        'url': info.get('webpage_url', url),
    }


def extract_transcript(video_id: str, preferred_lang: str = 'pt') -> dict:
    """
    Extract transcript using youtube-transcript-api v1.x.
    The new API requires instantiation: YouTubeTranscriptApi().
    Methods: .list(video_id) and .fetch(video_id, languages=[...]).
    Tries in order: preferred_lang, pt-BR, pt, en, then any available.
    Returns dict with 'text', 'language', 'is_auto_generated', 'success'.
    """
    from youtube_transcript_api import YouTubeTranscriptApi

    result = {
        'text': '',
        'language': '',
        'is_auto_generated': False,
        'success': False,
        'segments': [],
    }

    ytt = YouTubeTranscriptApi()

    # Build language priority list
    lang_priority = [preferred_lang]
    if preferred_lang == 'pt':
        lang_priority.extend(['pt-BR', 'pt', 'en', 'es'])
    elif preferred_lang == 'pt-BR':
        lang_priority.extend(['pt', 'en', 'es'])
    else:
        lang_priority.extend(['pt-BR', 'pt', 'en', 'es'])
    # Deduplicate while preserving order
    seen = set()
    lang_priority = [x for x in lang_priority if not (x in seen or seen.add(x))]

    try:
        # Try fetching with language priority (the API picks the best match)
        fetched = ytt.fetch(video_id, languages=lang_priority)
        result['language'] = fetched.language_code
        result['is_auto_generated'] = fetched.is_generated
        result['segments'] = [
            {
                'start': s.start,
                'duration': s.duration,
                'text': s.text,
            }
            for s in fetched.snippets
        ]
        result['text'] = ' '.join(s.text for s in fetched.snippets)
        result['success'] = True

    except Exception:
        # If preferred languages fail, try fetching any available transcript
        try:
            transcript_list = ytt.list(video_id)
            # Pick the first available one
            first_available = None
            for t in transcript_list:
                first_available = t
                break

            if first_available:
                fetched = ytt.fetch(video_id, languages=[first_available.language_code])
                result['language'] = fetched.language_code
                result['is_auto_generated'] = fetched.is_generated
                result['segments'] = [
                    {
                        'start': s.start,
                        'duration': s.duration,
                        'text': s.text,
                    }
                    for s in fetched.snippets
                ]
                result['text'] = ' '.join(s.text for s in fetched.snippets)
                result['success'] = True

        except Exception as e:
            result['error'] = str(e)

    return result


def extract_with_gemini(video_url: str, api_key: str, max_retries: int = 2) -> dict:
    """
    Use Gemini API to extract content from a YouTube video.
    Gemini can process YouTube URLs directly.
    Retries on rate limit (429) with exponential backoff.
    """
    import time
    from google import genai

    result = {
        'text': '',
        'success': False,
        'method': 'gemini',
    }

    client = genai.Client(api_key=api_key)

    prompt = """Assista este vídeo do YouTube e forneça uma transcrição completa e detalhada
do conteúdo falado no vídeo, em português brasileiro (pt-BR).

Se o vídeo estiver em outro idioma, traduza para pt-BR.

Forneça APENAS a transcrição/conteúdo, sem comentários adicionais ou formatação especial.
Seja o mais fiel possível ao conteúdo original."""

    for attempt in range(max_retries + 1):
        try:
            response = client.models.generate_content(
                model='gemini-2.0-flash',
                contents=[
                    {
                        'file_data': {
                            'file_uri': video_url,
                        }
                    },
                    prompt,
                ],
            )

            if response.text:
                result['text'] = response.text.strip()
                result['success'] = True
                return result

        except Exception as e:
            error_str = str(e)
            # Retry on rate limit errors
            if '429' in error_str and attempt < max_retries:
                wait_time = 20 * (attempt + 1)  # 20s, 40s
                print(f"    ⏳ Rate limit, aguardando {wait_time}s... (tentativa {attempt + 1}/{max_retries})")
                time.sleep(wait_time)
                continue
            result['error'] = error_str

    return result


def format_timestamp(seconds: float) -> str:
    """Format seconds into HH:MM:SS or MM:SS."""
    hours, remainder = divmod(int(seconds), 3600)
    minutes, secs = divmod(remainder, 60)
    if hours > 0:
        return f'{hours:02d}:{minutes:02d}:{secs:02d}'
    return f'{minutes:02d}:{secs:02d}'


def build_markdown(metadata: dict, transcript: dict, include_timestamps: bool = False) -> str:
    """Build the final Markdown document."""
    lines = []

    # Header
    lines.append(f"# {metadata['title']}")
    lines.append('')

    # Metadata table
    lines.append('## Informações do vídeo')
    lines.append('')
    lines.append(f"| Campo | Valor |")
    lines.append(f"| --- | --- |")
    lines.append(f"| **Canal** | [{metadata['channel']}]({metadata['channel_url']}) |")
    lines.append(f"| **Data de publicação** | {metadata['upload_date']} |")
    lines.append(f"| **Duração** | {metadata['duration']} |")
    lines.append(f"| **Visualizações** | {metadata['views_str']} |")
    if metadata.get('like_count'):
        likes = metadata['like_count']
        if likes >= 1000:
            likes_str = f'{likes/1000:.1f}K'
        else:
            likes_str = str(likes)
        lines.append(f"| **Likes** | {likes_str} |")
    lines.append(f"| **URL** | {metadata['url']} |")
    if metadata.get('language'):
        lines.append(f"| **Idioma original** | {metadata['language']} |")
    lines.append('')

    # Tags
    if metadata.get('tags'):
        tags_str = ', '.join(f'`{t}`' for t in metadata['tags'][:20])
        lines.append(f"**Tags:** {tags_str}")
        lines.append('')

    # Categories
    if metadata.get('categories'):
        lines.append(f"**Categorias:** {', '.join(metadata['categories'])}")
        lines.append('')

    # Description
    if metadata.get('description'):
        lines.append('## Descrição original')
        lines.append('')
        lines.append(metadata['description'])
        lines.append('')

    # Transcript
    lines.append('## Conteúdo do vídeo (transcrição)')
    lines.append('')

    if transcript.get('success') and transcript.get('text'):
        # Source info
        method = transcript.get('method', 'youtube-transcript-api')
        if method == 'gemini':
            source = 'Gemini AI'
        elif transcript.get('is_auto_generated'):
            source = f"Legendas automáticas ({transcript.get('language', 'N/A')})"
        else:
            source = f"Legendas manuais ({transcript.get('language', 'N/A')})"

        lines.append(f"*Fonte: {source}*")
        lines.append('')

        if include_timestamps and transcript.get('segments'):
            # Timestamped version
            for seg in transcript['segments']:
                ts = format_timestamp(seg['start'])
                lines.append(f"**[{ts}]** {seg['text']}")
            lines.append('')
        else:
            # Flowing text, broken into paragraphs every ~500 chars
            text = transcript['text']
            # Try to break on sentence boundaries
            sentences = re.split(r'(?<=[.!?])\s+', text)
            paragraph = []
            char_count = 0
            for sentence in sentences:
                paragraph.append(sentence)
                char_count += len(sentence)
                if char_count >= 500:
                    lines.append(' '.join(paragraph))
                    lines.append('')
                    paragraph = []
                    char_count = 0
            if paragraph:
                lines.append(' '.join(paragraph))
                lines.append('')
    else:
        error = transcript.get('error', 'Motivo desconhecido')
        lines.append(f"*Transcrição não disponível. {error}*")
        lines.append('')

    # Footer
    lines.append('---')
    date_str = datetime.now().strftime("%d/%m/%Y às %H:%M")
    lines.append(f"*Extraído em {date_str} via youtube-extractor skill*")

    return '\n'.join(lines)


def slugify(text: str, max_len: int = 60) -> str:
    """Create a filename-safe slug from text."""
    # Remove accents (simple approach)
    text = text.lower().strip()
    text = re.sub(r'[àáâãäå]', 'a', text)
    text = re.sub(r'[èéêë]', 'e', text)
    text = re.sub(r'[ìíîï]', 'i', text)
    text = re.sub(r'[òóôõö]', 'o', text)
    text = re.sub(r'[ùúûü]', 'u', text)
    text = re.sub(r'[ñ]', 'n', text)
    text = re.sub(r'[ç]', 'c', text)
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'[\s-]+', '-', text)
    return text[:max_len].strip('-')


def main():
    parser = argparse.ArgumentParser(description='Extract YouTube video content to Markdown')
    parser.add_argument('url', help='YouTube video URL or ID')
    parser.add_argument('--output', '-o', help='Output file path (default: auto-generated)')
    parser.add_argument('--output-dir', '-d', help='Output directory (default: current)')
    parser.add_argument('--gemini-key', help='Gemini API key for fallback extraction')
    parser.add_argument('--lang', default='pt', help='Preferred transcript language (default: pt)')
    parser.add_argument('--timestamps', action='store_true', help='Include timestamps in transcript')
    parser.add_argument('--json', action='store_true', help='Also output raw data as JSON')
    parser.add_argument('--raw-json', action='store_true',
                        help='Output only raw JSON to stdout (for piping to Claude)')

    args = parser.parse_args()

    # Raw JSON mode: output structured data to stdout and exit
    if args.raw_json:
        video_id = parse_youtube_url(args.url)
        if not video_id:
            json.dump({'error': f'URL inválida: {args.url}'}, sys.stdout, ensure_ascii=False)
            sys.exit(1)
        url = f'https://www.youtube.com/watch?v={video_id}'
        try:
            metadata = extract_metadata(url)
        except Exception as e:
            json.dump({'error': f'Metadados: {e}'}, sys.stdout, ensure_ascii=False)
            sys.exit(1)
        transcript = extract_transcript(video_id, preferred_lang=args.lang)
        if not transcript['success']:
            gemini_key = args.gemini_key or os.environ.get('GEMINI_API_KEY', '')
            if gemini_key:
                transcript = extract_with_gemini(url, gemini_key)
        output = {
            'metadata': metadata,
            'transcript': {
                'text': transcript.get('text', ''),
                'language': transcript.get('language', ''),
                'is_auto_generated': transcript.get('is_auto_generated', False),
                'success': transcript.get('success', False),
                'method': transcript.get('method', 'youtube-transcript-api'),
                'segments': transcript.get('segments', []),
            },
        }
        json.dump(output, sys.stdout, ensure_ascii=False, indent=2)
        sys.exit(0)

    # Parse URL
    video_id = parse_youtube_url(args.url)
    if not video_id:
        print(f"ERRO: URL inválida: {args.url}", file=sys.stderr)
        sys.exit(1)

    url = f'https://www.youtube.com/watch?v={video_id}'
    print(f"Extraindo vídeo: {video_id}")

    # Step 1: Metadata
    print("  [1/3] Extraindo metadados...")
    try:
        metadata = extract_metadata(url)
        print(f"  ✓ Título: {metadata['title']}")
        print(f"  ✓ Canal: {metadata['channel']}")
        print(f"  ✓ Data: {metadata['upload_date']}")
    except Exception as e:
        print(f"  ERRO ao extrair metadados: {e}", file=sys.stderr)
        sys.exit(1)

    # Step 2: Transcript
    print("  [2/3] Extraindo transcrição...")
    transcript = extract_transcript(video_id, preferred_lang=args.lang)

    if transcript['success']:
        word_count = len(transcript['text'].split())
        auto_tag = " (auto-gerada)" if transcript['is_auto_generated'] else ""
        print(f"  ✓ Transcrição obtida: {word_count} palavras, idioma: {transcript.get('language', '?')}{auto_tag}")
    else:
        print(f"  ✗ Transcrição não encontrada via YouTube")
        # Try Gemini fallback
        gemini_key = args.gemini_key or os.environ.get('GEMINI_API_KEY', '')
        if gemini_key:
            print("  [2b/3] Tentando Gemini como fallback...")
            transcript = extract_with_gemini(url, gemini_key)
            if transcript['success']:
                word_count = len(transcript['text'].split())
                print(f"  ✓ Transcrição via Gemini: {word_count} palavras")
            else:
                print(f"  ✗ Gemini também falhou: {transcript.get('error', '?')}")
        else:
            print("  ℹ Sem chave Gemini configurada. Use --gemini-key ou GEMINI_API_KEY para fallback.")

    # Step 3: Build Markdown
    print("  [3/3] Gerando Markdown...")
    md_content = build_markdown(metadata, transcript, include_timestamps=args.timestamps)

    # Determine output path
    if args.output:
        output_path = Path(args.output)
    else:
        slug = slugify(metadata['title'])
        filename = f"{slug}.md"
        output_dir = Path(args.output_dir) if args.output_dir else Path('.')
        output_path = output_dir / filename

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(md_content, encoding='utf-8')
    print(f"\n✅ Arquivo salvo: {output_path}")

    # Optional JSON output
    if args.json:
        json_path = output_path.with_suffix('.json')
        json_data = {
            'metadata': metadata,
            'transcript': {
                'text': transcript.get('text', ''),
                'language': transcript.get('language', ''),
                'is_auto_generated': transcript.get('is_auto_generated', False),
                'success': transcript.get('success', False),
                'method': transcript.get('method', 'youtube-transcript-api'),
                'word_count': len(transcript.get('text', '').split()) if transcript.get('text') else 0,
            },
            'extracted_at': datetime.now().isoformat(),
        }
        json_path.write_text(json.dumps(json_data, ensure_ascii=False, indent=2), encoding='utf-8')
        print(f"✅ JSON salvo: {json_path}")

    # Print summary
    print(f"\n--- Resumo ---")
    print(f"Título: {metadata['title']}")
    print(f"Canal: {metadata['channel']}")
    print(f"Duração: {metadata['duration']}")
    print(f"Transcrição: {'Sim' if transcript.get('success') else 'Não'}")
    if transcript.get('success'):
        print(f"Palavras: {len(transcript.get('text', '').split())}")

    return str(output_path)


if __name__ == '__main__':
    main()
