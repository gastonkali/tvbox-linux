// Hydra TV Shield - Acelerador Instantáneo y Neutralizador de Trampas
(function() {
  'use strict';

  const host = window.location.hostname.toLowerCase();
  
  // No intervenir en páginas del sistema, buscadores o localhost
  if (host === 'localhost' || host === '127.0.0.1' || window.location.port === '5000' ||
      host.includes('brave') || host.includes('google') || host.includes('youtube') || host.includes('github')) {
    return;
  }

  const STREAMING_KEYWORDS = [
    'pelicine', 'poseidon', 'series24', 'repelis', 'cinemitas', 
    'ultrapeli', 'dramafuntv', 'gnula', 'maspelicula', 'argflix',
    'stream', 'movie', 'pelicula', 'serie', 'watch', 'play', 'embed',
    'wish', 'moon', 'dood', 'voe', 'netu', 'waaw', 'uqload', 'mixdrop',
    'peelink'
  ];

  const esSitioStreaming = STREAMING_KEYWORDS.some(k => host.includes(k) || window.location.pathname.includes(k));
  if (!esSitioStreaming) {
    return;
  }

  console.log('[Hydra Shield] Acelerador activo en:', host);

  // 1. Destructor de capas invisibles superpuestas (Clickjacking Overlays)
  function limpiarCapasYTrampas() {
    try {
      const elements = document.querySelectorAll('div, a, span');
      for (const el of elements) {
        const style = window.getComputedStyle(el);
        const isOverlay = (style.position === 'fixed' || style.position === 'absolute');
        const zIndex = parseInt(style.zIndex, 10);
        
        if (isOverlay && zIndex > 99) {
          const rect = el.getBoundingClientRect();
          const esGigante = (rect.width >= window.innerWidth * 0.7 && rect.height >= window.innerHeight * 0.7);
          const esTransparente = (style.opacity === '0' || style.backgroundColor === 'rgba(0, 0, 0, 0)' || style.background === 'transparent');

          if (esGigante && esTransparente && !el.querySelector('video') && !el.querySelector('iframe')) {
            console.warn('[Hydra Shield] Capa invisible destruida:', el);
            el.remove();
          }
        }
      }
    } catch(e) {}
  }

  // 2. Acelerador de Reproducción Inmediata (PoseidonHD, Cinemitas, PelicineHD, Embeds)
  function acelerarReproduccion() {
    try {
      // A. Caso PoseidonHD: auto-desplegar lista de servidores y auto-click en el primer servidor
      if (host.includes('poseidon')) {
        const subTabs = document.querySelector('.sub-tab-lang');
        if (subTabs && subTabs.classList.contains('hide')) {
          subTabs.classList.remove('hide');
        }
        
        const primerServidor = document.querySelector('li.clili[data-tr]');
        if (primerServidor && !primerServidor.classList.contains('active') && !primerServidor.classList.contains('actives')) {
          console.log('[Hydra Shield] Auto-activando primer servidor en PoseidonHD...');
          primerServidor.click();
        }
      }

      // B. Caso Cinemitas / DooPlay: auto-click en primera opción de reproductor
      if (host.includes('cinemitas') || document.querySelector('#playeroptionsul')) {
        const primeraOpcion = document.querySelector('#playeroptionsul li:first-child');
        if (primeraOpcion && !primeraOpcion.classList.contains('active')) {
          console.log('[Hydra Shield] Auto-activando opción en Cinemitas...');
          primeraOpcion.click();
        }
      }

      // C. Caso Peelink / Redirectores con cuenta regresiva: saltar de inmediato
      if (host.includes('peelink')) {
        const btnLink = document.querySelector('#btn-link, a.btn-success, .btn-link');
        if (btnLink && btnLink.offsetParent !== null) {
          console.log('[Hydra Shield] Auto-clic inmediato en Peelink...');
          btnLink.click();
        }
      }

      // D. Forzar visibilidad inmediata de contenedores de video
      const playerContainers = document.querySelectorAll(
        '#player, #reproductor, .player, .play-box, .video-player, #play-video, .video-content, iframe[src*="embed"], iframe[src*="stream"]'
      );
      playerContainers.forEach(el => {
        if (el.style.display === 'none') el.style.display = 'block';
        if (el.style.visibility === 'hidden') el.style.visibility = 'visible';
        if (el.style.opacity === '0') el.style.opacity = '1';
      });

      // E. Auto-clic en botones de play y saltar cuenta regresiva
      const playButtons = document.querySelectorAll(
        '.jw-display-icon-container, .vjs-big-play-button, .play-btn, #btn-play, .btn-play, button.play, div.play, svg.play'
      );
      for (const btn of playButtons) {
        if (btn && btn.offsetParent !== null && !btn.dataset.hydraClicked) {
          btn.dataset.hydraClicked = 'true';
          console.log('[Hydra Shield] Auto-clic en botón Play del reproductor');
          btn.click();
          break;
        }
      }

      // F. Auto-clic en botones "Saltar", "Omitir", "Cerrar"
      const skipButtons = document.querySelectorAll('button, a, div[role="button"], span');
      for (const b of skipButtons) {
        const text = (b.innerText || '').trim().toLowerCase();
        if (text === 'saltar' || text === 'skip' || text === 'cerrar' || text === 'continuar' || text === 'omitir') {
          if (b.offsetParent !== null && !b.dataset.hydraClicked) {
            b.dataset.hydraClicked = 'true';
            console.log('[Hydra Shield] Auto-clic en botón omitir/saltar:', text);
            b.click();
            break;
          }
        }
      }
    } catch(err) {}
  }

  // Ejecución ultra-rápida en ráfaga para eliminar el retraso de minutos
  limpiarCapasYTrampas();
  acelerarReproduccion();

  const rafagaInterval = setInterval(() => {
    limpiarCapasYTrampas();
    acelerarReproduccion();
  }, 200);

  // Reducir la frecuencia después de 3 segundos
  setTimeout(() => {
    clearInterval(rafagaInterval);
    const regularInterval = setInterval(() => {
      limpiarCapasYTrampas();
      acelerarReproduccion();
    }, 1000);
    setTimeout(() => clearInterval(regularInterval), 15000);
  }, 3000);

  document.addEventListener('DOMContentLoaded', () => {
    limpiarCapasYTrampas();
    acelerarReproduccion();
  });
})();
