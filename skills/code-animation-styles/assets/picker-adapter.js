/* Local adapter; upstream picker is preserved byte-for-byte in vendor. */
(() => {
  const data = JSON.parse(document.getElementById('data').textContent);
  const notice = document.createElement('p');
  notice.textContent = '本地适配：333 个可用提示词；8 个空条目已禁用。X 系列已补齐 31 个原项目动画演示。选好后点击「交给 agent · JSON」。';
  document.querySelector('h1').insertAdjacentElement('afterend', notice);
  // The picker now contains both original stills and supplemental animated GIFs.
  document.querySelectorAll('#f-img button').forEach(node => {
    node.textContent = node.textContent.replace('静帧', '预览').replace('没图', '没预览');
  });
  document.querySelectorAll('#stats span').forEach(node => {
    node.textContent = node.textContent.replace('有静帧', '有预览');
  });
  document.querySelectorAll('#grid img').forEach(img => {
    img.loading = 'lazy';
    img.decoding = 'async';
  });
  data.entries.filter(e => e.preview_source).forEach(e => {
    const card = document.getElementById('c-' + e.id);
    const note = document.createElement('p');
    note.append('动画演示 · ');
    const link = document.createElement('a');
    link.href = e.preview_source;
    link.target = '_blank';
    link.rel = 'noopener noreferrer';
    link.textContent = 'code-video 原项目';
    note.appendChild(link);
    card.appendChild(note);
    card.querySelector('img').alt = e.id + ' ' + e.name + ' 原项目动画演示';
  });
  const button = document.createElement('button');
  button.className = 'act primary';
  button.id = 'agent-export';
  button.textContent = '交给 agent · JSON';
  document.getElementById('export').insertAdjacentElement('afterend', button);
  const download = document.createElement('button');
  download.className = 'act';
  download.textContent = '下载 JSON';
  download.id = 'agent-download';
  document.getElementById('dlg-dl').insertAdjacentElement('afterend', download);
  const selection = () => {
    // Visible controls remain authoritative when browser storage is disabled.
    const checked = Array.from(document.querySelectorAll('#grid input[type=checkbox]:checked'));
    const names = new Set(checked.map(node => node.getAttribute('aria-label')));
    const selected = data.entries.filter(e => e.name && names.has('选 ' + e.id + ' ' + e.name)).map(e => e.id);
    return {schema_version: 1, source_commit: '__SOURCE_COMMIT__', style_ids: selected};
  };
  data.entries.filter(e => !e.name).forEach(e => {
    const card = document.getElementById('c-' + e.id);
    const checkbox = card.querySelector('input[type=checkbox]');
    if (checkbox.checked) checkbox.click();
    checkbox.disabled = true;
    const note = document.createElement('p');
    note.textContent = '上游占位条目，暂无风格提示词。';
    card.appendChild(note);
  });
  button.addEventListener('click', () => {
    document.getElementById('export').click();
    const text = document.getElementById('dlg-text');
    text.value = JSON.stringify(selection(), null, 2);
    text.focus();
    text.select();
    document.getElementById('dlg-msg').textContent = '选好后告诉 agent「选好了」；也可复制或下载 JSON。';
  });
  download.addEventListener('click', () => {
    const blob = new Blob([JSON.stringify(selection(), null, 2)], {type: 'application/json'});
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'animation-style-selection.json';
    link.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  });
})();
