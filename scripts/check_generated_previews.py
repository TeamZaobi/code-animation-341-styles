#!/usr/bin/env python3
"""Validate generated preview provenance, exact mapping and portable offline assets."""
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def main():
    folder = ROOT / '生成示例'
    lock = json.loads((folder / 'source-lock.json').read_text())
    text = (ROOT / '风格挑选.html').read_text()
    entries = json.loads(re.search(r'<script id="data" type="application/json">(.*?)</script>', text, re.S)[1])['entries']
    generated = {e['id']: e for e in entries if e.get('generatedPreview')}
    assert set(generated) == set(lock['styles']) and len(generated) == 109
    actual = {str(p.relative_to(folder)): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in folder.rglob('*') if p.is_file() and p.name != 'source-lock.json'}
    assert actual == lock['sha256'], 'Generated asset inventory or SHA-256 mismatch'
    counts = {}
    for id, item in lock['styles'].items():
        entry = generated[id]
        counts[entry['s']] = counts.get(entry['s'], 0) + 1
        assert item['source_prompt'] == entry['file'], id
        source = ROOT / item['source_prompt']
        assert hashlib.sha256(source.read_bytes()).hexdigest() == item['source_prompt_sha256'], id
        assert entry['img'] == '生成示例/' + item['poster'], id
        assert entry['animatedPreview'] == '生成示例/' + item['gif'], id
        assert entry['htmlPreview'] == '生成示例/' + item['html'], id
        for kind in ('poster', 'gif', 'html'):
            asset = (folder / item[kind]).resolve()
            assert asset.is_relative_to(folder.resolve()) and asset.is_file(), (id, kind)
        assert (folder / item['gif']).read_bytes().startswith(b'GIF8'), id
        assert (folder / item['poster']).read_bytes().startswith(b'\x89PNG'), id
        assert item['delivered_html_sha256'] and item['codex_modifications'], id
    assert counts == {'M': 31, 'K': 38, 'Z': 14, 'H': 11, 'V': 15}, counts
    stats = json.loads((ROOT / '_统计.json').read_text())
    assert stats['withGeneratedPreview'] == 109
    assert stats['withOriginalAnimatedPreview'] == 31
    assert stats['withAnimatedPreview'] == 140 and stats['withPreview'] == 333
    print('PASS: exact109 generated entries, provenance, asset hashes and poster-first mapping')


if __name__ == '__main__':
    main()
