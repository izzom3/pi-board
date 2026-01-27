const PiBoard = (() => {
  let selected = new Set();

  function delaySeconds() {
    const el = document.getElementById('delaySeconds');
    const v = parseInt(el?.value ?? '10', 10);
    return Number.isFinite(v) && v > 0 ? v : 10;
  }

  function shuffleEnabled() {
    return Boolean(document.getElementById('shuffle')?.checked);
  }

  function updateButtons() {
    const playSelected = document.getElementById('playSelected');
    const showSingle = document.getElementById('showSingle');
    if (playSelected) playSelected.disabled = selected.size === 0;
    if (showSingle) showSingle.disabled = selected.size !== 1;
  }

  function toggle(card) {
    const filename = card?.dataset?.filename;
    if (!filename) return;

    if (selected.has(filename)) {
      selected.delete(filename);
      card.classList.remove('selected');
    } else {
      selected.add(filename);
      card.classList.add('selected');
    }
    updateButtons();
  }

  async function postJson(url, body) {
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body ?? {}),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      throw new Error(data.error || `Request failed: ${res.status}`);
    }
    return data;
  }

  async function startRandom() {
    await postJson('/api/display/start', {
      mode: 'random',
      delay_seconds: delaySeconds(),
    });
  }

  async function startSelected() {
    await postJson('/api/display/start', {
      mode: 'playlist',
      posters: Array.from(selected),
      delay_seconds: delaySeconds(),
      shuffle: shuffleEnabled(),
    });
  }

  async function showSingle() {
    const only = Array.from(selected)[0];
    await postJson('/api/display/start', {
      mode: 'single',
      poster: only,
    });
  }

  async function stop() {
    await postJson('/api/display/stop', {});
  }

  async function deletePoster(event, filename) {
    event?.stopPropagation?.();
    if (!confirm(`Delete ${filename}?`)) return;
    await postJson('/api/posters/delete', { filename });
    window.location.reload();
  }

  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') {
      selected.clear();
      document.querySelectorAll('.poster.selected').forEach((el) => el.classList.remove('selected'));
      updateButtons();
    }
  });

  window.addEventListener('load', updateButtons);

  return { toggle, startRandom, startSelected, showSingle, stop, deletePoster };
})();
