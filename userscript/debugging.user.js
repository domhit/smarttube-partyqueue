// ==UserScript==
// @name         PartyQueue Debug Test
// @namespace    smarttube-partyqueue
// @version      0.1
// @description Debug-Test für SmartTube PartyQueue
// @author       Dominic
// @match        https://www.youtube.com/*
// @match        https://youtube.com/*
// @grant        none
// ==/UserScript==

(function () {
    'use strict';

    console.log("PartyQueue Debug Script gestartet");

    function addButton() {

        console.log("addButton() aufgerufen");

        if (!document.body) {
            console.log("document.body noch nicht vorhanden");
            return;
        }

        if (document.getElementById("partyqueue-debug")) {
            console.log("Button existiert bereits");
            return;
        }

        const btn = document.createElement("button");

        btn.id = "partyqueue-debug";
        btn.textContent = "PARTYQUEUE TEST";

        btn.style.position = "fixed";
        btn.style.bottom = "20px";
        btn.style.right = "20px";
        btn.style.zIndex = "999999";
        btn.style.background = "red";
        btn.style.color = "white";
        btn.style.border = "none";
        btn.style.padding = "20px";
        btn.style.borderRadius = "12px";
        btn.style.fontSize = "18px";
        btn.style.fontWeight = "bold";
        btn.style.cursor = "pointer";

        btn.onclick = () => {
            alert("PartyQueue Debug erfolgreich");
        };

        document.body.appendChild(btn);

        console.log("Button erfolgreich eingefügt");
    }

    window.addEventListener("load", () => {
        console.log("window.load");
        addButton();
    });

    setTimeout(addButton, 1000);
    setTimeout(addButton, 3000);
    setTimeout(addButton, 5000);

})();