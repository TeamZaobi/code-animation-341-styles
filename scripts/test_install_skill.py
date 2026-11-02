"""Verify portable installation and refusal of unsafe destinations."""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'skills/code-animation-styles'
INSTALLER = ROOT / 'scripts/install_skill.py'


class InstallationTests(unittest.TestCase):
    def install(self, target):
        return subprocess.run([sys.executable, str(INSTALLER), '--target', str(target)],
                              capture_output=True, text=True)

    def test_relocated_install_and_existing_target(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / 'installed'
            self.assertEqual(self.install(target).returncode, 0)
            check = subprocess.run([sys.executable, str(target / 'scripts/styles.py'), 'check'],
                                   capture_output=True, text=True)
            self.assertEqual(check.returncode, 0, check.stderr)
            self.assertEqual(self.install(target).returncode, 2)

    def test_direct_source_descendant_refused(self):
        result = self.install(SOURCE / 'nested-install')
        self.assertEqual(result.returncode, 2)
        self.assertIn('outside the source skill package', result.stderr)

    def test_symlinked_source_descendant_refused(self):
        with tempfile.TemporaryDirectory() as folder:
            link = Path(folder) / 'source-link'
            try:
                link.symlink_to(SOURCE, target_is_directory=True)
            except (OSError, NotImplementedError):
                self.skipTest('Symlink creation is unavailable')
            result = self.install(link / 'nested-install')
            self.assertEqual(result.returncode, 2)
            self.assertIn('outside the source skill package', result.stderr)


if __name__ == '__main__':
    unittest.main()
