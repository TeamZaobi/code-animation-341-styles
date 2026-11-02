#!/usr/bin/env python3
"""Offline access to the pinned animation catalog and a local picker adapter."""
import argparse
import functools
import hashlib
import http.server
import json
from pathlib import Path
import re
import sys
from urllib.parse import urlsplit, unquote

ROOT = Path(__file__).resolve().parents[1]
VENDOR = ROOT / 'vendor'
LOCK = ROOT / 'references/source-lock.json'
PREVIEWS = ROOT / 'assets/x-previews'
GENERATED = ROOT / 'assets/generated-previews'


def generated_file(relative):
    path = (GENERATED / relative).resolve()
    if not path.is_relative_to(GENERATED.resolve()):
        raise ValueError('Generated preview path escapes assets directory')
    return path


def generated_catalog():
    path = ROOT / 'references/generated-preview-lock.json'
    if not path.exists():
        return {'styles': {}}
    lock = json.loads(path.read_text())
    actual = {str(p.relative_to(GENERATED)): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in GENERATED.rglob('*') if p.is_file()}
    if actual != lock['sha256']:
        raise ValueError('Generated preview inventory or SHA256 mismatch')
    expected = {e['id']: e for e in catalog() if not e.get('img') and e['s'] != 'X' and available(e)}
    if set(lock['styles']) != set(expected):
        raise ValueError('Generated previews must cover exactly the missing usable entries')
    if lock['source_commit'] != json.loads(LOCK.read_text())['commit']:
        raise ValueError('Generated preview source revision mismatch')
    for id, entry in lock['styles'].items():
        if entry['source_prompt'] != expected[id]['file']:
            raise ValueError(f'Generated preview source binding mismatch: {id}')
        if hashlib.sha256(source_file(entry['source_prompt']).read_bytes()).hexdigest() != entry['source_prompt_sha256']:
            raise ValueError(f'Generated preview source digest mismatch: {id}')
        for kind in ('poster', 'gif', 'html'):
            if entry[kind] not in actual or not generated_file(entry[kind]).is_file():
                raise ValueError(f'Missing generated asset: {id}/{kind}')
    return lock


def preview_file(relative):
    path = (PREVIEWS / relative).resolve()
    if not path.is_relative_to(PREVIEWS.resolve()):
        raise ValueError('Preview path escapes assets directory')
    return path


def preview_catalog():
    lock = json.loads((ROOT / 'references/preview-lock.json').read_text())
    actual = {str(p.relative_to(PREVIEWS)): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in PREVIEWS.rglob('*') if p.is_file()}
    if actual != lock['sha256']:
        raise ValueError('Preview inventory or SHA256 mismatch')
    ids = {e['id'] for e in catalog() if e['s'] == 'X'}
    if set(lock['styles']) != ids:
        raise ValueError('Preview mapping must cover the exact X series')
    for entry in lock['styles'].values():
        if entry['file'] not in actual or not preview_file(entry['file']).read_bytes().startswith(b'GIF8'):
            raise ValueError('Invalid GIF preview')
    return lock


def catalog():
    html = (VENDOR / '风格挑选.html').read_text()
    match = re.search(r'<script id="data" type="application/json">(.*?)</script>', html, re.S)
    if not match:
        raise ValueError('Upstream picker data schema changed')
    return json.loads(match[1])['entries']


def license_for(entry):
    return 'MIT' if entry['s'] in {'L', 'V', 'X'} else 'upstream-custom-noncommercial'


def available(entry):
    text = source_file(entry['file']).read_text()
    parts = re.split(r'^## 风格提示词\s*$', text, maxsplit=1, flags=re.M)
    return bool(entry.get('name')) and (len(parts) == 1 or bool(parts[1].strip()))


def source_file(relative):
    path = (VENDOR / relative).resolve()
    if not path.is_relative_to(VENDOR.resolve()):
        raise ValueError('Source path escapes vendor directory')
    return path


def check():
    lock = json.loads(LOCK.read_text())
    actual = {str(p.relative_to(VENDOR)): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in VENDOR.rglob('*') if p.is_file()}
    if actual != lock['sha256']:
        raise ValueError('Vendor inventory or SHA256 mismatch')
    entries = catalog()
    stats = json.loads((VENDOR / '_统计.json').read_text())
    ids = [e['id'] for e in entries]
    if len(ids) != len(set(ids)) or len(ids) != stats['total']:
        raise ValueError('Catalog count or ID uniqueness mismatch')
    counts = {}
    for e in entries:
        counts[e['s']] = counts.get(e['s'], 0) + 1
        if not source_file(e['file']).is_file():
            raise ValueError(f"Missing prompt: {e['id']}")
        if e.get('img') and not source_file(e['img']).is_file():
            raise ValueError(f"Missing still: {e['id']}")
    prompts = {str(p.relative_to(VENDOR)) for p in (VENDOR / '风格提示词').rglob('*.md')}
    if prompts != {e['file'] for e in entries}:
        raise ValueError('Prompt file inventory differs from catalog')
    stills = {str(p.relative_to(VENDOR)) for p in (VENDOR / '风格提示词').rglob('*.jpg')}
    if stills != {e['img'] for e in entries if e.get('img')}:
        raise ValueError('Still inventory differs from catalog')
    if counts != stats['bySeries'] or len(stills) != stats['withStill']:
        raise ValueError('Series or still counts mismatch')
    placeholders = [e['id'] for e in entries if not available(e)]
    previews = preview_catalog()
    generated = generated_catalog()
    return {'status': 'pass', 'commit': lock['commit'], 'styles': len(ids),
            'generated_previews': len(generated['styles']),
            'supplemental_animated_previews': len(previews['styles']), 'preview_commit': previews['commit'],
            'usable_styles': len(ids) - len(placeholders), 'upstream_placeholders': placeholders,
            'stills': len(stills), 'files': len(actual), 'by_series': counts}


def picker_html():
    html = (VENDOR / '风格挑选.html').read_text()
    previews = preview_catalog()
    generated = generated_catalog()
    def overlay(match):
        data = json.loads(match[1])
        for entry in data['entries']:
            if entry['id'] in previews['styles']:
                entry['img'] = '/previews/' + previews['styles'][entry['id']]['file']
                entry['preview_source'] = previews['repository'] + '/blob/' + previews['commit'] + '/' + previews['styles'][entry['id']]['source_path']
            if entry['id'] in generated['styles']:
                item = generated['styles'][entry['id']]
                entry.update(img='/generated-previews/' + item['poster'],
                             animatedPreview='/generated-previews/' + item['gif'],
                             htmlPreview='/generated-previews/' + item['html'],
                             generatedPreview=True, previewLimitations=item['limitations'])
        return '<script id="data" type="application/json">' + json.dumps(data, ensure_ascii=False).replace('</', '<\\/') + '</script>'
    html = re.sub(r'<script id="data" type="application/json">(.*?)</script>', overlay, html, flags=re.S)
    revision = json.loads(LOCK.read_text())['commit']
    adapter = (ROOT / 'assets/picker-adapter.js').read_text()
    adapter = adapter.replace('__SOURCE_COMMIT__', revision)
    return html.replace('</body>', '<script>\n' + adapter + '\n</script>\n</body>')


class Handler(http.server.SimpleHTTPRequestHandler):
    def send_asset(self, path):
        if not path.is_file():
            return self.send_error(404)
        content = path.read_bytes()
        self.send_response(200)
        self.send_header('Content-Type', self.guess_type(str(path)))
        self.send_header('Content-Length', str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def do_GET(self):
        path = urlsplit(self.path).path
        if path in {'/', '/picker.html'}:
            content = picker_html().encode()
        elif path == '/demo.html':
            content = (ROOT / 'assets/word-rain.html').read_bytes()
        elif path.startswith('/previews/'):
            try:
                return self.send_asset(preview_file(unquote(path[len('/previews/'):])) )
            except ValueError:
                return self.send_error(403)
        elif path.startswith('/generated-previews/'):
            try:
                return self.send_asset(generated_file(unquote(path[len('/generated-previews/'):])) )
            except ValueError:
                return self.send_error(403)
        else:
            return super().do_GET()
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(content)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(content)

    def list_directory(self, path):
        self.send_error(403, 'Directory listing disabled')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    search = sub.add_parser('search', help='Search metadata without loading all prompts')
    search.add_argument('query', nargs='?', default='')
    search.add_argument('--license', choices=['MIT', 'custom'])
    show = sub.add_parser('show', help='Read one exact style ID and its shared code')
    show.add_argument('id')
    sub.add_parser('check', help='Verify source inventory and hashes')
    serve = sub.add_parser('serve', help='Serve visual picker on loopback only')
    serve.add_argument('--port', type=int, default=8765)
    args = parser.parse_args()
    if args.command == 'check':
        print(json.dumps(check(), ensure_ascii=False, indent=2))
    elif args.command == 'search':
        terms = args.query.casefold().split()
        matches = []
        for entry in catalog():
            fields = [entry.get(k, '') for k in ['id', 'name', 'en', 'cat', 'desc', 'fit']]
            if not available(entry):
                continue
            text = ' '.join(map(str, fields)) + ' ' + ' '.join(entry.get('tags', []))
            license_name = license_for(entry)
            if args.license and (args.license == 'MIT') != (license_name == 'MIT'):
                continue
            if all(term in text.casefold() for term in terms):
                matches.append({k: entry.get(k, '') for k in ['id', 'name', 'desc', 'fit', 'file']}
                               | {'license': license_name})
        print(json.dumps(matches, ensure_ascii=False, indent=2))
    elif args.command == 'show':
        entry = next((e for e in catalog() if e['id'].casefold() == args.id.casefold()), None)
        if entry is None:
            raise ValueError(f'Unknown style ID: {args.id}')
        if not available(entry):
            raise ValueError(f"Upstream placeholder has no usable prompt: {entry['id']}")
        print(f"Source: {entry['file']}\nLicense: {license_for(entry)}\n")
        print(source_file(entry['file']).read_text())
        if entry['s'] == 'AG':
            print('\n## Shared JavaScript reference\n')
            print((VENDOR / '风格提示词/A-G_代码样片/_公共函数.js').read_text())
    elif args.command == 'serve':
        check()
        handler = functools.partial(Handler, directory=str(VENDOR))
        with http.server.ThreadingHTTPServer(('127.0.0.1', args.port), handler) as server:
            print(f'http://127.0.0.1:{server.server_port}/picker.html', flush=True)
            try:
                server.serve_forever()
            except KeyboardInterrupt:
                pass


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, KeyError) as error:
        print(f'Error: {error}', file=sys.stderr)
        sys.exit(1)
