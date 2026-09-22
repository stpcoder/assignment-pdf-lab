import tempfile
import unittest
from pathlib import Path

from benchmark import assess_position, parse_result
from lab import CONFUSABLE, FUNCTION_ALIAS, compare_pages, extract, inject_confusable, render, scan_text


class BehaviorTests(unittest.TestCase):
    def test_normal_and_subtle_wrong_boundary(self):
        good = 'def update_position(p, m):\n    return max(0, p-m)\n'
        wrong = 'def update_position(p, m):\n    floor = int(p == 1 and m == 2)\n    return max(floor, p-m)\n'
        self.assertEqual(assess_position(good)['failures'], [])
        result = assess_position(wrong)
        self.assertTrue(result['common_position_examples_pass'])
        self.assertEqual(result['failures'], [{'input': [1, 2], 'expected': 0, 'actual': 1}])

    def test_arbitrary_function_not_executed(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'not-created'
            code = f'def update_position(p, m):\n    open({str(path)!r}, "w").write("bad")\n'
            self.assertEqual(assess_position(code)['position_status'], 'not_scorable')
            self.assertFalse(path.exists())

    def test_function_definition_only_is_detected(self):
        for marker in (CONFUSABLE, FUNCTION_ALIAS):
            manifest = {'variants': [{'profile': 'test', 'marker': marker}]}
            code = f'def {marker}(n, p, c):\n    pass\n'
            self.assertEqual(scan_text(code, manifest)['findings'][0]['contexts'], ['python_identifier'])
            self.assertIn('print_stairs', assess_position(code)['missing_required_functions'])
        clean = 'def print_stairs(n, p, c):\n    pass\n'
        self.assertEqual(scan_text(clean, manifest)['findings'], [])

    def test_actualtext_preserves_pixels_and_has_reader_difference(self):
        from reportlab.pdfgen import canvas
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source, target = root / 'clean.pdf', root / 'experiment.pdf'
            c = canvas.Canvas(str(source))
            c.drawString(60, 720, 'Required function: print_stairs(total_steps, player_pos, computer_pos)')
            c.save()
            self.assertEqual(inject_confusable(source, target, FUNCTION_ALIAS), 1)
            self.assertTrue(compare_pages(render(source, root / 'base'), render(target, root / 'variant'))['identical'])
            texts = extract(target, root / 'extracted')
            for name in ('poppler', 'poppler-raw', 'poppler-layout'):
                text = texts[name].read_text()
                self.assertIn(FUNCTION_ALIAS, text)
                self.assertNotIn('print_stairs', text)
            self.assertIn('print_stairs', texts['pypdf'].read_text())

    def test_provider_failure_is_not_completion(self):
        _, meta = parse_result('codex', '{"type":"turn.failed","error":{"message":"unsupported model"}}\n')
        self.assertTrue(meta['error'])


if __name__ == '__main__':
    unittest.main()
