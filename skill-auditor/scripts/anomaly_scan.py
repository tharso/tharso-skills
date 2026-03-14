#!/usr/bin/env python3
"""
Anomaly Scanner for Skill Auditor
Scans skill files for suspicious patterns, obfuscated content, and misidentified files.
Read-only analysis — does not modify anything.

Usage:
    python anomaly_scan.py <skill_directory> [--json]
"""

import argparse
import base64
import json
import mimetypes
import os
import re
import struct
import sys
from pathlib import Path

# --- Magic bytes for common file types ---
MAGIC_BYTES = {
    b'\x89PNG': 'image/png',
    b'\xff\xd8\xff': 'image/jpeg',
    b'GIF87a': 'image/gif',
    b'GIF89a': 'image/gif',
    b'%PDF': 'application/pdf',
    b'PK\x03\x04': 'application/zip',
    b'\x1f\x8b': 'application/gzip',
    b'RIFF': 'audio/wav',  # or webp — needs further check
    b'\x00\x00\x01\x00': 'image/x-icon',
}

# --- Suspicious patterns in code/text files ---
SUSPICIOUS_PATTERNS = [
    # Code execution
    (r'\beval\s*\(', 'eval() call — dynamic code execution', 'CRÍTICO'),
    (r'\bexec\s*\(', 'exec() call — dynamic code execution', 'CRÍTICO'),
    (r'\b__import__\s*\(', '__import__() — dynamic module import', 'CRÍTICO'),
    (r'\bcompile\s*\(', 'compile() — dynamic code compilation', 'MÉDIO'),
    (r'\bgetattr\s*\(.*,\s*["\']__', 'getattr with dunder — potential sandbox escape', 'CRÍTICO'),

    # System access
    (r'\bos\.system\s*\(', 'os.system() — shell command execution', 'CRÍTICO'),
    (r'\bos\.popen\s*\(', 'os.popen() — shell command execution', 'CRÍTICO'),
    (r'\bsubprocess\b', 'subprocess module — shell command execution', 'MÉDIO'),
    (r'\bos\.environ\b', 'os.environ access — reads environment variables', 'MÉDIO'),
    (r'\bos\.getenv\s*\(', 'os.getenv() — reads environment variable', 'MÉDIO'),
    (r'\bshutil\.rmtree\s*\(', 'shutil.rmtree() — recursive directory deletion', 'CRÍTICO'),
    (r'\bos\.remove\s*\(', 'os.remove() — file deletion', 'MÉDIO'),
    (r'\bos\.unlink\s*\(', 'os.unlink() — file deletion', 'MÉDIO'),

    # Network access
    (r'\brequests\.(get|post|put|delete|patch|head)\s*\(', 'HTTP request via requests library', 'MÉDIO'),
    (r'\bhttpx\.(get|post|put|delete|patch|head|AsyncClient|Client)\b', 'HTTP request via httpx', 'MÉDIO'),
    (r'\burllib\.request\b', 'urllib network access', 'MÉDIO'),
    (r'\bsocket\b', 'socket module — low-level network access', 'CRÍTICO'),
    (r'\bhttp\.client\b', 'http.client — direct HTTP connections', 'MÉDIO'),
    (r'\baiohttp\b', 'aiohttp — async HTTP client', 'MÉDIO'),

    # Encoding/obfuscation
    (r'\bbase64\.b64decode\s*\(', 'base64 decode — potential payload deobfuscation', 'CRÍTICO'),
    (r'\bbase64\.b64encode\s*\(', 'base64 encode — potential data encoding for exfil', 'MÉDIO'),
    (r'\bcodecs\.decode\s*\(', 'codecs.decode — potential deobfuscation', 'MÉDIO'),
    (r'\bbytes\.fromhex\s*\(', 'bytes.fromhex — hex-encoded payload', 'CRÍTICO'),
    (r'\bchr\s*\(\s*\d+\s*\)', 'chr() with number — character-by-character string construction', 'MÉDIO'),
    (r'\\x[0-9a-fA-F]{2}(?:\\x[0-9a-fA-F]{2}){5,}', 'long hex escape sequence — obfuscated string', 'MÉDIO'),

    # File system traversal
    (r'\.\./\.\./', 'path traversal pattern (../../)', 'CRÍTICO'),
    (r'~/', 'home directory reference', 'BAIXO'),
    (r'/etc/', 'system config directory reference', 'MÉDIO'),
    (r'\.ssh/', 'SSH directory reference', 'CRÍTICO'),
    (r'\.aws/', 'AWS credentials directory reference', 'CRÍTICO'),
    (r'\.env\b', '.env file reference — potential secrets', 'MÉDIO'),
    (r'CLAUDE\.md', 'CLAUDE.md reference — system context file', 'MÉDIO'),

    # Prompt injection patterns (in non-SKILL.md files)
    (r'(?i)ignore\s+(all\s+)?previous\s+instructions', 'prompt injection pattern — instruction override', 'CRÍTICO'),
    (r'(?i)you\s+are\s+now\s+', 'prompt injection pattern — role reassignment', 'CRÍTICO'),
    (r'(?i)system\s*:\s*', 'system prompt mimicry', 'MÉDIO'),
    (r'(?i)IMPORTANT:\s*override', 'instruction override attempt', 'CRÍTICO'),
    (r'(?i)disregard\s+(all\s+)?(prior|previous|above)', 'prompt injection — disregard instructions', 'CRÍTICO'),
]

# --- Patterns specifically for SKILL.md (different severity context) ---
SKILLMD_SUSPICIOUS = [
    (r'(?i)read.*CLAUDE\.md', 'skill reads CLAUDE.md — accesses system context', 'MÉDIO'),
    (r'(?i)read.*\.env', 'skill reads .env — accesses secrets', 'CRÍTICO'),
    (r'(?i)(list|read|scan).*installed.*skills', 'skill enumerates other installed skills', 'CRÍTICO'),
    (r'(?i)send.*to.*(api|server|endpoint|webhook|url)', 'skill sends data to external service', 'MÉDIO'),
    (r'(?i)curl\s+-.*-d\s', 'curl with data flag — sends data externally', 'CRÍTICO'),
    (r'(?i)wget\s+--post', 'wget POST — sends data externally', 'CRÍTICO'),
    (r'(?i)nc\s+-', 'netcat usage', 'CRÍTICO'),
]


def detect_file_type(filepath: Path) -> dict:
    """Check if a file's actual content matches its extension."""
    result = {
        'path': str(filepath),
        'extension': filepath.suffix,
        'declared_type': mimetypes.guess_type(str(filepath))[0] or 'unknown',
        'actual_type': 'unknown',
        'mismatch': False,
        'is_binary': False,
        'is_executable': False,
    }

    try:
        with open(filepath, 'rb') as f:
            header = f.read(16)
    except (PermissionError, OSError):
        result['error'] = 'cannot read file'
        return result

    if not header:
        result['actual_type'] = 'empty'
        return result

    # Check magic bytes
    for magic, ftype in MAGIC_BYTES.items():
        if header.startswith(magic):
            result['actual_type'] = ftype
            result['is_binary'] = True
            break

    # Check for shebang
    if header.startswith(b'#!'):
        result['is_executable'] = True
        try:
            with open(filepath, 'r', errors='replace') as f:
                first_line = f.readline().strip()
            result['shebang'] = first_line
        except Exception:
            pass

    # Check for executable permission
    if os.access(filepath, os.X_OK):
        result['is_executable'] = True

    # Detect mismatch
    text_extensions = {'.md', '.txt', '.json', '.yaml', '.yml', '.toml', '.csv', '.html', '.css', '.xml'}
    if filepath.suffix in text_extensions and result['is_binary']:
        result['mismatch'] = True

    image_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.ico', '.webp', '.svg'}
    if filepath.suffix in image_extensions and not result['is_binary'] and result['actual_type'] == 'unknown':
        # Could be a text file masquerading as image
        try:
            with open(filepath, 'r') as f:
                content = f.read(200)
            if any(keyword in content.lower() for keyword in ['import ', 'def ', 'class ', 'function ', '#!/']):
                result['mismatch'] = True
                result['actual_type'] = 'text/script-disguised-as-image'
        except UnicodeDecodeError:
            pass  # Actually binary, probably fine

    return result


def scan_text_content(filepath: Path, is_skill_md: bool = False) -> list:
    """Scan a text file for suspicious patterns."""
    findings = []

    try:
        with open(filepath, 'r', errors='replace') as f:
            content = f.read()
    except (PermissionError, OSError):
        return [{'pattern': 'file unreadable', 'severity': 'MÉDIO', 'line': 0}]

    lines = content.split('\n')
    patterns = SUSPICIOUS_PATTERNS + (SKILLMD_SUSPICIOUS if is_skill_md else [])

    for pattern, description, severity in patterns:
        # For prompt injection patterns, skip SKILL.md itself (it's expected to discuss these)
        if 'prompt injection' in description and is_skill_md:
            continue

        for i, line in enumerate(lines, 1):
            if re.search(pattern, line):
                findings.append({
                    'pattern': description,
                    'severity': severity,
                    'line': i,
                    'context': line.strip()[:120],
                })

    # Check for embedded base64 blobs (>100 chars of base64-looking content)
    b64_pattern = re.compile(r'[A-Za-z0-9+/=]{100,}')
    for i, line in enumerate(lines, 1):
        matches = b64_pattern.findall(line)
        for match in matches:
            try:
                decoded = base64.b64decode(match)
                # If it decodes successfully and contains text-like content
                if any(c < 32 and c not in (9, 10, 13) for c in decoded[:50]):
                    desc = 'embedded base64 blob decoding to binary data'
                else:
                    desc = 'embedded base64 blob decoding to text'
                findings.append({
                    'pattern': desc,
                    'severity': 'CRÍTICO',
                    'line': i,
                    'context': f'base64 blob ({len(match)} chars)',
                    'decoded_preview': decoded[:80].decode('utf-8', errors='replace'),
                })
            except Exception:
                pass  # Not valid base64, ignore

    return findings


def scan_skill(skill_dir: str) -> dict:
    """Run full anomaly scan on a skill directory."""
    skill_path = Path(skill_dir)
    if not skill_path.is_dir():
        return {'error': f'Not a directory: {skill_dir}'}

    results = {
        'skill_dir': str(skill_path),
        'files': [],
        'findings': [],
        'summary': {
            'total_files': 0,
            'binary_files': 0,
            'executable_files': 0,
            'type_mismatches': 0,
            'suspicious_patterns': {'CRÍTICO': 0, 'MÉDIO': 0, 'BAIXO': 0},
        },
    }

    # Scan all files
    for filepath in sorted(skill_path.rglob('*')):
        if filepath.is_dir():
            continue
        if filepath.name == '.DS_Store':
            continue

        results['summary']['total_files'] += 1
        rel_path = filepath.relative_to(skill_path)

        # File type detection
        file_info = detect_file_type(filepath)
        results['files'].append(file_info)

        if file_info.get('is_binary'):
            results['summary']['binary_files'] += 1

        if file_info.get('is_executable'):
            results['summary']['executable_files'] += 1
            results['findings'].append({
                'file': str(rel_path),
                'type': 'executable_file',
                'severity': 'MÉDIO',
                'description': f'File is executable: {file_info.get("shebang", "no shebang")}',
            })

        if file_info.get('mismatch'):
            results['summary']['type_mismatches'] += 1
            results['findings'].append({
                'file': str(rel_path),
                'type': 'type_mismatch',
                'severity': 'CRÍTICO',
                'description': f'File type mismatch: extension is {filepath.suffix} but content is {file_info["actual_type"]}',
            })

        # Text content scanning (skip binary files)
        if not file_info.get('is_binary'):
            is_skill_md = filepath.name == 'SKILL.md'
            text_findings = scan_text_content(filepath, is_skill_md=is_skill_md)
            for finding in text_findings:
                sev = finding['severity']
                results['summary']['suspicious_patterns'][sev] = \
                    results['summary']['suspicious_patterns'].get(sev, 0) + 1
                results['findings'].append({
                    'file': str(rel_path),
                    'type': 'suspicious_pattern',
                    'severity': sev,
                    'line': finding['line'],
                    'description': finding['pattern'],
                    'context': finding.get('context', ''),
                    'decoded_preview': finding.get('decoded_preview', ''),
                })

    return results


def format_text_report(results: dict) -> str:
    """Format results as human-readable text."""
    lines = []
    lines.append('=' * 60)
    lines.append('ANOMALY SCAN REPORT')
    lines.append('=' * 60)
    lines.append(f'Skill: {results["skill_dir"]}')
    lines.append(f'Files scanned: {results["summary"]["total_files"]}')
    lines.append(f'Binary files: {results["summary"]["binary_files"]}')
    lines.append(f'Executable files: {results["summary"]["executable_files"]}')
    lines.append(f'Type mismatches: {results["summary"]["type_mismatches"]}')
    lines.append('')

    pats = results['summary']['suspicious_patterns']
    lines.append(f'Suspicious patterns: {pats.get("CRÍTICO", 0)} CRÍTICO, {pats.get("MÉDIO", 0)} MÉDIO, {pats.get("BAIXO", 0)} BAIXO')
    lines.append('')

    if not results['findings']:
        lines.append('No anomalies detected.')
    else:
        lines.append('-' * 60)
        # Sort: CRÍTICO first
        severity_order = {'CRÍTICO': 0, 'MÉDIO': 1, 'BAIXO': 2}
        sorted_findings = sorted(results['findings'], key=lambda f: severity_order.get(f['severity'], 3))

        for f in sorted_findings:
            lines.append(f'[{f["severity"]}] {f["file"]}' + (f':{f["line"]}' if f.get('line') else ''))
            lines.append(f'  {f["description"]}')
            if f.get('context'):
                lines.append(f'  > {f["context"]}')
            if f.get('decoded_preview'):
                lines.append(f'  decoded: {f["decoded_preview"]}')
            lines.append('')

    lines.append('=' * 60)
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description='Anomaly scanner for skill auditor')
    parser.add_argument('skill_dir', help='Path to the skill directory')
    parser.add_argument('--json', action='store_true', help='Output as JSON')
    args = parser.parse_args()

    results = scan_skill(args.skill_dir)

    if args.json:
        print(json.dumps(results, indent=2, ensure_ascii=False))
    else:
        print(format_text_report(results))

    # Exit code based on findings
    if results.get('error'):
        sys.exit(2)
    crit = results['summary']['suspicious_patterns'].get('CRÍTICO', 0)
    crit += results['summary']['type_mismatches']
    if crit > 0:
        sys.exit(1)
    sys.exit(0)


if __name__ == '__main__':
    main()
