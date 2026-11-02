/* Local adapter; upstream picker is preserved byte-for-byte in vendor. */
(() => {
  const data = JSON.parse(document.getElementById('data').textContent);
  const generated = data.entries.filter(e => e.generatedPreview);
  const notice = document.createElement('p');
  notice.textContent = '本地适配：333 个可用提示词；8 个空条目已禁用。31 个原项目动画演示' + (generated.length ? '，另有 ' + generated.length + ' 个 DeepSeek Harness 生成示例（点击海报播放）' : '') + '。选好后点击「交给 agent · JSON」。';
  document.querySelector('h1').insertAdjacentElement('afterend', notice);
  // The picker now contains both original stills and supplemental animated GIFs.
  document.querySelectorAll('#f-img button').forEach(node => {
    node.textContent = node.textContent.replace('静帧', '预览').replace('没图', '没预览');
  });
  document.querySelectorAll('#stats span').forEach(node => {
    node.textContent = node.textContent.replace('有静帧', '有预览');
    if (generated.length) node.textContent = node.textContent.replace('个只有文字', '个空提示词条目');
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
  const reducedMotion = matchMedia('(prefers-reduced-motion: reduce)');
  const lightbox = document.getElementById('lb');
  const largeImage = document.getElementById('lb-img');
  const motionButton = document.createElement('button');
  motionButton.className = 'act';
  motionButton.id = 'generated-motion';
  motionButton.textContent = '播放动图';
  motionButton.hidden = true;
  document.getElementById('lb-pick').insertAdjacentElement('beforebegin', motionButton);
  function currentGenerated() {
    const src = largeImage.getAttribute('src');
    return generated.find(e => e.img === src || e.animatedPreview === src);
  }
  function updateGeneratedPreview(autoplay) {
    const entry = currentGenerated();
    motionButton.hidden = !entry || !lightbox.classList.contains('on');
    if (!entry) return;
    const play = autoplay && !reducedMotion.matches && lightbox.classList.contains('on');
    largeImage.src = play ? entry.animatedPreview : entry.img;
    motionButton.textContent = play ? '暂停动图' : '播放动图';
  }
  generated.forEach(e => {
    const card = document.getElementById('c-' + e.id);
    const img = card.querySelector('img');
    img.alt = e.id + ' ' + e.name + ' DeepSeek Harness 生成示例（点击播放）';
    img.addEventListener('click', () => updateGeneratedPreview(true));
    const note = document.createElement('p');
    note.textContent = 'DeepSeek Harness 生成示例 · ';
    const html = document.createElement('a');
    html.href = e.htmlPreview;
    html.target = '_blank';
    html.rel = 'noopener noreferrer';
    html.textContent = '打开完整 HTML';
    note.appendChild(html);
    card.appendChild(note);
    const limitations = document.createElement('details');
    const summary = document.createElement('summary');
    summary.textContent = '生成示例的局限';
    const text = document.createElement('p');
    text.textContent = e.previewLimitations;
    limitations.append(summary, text);
    card.appendChild(limitations);
  });
  motionButton.addEventListener('click', () => {
    const entry = currentGenerated();
    if (!entry) return;
    const play = largeImage.getAttribute('src') !== entry.animatedPreview;
    largeImage.src = play ? entry.animatedPreview : entry.img;
    motionButton.textContent = play ? '暂停动图' : '播放动图';
  });
  ['lb-prev', 'lb-next'].forEach(id => document.getElementById(id).addEventListener('click', () => updateGeneratedPreview(true)));
  document.getElementById('lb-close').addEventListener('click', () => updateGeneratedPreview(false));
  lightbox.addEventListener('click', event => { if (event.target === lightbox) updateGeneratedPreview(false); });
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape') updateGeneratedPreview(false);
    else if (event.key === 'ArrowLeft' || event.key === 'ArrowRight') updateGeneratedPreview(true);
  });
  reducedMotion.addEventListener('change', () => { if (reducedMotion.matches) updateGeneratedPreview(false); });
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
