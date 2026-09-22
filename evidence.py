#!/usr/bin/env python3
"""Preserve review evidence locally; never classifies authorship or runs a submission."""
import argparse
import ast
from datetime import datetime, timezone
import hashlib
import hmac
import io
import json
import os
from pathlib import Path
import re
import secrets
import tokenize

ROOT = Path(__file__).resolve().parent
DEFAULT_KEY = ROOT / 'private/evidence-signing.key'
LIMIT = 2_000_000


def sha(data):
    return hashlib.sha256(data).hexdigest()


def canonical(data):
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()


def code_from(text):
    blocks = re.findall(r'```(?:python|py)?\s*\n(.*?)```', text, flags=re.S | re.I)
    return max(blocks, key=len) if blocks else text


def fingerprints(text):
    code = code_from(text)
    result = {'text_sha256': sha(code.encode()), 'ast_sha256': None, 'token_sha256': None, 'functions': []}
    try:
        tree = ast.parse(code)
        result['ast_sha256'] = sha(ast.dump(tree, include_attributes=False).encode())
        result['functions'] = [n.name for n in tree.body if isinstance(n, ast.FunctionDef)]
    except (SyntaxError, ValueError, RecursionError):
        pass
    try:
        tokens = [(t.type, t.string) for t in tokenize.generate_tokens(io.StringIO(code).readline)
                  if t.type not in (tokenize.COMMENT, tokenize.NL, tokenize.ENCODING, tokenize.ENDMARKER)]
        result['token_sha256'] = sha(canonical(tokens))
    except (tokenize.TokenError, IndentationError, SyntaxError, RecursionError):
        pass
    return result


def read_limited(path):
    path = Path(path).resolve()
    if not path.is_file() or path.stat().st_size > LIMIT:
        raise ValueError('Evidence file must exist and be at most 2 MB')
    return path.read_bytes()


def get_key(path, create=False):
    path = Path(path)
    if create and not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, 'wb') as stream:
            stream.write(secrets.token_bytes(32))
    key = path.read_bytes()
    if len(key) != 32:
        raise ValueError('Signing key must contain exactly 32 bytes')
    return key


def capture(submission, out, key_path=DEFAULT_KEY, manifest=None, model_record=None, origin='unverified supplied record'):
    source = read_limited(submission)
    model = read_limited(model_record) if model_record else None
    manifest_bytes = read_limited(manifest) if manifest else None
    out = Path(out).resolve()
    out.mkdir(parents=True, exist_ok=False)
    artifacts = []
    for role, data, name in [('submission', source, 'submission.py'), ('model_record', model, 'model-record.txt'),
                             ('build_manifest', manifest_bytes, 'build-manifest.json')]:
        if data is not None:
            (out / name).write_bytes(data)
            artifacts.append({'role': role, 'file': name, 'sha256': sha(data), 'bytes': len(data)})
    text = source.decode('utf-8-sig', errors='replace')
    fp = fingerprints(text)
    result = {'schema': 1, 'captured_at_utc': datetime.now(timezone.utc).isoformat(),
              'timestamp_meaning': 'local capture time, not original submission or model generation time',
              'authorship': 'undetermined', 'student_code_executed': False, 'network_used': False,
              'artifacts': artifacts, 'submission_fingerprints': fp,
              'record_origin_label': origin, 'record_origin_independently_verified': False,
              'integrity_meaning': 'HMAC detects changes after capture if the separate key remains trusted; it does not authenticate an AI conversation or prove misconduct.'}
    if manifest_bytes:
        from lab import scan_text
        result['canary_observations'] = scan_text(text, json.loads(manifest_bytes))
    if model is not None:
        mf = fingerprints(model.decode('utf-8-sig', errors='replace'))
        result['model_record_fingerprints'] = mf
        result['comparison'] = {name: fp[name] is not None and fp[name] == mf[name]
                                for name in ('text_sha256', 'ast_sha256', 'token_sha256')}
        result['comparison_meaning'] = 'Same code structure is a correspondence signal, not a direction-of-copying or authorship finding.'
    stairs = next((name for name in fp['functions'] if 'stairs' in name), 'print_stairs')
    followup = f'''# 추가 확인 기록지 — 자동 판정 없음

대상 제출물 SHA-256: {sha(source)}

1. 본인의 update_position 함수에서 (2, 3), (1, 2)를 한 줄씩 추적하고 반환값의 이유를 설명한다.
2. {stairs}(5, 3, 3)의 위치 표시와 중첩 반복문의 역할을 설명한다. 본인의 코드에서 관련 줄을 가리킨다.
3. 검토자가 고른 작은 규칙 변경을 현장에서 구현하고, 변경 전후를 구분하는 입력 한 가지를 직접 만든다.

관찰 시각 / 검토자:

실제 답변 및 수정한 코드:

적용한 수업 규정과 학생 설명:

추가로 확인한 독립 자료(있다면):

일반 실수, 복사·접근성 도구, 다른 예제 재사용 등 대안 설명:

이 기록은 이해도 확인 자료다. 답변 실패나 코드 유사성만으로 AI 사용을 확정하지 않는다.
'''
    # Byte-exact on Windows too: text-mode CRLF conversion would invalidate the hash.
    (out / 'followup.md').write_bytes(followup.encode('utf-8'))
    result['artifacts'].append({'role': 'review_form', 'file': 'followup.md', 'sha256': sha(followup.encode()), 'bytes': len(followup.encode())})
    # Preserve this blank form; fill a copy so the captured bundle remains immutable.
    signature = hmac.new(get_key(key_path, create=True), canonical(result), hashlib.sha256).hexdigest()
    (out / 'record.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (out / 'record.hmac').write_text(signature + '\n', encoding='ascii')
    return result


def verify(out, key_path=DEFAULT_KEY):
    out = Path(out).resolve()
    record = json.loads((out / 'record.json').read_text(encoding='utf-8'))
    expected = hmac.new(get_key(key_path), canonical(record), hashlib.sha256).hexdigest()
    signed = hmac.compare_digest(expected, (out / 'record.hmac').read_text().strip())
    checks = []
    for item in record['artifacts']:
        path = out / item['file']
        safe_path = path.resolve().parent == out and not path.is_symlink()
        valid = safe_path and path.is_file() and sha(read_limited(path)) == item['sha256']
        checks.append({'file': item['file'], 'intact': bool(valid)})
    return {'signature_valid': signed, 'artifacts': checks, 'intact': signed and all(c['intact'] for c in checks),
            'authorship': 'undetermined', 'meaning': 'Integrity only; no AI-use verdict.'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    commands = p.add_subparsers(dest='command', required=True)
    c = commands.add_parser('capture')
    c.add_argument('--submission', type=Path, required=True)
    c.add_argument('--manifest', type=Path)
    c.add_argument('--model-record', type=Path, help='Already obtained record; this tool never retrieves private accounts')
    c.add_argument('--origin', default='unverified supplied record')
    c.add_argument('--out', type=Path, required=True)
    c.add_argument('--key', type=Path, default=DEFAULT_KEY)
    v = commands.add_parser('verify')
    v.add_argument('bundle', type=Path)
    v.add_argument('--key', type=Path, default=DEFAULT_KEY)
    args = p.parse_args()
    try:
        if args.command == 'capture':
            result = capture(args.submission, args.out, args.key, args.manifest, args.model_record, args.origin)
            print(json.dumps({'out': str(args.out.resolve()), 'authorship': result['authorship'], 'comparison': result.get('comparison')}, ensure_ascii=False))
        else:
            result = verify(args.bundle, args.key)
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0 if result['intact'] else 1
    except (ValueError, OSError, KeyError) as exc:
        print('ERROR:', exc)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
