// Hydra TV Shield - Acelerador y Neutralizador de Anuncios y Trampas
(function() {
  'use strict';

  const host = window.location.hostname.toLowerCase();
  
  if (host === 'localhost' || host === '127.0.0.1' || window.location.port === '5000' ||
      host.includes('brave') || host.includes('google') || host.includes('youtube') || host.includes('github')) {
    return;
  }

  const isEmbedded = (window.self !== window.top);

  // No intervenir en reproductores de streaming directos (cyberlockers de video crudo)
  if (isEmbedded && (
      host.includes('streamwish') || host.includes('vidhide') || host.includes('voe') ||
      host.includes('dood') || host.includes('filemoon') || host.includes('streamtape') ||
      host.includes('waaw') || host.includes('netu')
  )) {
    return;
  }

  // 1. Estilos Anti-Publicidad y Modo Pantalla Completa Limpio
  function inyectarEstilosAntiPublicidad() {
    if (document.getElementById('hydra-shield-antiad-style')) return;
    const style = document.createElement('style');
    style.id = 'hydra-shield-antiad-style';
    style.textContent = `
      /* Ocultar banners publicitarios conocidos y trampas flotantes */
      .bannerAds, .banner_bannerAds__PHIkK, [class*="bannerAds"],
      .floating-banner, .ribbon-1, [class*="floating-banner"],
      #player-advertising, ins.adsbygoogle, .ad-placement,
      #mdl-downloads {
        display: none !important;
        visibility: hidden !important;
        pointer-events: none !important;
        height: 0 !important;
        overflow: hidden !important;
      }

      /* =========================================================================
         MODO PANTALLA COMPLETA LIMPIO (Solo se activa al presionar Pantalla Completa)
         ========================================================================= */
      html.hydra-is-fullscreen,
      html.hydra-is-fullscreen body {
        overflow: hidden !important;
        background: #000 !important;
        margin: 0 !important;
        padding: 0 !important;
        width: 100vw !important;
        height: 100vh !important;
      }

      html.hydra-is-fullscreen .video-container,
      html.hydra-is-fullscreen .TPlayer,
      html.hydra-is-fullscreen .TPlayerCn,
      html.hydra-is-fullscreen .embed_div,
      html.hydra-is-fullscreen #video,
      html.hydra-is-fullscreen #player,
      html.hydra-is-fullscreen #reproductor,
      html.hydra-is-fullscreen .player-placeholder,
      html.hydra-is-fullscreen .player-container,
      html.hydra-is-fullscreen .play-box,
      html.hydra-is-fullscreen #play-video,
      html.hydra-is-fullscreen .video-content,
      html.hydra-is-fullscreen .player_content,
      html.hydra-is-fullscreen .player-holder {
        position: fixed !important;
        top: 0 !important;
        left: 0 !important;
        right: 0 !important;
        bottom: 0 !important;
        width: 100vw !important;
        height: 100vh !important;
        max-width: 100vw !important;
        max-height: 100vh !important;
        z-index: 2147483640 !important;
        margin: 0 !important;
        padding: 0 !important;
        padding-bottom: 0 !important;
        border: none !important;
        border-radius: 0 !important;
        background: #000 !important;
      }

      html.hydra-is-fullscreen .video-container iframe,
      html.hydra-is-fullscreen .TPlayer iframe,
      html.hydra-is-fullscreen .TPlayerCn iframe,
      html.hydra-is-fullscreen .embed_div iframe,
      html.hydra-is-fullscreen #video iframe,
      html.hydra-is-fullscreen #player iframe,
      html.hydra-is-fullscreen #reproductor iframe,
      html.hydra-is-fullscreen .player-placeholder iframe,
      html.hydra-is-fullscreen .player-container iframe,
      html.hydra-is-fullscreen .play-box iframe,
      html.hydra-is-fullscreen #play-video iframe,
      html.hydra-is-fullscreen .video-content iframe,
      html.hydra-is-fullscreen video {
        position: absolute !important;
        top: 0 !important;
        left: 0 !important;
        width: 100vw !important;
        height: 100vh !important;
        max-width: 100vw !important;
        max-height: 100vh !important;
        border: none !important;
        border-radius: 0 !important;
        background: #000 !important;
      }

      /* En pantalla completa, ocultar todo contenido periférico que no sea el reproductor */
      html.hydra-is-fullscreen header,
      html.hydra-is-fullscreen nav,
      html.hydra-is-fullscreen aside,
      html.hydra-is-fullscreen footer,
      html.hydra-is-fullscreen .related-movies,
      html.hydra-is-fullscreen .top-movies,
      html.hydra-is-fullscreen .s-related,
      html.hydra-is-fullscreen [class*="similar" i],
      html.hydra-is-fullscreen [class*="destacadas" i],
      html.hydra-is-fullscreen [class*="relacionadas" i],
      html.hydra-is-fullscreen .movie-sidebar,
      html.hydra-is-fullscreen .movie-sidebar-right,
      html.hydra-is-fullscreen .alert,
      html.hydra-is-fullscreen .adang,
      html.hydra-is-fullscreen .notice,
      html.hydra-is-fullscreen .warning-box,
      html.hydra-is-fullscreen .comments,
      html.hydra-is-fullscreen #comments {
        display: none !important;
        visibility: hidden !important;
        height: 0 !important;
        overflow: hidden !important;
      }

      /* Mantener el selector interno de servidores accesible y flotante */
      html.hydra-is-fullscreen ul.TPlayerNv,
      html.hydra-is-fullscreen .sub-tab-lang,
      html.hydra-is-fullscreen .tab_language_movie,
      html.hydra-is-fullscreen .lang,
      html.hydra-is-fullscreen .player-options,
      html.hydra-is-fullscreen #playeroptionsul,
      html.hydra-is-fullscreen ._1R6bW_0 {
        position: fixed !important;
        top: 14px !important;
        left: 16px !important;
        z-index: 2147483646 !important;
        background: rgba(10, 11, 14, 0.92) !important;
        border-radius: 8px !important;
        padding: 6px 12px !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        backdrop-filter: blur(10px) !important;
        -webkit-backdrop-filter: blur(10px) !important;
      }
    `;
    (document.head || document.documentElement).appendChild(style);
  }

  // 2. Barra Superior Interactiva de Hydra TV con botón Volver (Solo modo Kiosk TV top-level)
  function inyectarBarraSuperiorHydra() {
    if (isEmbedded) {
      // Capturar Backspace para avisar al reproductor padre que cierre
      window.addEventListener('keydown', (e) => {
        if (e.key === 'Backspace' && !['INPUT', 'TEXTAREA'].includes(document.activeElement?.tagName)) {
          window.parent.postMessage({ type: 'HYDRA_CLOSE_PLAYER' }, '*');
        }
      });
      return;
    }

    if (document.getElementById('hydra-tv-topbar')) return;
    if (!document.body) return;

    document.body.classList.add('has-hydra-topbar');

    const bar = document.createElement('div');
    bar.id = 'hydra-tv-topbar';
    bar.style.cssText = 'position:fixed;top:0;left:0;right:0;height:52px;background:rgba(10,11,14,0.98);backdrop-filter:blur(12px);border-bottom:1px solid rgba(255,255,255,0.12);display:flex;align-items:center;justify-content:space-between;padding:0 20px;z-index:2147483647;font-family:system-ui,sans-serif;box-shadow:0 4px 20px rgba(0,0,0,0.8);';
    bar.innerHTML = `
      <button id="hydra-btn-back" style="background:rgba(255,255,255,0.12);border:1px solid rgba(255,255,255,0.2);color:#fff;padding:8px 18px;border-radius:8px;cursor:pointer;font-weight:700;font-size:0.95rem;display:inline-flex;align-items:center;gap:8px;outline:none;" title="Volver al catálogo (Esc o Retroceso)">
        ← Volver al Inicio
      </button>
      <div id="hydra-brand-info" style="display:inline-flex;align-items:center;gap:8px;font-weight:900;font-size:1.15rem;color:#fff;user-select:none;">
        <span style="color:#e50914;font-size:1.3rem;">⚡</span>
        <span>HYDRA TV</span>
      </div>
    `;

    document.body.prepend(bar);

    function volverAlInicio() {
      try {
        fetch('http://localhost:5000/stop', { method: 'POST' }).catch(() => {});
      } catch(e) {}
      window.location.href = 'http://localhost:5000';
    }

    const btnBack = bar.querySelector('#hydra-btn-back');
    btnBack.addEventListener('click', volverAlInicio);

    window.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' || (e.key === 'Backspace' && !['INPUT', 'TEXTAREA'].includes(document.activeElement?.tagName))) {
        volverAlInicio();
      }
    });
  }

  // 3. Destructor de capas invisibles superpuestas (Clickjacking Overlays)
  function limpiarCapasYTrampas() {
    try {
      const elements = document.querySelectorAll('div, a, span, section');
      for (const el of elements) {
        if (el.id === 'hydra-tv-topbar' || el.closest('#hydra-tv-topbar')) continue;
        if (el.id === 'start' || el.id === 'container' || el.id === 'player' || el.id === 'video' ||
            el.closest('#player') || el.closest('#video') || el.closest('#container') || el.closest('.TPlayer') ||
            el.closest('.video-container') || el.closest('#playeroptionsul') || el.closest('.sub-tab-lang')) continue;

        const style = window.getComputedStyle(el);
        const isOverlay = (style.position === 'fixed' || style.position === 'absolute');
        const zIndex = parseInt(style.zIndex, 10);
        
        if (isOverlay && zIndex > 90) {
          const rect = el.getBoundingClientRect();
          const esGigante = (rect.width >= window.innerWidth * 0.6 && rect.height >= window.innerHeight * 0.6);
          const esTransparente = (style.opacity === '0' || style.backgroundColor === 'rgba(0, 0, 0, 0)' || style.background === 'transparent');

          if (esGigante && esTransparente && !el.querySelector('video') && el.tagName !== 'VIDEO') {
            console.warn('[Hydra Shield] Capa invisible destruida:', el);
            el.remove();
          }
        }
      }

      // Eliminar únicamente iframes publicitarios confirmados externos
      const adIframes = document.querySelectorAll('iframe');
      adIframes.forEach(f => {
        if (f.id === 'playerIframe' || f.id === 'hydra-player-iframe') return;
        if (f.closest('#player') || f.closest('#video') || f.closest('#reproductor') ||
            f.closest('.video-container') || f.closest('.TPlayer') || f.closest('#container')) return;

        const src = (f.src || '').toLowerCase();
        const esAdUrl = ['adsterra', 'popcash', 'popads', 'propeller', 'onclick', 'monetag', 'exoclick', 'doubleclick', 'ad-maven', 'richpush', 'trafficjunky'].some(ad => src.includes(ad));
        if (esAdUrl) {
          f.remove();
        }
      });
    } catch(e) {}
  }

  // 4. Interceptor de clics en la fase de captura
  window.addEventListener('click', function(e) {
    const el = e.target;
    if (!el) return;
    if (el.id === 'hydra-btn-back' || el.closest('#hydra-tv-topbar')) return;

    // Si el usuario o un script hace clic en un enlace con target="_blank" o target="_new"
    const a = el.closest('a');
    if (a) {
      const target = (a.getAttribute('target') || '').toLowerCase();
      const href = (a.getAttribute('href') || '').toLowerCase();
      if (target === '_blank' || target === '_new') {
        const esAdUrl = ['adsterra', 'popcash', 'popads', 'propeller', 'onclick', 'monetag', 'exoclick', 'doubleclick', 'ad-maven', 'richpush', 'trafficjunky', 'bet365', '1xbet'].some(ad => href.includes(ad));
        if (esAdUrl) {
          console.warn('[Hydra Shield CAPTURE] Enlace publicitario bloqueado:', href);
          e.preventDefault();
          e.stopPropagation();
          e.stopImmediatePropagation();
          return;
        }
        // Para reproductores y enlaces de servidores legítimos, permitir apertura en el mismo frame
        a.removeAttribute('target');
        a.target = '_self';
      }
    }

    // Si el clic fue en un overlay transparente gigante
    try {
      const style = window.getComputedStyle(el);
      if ((style.position === 'fixed' || style.position === 'absolute') && parseInt(style.zIndex, 10) > 90) {
        if (el.id === 'start' || el.id === 'container' || el.id === 'player' || el.id === 'video' ||
            el.closest('#player') || el.closest('#video') || el.closest('#container') || el.closest('.TPlayer') ||
            el.closest('.video-container') || el.closest('#playeroptionsul') || el.closest('.sub-tab-lang')) return;

        const rect = el.getBoundingClientRect();
        if (rect.width >= window.innerWidth * 0.6 && rect.height >= window.innerHeight * 0.6) {
          if (!el.querySelector('video') && el.tagName !== 'VIDEO') {
            e.preventDefault();
            e.stopPropagation();
            e.stopImmediatePropagation();
            el.remove();
          }
        }
      }
    } catch(err) {}
  }, true);

  // 5. Acelerador de Reproducción Inmediata y Visibilidad de Reproductores
  function acelerarReproduccion() {
    try {
      // A. PoseidonHD: Si el reproductor no tiene iframe todavía, activar el primer servidor una sola vez
      if (host.includes('poseidon')) {
        const container = document.querySelector('.video-container');
        const hasIframe = container && container.querySelector('iframe');
        if (!hasIframe) {
          const primerServidor = document.querySelector('li.clili[data-tr]');
          if (primerServidor && !primerServidor.dataset.hydraActivated) {
            primerServidor.dataset.hydraActivated = 'true';
            console.log('[Hydra Shield] Auto-activando primer servidor en PoseidonHD:', primerServidor.innerText);
            primerServidor.click();
          }
        }
        // Desplegar automáticamente los servidores de Poseidon para que el usuario pueda cambiarlos libremente
        const subTabs = document.querySelector('.sub-tab-lang');
        if (subTabs && subTabs.classList.contains('hide')) {
          subTabs.classList.remove('hide');
        }
      }

      // B. Cinemitas: Si la opción activa es un trailer, buscar la primera opción de servidor real
      if (host.includes('cinemitas') || document.querySelector('#playeroptionsul')) {
        const opciones = document.querySelectorAll('#playeroptionsul li');
        let servidorReal = null;
        for (const opt of opciones) {
          const texto = (opt.innerText || opt.textContent || '').toLowerCase();
          const dataType = (opt.getAttribute('data-type') || '').toLowerCase();
          const optId = (opt.id || '').toLowerCase();
          if (texto.includes('trailer') || dataType.includes('trailer') || optId.includes('trailer')) {
            continue;
          }
          servidorReal = opt;
          break;
        }

        const optActiva = document.querySelector('#playeroptionsul li.active');
        const activaEsTrailer = optActiva && (
          (optActiva.innerText || '').toLowerCase().includes('trailer') ||
          (optActiva.getAttribute('data-type') || '').toLowerCase().includes('trailer') ||
          (optActiva.id || '').toLowerCase().includes('trailer')
        );

        if (servidorReal && (!optActiva || activaEsTrailer) && !servidorReal.dataset.hydraActivated) {
          servidorReal.dataset.hydraActivated = 'true';
          console.log('[Hydra Shield] Seleccionando servidor real en Cinemitas (evitando trailer)');
          servidorReal.click();
        }
      }

      // C. Peelink
      if (host.includes('peelink')) {
        const btnLink = document.querySelector('#btn-link, a.btn-success, .btn-link');
        if (btnLink && btnLink.offsetParent !== null) btnLink.click();
      }

      // D. Forzar visibilidad de reproductores legítimos
      const playerContainers = document.querySelectorAll(
        '#player, #reproductor, .player, .play-box, .video-player, #play-video, .video-content, iframe[src*="embed"], iframe[src*="stream"]'
      );
      playerContainers.forEach(el => {
        if (el.style.display === 'none') el.style.display = 'block';
        if (el.style.visibility === 'hidden') el.style.visibility = 'visible';
        if (el.style.opacity === '0') el.style.opacity = '1';
      });

      // E. PeliculasHD / MasPeliculasHD
      if (host.includes('peliculashd') || document.querySelector('.play-button')) {
        const btnPlayMaspeli = document.querySelector('.play-button');
        if (btnPlayMaspeli && !btnPlayMaspeli.dataset.hydraClicked) {
          btnPlayMaspeli.dataset.hydraClicked = 'true';
          btnPlayMaspeli.click();
        }
      }

      // F. Auto-clic en botones Play genéricos
      const playButtons = document.querySelectorAll(
        '.jw-display-icon-container, .vjs-big-play-button, .play-btn, #btn-play, .btn-play, button.play, div.play, svg.play'
      );
      for (const btn of playButtons) {
        if (btn && btn.offsetParent !== null && !btn.dataset.hydraClicked) {
          btn.dataset.hydraClicked = 'true';
          btn.click();
          break;
        }
      }
    } catch(err) {}
  }

  // 6. Corrección de Temporadas Vacías (Temporada 0) en Series
  function corregirTemporadas() {
    try {
      const selectSeasons = document.querySelectorAll('#select-season, select[name*="season" i], select[class*="season" i]');
      selectSeasons.forEach(selectEl => {
        const options = Array.from(selectEl.options);
        if (!options.length) return;

        const optCero = options.find(o => o.value === '0' || o.text.toLowerCase().includes('temporada 0') || o.text.toLowerCase().includes('season 0'));
        const optValida = options.find(o => o.value === '1' || o.text.toLowerCase().includes('temporada 1') || o.text.toLowerCase().includes('season 1'))
                          || options.find(o => o !== optCero);

        const epContainer = document.querySelector('.all-episodes, .episodes, ul.MovieList, #episodes, .episode-list');
        const tieneEpisodios = epContainer && epContainer.querySelectorAll('li, .episode-item, article, a').length > 0;

        if (optCero && optValida) {
          if (selectEl.value === optCero.value || !tieneEpisodios) {
            const valueSetter = Object.getOwnPropertyDescriptor(window.HTMLSelectElement.prototype, 'value')?.set;
            if (valueSetter) {
              valueSetter.call(selectEl, optValida.value);
            } else {
              selectEl.value = optValida.value;
            }

            selectEl.dispatchEvent(new Event('input', { bubbles: true }));
            selectEl.dispatchEvent(new Event('change', { bubbles: true }));
            optCero.remove();
          } else if (tieneEpisodios && selectEl.value !== optCero.value) {
            optCero.remove();
          }
        }
      });

      const tabsCero = document.querySelectorAll('[data-season="0"], .season-item, .season-btn, .seasons li');
      tabsCero.forEach(tab => {
        const txt = tab.textContent.toLowerCase();
        if (txt.includes('temporada 0') || txt.includes('season 0') || tab.getAttribute('data-season') === '0') {
          tab.style.display = 'none';
          tab.remove();

          if (tab.classList.contains('active') || tab.classList.contains('current')) {
            const tabUno = document.querySelector('[data-season="1"], .season-item:nth-child(2), .season-btn:nth-child(2)');
            if (tabUno) tabUno.click();
          }
        }
      });
    } catch(err) {}
  }

  // 7. Sincronización de Pantalla Completa con Hydra TV
  window.addEventListener('message', (e) => {
    if (e.data && e.data.type === 'HYDRA_FULLSCREEN_CHANGE') {
      const active = !!e.data.active;
      document.documentElement.classList.toggle('hydra-is-fullscreen', active);
      if (document.body) document.body.classList.toggle('hydra-is-fullscreen', active);
    }
  });

  document.addEventListener('fullscreenchange', () => {
    const isFs = !!document.fullscreenElement;
    document.documentElement.classList.toggle('hydra-is-fullscreen', isFs);
    if (document.body) document.body.classList.toggle('hydra-is-fullscreen', isFs);
  });

  inyectarEstilosAntiPublicidad();
  inyectarBarraSuperiorHydra();
  corregirTemporadas();
  limpiarCapasYTrampas();
  acelerarReproduccion();

  const intervalId = setInterval(() => {
    inyectarEstilosAntiPublicidad();
    inyectarBarraSuperiorHydra();
    corregirTemporadas();
    limpiarCapasYTrampas();
    acelerarReproduccion();
  }, 350);

  setTimeout(() => {
    clearInterval(intervalId);
    const slowInterval = setInterval(() => {
      inyectarBarraSuperiorHydra();
      corregirTemporadas();
      limpiarCapasYTrampas();
      acelerarReproduccion();
    }, 1500);
    setTimeout(() => clearInterval(slowInterval), 20000);
  }, 4000);

  document.addEventListener('DOMContentLoaded', () => {
    inyectarEstilosAntiPublicidad();
    inyectarBarraSuperiorHydra();
    corregirTemporadas();
    limpiarCapasYTrampas();
    acelerarReproduccion();
  });
})();
