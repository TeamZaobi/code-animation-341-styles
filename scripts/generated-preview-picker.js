/* Generated previews: posters first, click to load GIF; original media stays separate. */
(() => {
  const data = JSON.parse(document.getElementById("data").textContent);
  const generated = data.entries.filter(e => e.generatedPreview);
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
})();
