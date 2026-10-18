// ==UserScript==
// @name         YouTube → SmartTube PartyQueue
// @namespace    smarttube-partyqueue
// @version      2.5.3
// @description  Fügt Videos aus YouTube-Watchseiten und Suchergebnissen direkt zur SmartTube PartyQueue hinzu
// @author       Dominic
// @match        https://www.youtube.com/*
// @match        https://youtube.com/*
// @grant        GM_xmlhttpRequest
// @connect      *
// @run-at       document-idle
// ==/UserScript==

(() => {
    'use strict';

    /*
     * PartyQueue-Adresse anpassen.
     *
     * Beispiele:
     * const PARTYQUEUE = 'http://192.168.178.20:8787';
     * const PARTYQUEUE = 'http://partyqueue.local:8787';
     */
    const PARTYQUEUE = 'http://partyqueue.local:8787';

    const RESULT_BUTTON_CLASS = 'partyqueue-result-button';

    let activeDialog = null;
    let refreshScheduled = false;

    /**
     * API-Anfrage über Tampermonkey.
     */
    function request(method, path, data = null) {
        return new Promise((resolve, reject) => {
            GM_xmlhttpRequest({
                method,
                url: PARTYQUEUE + path,

                headers: data
                    ? {
                        'Content-Type': 'application/json'
                    }
                    : {},

                data: data
                    ? JSON.stringify(data)
                    : undefined,

                timeout: 15000,

                onload(response) {
                    let responseData = {};

                    try {
                        responseData = JSON.parse(response.responseText);
                    } catch (_) {
                        responseData = {};
                    }

                    if (
                        response.status >= 200 &&
                        response.status < 300
                    ) {
                        resolve(responseData);
                        return;
                    }

                    reject(
                        new Error(
                            responseData.detail ||
                            `HTTP-Fehler ${response.status}`
                        )
                    );
                },

                onerror() {
                    reject(
                        new Error(
                            'PartyQueue ist nicht erreichbar'
                        )
                    );
                },

                ontimeout() {
                    reject(
                        new Error(
                            'Zeitüberschreitung beim Zugriff auf die PartyQueue'
                        )
                    );
                }
            });
        });
    }

    /**
     * Liest beziehungsweise erstellt die lokale Gast-ID.
     */
    function createGuestId() {
        if (
            globalThis.crypto &&
            typeof globalThis.crypto.randomUUID === 'function'
        ) {
            return globalThis.crypto.randomUUID();
        }

        return (
            'g-' +
            Date.now().toString(36) +
            '-' +
            Math.random().toString(36).slice(2) +
            Math.random().toString(36).slice(2)
        );
    }

    /**
     * Gastname und Gast-ID laden.
     */
    function getGuestData() {
        let name = localStorage.getItem(
            'partyqueue_name'
        );

        if (!name) {
            name =
                window.prompt('Dein Name?') ||
                'Gast';

            localStorage.setItem(
                'partyqueue_name',
                name
            );
        }

        let guestId = localStorage.getItem(
            'partyqueue_guest_id'
        );

        if (!guestId) {
            guestId = createGuestId();

            localStorage.setItem(
                'partyqueue_guest_id',
                guestId
            );
        }

        return {
            name,
            guestId
        };
    }

    /**
     * Entfernt Playlist-, Zeit- und Trackingparameter.
     */
    function cleanVideoUrl(input) {
        try {
            const url = new URL(
                input,
                window.location.origin
            );

            const videoId =
                url.searchParams.get('v');

            if (!videoId) {
                return null;
            }

            return (
                url.origin +
                '/watch?v=' +
                encodeURIComponent(videoId)
            );
        } catch (_) {
            return null;
        }
    }

    /**
     * Generische DOM-Hilfe.
     */
    function createElement(
        tagName,
        options = {}
    ) {
        const element =
            document.createElement(tagName);

        if (options.id) {
            element.id = options.id;
        }

        if (options.className) {
            element.className =
                options.className;
        }

        if (
            options.text !== undefined
        ) {
            element.textContent =
                options.text;
        }

        if (options.title) {
            element.title =
                options.title;
        }

        if (options.type) {
            element.type =
                options.type;
        }

        return element;
    }

    /**
     * Toast-Nachricht darstellen.
     */
    function showToast(
        message,
        success = false
    ) {
        let toast =
            document.getElementById(
                'partyqueue-toast'
            );

        if (!toast) {
            toast = createElement('div', {
                id: 'partyqueue-toast'
            });

            document.body.appendChild(toast);
        }

        toast.textContent = message;

        toast.className =
            'partyqueue-toast-show ' +
            (
                success
                    ? 'partyqueue-toast-success'
                    : 'partyqueue-toast-error'
            );

        window.clearTimeout(
            toast.partyQueueTimer
        );

        toast.partyQueueTimer =
            window.setTimeout(() => {
                toast.className = '';
            }, 4000);
    }

    /**
     * Titel an ein Zielgerät senden.
     */
    async function enqueueVideo(
        videoUrl,
        targetTv
    ) {
        const guest = getGuestData();

        const result = await request(
            'POST',
            '/api/queue',
            {
                url: videoUrl,
                requested_by: guest.name,
                guest_id: guest.guestId,
                target_tv: targetTv
            }
        );

        localStorage.setItem(
            'partyqueue_last_tv',
            targetTv
        );

        const position =
            result.position ?? '?';

        showToast(
            `✓ Zur Queue hinzugefügt · Position ${position}`,
            true
        );
    }

    /**
     * Offenen Dialog schließen.
     */
    function closeDialog() {
        if (activeDialog) {
            activeDialog.remove();
        }

        activeDialog = null;
    }

    /**
     * Dialogtitel erzeugen.
     */
    function createDialogHeader() {
        const header =
            createElement('div', {
                className:
                    'partyqueue-dialog-header'
            });

        const heading =
            createElement('h2', {
                text: '🎉 Zur PartyQueue'
            });

        const closeButton =
            createElement('button', {
                id: 'partyqueue-close',
                text: '×',
                title: 'Schließen',
                type: 'button'
            });

        closeButton.addEventListener(
            'click',
            closeDialog
        );

        header.appendChild(heading);
        header.appendChild(closeButton);

        return header;
    }

    /**
     * Geräteauswahl öffnen.
     */
    async function chooseTarget(videoUrl) {
        try {
            const party = await request(
                'GET',
                '/api/party/public'
            );

            if (party.queue_locked) {
                throw new Error(
                    'Musikwünsche sind derzeit gesperrt'
                );
            }

            const devices =
                Array.isArray(
                    party.allowed_devices
                )
                    ? party.allowed_devices
                    : [];

            if (devices.length === 0) {
                throw new Error(
                    'Für diese Party ist kein Abspieler freigegeben'
                );
            }

            /*
             * Bei genau einem freigegebenen TV
             * direkt hinzufügen.
             */
            if (devices.length === 1) {
                await enqueueVideo(
                    videoUrl,
                    devices[0].id
                );

                return;
            }

            closeDialog();

            const overlay =
                createElement('div', {
                    id: 'partyqueue-overlay'
                });

            const dialog =
                createElement('div', {
                    id: 'partyqueue-dialog'
                });

            const description =
                createElement('p', {
                    text: 'Zielgerät auswählen'
                });

            const deviceButtons =
                createElement('div', {
                    id:
                        'partyqueue-device-buttons'
                });

            dialog.appendChild(
                createDialogHeader()
            );

            dialog.appendChild(
                description
            );

            dialog.appendChild(
                deviceButtons
            );

            overlay.appendChild(dialog);
            document.body.appendChild(overlay);

            activeDialog = overlay;

            overlay.addEventListener(
                'click',
                event => {
                    if (event.target === overlay) {
                        closeDialog();
                    }
                }
            );

            const lastTv =
                localStorage.getItem(
                    'partyqueue_last_tv'
                ) ||
                party.default_tv;

            devices.forEach(device => {
                const button =
                    createElement('button', {
                        text: device.name,
                        type: 'button'
                    });

                button.dataset.targetTv =
                    device.id;

                if (device.id === lastTv) {
                    button.classList.add(
                        'partyqueue-last-device'
                    );
                }

                button.addEventListener(
                    'click',
                    async () => {
                        const allButtons =
                            deviceButtons
                                .querySelectorAll(
                                    'button'
                                );

                        allButtons.forEach(
                            item => {
                                item.disabled = true;
                            }
                        );

                        button.textContent =
                            'Wird hinzugefügt …';

                        try {
                            await enqueueVideo(
                                videoUrl,
                                device.id
                            );

                            closeDialog();
                        } catch (error) {
                            allButtons.forEach(
                                item => {
                                    item.disabled = false;
                                }
                            );

                            button.textContent =
                                device.name;

                            showToast(
                                error.message
                            );
                        }
                    }
                );

                deviceButtons.appendChild(
                    button
                );
            });
        } catch (error) {
            showToast(error.message);
        }
    }

    /**
     * Schwebenden Button auf einer Watch-Seite
     * hinzufügen.
     */
    function addWatchButton() {
        if (
            !window.location.pathname
                .startsWith('/watch')
        ) {
            const existing =
                document.getElementById(
                    'partyqueue-floating-button'
                );

            if (existing) {
                existing.remove();
            }

            return;
        }

        if (
            document.getElementById(
                'partyqueue-floating-button'
            )
        ) {
            return;
        }

        if (!document.body) {
            return;
        }

        const videoUrl =
            cleanVideoUrl(
                window.location.href
            );

        if (!videoUrl) {
            return;
        }

        const button =
            createElement('button', {
                id:
                    'partyqueue-floating-button',
                text: '🎉 PartyQueue',
                title:
                    'Video zur PartyQueue hinzufügen',
                type: 'button'
            });

        button.addEventListener(
            'click',
            event => {
                event.preventDefault();
                event.stopPropagation();

                chooseTarget(videoUrl);
            }
        );

        document.body.appendChild(button);
    }

    /**
     * Videolink aus einem Suchergebnis beziehungsweise
     * einer Videokarte ermitteln.
     */
    function findVideoLink(renderer) {
        return renderer.querySelector(
            [
                'a#video-title[href*="/watch?v="]',
                'a[href*="/watch?v="][title]',
                'a.yt-lockup-metadata-view-model-wiz__title[href*="/watch?v="]'
            ].join(',')
        );
    }

    /**
     * Geeigneten Container für den PartyQueue-Button
     * innerhalb einer YouTube-Karte finden.
     */
    function findButtonTarget(
        renderer,
        link
    ) {
        return (
            renderer.querySelector(
                [
                    '#meta',
                    '#metadata',
                    '#details',
                    '#dismissible',
                    '.yt-lockup-metadata-view-model-wiz__metadata'
                ].join(',')
            ) ||
            link.parentElement ||
            renderer
        );
    }

    /**
     * Eine einzelne YouTube-Videokarte dekorieren.
     */
    function decorateRenderer(renderer) {
        if (
            renderer.querySelector(
                `.${RESULT_BUTTON_CLASS}`
            )
        ) {
            return;
        }

        const link =
            findVideoLink(renderer);

        if (!link) {
            return;
        }

        const videoUrl =
            cleanVideoUrl(link.href);

        if (!videoUrl) {
            return;
        }

        const button =
            createElement('button', {
                className:
                    RESULT_BUTTON_CLASS,
                text: '🎉 PartyQueue',
                title:
                    'Direkt zur PartyQueue hinzufügen',
                type: 'button'
            });

        button.dataset.videoUrl =
            videoUrl;

        button.addEventListener(
            'click',
            event => {
                event.preventDefault();
                event.stopPropagation();
                event.stopImmediatePropagation();

                chooseTarget(videoUrl);
            },
            true
        );

        const target =
            findButtonTarget(
                renderer,
                link
            );

        target.appendChild(button);
    }

    /**
     * Suchergebnisse, Empfehlungen und Videokarten
     * nachträglich dekorieren.
     */
    function decorateResults() {
        const selectors = [
            'ytd-video-renderer',
            'ytd-grid-video-renderer',
            'ytd-compact-video-renderer',
            'ytd-rich-item-renderer',
            'yt-lockup-view-model'
        ];

        document
            .querySelectorAll(
                selectors.join(',')
            )
            .forEach(decorateRenderer);
    }

    /**
     * Kontextmenü auf Videolinks abfangen.
     *
     * Shift + Rechtsklick öffnet weiterhin
     * das originale Browser-Kontextmenü.
     */
    function handleContextMenu(event) {
        if (event.shiftKey) {
            return;
        }

        const target =
            event.target instanceof Element
                ? event.target
                : null;

        if (!target) {
            return;
        }

        const link =
            target.closest(
                'a[href*="/watch?v="]'
            );

        if (!link) {
            return;
        }

        const videoUrl =
            cleanVideoUrl(link.href);

        if (!videoUrl) {
            return;
        }

        event.preventDefault();
        event.stopPropagation();

        chooseTarget(videoUrl);
    }

    /**
     * CSS ausschließlich über textContent setzen.
     * Auch dies ist Trusted-Types-sicher.
     */
    function installStyles() {
        if (
            document.getElementById(
                'partyqueue-userscript-style'
            )
        ) {
            return;
        }

        const style =
            createElement('style', {
                id:
                    'partyqueue-userscript-style'
            });

        style.textContent = `
            #partyqueue-floating-button {
                position: fixed;
                right: 20px;
                bottom: 20px;
                z-index: 999999;
                background: #2563eb;
                color: #ffffff;
                border: 0;
                padding: 14px 18px;
                border-radius: 12px;
                font-weight: 700;
                cursor: pointer;
                box-shadow: 0 8px 24px rgba(0,0,0,.55);
            }

            .partyqueue-result-button {
                display: inline-flex !important;
                align-items: center !important;
                justify-content: center !important;
                width: auto !important;
                min-height: 34px !important;
                margin: 8px 6px 4px 0 !important;
                background: #2563eb !important;
                color: #ffffff !important;
                border: 0 !important;
                padding: 8px 11px !important;
                border-radius: 10px !important;
                font-family: system-ui, sans-serif !important;
                font-size: 13px !important;
                font-weight: 700 !important;
                line-height: 1 !important;
                cursor: pointer !important;
            }

            .partyqueue-result-button:hover,
            #partyqueue-floating-button:hover {
                background: #1d4ed8 !important;
            }

            #partyqueue-overlay {
                position: fixed;
                inset: 0;
                z-index: 1000000;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 20px;
                background: rgba(0,0,0,.72);
                font-family: system-ui, sans-serif;
            }

            #partyqueue-dialog {
                width: min(440px, 100%);
                padding: 24px;
                color: #ffffff;
                background: #151c31;
                border: 1px solid #475569;
                border-radius: 18px;
                box-shadow: 0 20px 70px rgba(0,0,0,.8);
            }

            .partyqueue-dialog-header {
                display: flex;
                align-items: center;
                justify-content: space-between;
                gap: 16px;
            }

            .partyqueue-dialog-header h2 {
                margin: 0;
                color: #ffffff;
                font-size: 22px;
            }

            #partyqueue-close {
                padding: 0;
                color: #ffffff;
                background: transparent;
                border: 0;
                font-size: 30px;
                line-height: 1;
                cursor: pointer;
            }

            #partyqueue-dialog p {
                margin: 14px 0;
                color: #cbd5e1;
                font-size: 15px;
            }

            #partyqueue-device-buttons {
                display: grid;
                gap: 10px;
                margin-top: 16px;
            }

            #partyqueue-device-buttons button {
                width: 100%;
                padding: 13px;
                color: #ffffff;
                background: #2563eb;
                border: 0;
                border-radius: 12px;
                font-family: system-ui, sans-serif;
                font-size: 15px;
                font-weight: 700;
                cursor: pointer;
            }

            #partyqueue-device-buttons button:hover {
                background: #1d4ed8;
            }

            #partyqueue-device-buttons button:disabled {
                opacity: .55;
                cursor: wait;
            }

            #partyqueue-device-buttons
            button.partyqueue-last-device {
                outline: 3px solid #22c55e;
                outline-offset: 2px;
            }

            #partyqueue-toast {
                position: fixed;
                left: 50%;
                top: 22px;
                z-index: 1000001;
                max-width: min(520px, 90vw);
                padding: 15px 22px;
                color: #ffffff;
                border-radius: 13px;
                box-shadow: 0 12px 35px rgba(0,0,0,.6);
                font-family: system-ui, sans-serif;
                font-size: 15px;
                font-weight: 700;
                text-align: center;
                pointer-events: none;
                opacity: 0;
                transform: translate(-50%, -30px);
                transition:
                    opacity .2s ease,
                    transform .2s ease;
            }

            #partyqueue-toast.partyqueue-toast-show {
                opacity: 1;
                transform: translate(-50%, 0);
            }

            #partyqueue-toast.partyqueue-toast-success {
                background: #166534;
            }

            #partyqueue-toast.partyqueue-toast-error {
                background: #991b1b;
            }
        `;

        document.documentElement.appendChild(
            style
        );
    }

    /**
     * Mehrere DOM-Updates zu einem Refresh bündeln.
     */
    function scheduleRefresh() {
        if (refreshScheduled) {
            return;
        }

        refreshScheduled = true;

        window.requestAnimationFrame(() => {
            refreshScheduled = false;

            installStyles();
            addWatchButton();
            decorateResults();
        });
    }

    /*
     * YouTube ist eine Single-Page-App.
     * Deshalb reagieren wir sowohl auf DOM-Änderungen
     * als auch auf YouTubes Navigationsevent.
     */
    const observer =
        new MutationObserver(
            scheduleRefresh
        );

    observer.observe(
        document.documentElement,
        {
            childList: true,
            subtree: true
        }
    );

    document.addEventListener(
        'yt-navigate-finish',
        scheduleRefresh
    );

    document.addEventListener(
        'contextmenu',
        handleContextMenu,
        true
    );

    window.addEventListener(
        'load',
        scheduleRefresh
    );

    window.setInterval(
        scheduleRefresh,
        2500
    );

    scheduleRefresh();
})();