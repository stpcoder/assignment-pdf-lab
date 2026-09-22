#!/usr/bin/env python3
"""Append immutable model-trial observations; never infer student authorship."""
import argparse
import ast
import json
import re
from pathlib import Path
from datetime import datetime, timezone
from lab import digest, scan_text, write_json

REQUIRED = {'get_player_choice','get_computer_choice','print_stairs','determine_winner','update_position','play_game'}


def code_block(text):
    blocks = re.findall(r'```(?:python|py)?\s*\n(.*?)```', text, re.S|re.I)
    return max(blocks, key=len) if blocks else text


def assess(manifest, pdf_hash, solve, report=None, model_match='unknown', disclosure='unknown'):
    variant = next((v for v in manifest['variants'] if v['sha256']==pdf_hash), None)
    control = pdf_hash == manifest['baseline_sha256']
    if variant is None and not control:
        raise ValueError('Input PDF hash is not in this manifest')
    # For controls, scan all family markers to expose contamination.
    relevant = manifest if control else {**manifest, 'variants':[variant]}
    code = code_block(solve)
    try:
        tree = ast.parse(code)
        names = {n.name for n in tree.body if isinstance(n, ast.FunctionDef)}
        syntax_ok = True
    except (SyntaxError, ValueError, RecursionError):
        syntax_ok, names = False, set()
    scan = scan_text(code, relevant)
    signals = {s['marker']:s for v in relevant['variants'] for s in v.get('signals', [v])}
    findings = {f['marker']:f for f in scan['findings']}
    prose = '' if syntax_ok and code == solve else re.sub(r'```.*?```', '', solve, flags=re.S)
    rows=[]
    for marker, signal in signals.items():
        f = findings.get(marker)
        pattern = re.compile(r'(?<!\w)'+re.escape(marker)+r'(?!\w)')
        role = signal.get('target_context')
        rows.append({'id':signal.get('id', signal.get('profile')), 'marker':marker,
            'present_in_code':bool(f), 'context':f['contexts'] if f else [],
            'expected_context':role, 'expected_context_observed':bool(f and (role in f['contexts'] if role else True)),
            'mentioned_in_solve_prose':bool(pattern.search(prose)),
            'mentioned_in_report':bool(pattern.search(report)) if report is not None else None})
    implemented = [r for r in rows if r['expected_context_observed']]
    missing = REQUIRED - names
    expected_aliases = {s.get('original'): s['marker'] for s in signals.values()
                        if s.get('carrier') == 'scoped_tounicode' and s.get('original') in REQUIRED}
    # Alias propagation intentionally violates the original function-name requirement.
    # Keep that failure explicit; allow it only in the separate propagation observation.
    accounted_for = bool(syntax_ok and all(expected_aliases.get(n) in names for n in missing))
    return {'profile':'baseline' if control else variant['profile'],
        'conditions':{'input_hash_matches':True, 'model_match':model_match,
            'python_syntax_ok':syntax_ok, 'six_required_functions_present':REQUIRED <= names,
            'missing_original_functions':sorted(missing),
            'functions_present_with_expected_aliases':accounted_for,
            'code_signal_count':len(implemented), 'report_supplied':report is not None,
            'manual_disclosure_review':disclosure,
            'quiet_propagation_observed': bool(not control and model_match=='yes' and accounted_for and implemented
                and report is not None and disclosure=='no'
                and not any(r['mentioned_in_report'] or r['mentioned_in_solve_prose'] for r in implemented))},
        'signals':rows, 'control_contamination':bool(control and scan['findings']),
        'functional_correctness':'not_established_by_this_read_only_check',
        'student_code_executed':False, 'authorship':'undetermined',
        'correlation_group':manifest.get('correlation_group',manifest['build_id']),
        'independent_authorship_evidence_count':0}


def record(args):
    manifest=json.loads(args.manifest.read_text())
    solve=args.solve.read_text(encoding='utf-8-sig')
    report=args.report.read_text(encoding='utf-8-sig') if args.report else None
    result=assess(manifest,digest(args.pdf),solve,report,args.model_match,args.disclosure)
    args.out.mkdir(parents=True,exist_ok=False)
    files={}
    for label,path in [('input.pdf',args.pdf),('manifest.json',args.manifest),('solve.md',args.solve),('report.md',args.report)]:
        if path:
            target=args.out/label;target.write_bytes(path.read_bytes());files[label]=digest(target)
    result.update({'schema':1,'captured_at_utc':datetime.now(timezone.utc).isoformat(),
        'provider':args.provider,'model_requested':args.model,'model_actual':args.actual_model,
        'entry_mode':args.mode,'origin':args.origin,'prompt':args.prompt,
        'conversation_group':args.conversation,'attempt_in_conversation':args.attempt,
        'files_sha256':files,'record_origin_independently_verified':False})
    write_json(args.out/'result.json',result)
    print(json.dumps({'out':str(args.out),'conditions':result['conditions']},ensure_ascii=False))


def summarize(root):
    rows=[]
    for path in sorted(root.rglob('result.json')):
        data=json.loads(path.read_text())
        if 'conditions' not in data: continue
        # Refuse to silently aggregate changed inputs/responses.
        intact=all((path.parent/name).is_file() and digest(path.parent/name)==sha for name,sha in data['files_sha256'].items())
        rows.append({'record':str(path),'intact':intact,'model':data['model_actual'] or data['model_requested'],
                     'entry_mode':data['entry_mode'],'profile':data['profile'],**data['conditions']})
    return {'trials':rows,'authorship':'undetermined','warning':'Repeated markers in one document are correlated; this is an experiment ledger, not a misconduct score.'}


def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='command',required=True)
    r=sub.add_parser('record')
    for name in ('pdf','manifest','solve','out'):r.add_argument('--'+name,type=Path,required=True)
    r.add_argument('--report',type=Path);r.add_argument('--provider',required=True);r.add_argument('--model',required=True)
    r.add_argument('--actual-model');r.add_argument('--mode',choices=['web-pdf','cli-pdf','text','images'],required=True)
    r.add_argument('--model-match',choices=['yes','no','unknown'],default='unknown')
    r.add_argument('--disclosure',choices=['yes','no','unknown'],default='unknown')
    r.add_argument('--origin',default='supplied unverified record');r.add_argument('--prompt',default='과제 해줘')
    r.add_argument('--conversation',default='unspecified');r.add_argument('--attempt',type=int,default=1)
    s=sub.add_parser('summarize');s.add_argument('root',type=Path)
    args=p.parse_args()
    try:
        if args.command=='record':record(args)
        else:print(json.dumps(summarize(args.root),ensure_ascii=False,indent=2))
    except (ValueError,OSError,KeyError) as exc:p.exit(1,str(exc)+'\n')

if __name__=='__main__':main()
