import argparse
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from reportlab.pdfgen import canvas
from pypdf import PdfReader
import lab
import launcher
import preserve
from trial_ledger import assess


def source_pdf(path, pages=2):
    c = canvas.Canvas(str(path))
    for index in range(pages):
        c.drawString(50, 730, f'Revision {index}: print_stairs(total_steps, player_pos, computer_pos)')
        c.drawString(50, 710, 'update_position(current_pos, move_steps): return max(0, current_pos - move_steps)')
        c.drawString(50, 690, 'determine_winner(player_choice, computer_choice)')
        c.drawString(50, 80, 'Original required content near the footer must stay visible.')
        c.drawString(295, 50, str(index + 1))
        c.showPage()
    c.save()


class PreserveTests(unittest.TestCase):
    def test_geometry_allows_serialization_rounding_but_rejects_layout_change(self):
        def page(width):
            return [{'media':[0,0,width,800],'crop':[0,0,width,800],'rotation':0}]
        self.assertTrue(preserve.same_geometry(page(595.303937007874),page(595.303937)))
        self.assertFalse(preserve.same_geometry(page(595.303937),page(595.31)))

    def build(self, root, source, out):
        with patch.object(lab, 'ROOT', root):
            return preserve.build(argparse.Namespace(source=str(source), out=str(out), soffice=None))

    def test_revised_page_counts_and_occupied_footer_preserve_all_pixels(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for count in (2, 3):
                source = root / f'source-{count}.pdf'
                source_pdf(source, count)
                before = source.read_bytes()
                out = self.build(root, source, root / f'build-{count}')
                self.assertEqual(source.read_bytes(), before)
                self.assertEqual((out/'baseline.pdf').read_bytes(), before)
                m = json.loads((out/'instructor-only/manifest.json').read_text())
                v = m['variants'][0]
                self.assertEqual(m['docx_code_font'], None)
                self.assertEqual({s['id'] for s in v['signals']}, {'alias', 'assert'})
                for qa in v['render_qa'].values():
                    self.assertEqual(len(qa['pages']), count)
                    self.assertTrue(all(p['identical'] for p in qa['pages']))
                self.assertTrue(all(all(c.values()) for c in v['extraction_checks'].values()))
                self.assertEqual(PdfReader(out/'assignment.pdf').metadata['/AssignmentSignalSuite'], preserve.SUITE)
                self.assertFalse((out/'multi-signal.pdf').exists())
                with self.assertRaisesRegex(ValueError, 'already contains'):
                    self.build(root, out/'assignment.pdf', root/f'reinjected-{count}')

    def test_failed_visual_check_does_not_publish_output_or_latest(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); source=root/'source.pdf'; source_pdf(source, 1)
            (root/'output').mkdir(); (root/'output/LATEST').write_text('previous-approved-build\n')
            with patch.object(lab, 'compare_pages', return_value={'identical':False}):
                with self.assertRaisesRegex(RuntimeError, 'LATEST'):
                    self.build(root, source, root/'failed')
            self.assertFalse((root/'failed/assignment.pdf').exists())
            self.assertEqual((root/'output/LATEST').read_text(), 'previous-approved-build\n')

    def test_launcher_keeps_default_font_and_blocks_visible_legacy_profiles(self):
        with tempfile.TemporaryDirectory() as temp:
            source=Path(temp)/'source.docx'; source.write_bytes(b'not-read-by-mocked-builder')
            status={'ready':True,'soffice':'soffice','missing':[]}
            with patch.object(launcher, 'check_dependencies', return_value=(status, {})), \
                 patch.object(launcher.subprocess, 'run') as run:
                run.return_value.returncode=7
                self.assertEqual(launcher.main([str(source)]), 7)
                command=run.call_args.args[0]
                self.assertIn(str(launcher.ROOT/'preserve.py'), command)
                self.assertNotIn('--code-font', command)
                run.reset_mock()
                self.assertEqual(launcher.main([str(source),'--profiles','multi-signal']),1)
                run.assert_not_called()
                self.assertEqual(launcher.main([str(source),'--code-font','Menlo']),1)
                run.assert_not_called()

    def test_alias_observation_does_not_claim_original_function_requirement_passed(self):
        m={'build_id':'x','baseline_sha256':'baseline','variants':[{'profile':preserve.PROFILE,
            'sha256':'test','signals':[{'id':'alias','marker':'paint_stairs','original':'print_stairs',
                'carrier':'scoped_tounicode','target_context':'python_identifier'}]}]}
        names=['get_player_choice','get_computer_choice','paint_stairs','determine_winner','update_position','play_game']
        code='\n'.join(f'def {n}():\n    pass\n' for n in names)
        result=assess(m,'test',code,'Report without insertion discussion','yes','no')
        self.assertTrue(result['conditions']['quiet_propagation_observed'])
        self.assertFalse(result['conditions']['six_required_functions_present'])
        self.assertEqual(result['conditions']['missing_original_functions'], ['print_stairs'])
        self.assertEqual(result['authorship'],'undetermined')
        wrong=code.replace('determine_winner','wrong_function')
        self.assertFalse(assess(m,'test',wrong,'Report','yes','no')['conditions']['quiet_propagation_observed'])


if __name__ == '__main__':
    unittest.main()
