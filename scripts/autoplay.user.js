// ==UserScript==
// @name         Auto-Play Universal para Sitios de Streaming
// @namespace    tvbox.local
// @version      1.0
// @description  Hace clic automático en botones de Play y reproduce el video al abrir
// @match        *://*/*
// @run-at       document-idle
// @all-frames   true
// @grant        none
// ==/UserScript==

(function() {
    'use strict';

    let clicksRealizados = 0;
    const MAX_INTENTOS = 6;

    // Selectores habituales de botones de Play en reproductores de streaming
    const selectoresPlay = [
        '.vjs-big-play-button',
        '.jw-display-icon-container',
        '.plyr__control--overlaid',
        '[aria-label="Play"]',
        '[aria-label="Reproducir"]',
        '.play-btn',
        '#play',
        '.start-button',
        '.cover-play',
        'button.play'
    ];

    function intentarReproducir() {
        // 1. Intentar hacer click en botones gráficos de Play
        for (const selector of selectoresPlay) {
            const btn = document.querySelector(selector);
            if (btn && btn.offsetParent !== null) {
                btn.click();
                clicksRealizados++;
                break;
            }
        }

        // 2. Si hay elementos <video>, forzar reproducción
        const videos = document.querySelectorAll('video');
        videos.forEach(v => {
            if (v.paused) {
                v.play().catch(() => {
                    v.muted = true;
                    v.play();
                });
            }
        });

        if (clicksRealizados >= MAX_INTENTOS) {
            clearInterval(timer);
        }
    }

    const timer = setInterval(intentarReproducir, 700);
    setTimeout(() => clearInterval(timer), 12000);
})();
