// ==UserScript==
// @name         YouTube → SmartTube PartyQueue
// @namespace    smarttube-partyqueue
// @version      2.5.2
// @description  Fügt Videos aus YouTube-Watchseiten und Suchergebnissen direkt zur SmartTube PartyQueue hinzu
// @match        https://www.youtube.com/*
// @match        https://youtube.com/*
// @grant        GM_xmlhttpRequest
// @connect      *
// @run-at       document-idle
// ==/UserScript==

(() => {
  'use strict';

  const PARTYQUEUE = 'http://partyqueue.local:8787';
  const BUTTON_CLASS = 'partyqueue-result-button';
  let activeDialog = null;

  function request(method, path, data = null) {
    return new Promise((resolve, reject) => {
      GM_xmlhttpRequest({
        method,
        url: PARTYQUEUE + path,
        headers: data ? {'Content-Type': 'application/json'} : {},
        data: data ? JSON.stringify(data) : undefined,
        onload: (response) => {
          let body = {};
          try { body = JSON.parse(response.responseText); } catch (_) {}
          if (response.status >= 200 && response.status < 300) resolve(body);
          else reject(new Error(body.detail || `HTTP ${response.status}`));
        },
        onerror: () => reject(new Error('PartyQueue ist nicht erreichbar'))
      });
    });
  }

  function guestData() {
    let name = localStorage.partyqueue_name;
    if (!name) {
      name = prompt('Dein Name?') || 'Gast';
      localStorage.partyqueue_name = name;
    }
    let guestId = localStorage.partyqueue_gid;
    if (!guestId) {
      guestId = `g-${Date.now().toString(36)}-${Math.random().toString(36).slice(2)}`;
      localStorage.partyqueue_gid = guestId;
    }
    return {name, guestId};
  }

  function cleanVideoUrl(input) {
    const url = new URL(input, location.origin);
    const id = url.searchParams.get('v');
    if (!id) return null;
    return `${url.origin}/watch?v=${id}`;
  }

  function toast(message, ok = false) {
    let el = document.getElementById('partyqueue-toast');
    if (!el) {
      el = document.createElement('div');
      el.id = 'partyqueue-toast';
      document.body.appendChild(el);
    }
    el.textContent = message;
    el.className = `partyqueue-toast-show ${ok ? 'partyqueue-toast-ok' : 'partyqueue-toast-error'}`;
    clearTimeout(el.timer);
    el.timer = setTimeout(() => el.className = '', 4000);
  }

  async function enqueue(videoUrl, targetTv) {
    const guest = guestData();
    const result = await request('POST', '/api/queue', {
      url: videoUrl,
      requested_by: guest.name,
      guest_id: guest.guestId,
      target_tv: targetTv
    });
    localStorage.partyqueue_last_tv = targetTv;
    toast(`✓ Zur Queue hinzugefügt · Position ${result.position}`, true);
  }

  function closeDialog() {
    if (activeDialog) activeDialog.remove();
    activeDialog = null;
  }

  async function chooseTarget(videoUrl) {
    try {
      const party = await request('GET', '/api/party/public');
      if (party.queue_locked) throw new Error('Musikwünsche sind derzeit gesperrt');
      const devices = party.allowed_devices || [];
      if (!devices.length) throw new Error('Für diese Party ist kein Abspieler freigegeben');
      if (devices.length === 1) {
        await enqueue(videoUrl, devices[0].id);
        return;
      }

      closeDialog();
      const overlay = document.createElement('div');
      overlay.id = 'partyqueue-overlay';
      const lastTv = localStorage.partyqueue_last_tv || party.default_tv;
      overlay.innerHTML = `
        <div id="partyqueue-dialog">
          <button id="partyqueue-close" title="Schließen">×</button>
          <h2>🎉 Zur PartyQueue</h2>
          <p>Zielgerät auswählen</p>
          <div id="partyqueue-device-buttons"></div>
        </div>`;
      document.body.appendChild(overlay);
      activeDialog = overlay;
      overlay.onclick = (event) => { if (event.target === overlay) closeDialog(); };
      overlay.querySelector('#partyqueue-close').onclick = closeDialog;
      const holder = overlay.querySelector('#partyqueue-device-buttons');
      devices.forEach((device) => {
        const button = document.createElement('button');
        button.textContent = device.name;
        if (device.id === lastTv) button.classList.add('partyqueue-last-device');
        button.onclick = async () => {
          button.disabled = true;
          try {
            await enqueue(videoUrl, device.id);
            closeDialog();
          } catch (error) {
            button.disabled = false;
            toast(error.message);
          }
        };
        holder.appendChild(button);
      });
    } catch (error) {
      toast(error.message);
    }
  }

  function addWatchButton() {
    if (!location.pathname.startsWith('/watch') || document.getElementById('partyqueue-floating-button')) return;
    const videoUrl = cleanVideoUrl(location.href);
    if (!videoUrl || !document.body) return;
    const button = document.createElement('button');
    button.id = 'partyqueue-floating-button';
    button.textContent = '🎉 PartyQueue';
    button.onclick = () => chooseTarget(videoUrl);
    document.body.appendChild(button);
  }

  function decorateResults() {
    document.querySelectorAll('a#video-title[href*="/watch?v="], a.yt-lockup-metadata-view-model-wiz__title[href*="/watch?v="]').forEach((link) => {
      const renderer = link.closest('ytd-video-renderer, ytd-grid-video-renderer, ytd-compact-video-renderer, ytd-rich-item-renderer, yt-lockup-view-model') || link.parentElement;
      if (!renderer || renderer.querySelector(`.${BUTTON_CLASS}`)) return;
      const videoUrl = cleanVideoUrl(link.href);
      if (!videoUrl) return;
      const button = document.createElement('button');
      button.className = BUTTON_CLASS;
      button.textContent = '🎉 PartyQueue';
      button.title = 'Direkt zur PartyQueue hinzufügen';
      button.onclick = (event) => {
        event.preventDefault();
        event.stopPropagation();
        chooseTarget(videoUrl);
      };
      const target = renderer.querySelector('#meta, #metadata, #details, .yt-lockup-metadata-view-model-wiz__metadata') || link.parentElement;
      target.appendChild(button);
    });
  }

  document.addEventListener('contextmenu', (event) => {
    const link = event.target.closest('a[href*="/watch?v="]');
    if (!link || event.shiftKey) return;
    const videoUrl = cleanVideoUrl(link.href);
    if (!videoUrl) return;
    event.preventDefault();
    chooseTarget(videoUrl);
  }, true);

  function refresh() {
    addWatchButton();
    decorateResults();
  }

  const style = document.createElement('style');
  style.textContent = `
    #partyqueue-floating-button{position:fixed;right:20px;bottom:20px;z-index:999999;background:#2563eb;color:#fff;border:0;padding:14px 18px;border-radius:12px;font-weight:700;cursor:pointer;box-shadow:0 8px 24px #0008}
    .partyqueue-result-button{margin:8px 0 0 8px;background:#2563eb!important;color:#fff!important;border:0!important;padding:8px 11px!important;border-radius:10px!important;font-weight:700!important;cursor:pointer!important}
    #partyqueue-overlay{position:fixed;inset:0;z-index:1000000;background:#000a;display:flex;align-items:center;justify-content:center;padding:20px}
    #partyqueue-dialog{position:relative;width:min(440px,100%);background:#151c31;color:#fff;border:1px solid #475569;border-radius:18px;padding:24px;box-shadow:0 20px 70px #000}
    #partyqueue-close{position:absolute;right:12px;top:10px;background:transparent;color:#fff;border:0;font-size:28px;cursor:pointer}
    #partyqueue-device-buttons{display:grid;gap:10px;margin-top:16px}
    #partyqueue-device-buttons button{background:#2563eb;color:#fff;border:0;padding:13px;border-radius:12px;font-weight:700;cursor:pointer}
    #partyqueue-device-buttons button.partyqueue-last-device{outline:3px solid #22c55e}
    #partyqueue-toast{position:fixed;left:50%;top:22px;z-index:1000001;transform:translate(-50%,-30px);opacity:0;padding:15px 22px;border-radius:13px;color:#fff;font:700 15px system-ui;box-shadow:0 12px 35px #0008;transition:.2s;pointer-events:none}
    #partyqueue-toast.partyqueue-toast-show{opacity:1;transform:translate(-50%,0)}
    .partyqueue-toast-ok{background:#166534}.partyqueue-toast-error{background:#991b1b}
  `;
  document.documentElement.appendChild(style);
  new MutationObserver(refresh).observe(document.documentElement, {childList:true, subtree:true});
  document.addEventListener('yt-navigate-finish', refresh);
  window.addEventListener('load', refresh);
  setInterval(refresh, 2500);
  refresh();
})();
