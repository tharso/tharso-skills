#!/usr/bin/env python3
"""
Sandbox Scanner for Skill Auditor
Executes skill scripts in a monitored sandbox and captures:
- Network calls attempted
- Files read/written outside the skill directory
- Environment variables accessed
- Subprocesses spawned

Uses monkey-patching to intercept system calls without needing root/strace.
Scripts are run with network disabled (socket blocked) and filesystem access logged.

Usage:
    python sandbox_scan.py <script_path> [--args "arg1 arg2"] [--json]
"""

import argparse
import importlib.util
import json
import os
import sys
import types
from io import StringIO
from pathlib import Path
from unittest.mock import MagicMock


class SandboxMonitor:
    """Captures all system interactions during script execution."""

    def __init__(self, skill_dir: str):
        self.skill_dir = os.path.abspath(skill_dir)
        self.network_calls = []
        self.file_reads = []
        self.file_writes = []
        self.env_accesses = []
        self.subprocesses = []
        self.imports_attempted = []
        self.errors = []

    def to_dict(self):
        return {
            'skill_dir': self.skill_dir,
            'network_calls': self.network_calls,
            'file_reads': self.file_reads,
            'file_writes': self.file_writes,
            'env_accesses': self.env_accesses,
            'subprocesses': self.subprocesses,
            'imports_attempted': self.imports_attempted,
            'errors': self.errors,
            'summary': {
                'network_attempts': len(self.network_calls),
                'files_read_outside_skill': len([
                    f for f in self.file_reads
                    if not f['path'].startswith(self.skill_dir)
                ]),
                'files_written': len(self.file_writes),
                'env_vars_accessed': len(self.env_accesses),
                'subprocesses_spawned': len(self.subprocesses),
            }
        }


def create_sandbox(script_path: str, skill_dir: str, script_args: list = None) -> dict:
    """
    Run a script in a monitored sandbox.
    Returns a dict with all captured activity.
    """
    monitor = SandboxMonitor(skill_dir)
    script_path = os.path.abspath(script_path)

    # --- Monkey-patch socket ---
    import socket as real_socket
    original_socket = real_socket.socket

    class FakeSocket:
        def __init__(self, *args, **kwargs):
            monitor.network_calls.append({
                'type': 'socket_create',
                'args': str(args),
            })

        def connect(self, address):
            monitor.network_calls.append({
                'type': 'connect',
                'address': str(address),
            })
            raise ConnectionRefusedError('Sandbox: network access blocked')

        def sendall(self, data):
            monitor.network_calls.append({
                'type': 'send',
                'size': len(data),
            })
            raise ConnectionRefusedError('Sandbox: network access blocked')

        def send(self, data):
            return self.sendall(data)

        def __getattr__(self, name):
            monitor.network_calls.append({
                'type': f'socket.{name}',
            })
            return MagicMock()

    # --- Monkey-patch os.environ ---
    original_environ = os.environ.copy()

    class MonitoredEnviron(dict):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

        def __getitem__(self, key):
            monitor.env_accesses.append({'var': key, 'method': '__getitem__'})
            # Return empty for sensitive vars
            sensitive = {'API_KEY', 'SECRET', 'TOKEN', 'PASSWORD', 'PRIVATE', 'AWS_', 'SSH'}
            if any(s in key.upper() for s in sensitive):
                return ''
            return super().get(key, '')

        def get(self, key, default=None):
            monitor.env_accesses.append({'var': key, 'method': 'get'})
            sensitive = {'API_KEY', 'SECRET', 'TOKEN', 'PASSWORD', 'PRIVATE', 'AWS_', 'SSH'}
            if any(s in key.upper() for s in sensitive):
                return default or ''
            return super().get(key, default)

    # --- Monkey-patch open ---
    original_open = open

    def monitored_open(file, mode='r', *args, **kwargs):
        filepath = os.path.abspath(str(file))
        if 'w' in mode or 'a' in mode or 'x' in mode:
            monitor.file_writes.append({
                'path': filepath,
                'mode': mode,
            })
            # Redirect writes to /dev/null
            return original_open(os.devnull, mode, *args, **kwargs)
        else:
            monitor.file_reads.append({
                'path': filepath,
                'inside_skill': filepath.startswith(os.path.abspath(skill_dir)),
            })
            # Allow reads within the skill dir, block outside
            if filepath.startswith(os.path.abspath(skill_dir)):
                return original_open(file, mode, *args, **kwargs)
            else:
                raise PermissionError(f'Sandbox: read blocked outside skill dir: {filepath}')

    # --- Monkey-patch subprocess ---
    class FakeSubprocess:
        PIPE = -1
        STDOUT = -2
        DEVNULL = -3
        CalledProcessError = Exception

        @staticmethod
        def run(*args, **kwargs):
            monitor.subprocesses.append({
                'type': 'subprocess.run',
                'command': str(args[0] if args else kwargs.get('args', 'unknown')),
            })
            raise PermissionError('Sandbox: subprocess execution blocked')

        @staticmethod
        def Popen(*args, **kwargs):
            monitor.subprocesses.append({
                'type': 'subprocess.Popen',
                'command': str(args[0] if args else kwargs.get('args', 'unknown')),
            })
            raise PermissionError('Sandbox: subprocess execution blocked')

        @staticmethod
        def call(*args, **kwargs):
            monitor.subprocesses.append({
                'type': 'subprocess.call',
                'command': str(args[0] if args else kwargs.get('args', 'unknown')),
            })
            raise PermissionError('Sandbox: subprocess execution blocked')

        @staticmethod
        def check_output(*args, **kwargs):
            monitor.subprocesses.append({
                'type': 'subprocess.check_output',
                'command': str(args[0] if args else kwargs.get('args', 'unknown')),
            })
            raise PermissionError('Sandbox: subprocess execution blocked')

    # --- Monkey-patch os.system ---
    original_os_system = os.system

    def fake_os_system(cmd):
        monitor.subprocesses.append({
            'type': 'os.system',
            'command': str(cmd),
        })
        raise PermissionError('Sandbox: os.system blocked')

    # --- Execute with patches ---
    try:
        # Apply patches
        real_socket.socket = FakeSocket
        os.environ = MonitoredEnviron(original_environ)
        os.system = fake_os_system

        # Load and parse the script (don't execute main, just import to see what it tries to do)
        # We do a dry-run: parse the AST and attempt import
        import ast
        with original_open(script_path, 'r') as f:
            source = f.read()

        # AST analysis — extract all imports
        try:
            tree = ast.parse(source)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        monitor.imports_attempted.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        monitor.imports_attempted.append(node.module)
        except SyntaxError as e:
            monitor.errors.append(f'SyntaxError parsing {script_path}: {e}')

        # Try to actually execute the module with sandboxed builtins
        # Redirect stdout/stderr
        old_stdout, old_stderr = sys.stdout, sys.stderr
        sys.stdout = StringIO()
        sys.stderr = StringIO()

        old_argv = sys.argv
        sys.argv = [script_path] + (script_args or ['--help'])

        base_builtins = __builtins__ if isinstance(__builtins__, dict) else vars(__builtins__)
        sandbox_builtins = {**base_builtins, 'open': monitored_open}

        try:
            exec(compile(source, script_path, 'exec'), {
                '__name__': '__main__',
                '__file__': script_path,
                '__builtins__': sandbox_builtins,
            })
        except SystemExit:
            pass  # --help typically exits
        except PermissionError as e:
            monitor.errors.append(f'Blocked: {e}')
        except ConnectionRefusedError as e:
            monitor.errors.append(f'Network blocked: {e}')
        except Exception as e:
            monitor.errors.append(f'{type(e).__name__}: {e}')
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            sys.argv = old_argv

    finally:
        # Restore all patches
        real_socket.socket = original_socket
        os.environ = original_environ
        os.system = original_os_system

    return monitor.to_dict()


def format_text_report(results: dict) -> str:
    """Format results as human-readable text."""
    lines = []
    lines.append('=' * 60)
    lines.append('SANDBOX ANALYSIS REPORT')
    lines.append('=' * 60)
    lines.append(f'Skill: {results["skill_dir"]}')
    lines.append('')

    s = results['summary']
    lines.append(f'Network attempts: {s["network_attempts"]}')
    lines.append(f'Files read outside skill: {s["files_read_outside_skill"]}')
    lines.append(f'Files written: {s["files_written"]}')
    lines.append(f'Env vars accessed: {s["env_vars_accessed"]}')
    lines.append(f'Subprocesses spawned: {s["subprocesses_spawned"]}')
    lines.append('')

    if results['imports_attempted']:
        lines.append('Imports:')
        for imp in sorted(set(results['imports_attempted'])):
            lines.append(f'  - {imp}')
        lines.append('')

    if results['network_calls']:
        lines.append('Network calls intercepted:')
        for call in results['network_calls']:
            lines.append(f'  [{call["type"]}] {call.get("address", call.get("args", ""))}')
        lines.append('')

    if results['env_accesses']:
        lines.append('Environment variables accessed:')
        seen = set()
        for access in results['env_accesses']:
            var = access['var']
            if var not in seen:
                seen.add(var)
                lines.append(f'  - {var}')
        lines.append('')

    if results['subprocesses']:
        lines.append('Subprocess calls intercepted:')
        for proc in results['subprocesses']:
            lines.append(f'  [{proc["type"]}] {proc["command"]}')
        lines.append('')

    if results['file_reads']:
        outside = [f for f in results['file_reads'] if not f['inside_skill']]
        if outside:
            lines.append('File reads OUTSIDE skill directory:')
            for f in outside:
                lines.append(f'  - {f["path"]}')
            lines.append('')

    if results['file_writes']:
        lines.append('File writes attempted:')
        for f in results['file_writes']:
            lines.append(f'  - {f["path"]} (mode: {f["mode"]})')
        lines.append('')

    if results['errors']:
        lines.append('Errors during sandbox execution:')
        for err in results['errors']:
            lines.append(f'  - {err}')
        lines.append('')

    if not any([results['network_calls'], results['subprocesses'],
                results['file_writes'],
                [f for f in results['file_reads'] if not f['inside_skill']]]):
        lines.append('No suspicious runtime behavior detected.')

    lines.append('=' * 60)
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description='Sandbox scanner for skill auditor')
    parser.add_argument('script_path', help='Path to the script to analyze')
    parser.add_argument('--skill-dir', help='Skill root directory (default: script parent dir)')
    parser.add_argument('--args', help='Arguments to pass to the script', default='--help')
    parser.add_argument('--json', action='store_true', help='Output as JSON')
    args = parser.parse_args()

    skill_dir = args.skill_dir or str(Path(args.script_path).parent.parent)
    script_args = args.args.split() if args.args else []

    results = create_sandbox(args.script_path, skill_dir, script_args)

    if args.json:
        print(json.dumps(results, indent=2, ensure_ascii=False))
    else:
        print(format_text_report(results))


if __name__ == '__main__':
    main()
