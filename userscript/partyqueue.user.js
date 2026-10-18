// ==UserScript==
// @name         YouTube → SmartTube PartyQueue
// @namespace    smarttube-partyqueue
// @version      2.5.0
// @description  Fügt das aktuelle YouTube-Video direkt zur SmartTube PartyQueue hinzu
// @match        https://www.youtube.com/*
// @match        https://youtube.com/*
// @grant        GM_xmlhttpRequest
// @connect      *
// ==/UserScript==
(()=>{const PARTYQUEUE='http://partyqueue.local:8787';function req(o){GM_xmlhttpRequest(o)}function add(){if(!document.body||document.getElementById('partyqueue-add'))return;let b=document.createElement('button');b.id='partyqueue-add';b.textContent='🎉 PartyQueue';Object.assign(b.style,{position:'fixed',right:'20px',bottom:'20px',zIndex:999999,background:'#2563eb',color:'white',border:0,padding:'14px',borderRadius:'12px',fontWeight:'bold'});b.onclick=()=>req({method:'GET',url:PARTYQUEUE+'/api/party/public',onload:r=>{let p=JSON.parse(r.responseText);if(p.queue_locked)return alert('Musikwünsche gesperrt');let name=localStorage.partyqueue_name||prompt('Dein Name?')||'Gast';localStorage.partyqueue_name=name;let gid=localStorage.partyqueue_gid||(localStorage.partyqueue_gid='g-'+Date.now().toString(36)+Math.random().toString(36).slice(2));let tv=p.allowed_devices.length===1?p.allowed_devices[0].id:prompt(p.allowed_devices.map(x=>x.id+' = '+x.name).join('\n'),p.default_tv);req({method:'POST',url:PARTYQUEUE+'/api/queue',headers:{'Content-Type':'application/json'},data:JSON.stringify({url:location.href,requested_by:name,guest_id:gid,target_tv:tv}),onload:x=>{let j={};try{j=JSON.parse(x.responseText)}catch{}alert(x.status<300?'Zur Queue hinzugefügt · Position '+j.position:(j.detail||'Fehler'))}})}});document.body.appendChild(b)}window.addEventListener('load',add);setInterval(add,3000)})();
