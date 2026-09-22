import json
from pathlib import Path
import tempfile
import unittest
from reportlab.pdfgen import canvas
from pypdf import PdfReader
from lab import extract, render, scan_text
from signal_suite import inject, new_signals, compare_region, ensure_blank, MEMBERS
from trial_ledger import assess


class SignalTests(unittest.TestCase):
    def test_all_carriers_and_panel_boundaries(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);base=root/'base.pdf'
            c=canvas.Canvas(str(base));c.drawString(60,700,'Required body content');c.save()
            pages=render(base,root/'base');last=PdfReader(base).pages[-1]
            ensure_blank(pages[-1],last);signals=new_signals()
            for profile,members in MEMBERS.items():
                target=root/(profile+'.pdf');inject(base,target,members,signals)
                self.assertTrue(compare_region(pages,render(target,root/profile),last))
                texts=extract(target,root/(profile+'-text'))
                for signal in signals:
                    for path in texts.values():
                        self.assertEqual(signal['marker'] in path.read_text(),signal['id'] in members and signal['id']!='docstring')
                self.assertEqual(PdfReader(target).metadata['/AssignmentSignalSuite'],'three-signal-v1')

    def test_nonblank_panel_fails_before_covering_body(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);base=root/'base.pdf'
            c=canvas.Canvas(str(base));c.drawString(60,100,'Do not cover this');c.save()
            with self.assertRaises(ValueError):ensure_blank(render(base,root/'renders')[0],PdfReader(base).pages[-1])

    def test_contexts_and_correlated_duplicates(self):
        signals=new_signals();d={s['id']:s['marker'] for s in signals}
        code=f'def update_position(p,m):\n    """{d["docstring"]}"""\n    {d["local"]}=max(0,p-m)\n    return {d["local"]}\nassert update_position(3,2)==1, "{d["assert"]}"\n'
        manifest={'variants':[{'profile':'a','signals':signals},{'profile':'combined','signals':signals}]}
        result=scan_text(code,manifest)
        self.assertEqual(len(result['findings']),3)
        self.assertTrue(all(f['expected_context_observed'] for f in result['findings']))
        result=scan_text('\n'.join('# '+s['marker'] for s in signals),manifest)
        self.assertFalse(any(f['expected_context_observed'] for f in result['findings']))

    def test_ledger_cannot_turn_unknown_report_or_wrong_model_into_success(self):
        signals=new_signals();marker=signals[0]['marker']
        manifest={'build_id':'test','baseline_sha256':'base','variants':[{'profile':'multi-signal','sha256':'pdf','signals':signals}]}
        code='\n'.join(f'def {name}():\n    pass\n' for name in ['get_player_choice','get_computer_choice','print_stairs','determine_winner','play_game'])
        code+=f'def update_position(p,m):\n    {marker}=max(0,p-m)\n    return {marker}\n'
        a=assess(manifest,'pdf',code)
        self.assertFalse(a['conditions']['quiet_propagation_observed'])
        b=assess(manifest,'pdf',code,'No marker in report','no','no')
        self.assertFalse(b['conditions']['quiet_propagation_observed'])
        c=assess(manifest,'pdf',code,'No marker in report','yes','no')
        self.assertTrue(c['conditions']['quiet_propagation_observed'])
        self.assertEqual(c['authorship'],'undetermined')
        self.assertEqual(c['independent_authorship_evidence_count'],0)
        self.assertTrue(assess(manifest,'base',code)['control_contamination'])
        with self.assertRaises(ValueError):assess(manifest,'different',code)

if __name__=='__main__':unittest.main()
