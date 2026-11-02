import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import {fileURLToPath} from 'node:url';

const directory = process.argv[2] || fileURLToPath(new URL('../生成示例/html/', import.meta.url));
const files = fs.readdirSync(directory).filter(name => name.endsWith('.html'));
if (files.length !== 109) throw new Error(`Expected 109 playback blocks, found ${files.length}`);
const failures = [];
for (const name of files) {
  try {
    const html = fs.readFileSync(path.join(directory, name), 'utf8');
    const start = html.indexOf("  const playBtn = document.getElementById('play');");
    const end = html.indexOf('  if (EXPORT) {', start);
    if (start < 0 || end < 0) throw new Error('Playback block not found');
    const pending = new Map();
    const elements = new Map();
    let sequence = 0;
    const context = {
      document: {getElementById(id) {
        if (!elements.has(id)) elements.set(id, {textContent: '', value: '', addEventListener() {}});
        return elements.get(id);
      }},
      window: {matchMedia: () => ({matches: false}), addEventListener() {}},
      performance: {now: () => 0},
      requestAnimationFrame(callback) { const id = ++sequence; pending.set(id, callback); return id; },
      cancelAnimationFrame(id) { pending.delete(id); },
      paint() {}, EXPORT: false, DURATION: 6,
    };
    vm.createContext(context);
    vm.runInContext(html.slice(start, end), context);
    for (let iteration = 0; iteration < 5; iteration++) {
      vm.runInContext('play(); pause(); play();', context);
      if (pending.size !== 1) throw new Error(`rapid play/pause/play leaves ${pending.size} callbacks`);
      const frame = [...pending.entries()];
      for (const [id, callback] of frame) { pending.delete(id); callback(16 + iteration * 16); }
      if (pending.size !== 1) throw new Error(`frame tick leaves ${pending.size} loops`);
      vm.runInContext('pause();', context);
      if (pending.size !== 0) throw new Error(`pause leaves ${pending.size} callbacks`);
    }
  } catch (error) {
    failures.push(`${name}: ${error.message}`);
  }
}
if (failures.length) {
  console.error(failures.slice(0, 8).join('\n'));
  console.error(`FAIL: ${failures.length}/${files.length} generated playback blocks`);
  process.exitCode = 1;
} else {
  console.log(`PASS: ${files.length} playback blocks maintain one loop, cancel on pause and survive five rapid-toggle cycles`);
}
