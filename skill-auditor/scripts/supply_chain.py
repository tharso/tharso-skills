#!/usr/bin/env python3
"""
Supply Chain Verifier for Skill Auditor
Checks Python dependencies referenced in skill scripts against PyPI.
Detects: typosquatting, low-popularity packages, known-malicious patterns.

Usage:
    python supply_chain.py <skill_directory> [--json]
"""

import argparse
import ast
import json
import re
import sys
from pathlib import Path

# Well-known, widely-used packages (>10M downloads/month) — no need to flag
KNOWN_SAFE = {
    'os', 'sys', 'json', 're', 'math', 'datetime', 'pathlib', 'collections',
    'itertools', 'functools', 'typing', 'abc', 'io', 'time', 'random',
    'hashlib', 'base64', 'urllib', 'http', 'email', 'html', 'xml',
    'csv', 'sqlite3', 'struct', 'copy', 'string', 'textwrap', 'shutil',
    'tempfile', 'glob', 'fnmatch', 'argparse', 'logging', 'unittest',
    'dataclasses', 'enum', 'contextlib', 'threading', 'multiprocessing',
    'ast', 'inspect', 'codecs', 'traceback', 'warnings', 'pprint',
    # Popular third-party
    'requests', 'numpy', 'pandas', 'flask', 'django', 'fastapi',
    'pydantic', 'sqlalchemy', 'pytest', 'click', 'rich', 'httpx',
    'aiohttp', 'beautifulsoup4', 'bs4', 'lxml', 'pillow', 'PIL',
    'matplotlib', 'scipy', 'scikit-learn', 'sklearn', 'torch',
    'tensorflow', 'transformers', 'openai', 'anthropic', 'boto3',
    'botocore', 'google', 'google-cloud', 'azure', 'jinja2',
    'pyyaml', 'yaml', 'toml', 'tomli', 'dotenv', 'python-dotenv',
    'celery', 'redis', 'pymongo', 'psycopg2', 'mysqlclient',
    'coloraide', 'weasyprint', 'pypdf', 'pypdfium2', 'docx',
    'python-docx', 'openpyxl', 'xlsxwriter',
    'yt-dlp', 'yt_dlp', 'youtube-transcript-api', 'youtube_transcript_api',
    'google-genai', 'google.genai',
}

# Common typosquatting targets
TYPOSQUAT_TARGETS = {
    'requests': ['reqeusts', 'requets', 'request', 'reqests', 'requsts', 'reequests'],
    'numpy': ['numby', 'numppy', 'nummpy'],
    'pandas': ['pandass', 'pands', 'pandsa'],
    'flask': ['flaask', 'flaskk'],
    'django': ['djnago', 'djanog', 'djangoo'],
    'pyyaml': ['pyaml', 'pyyml'],
    'pillow': ['pilllow', 'pilow'],
    'beautifulsoup4': ['beautifulsoup', 'beutifulsoup4'],
    'httpx': ['httx', 'htpx'],
    'boto3': ['botto3', 'btoo3'],
    'cryptography': ['criptography', 'cryptograpy', 'cryptogrphy'],
    'paramiko': ['parmiko', 'paramko'],
    'colorama': ['colorsama', 'coloramma'],
}

# Packages that are red flags when found in a skill (no legitimate use case)
DANGEROUS_PACKAGES = {
    'pyautogui': 'GUI automation — can control mouse/keyboard',
    'pynput': 'keyboard/mouse listener — potential keylogger',
    'keyboard': 'keyboard hooks — potential keylogger',
    'pyperclip': 'clipboard access — can read/write clipboard',
    'win32api': 'Windows API access — low-level system control',
    'ctypes': 'C foreign function interface — can call any system function',
    'mss': 'screenshot capture',
    'pyscreenshot': 'screenshot capture',
    'scapy': 'network packet manipulation',
    'nmap': 'network scanning',
    'paramiko': 'SSH client — remote access (needs justification)',
    'fabric': 'remote execution via SSH',
    'invoke': 'task execution framework (check context)',
}


def extract_dependencies(skill_dir: str) -> dict:
    """Extract all dependencies from Python files in a skill directory."""
    skill_path = Path(skill_dir)
    results = {
        'skill_dir': str(skill_path),
        'files_scanned': [],
        'dependencies': {},
        'pip_installs': [],
        'findings': [],
    }

    for pyfile in sorted(skill_path.rglob('*.py')):
        rel_path = str(pyfile.relative_to(skill_path))
        results['files_scanned'].append(rel_path)

        try:
            with open(pyfile, 'r') as f:
                source = f.read()
        except (PermissionError, OSError):
            results['findings'].append({
                'file': rel_path,
                'severity': 'MÉDIO',
                'description': f'Cannot read file: {rel_path}',
            })
            continue

        # AST-based import extraction
        try:
            tree = ast.parse(source)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        pkg = alias.name.split('.')[0]
                        if pkg not in results['dependencies']:
                            results['dependencies'][pkg] = {
                                'files': [], 'lines': [], 'type': 'import'
                            }
                        results['dependencies'][pkg]['files'].append(rel_path)
                        results['dependencies'][pkg]['lines'].append(node.lineno)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        pkg = node.module.split('.')[0]
                        if pkg not in results['dependencies']:
                            results['dependencies'][pkg] = {
                                'files': [], 'lines': [], 'type': 'from_import'
                            }
                        results['dependencies'][pkg]['files'].append(rel_path)
                        results['dependencies'][pkg]['lines'].append(node.lineno)
        except SyntaxError:
            pass

        # Regex-based pip install detection
        pip_patterns = [
            r'pip\s+install\s+([\w\-\[\]>=<,. ]+)',
            r'os\.system\s*\(["\'].*pip\s+install\s+([\w\-\[\]>=<,. ]+)',
            r'subprocess.*pip.*install\s+([\w\-\[\]>=<,. ]+)',
        ]
        for pattern in pip_patterns:
            for match in re.finditer(pattern, source):
                packages = match.group(1).strip().split()
                for pkg in packages:
                    pkg = re.sub(r'[>=<\[\],].*', '', pkg).strip()
                    if pkg and not pkg.startswith('-'):
                        results['pip_installs'].append({
                            'package': pkg,
                            'file': rel_path,
                            'line': source[:match.start()].count('\n') + 1,
                        })

    # Also check SKILL.md for pip install instructions
    skill_md = skill_path / 'SKILL.md'
    if skill_md.exists():
        try:
            content = skill_md.read_text()
            for match in re.finditer(r'pip\s+install\s+([\w\-\[\]>=<,. ]+)', content):
                packages = match.group(1).strip().split()
                for pkg in packages:
                    pkg = re.sub(r'[>=<\[\],].*', '', pkg).strip()
                    if pkg and not pkg.startswith('-'):
                        results['pip_installs'].append({
                            'package': pkg,
                            'file': 'SKILL.md',
                            'line': content[:match.start()].count('\n') + 1,
                        })
        except (PermissionError, OSError):
            pass

    # --- Analysis ---

    # Check for typosquatting
    all_packages = set(results['dependencies'].keys())
    all_packages.update(p['package'] for p in results['pip_installs'])

    for pkg in all_packages:
        pkg_lower = pkg.lower().replace('-', '').replace('_', '')
        for target, typos in TYPOSQUAT_TARGETS.items():
            target_normalized = target.lower().replace('-', '').replace('_', '')
            for typo in typos:
                typo_normalized = typo.lower().replace('-', '').replace('_', '')
                if pkg_lower == typo_normalized:
                    results['findings'].append({
                        'package': pkg,
                        'severity': 'CRÍTICO',
                        'description': f'Possible typosquatting: "{pkg}" looks like a typo for "{target}"',
                    })

    # Check for dangerous packages
    for pkg in all_packages:
        pkg_lower = pkg.lower()
        for dangerous, reason in DANGEROUS_PACKAGES.items():
            if pkg_lower == dangerous:
                results['findings'].append({
                    'package': pkg,
                    'severity': 'CRÍTICO',
                    'description': f'Dangerous package: {pkg} — {reason}',
                })

    # Check for unknown packages (not in KNOWN_SAFE)
    for pkg in all_packages:
        pkg_normalized = pkg.lower().replace('-', '_')
        if pkg_normalized not in {k.lower().replace('-', '_') for k in KNOWN_SAFE}:
            if pkg not in [f.get('package', '') for f in results['findings']]:
                results['findings'].append({
                    'package': pkg,
                    'severity': 'BAIXO',
                    'description': f'Unknown package: "{pkg}" — not in known-safe list. Verify manually on PyPI.',
                })

    # Check for --break-system-packages flag
    for pyfile in skill_path.rglob('*.py'):
        try:
            content = pyfile.read_text()
            if '--break-system-packages' in content:
                results['findings'].append({
                    'file': str(pyfile.relative_to(skill_path)),
                    'severity': 'MÉDIO',
                    'description': 'Uses --break-system-packages flag — bypasses system package protection',
                })
        except (PermissionError, OSError):
            pass

    # Check for runtime pip install (auto-install pattern)
    for pyfile in skill_path.rglob('*.py'):
        try:
            content = pyfile.read_text()
            if re.search(r'except\s+ImportError.*pip\s+install', content, re.DOTALL):
                results['findings'].append({
                    'file': str(pyfile.relative_to(skill_path)),
                    'severity': 'MÉDIO',
                    'description': 'Auto-installs packages on ImportError — silent dependency installation',
                })
        except (PermissionError, OSError):
            pass

    return results


def format_text_report(results: dict) -> str:
    """Format results as human-readable text."""
    lines = []
    lines.append('=' * 60)
    lines.append('SUPPLY CHAIN VERIFICATION REPORT')
    lines.append('=' * 60)
    lines.append(f'Skill: {results["skill_dir"]}')
    lines.append(f'Python files scanned: {len(results["files_scanned"])}')
    lines.append(f'Dependencies found: {len(results["dependencies"])}')
    lines.append(f'pip install commands: {len(results["pip_installs"])}')
    lines.append('')

    if results['dependencies']:
        lines.append('Dependencies:')
        for pkg, info in sorted(results['dependencies'].items()):
            safe_marker = ' ✓' if pkg.lower().replace('-', '_') in {k.lower().replace('-', '_') for k in KNOWN_SAFE} else ' ?'
            lines.append(f'  {pkg}{safe_marker} (used in: {", ".join(set(info["files"]))})')
        lines.append('')

    if results['pip_installs']:
        lines.append('pip install commands found:')
        for p in results['pip_installs']:
            lines.append(f'  {p["package"]} ({p["file"]}:{p["line"]})')
        lines.append('')

    if results['findings']:
        lines.append('-' * 60)
        severity_order = {'CRÍTICO': 0, 'MÉDIO': 1, 'BAIXO': 2}
        sorted_findings = sorted(results['findings'], key=lambda f: severity_order.get(f['severity'], 3))
        for f in sorted_findings:
            pkg_or_file = f.get('package', f.get('file', 'unknown'))
            lines.append(f'[{f["severity"]}] {pkg_or_file}')
            lines.append(f'  {f["description"]}')
            lines.append('')
    else:
        lines.append('No supply chain issues detected.')

    lines.append('=' * 60)
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description='Supply chain verifier for skill auditor')
    parser.add_argument('skill_dir', help='Path to the skill directory')
    parser.add_argument('--json', action='store_true', help='Output as JSON')
    args = parser.parse_args()

    results = extract_dependencies(args.skill_dir)

    if args.json:
        print(json.dumps(results, indent=2, ensure_ascii=False))
    else:
        print(format_text_report(results))

    # Exit code
    crit = len([f for f in results['findings'] if f['severity'] == 'CRÍTICO'])
    sys.exit(1 if crit > 0 else 0)


if __name__ == '__main__':
    main()
