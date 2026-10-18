const $ = (s) => document.querySelector(s);
const esc = (s) => String(s || '').replace(/[&<>"']/g, (c) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let state = null;
let formPartyId = null;
let formDirty = false;

$('#pw').value = sessionStorage.pw || '';
const headers = () => ({'content-type':'application/json','x-admin-password':$('#pw').value});
const body = (x) => JSON.stringify(x);
const selectedTv = () => $('#tv').value;

async function api(url, options = {}) {
  const response = await fetch(url, {...options, headers:{...headers(), ...(options.headers || {})}});
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.detail || 'Fehler');
  return data;
}

function toast(text, ok = false) {
  $('#msg').textContent = text;
  const el = $('#toast');
  el.textContent = text;
  el.className = `show ${ok ? 'toast-ok' : 'toast-err'}`;
  clearTimeout(window.partyToastTimer);
  window.partyToastTimer = setTimeout(() => el.className = '', 4000);
}

function options(items, value = 'id', label = 'name') {
  return items.map((x) => `<option value="${x[value]}">${esc(x[label])}</option>`).join('');
}

function fillPartyForm(s) {
  const p = s.party;
  $('#partyName').value = p.name;
  $('#playlist').innerHTML = options(s.playlists);
  $('#playlist').value = p.playlist_id ?? '';
  $('#defaultTv').innerHTML = options(s.all_devices);
  $('#defaultTv').value = p.default_tv;
  $('#devices').innerHTML = s.all_devices.map((d) =>
    `<label><input type="checkbox" data-device="${d.id}" ${p.allowed_devices.some((x) => x.id === d.id) ? 'checked' : ''}> ${esc(d.name)}</label>`
  ).join('');
  $('#limit').value = p.request_limit;
  $('#repeat').value = p.repeat_window;
  $('#upvotes').checked = !!p.upvote_sort;
  $('#externalSkip').checked = !!p.detect_external_skip;
  formPartyId = p.id;
  formDirty = false;
}

function bindDynamicButtons() {
  document.querySelectorAll('[data-delitem]').forEach((b) => b.onclick = () =>
    api(`/api/admin/playlists/item/${b.dataset.delitem}`, {method:'DELETE'}).catch((e) => toast(e.message))
  );
  document.querySelectorAll('[data-hist]').forEach((b) => b.onclick = () =>
    api('/api/admin/playlists/item', {method:'POST', body:body({playlist_id:+$('#playlist').value, history_id:+b.dataset.hist})})
      .then(() => toast('Zur Playlist hinzugefügt', true)).catch((e) => toast(e.message))
  );
}

function renderLiveState(s) {
  const p = s.party;
  $('#toggleLock').textContent = p.queue_locked ? '🔒 Wünsche gesperrt' : '🔓 Wünsche erlaubt';
  $('#lockBanner').textContent = p.queue_locked ? '🔒 Wunschannahme ist deaktiviert' : '🔓 Wunschannahme ist aktiv';
  $('#lockBanner').className = `banner ${p.queue_locked ? 'locked-banner' : 'open-banner'}`;

  const oldTv = $('#tv').value || p.default_tv;
  $('#tv').innerHTML = options(s.devices);
  $('#tv').value = s.devices.some((x) => x.id === oldTv) ? oldTv : p.default_tv;
  const tv = selectedTv();
  const current = s.current[tv];
  $('#current').innerHTML = current ? `<h3>${esc(current.title)}</h3><div class="muted">${esc(current.channel)}</div>` : 'Noch nichts';

  const queue = s.queue.filter((x) => x.target_tv === tv);
  $('#queue').innerHTML = queue.length ? queue.map((x) =>
    `<div class="queue-item"><img src="${x.thumbnail}"><div><b>${esc(x.title)}</b><div class="muted">${esc(x.requested_by)} · ▲ ${x.votes}</div></div></div>`
  ).join('') : 'Queue leer';

  $('#playlistItems').innerHTML = s.playlist_items.length ? s.playlist_items.map((x) =>
    `<div class="queue-item"><img src="${x.thumbnail}"><div><b>${esc(x.title)}</b><div class="muted">${esc(x.channel)}</div></div><button data-delitem="${x.id}" class="danger">Löschen</button></div>`
  ).join('') : 'Playlist leer';

  $('#history').innerHTML = s.history.length ? s.history.map((x) =>
    `<div class="queue-item"><img src="${x.thumbnail}"><div><b>${esc(x.title)}</b><div class="muted">${esc(x.requested_by)} · ${x.source} · ${x.status}</div></div><button data-hist="${x.id}">⭐</button></div>`
  ).join('') : 'Leer';
  bindDynamicButtons();
}

function draw(s) {
  state = s;
  if (!s.party) return;
  if (formPartyId !== s.party.id || !formDirty) fillPartyForm(s);
  renderLiveState(s);
}

$('#login').onclick = async () => {
  try {
    await api('/api/admin/login', {method:'POST', body:body({password:$('#pw').value})});
    sessionStorage.pw = $('#pw').value;
    $('#host').className = '';
    toast('Angemeldet', true);
  } catch (e) { toast(e.message); }
};

['partyName','playlist','defaultTv','limit','repeat','upvotes','externalSkip'].forEach((id) => {
  $(`#${id}`).addEventListener('input', () => formDirty = true);
  $(`#${id}`).addEventListener('change', () => formDirty = true);
});
$('#devices').addEventListener('change', () => formDirty = true);

$('#saveParty').onclick = async () => {
  try {
    await api('/api/admin/party', {method:'PATCH', body:body({
      name:$('#partyName').value,
      playlist_id:+$('#playlist').value,
      allowed_devices:[...document.querySelectorAll('[data-device]:checked')].map((x) => x.dataset.device),
      default_tv:$('#defaultTv').value,
      request_limit:+$('#limit').value,
      repeat_window:+$('#repeat').value,
      upvote_sort:$('#upvotes').checked,
      detect_external_skip:$('#externalSkip').checked
    })});
    formDirty = false;
    toast('Party gespeichert', true);
  } catch (e) { toast(e.message); }
};

$('#toggleLock').onclick = () => api('/api/admin/party', {method:'PATCH', body:body({queue_locked:!state.party.queue_locked})}).catch((e) => toast(e.message));
$('#start').onclick = () => api('/api/admin/start', {method:'POST', body:body({target_tv:selectedTv()})}).catch((e) => toast(e.message));
$('#skip').onclick = () => api('/api/admin/skip', {method:'POST', body:body({target_tv:selectedTv()})}).catch((e) => toast(e.message));
$('#tv').onchange = () => state && renderLiveState(state);
$('#createPlaylist').onclick = () => api('/api/admin/playlists', {method:'POST', body:body({name:$('#newPlaylistName').value})}).then(() => toast('Playlist erstellt', true)).catch((e) => toast(e.message));
$('#importPlaylist').onclick = () => api('/api/admin/playlists/import', {method:'POST', body:body({playlist_id:+$('#playlist').value,playlist:$('#playlistUrl').value})}).then((x) => toast(`${x.added} Titel importiert`, true)).catch((e) => toast(e.message));
$('#newParty').onclick = () => {
  const name = prompt('Name der neuen Party');
  if (!name) return;
  api('/api/admin/parties', {method:'POST', body:body({name,playlist_id:+$('#playlist').value,allowed_devices:[...document.querySelectorAll('[data-device]:checked')].map((x) => x.dataset.device),default_tv:$('#defaultTv').value,request_limit:+$('#limit').value,repeat_window:+$('#repeat').value,upvote_sort:true})}).then(() => {formDirty=false;formPartyId=null;toast('Neue Party aktiv',true)}).catch((e) => toast(e.message));
};
document.querySelectorAll('[data-export]').forEach((b) => b.onclick = () => window.open(`/api/party/${state.party.id}/export/${b.dataset.export}?password=${encodeURIComponent($('#pw').value)}`));
$('#loadStats').onclick = () => api('/api/admin/stats').then((a) => $('#stats').innerHTML = a.map((x) => `<p><b>${esc(x.title)}</b>: ${x.played_total}× gesamt, ${x.requested_total}× gewünscht, ${x.skipped_total}× übersprungen, ${x.votes_total || 0} Votes</p>`).join('')).catch((e) => toast(e.message));

const ws = new WebSocket(`${location.protocol === 'https:' ? 'wss' : 'ws'}://${location.host}/ws`);
ws.onmessage = (e) => draw(JSON.parse(e.data));
ws.onopen = () => ws.send('hi');
