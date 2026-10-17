// ==UserScript==
// @name         YouTube → SmartTube PartyQueue
// @namespace    smarttube-partyqueue
// @version      2.1.0
// @match        https://www.youtube.com/watch*
// @grant        GM_xmlhttpRequest
// @connect      partyqueue.local
// ==/UserScript==
(() => {
  const PARTYQUEUE='http://partyqueue.local:8787';
  const TARGET_TV='ke75'; // Alternative z. B. kd70
  function addButton(){
    if(document.getElementById('partyqueue-add')) return;
    const b=document.createElement('button'); b.id='partyqueue-add'; b.textContent='🎉 Zur PartyQueue';
    Object.assign(b.style,{position:'fixed',right:'20px',bottom:'20px',zIndex:99999,padding:'14px',borderRadius:'12px',border:'0',background:'#2563eb',color:'white',fontWeight:'bold'});
    b.onclick=()=>{const name=localStorage.getItem('partyName')||prompt('Dein Name?')||'Gast';localStorage.setItem('partyName',name);GM_xmlhttpRequest({method:'POST',url:PARTYQUEUE+'/api/queue',headers:{'Content-Type':'application/json'},data:JSON.stringify({url:location.href,requested_by:name,target_tv:TARGET_TV}),onload:r=>alert(r.status<300?'Zur Queue hinzugefügt':'Fehler: '+r.responseText)})};
    document.body.appendChild(b);
  }
  new MutationObserver(addButton).observe(document.documentElement,{childList:true,subtree:true}); addButton();
})();
