#!/usr/bin/env python3
"""Choose a DOCX/PDF, export if needed, postprocess, and run the PDF checks."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parent


def tool_environment():
    env = os.environ.copy()
    runtime = Path.home() / '.cache/codex-runtimes/codex-primary-runtime/dependencies'
    extra = [runtime / 'bin/override', runtime / 'bin/fallback', Path('/opt/homebrew/bin'), Path('/usr/local/bin')]
    if env.get('POPPLER_BIN'):
        extra.insert(0, Path(env['POPPLER_BIN']))
    env['PATH'] = os.pathsep.join(str(p) for p in extra if p.is_dir()) + os.pathsep + env.get('PATH', '')
    soffice = shutil.which('soffice', path=env['PATH'])
    candidates = [Path('/Applications/LibreOffice.app/Contents/MacOS/soffice')]
    for key in ('ProgramFiles', 'ProgramFiles(x86)'):
        if env.get(key):
            candidates.append(Path(env[key]) / 'LibreOffice/program/soffice.exe')
    if not soffice:
        soffice = next((str(p) for p in candidates if p.is_file()), None)
    return env, soffice


def check_dependencies(source=None):
    env, soffice = tool_environment()
    checks = {name: importlib.util.find_spec(name) is not None for name in ('pypdf', 'reportlab', 'PIL')}
    tools = {name: shutil.which(name, path=env['PATH']) for name in ('pdftotext', 'pdftoppm')}
    missing = [name for name, present in checks.items() if not present]
    missing += [name for name, path in tools.items() if not path]
    needs_converter = source is not None and Path(source).suffix.lower() == '.docx'
    if needs_converter and not soffice:
        missing.append('LibreOffice/soffice')
    return {'python': sys.executable, 'python_packages': checks, 'tools': tools,
            'soffice': soffice, 'missing': missing, 'ready': not missing}, env


def choose_file():
    try:
        import tkinter as tk
        from tkinter import filedialog
    except ImportError as exc:
        raise ValueError('파일 선택기를 사용할 수 없습니다. 터미널에서 launcher.py 뒤에 DOCX/PDF 경로를 넣어 주세요.') from exc
    try:
        window = tk.Tk(); window.withdraw()
        try:
            return filedialog.askopenfilename(title='변환할 과제 DOCX 또는 PDF 선택',
                filetypes=[('과제 문서', '*.docx *.pdf'), ('모든 파일', '*.*')])
        finally:
            window.destroy()
    except (tk.TclError, RuntimeError) as exc:
        raise ValueError('파일 선택기를 사용할 수 없습니다. 터미널에서 launcher.py 뒤에 DOCX/PDF 경로를 넣어 주세요.') from exc


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', nargs='?', help='DOCX/PDF path; omitted = file chooser')
    parser.add_argument('--check', action='store_true', help='Print dependency status without creating a PDF')
    parser.add_argument('--profiles', nargs='+', default=['native-hidden'])
    parser.add_argument('--experimental', action='store_true', help='Allow historical profiles that may change visible content or rules')
    parser.add_argument('--out', help='New output directory')
    parser.add_argument('--code-font', help='Temporary DOCX Latin code font override')
    args = parser.parse_args(argv)
    if args.check:
        status, _ = check_dependencies(args.source)
        print(json.dumps(status, ensure_ascii=False, indent=2))
        return 0 if status['ready'] else 1
    try:
        value = args.source or choose_file()
        if not value:
            print('취소했습니다. 파일을 만들지 않았습니다.')
            return 0
        source = Path(value).expanduser().resolve()
        if not source.is_file() or source.suffix.lower() not in ('.docx', '.pdf'):
            raise ValueError('존재하는 DOCX 또는 PDF 파일을 선택하세요.')
        status, env = check_dependencies(source)
        if not status['ready']:
            raise ValueError('필요한 구성 요소가 없습니다: ' + ', '.join(status['missing']) + '\n설치 방법: PORTABLE_GUIDE.md')
        preserved = args.profiles == ['native-hidden']
        if not preserved and not args.experimental:
            raise ValueError('이전 실험은 --experimental이 필요합니다. 기본 실행은 원본 화면을 보존합니다.')
        if preserved and args.code_font:
            raise ValueError('원본 보존 경로에서는 글꼴을 교체하지 않습니다. 깨끗한 PDF를 입력하세요.')
        from signal_suite import PROFILES as SUITE_PROFILES
        suite = any(p in SUITE_PROFILES for p in args.profiles)
        if suite and not all(p in SUITE_PROFILES for p in args.profiles):
            raise ValueError('새 신호 실험과 이전 실험은 --profiles를 나누어 실행하세요.')
        script = 'preserve.py' if preserved else ('signal_suite.py' if suite else 'lab.py')
        command = [sys.executable, str(ROOT / script), 'build', str(source)]
        if not preserved:
            command += ['--profiles', *args.profiles, '--experimental']
        if source.suffix.lower() == '.docx':
            command += ['--soffice', status['soffice']]
            if args.code_font:
                command += ['--code-font', args.code_font]
        if args.out:
            command += ['--out', str(Path(args.out).expanduser().resolve())]
        print('DOCX 변환(필요한 경우) → PDF 후처리 → 화면·추출 검사', flush=True)
        result = subprocess.run(command, cwd=ROOT, env=env)
        if result.returncode == 0:
            print('생성된 폴더:', (ROOT / 'output/LATEST').read_text().strip())
            print('실험본입니다. Gemini Flash/Pro 지원 여부는 실제 모델 실험 결과에서 확인하세요.')
        return result.returncode
    except (ValueError, OSError) as exc:
        print('오류:', exc, file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
