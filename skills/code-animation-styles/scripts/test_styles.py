"""Regression checks for retrieval and frozen upstream integrity. Run with Python 3."""
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).with_name('styles.py')
spec = importlib.util.spec_from_file_location('styles', SCRIPT)
styles = importlib.util.module_from_spec(spec)
spec.loader.exec_module(styles)


class CatalogTests(unittest.TestCase):
    def run_cli(self, *args):
        return subprocess.run(['python3', str(SCRIPT), *args], text=True, capture_output=True)

    def test_complete_frozen_catalog(self):
        result = styles.check()
        self.assertEqual((result['styles'], result['usable_styles'], result['stills']), (341, 333, 193))

    def test_scene_search(self):
        result = json.loads(self.run_cli('search', '压力').stdout)
        self.assertIn('A1', [e['id'] for e in result])

    def test_mit_subset(self):
        result = json.loads(self.run_cli('search', '--license', 'MIT').stdout)
        self.assertEqual(len(result), 105)
        self.assertTrue(all(e['id'][0] in 'LVX' for e in result))

    def test_exact_id_and_shared_dependency(self):
        result = self.run_cli('show', 'a1')
        self.assertEqual(result.returncode, 0)
        self.assertIn('S.A1 =', result.stdout)
        self.assertIn('function rng(', result.stdout)
        self.assertEqual(self.run_cli('show', 'A10').returncode, 1)

    def test_empty_upstream_prompt_fails(self):
        self.assertEqual(self.run_cli('show', 'M14').returncode, 1)

    def test_source_path_cannot_escape(self):
        with self.assertRaises(ValueError):
            styles.source_file('../SKILL.md')

    def test_untracked_source_file_fails(self):
        with tempfile.TemporaryDirectory() as folder:
            extra = Path(folder) / 'unexpected'
            extra.write_text('drift')
            with patch.object(styles, 'VENDOR', Path(folder)):
                with self.assertRaisesRegex(ValueError, 'inventory or SHA256'):
                    styles.check()

    def test_x_previews_cover_exact_series(self):
        previews = styles.preview_catalog()
        x_ids = {e['id'] for e in styles.catalog() if e['s'] == 'X'}
        self.assertEqual(set(previews['styles']), x_ids)
        for entry in previews['styles'].values():
            self.assertTrue(styles.preview_file(entry['file']).read_bytes().startswith(b'GIF8'))

    def test_picker_overlay_preserves_frozen_source(self):
        before = styles.check()
        html = styles.picker_html()
        entries = json.loads(styles.re.search(r'<script id="data" type="application/json">(.*?)</script>', html, styles.re.S)[1])['entries']
        x_entries = [e for e in entries if e['s'] == 'X']
        self.assertEqual(len(x_entries), 31)
        self.assertTrue(all(e['img'].startswith('/previews/') for e in x_entries))
        self.assertEqual(styles.check(), before)


if __name__ == '__main__':
    unittest.main()
