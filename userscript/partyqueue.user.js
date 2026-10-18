// ==UserScript==
// @name         YouTube → SmartTube PartyQueue
// @namespace    smarttube-partyqueue
// @version      2.4-test
// @description Fügt das aktuelle YouTube-Video direkt zur PartyQueue hinzu
// @author       Dominic
// @match        https://www.youtube.com/*
// @match        https://youtube.com/*
// @grant        GM_xmlhttpRequest
// @connect      *
// ==/UserScript==

(function () {

    'use strict';

    const PARTYQUEUE = "http://partyqueue.local:8787";

    function createButton() {

        if (!document.body) {
            return;
        }

        if (document.getElementById("partyqueue-add")) {
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
        btn.style.padding = "14px 18px";
        btn.style.borderRadius = "12px";
        btn.style.fontWeight = "bold";
        btn.style.cursor = "pointer";
        btn.style.boxShadow = "0 4px 12px rgba(0,0,0,0.4)";

        btn.onclick = () => {

            console.log("PartyQueue Klick");

            GM_xmlhttpRequest({
                method: "GET",
                url: PARTYQUEUE + "/api/party/public",

                onload: function (response) {

                    try {

                        const party = JSON.parse(response.responseText);

                        console.log("Party:", party);

                        const guestName =
                            localStorage.partyqueue_name ||
                            prompt("Dein Name?") ||
                            "Gast";

                        localStorage.partyqueue_name = guestName;

                        const guestId =
                            localStorage.partyqueue_guestid ||
                            Math.random().toString(36).substring(2);

                        localStorage.partyqueue_guestid = guestId;

                        let targetTv = party.default_tv;

                        if (
                            Array.isArray(party.allowed_devices) &&
                            party.allowed_devices.length > 1
                        ) {

                            const deviceList = party.allowed_devices
                                .map(d => `${d.id} = ${d.name}`)
                                .join("\n");

                            targetTv =
                                prompt(
                                    "Abspieler wählen:\n\n" + deviceList,
                                    party.default_tv
                                ) || party.default_tv;
                        }

                        GM_xmlhttpRequest({
                            method: "POST",
                            url: PARTYQUEUE + "/api/queue",

                            headers: {
                                "Content-Type": "application/json"
                            },

                            data: JSON.stringify({
                                url: location.href,
                                requested_by: guestName,
                                guest_id: guestId,
                                target_tv: targetTv
                            }),

                            onload: function (r) {

                                console.log("Antwort:", r.responseText);

                                if (r.status >= 200 && r.status < 300) {

                                    let data = {};

                                    try {
                                        data = JSON.parse(r.responseText);
                                    } catch (_) {}

                                    alert(
                                        "✅ Zur PartyQueue hinzugefügt\n\n" +
                                        "Position: " +
                                        (data.position || "?")
                                    );
                                } else {

                                    try {

                                        const err = JSON.parse(r.responseText);

                                        alert(
                                            "❌ Fehler\n\n" +
                                            err.detail
                                        );

                                    } catch (_) {

                                        alert(
                                            "❌ HTTP Fehler " +
                                            r.status
                                        );
                                    }
                                }
                            },

                            onerror: function (err) {

                                console.error(err);

                                alert(
                                    "❌ POST Fehler zur PartyQueue"
                                );
                            }
                        });

                    } catch (e) {

                        console.error(e);

                        alert(
                            "❌ PartyQueue-Antwort konnte nicht gelesen werden"
                        );
                    }
                },

                onerror: function (err) {

                    console.error(err);

                    alert(
                        "❌ PartyQueue nicht erreichbar"
                    );
                }
            });
        };

        document.body.appendChild(btn);

        console.log("PartyQueue Button eingefügt");
    }

    window.addEventListener("load", createButton);

    setInterval(createButton, 3000);

})();