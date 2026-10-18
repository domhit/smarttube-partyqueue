// ==UserScript==
// @name         YouTube → SmartTube PartyQueue V2.4
// @namespace    smarttube-partyqueue
// @version      2.4.1
// @description  Fügt das aktuelle YouTube-Video direkt zur SmartTube PartyQueue hinzu
// @match        https://www.youtube.com/*
// @match        https://youtube.com/*
// @grant        GM_xmlhttpRequest
// @connect      *
// ==/UserScript==
(() => {
  const PARTYQUEUE='http://partyqueue.local:8787';
  const get=(path,cb)=>GM_xmlhttpRequest({method:'GET',url:PARTYQUEUE+path,onload:r=>cb(JSON.parse(r.responseText))});
  function button(){if(document.getElementById('partyqueue-add'))return;const b=document.createElement('button');b.id='partyqueue-add';b.textContent='🎉 Wunsch hinzufügen';Object.assign(b.style,{position:'fixed',right:'20px',bottom:'20px',zIndex:99999,padding:'14px',borderRadius:'12px',border:0,background:'#2563eb',color:'#fff',fontWeight:'bold'});b.onclick=()=>get('/api/party/public',p=>{if(p.queue_locked)return alert('Musikwünsche sind derzeit gesperrt');let name=localStorage.partyName||prompt('Dein Name?')||'Gast';localStorage.partyName=name;let ids=p.allowed_devices,choice=ids.length===1?ids[0].id:prompt(`Zielgerät: ${ids.map(x=>x.id+'='+x.name).join(', ')}`,p.default_tv);if(!ids.some(x=>x.id===choice))return alert('Ungültiges Zielgerät');let makeId=()=>globalThis.crypto&&typeof globalThis.crypto.randomUUID==='function'?globalThis.crypto.randomUUID():'g-'+Date.now().toString(36)+'-'+Math.random().toString(36).slice(2);let gid=localStorage.guestId||(localStorage.guestId=makeId());GM_xmlhttpRequest({method:'POST',url:PARTYQUEUE+'/api/queue',headers:{'Content-Type':'application/json'},data:JSON.stringify({url:location.href,requested_by:name,guest_id:gid,target_tv:choice}),onload:r=>{let j={};try{j=JSON.parse(r.responseText)}catch{}alert(r.status<300?`Zur Queue hinzugefügt · Position ${j.position}`:(j.detail||'Fehler'))}})});document.body.appendChild(b)}
  new MutationObserver(button).observe(document.documentElement,{childList:true,subtree:true});button();
})();
