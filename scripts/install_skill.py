#!/usr/bin/env python3
"""Copy the self-contained skill into a new directory without overwriting an install."""
import argparse
from pathlib import Path
import shutil
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--target', type=Path,
                        default=Path.home() / '.agents/skills/code-animation-styles')
    args = parser.parse_args()
    source = Path(__file__).resolve().parents[1] / 'skills/code-animation-styles'
    target = args.target.expanduser().absolute()
    if target.exists() or target.is_symlink():
        parser.error(f'Target already exists; choose a new --target: {target}')
    target = target.resolve()
    if not (source / 'SKILL.md').is_file():
        parser.error(f'Skill package not found: {source}')
    if target.is_relative_to(source.resolve()):
        parser.error('Target must be outside the source skill package')
    shutil.copytree(source, target,
                    ignore=shutil.ignore_patterns('__pycache__', '*.pyc', '.DS_Store', '._*'))
    print(f'Installed: {target}')
    print('Invoke $code-animation-styles in a host that discovers this skills directory.')


if __name__ == '__main__':
    try:
        main()
    except OSError as error:
        print(f'Installation failed: {error}', file=sys.stderr)
        sys.exit(1)
