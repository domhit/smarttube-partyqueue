// ==UserScript==
// @name         YouTube → SmartTube PartyQueue
// @namespace    smarttube-partyqueue
// @version      2.5
// @description Fügt Videos direkt zur PartyQueue hinzu
// @match        https://www.youtube.com/*
// @grant        GM_xmlhttpRequest
// @connect      *
// ==/UserScript==

(function () {

    'use strict';

    function addButton() {

        if (document.getElementById("partyqueue-add")) {
            return;
        }

        if (!document.body) {
            return;
        }

        const btn = document.createElement("button");

        btn.id = "partyqueue-add";
        btn.textContent = "🎉 PartyQueue";

        btn.style.position = "fixed";
        btn.style.bottom = "20px";
        btn.style.right = "20px";
        btn.style.zIndex = "999999";
        btn.style.background = "#2563eb";
        btn.style.color = "white";
        btn.style.border = "none";
        btn.style.padding = "14px";
        btn.style.borderRadius = "12px";
        btn.style.cursor = "pointer";

        btn.onclick = () => {

            alert(
                "PartyQueue Button funktioniert\n\n" +
                location.href
            );

        };

        document.body.appendChild(btn);

        console.log("PartyQueue Button erstellt");
    }

    window.addEventListener("load", addButton);

    setInterval(addButton, 3000);

})();