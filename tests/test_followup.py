import json
from pathlib import Path
import tempfile
import unittest

from evidence import capture, fingerprints, verify
from lab import compare_body, compare_pages, extract, inject, payload, render
from pdf_native import native_alias
from launcher import main


class NativeMappingTests(unittest.TestCase):
    def test_native_mapping_changes_both_readers_without_changing_pixels(self):
        from reportlab.pdfgen import canvas
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source, target = root / 'source.pdf', root / 'target.pdf'
            c = canvas.Canvas(str(source))
            c.drawString(70, 700, 'Function: print_stairs(n, p, c)')
            c.drawString(70, 650, 'Other prose: print and stairs remain unchanged.')
            c.save()
            locations = native_alias(source, target)
            self.assertEqual(locations[0]['occurrences'], 1)
            for path in extract(target, root / 'text').values():
                text = path.read_text()
                self.assertIn('paint_stairs', text)
                self.assertNotIn('print_stairs', text)
                self.assertIn('Other prose: print and stairs remain unchanged.', text)
            self.assertTrue(compare_pages(render(source, root / 'a'), render(target, root / 'b'))['identical'])

    def test_wrong_length_and_missing_target_fail_closed(self):
        with self.assertRaises(ValueError):
            native_alias('not-read.pdf', 'not-created.pdf', replacement='different_length')

    def test_visible_note_changes_footer_only_and_survives_all_extractors(self):
        from reportlab.pdfgen import canvas
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source, target = root / 'source.pdf', root / 'target.pdf'
            c = canvas.Canvas(str(source))
            c.drawString(70, 700, 'Required body text remains unchanged.')
            c.save()
            marker = 'stair_visual_comment_123456789abc'
            inject(source, target, payload('visual-comment', marker), 'visible-note')
            a, b = render(source, root / 'a'), render(target, root / 'b')
            self.assertTrue(compare_body(a, b))
            self.assertFalse(compare_pages(a, b)['identical'])
            for path in extract(target, root / 'text').values():
                self.assertIn(marker, path.read_text())


class EvidenceTests(unittest.TestCase):
    def test_capture_integrity_and_tamper_detection_without_execution(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); source = root / 'source.py'; model = root / 'chat.md'; key = root / 'key'
            marker = root / 'must-not-be-created'
            code = f'from pathlib import Path\nPath({str(marker)!r}).write_text("x")\n'
            source.write_text(code); model.write_text('```python\n' + code + '```')
            record = capture(source, root / 'bundle', key, model_record=model)
            self.assertFalse(marker.exists())
            self.assertEqual(record['authorship'], 'undetermined')
            self.assertTrue(record['comparison']['ast_sha256'])
            self.assertTrue(verify(root / 'bundle', key)['intact'])
            (root / 'bundle/submission.py').write_text('changed')
            self.assertFalse(verify(root / 'bundle', key)['intact'])
            data = json.loads((root / 'bundle/record.json').read_text())
            data['authorship'] = 'invented conclusion'
            (root / 'bundle/record.json').write_text(json.dumps(data))
            self.assertFalse(verify(root / 'bundle', key)['signature_valid'])

    def test_comment_and_format_changes_preserve_ast_not_author_identity(self):
        a = fingerprints('def f(x):\n    return x + 1\n')
        b = fingerprints('# changed\ndef f(x):\n return x+1\n')
        self.assertEqual(a['ast_sha256'], b['ast_sha256'])
        self.assertNotEqual(a['text_sha256'], b['text_sha256'])

    def test_launcher_dependency_check_is_non_mutating(self):
        self.assertEqual(main(['--check']), 0)


if __name__ == '__main__':
    unittest.main()
