// Hydra TV Shield - Acelerador y Neutralizador de Trampas en DOM
(function() {
  'use strict';

  const host = window.location.hostname.toLowerCase();
  
  if (host === 'localhost' || host === '127.0.0.1' || window.location.port === '5000' ||
      host.includes('brave') || host.includes('google') || host.includes('youtube') || host.includes('github')) {
    return;
  }

  // 1. Destructor de capas invisibles superpuestas (Clickjacking Overlays)
  function limpiarCapasYTrampas() {
    try {
      const elements = document.querySelectorAll('div, a, span, section');
      for (const el of elements) {
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

      // Eliminar iframes publicitarios obvios
      const adIframes = document.querySelectorAll('iframe[src*="ad"], iframe[src*="banner"], iframe[src*="pop"], iframe[src*="click"], iframe[src*="track"]');
      adIframes.forEach(f => f.remove());
    } catch(e) {}
  }

  // 2. Interceptor de clics en la fase de captura para evitar que capas invisibles o enlaces tramposos abran nada
  window.addEventListener('click', function(e) {
    const el = e.target;
    if (!el) return;

    // Si el usuario hace clic en un enlace con target="_blank"
    const a = el.closest('a');
    if (a) {
      const target = (a.getAttribute('target') || '').toLowerCase();
      const href = (a.getAttribute('href') || '').toLowerCase();
      if (target === '_blank' || target === '_new') {
        if (!href.startsWith(window.location.origin) && !href.startsWith('/') && !href.startsWith('#')) {
          console.warn('[Hydra Shield CAPTURE] Clic en enlace emergente bloqueado:', href);
          e.preventDefault();
          e.stopPropagation();
          e.stopImmediatePropagation();
          a.remove();
          return;
        }
      }
    }

    // Si el clic fue en un overlay transparente gigante
    try {
      const style = window.getComputedStyle(el);
      if ((style.position === 'fixed' || style.position === 'absolute') && parseInt(style.zIndex, 10) > 90) {
        const rect = el.getBoundingClientRect();
        if (rect.width >= window.innerWidth * 0.6 && rect.height >= window.innerHeight * 0.6) {
          if (!el.querySelector('video') && el.tagName !== 'VIDEO') {
            console.warn('[Hydra Shield CAPTURE] Clic en overlay absorbido y elemento destruido');
            e.preventDefault();
            e.stopPropagation();
            e.stopImmediatePropagation();
            el.remove();
          }
        }
      }
    } catch(err) {}
  }, true);

  // 3. Acelerador de Reproducción Inmediata
  function acelerarReproduccion() {
    try {
      // A. PoseidonHD: Desplegar servidores y clic en el primero
      if (host.includes('poseidon')) {
        const subTabs = document.querySelector('.sub-tab-lang');
        if (subTabs && subTabs.classList.contains('hide')) subTabs.classList.remove('hide');
        
        const primerServidor = document.querySelector('li.clili[data-tr]');
        if (primerServidor && !primerServidor.classList.contains('active') && !primerServidor.classList.contains('actives')) {
          primerServidor.click();
        }
      }

      // B. Cinemitas: Clic en primer servidor
      if (host.includes('cinemitas') || document.querySelector('#playeroptionsul')) {
        const primeraOpcion = document.querySelector('#playeroptionsul li:first-child');
        if (primeraOpcion && !primeraOpcion.classList.contains('active')) {
          primeraOpcion.click();
        }
      }

      // C. Peelink
      if (host.includes('peelink')) {
        const btnLink = document.querySelector('#btn-link, a.btn-success, .btn-link');
        if (btnLink && btnLink.offsetParent !== null) btnLink.click();
      }

      // D. Forzar visibilidad de reproductores
      const playerContainers = document.querySelectorAll(
        '#player, #reproductor, .player, .play-box, .video-player, #play-video, .video-content, iframe[src*="embed"], iframe[src*="stream"]'
      );
      playerContainers.forEach(el => {
        if (el.style.display === 'none') el.style.display = 'block';
        if (el.style.visibility === 'hidden') el.style.visibility = 'visible';
        if (el.style.opacity === '0') el.style.opacity = '1';
      });

      // E. Auto-clic en botones Play
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

  limpiarCapasYTrampas();
  acelerarReproduccion();

  const intervalId = setInterval(() => {
    limpiarCapasYTrampas();
    acelerarReproduccion();
  }, 250);

  setTimeout(() => {
    clearInterval(intervalId);
    const slowInterval = setInterval(() => {
      limpiarCapasYTrampas();
      acelerarReproduccion();
    }, 1200);
    setTimeout(() => clearInterval(slowInterval), 20000);
  }, 4000);

  document.addEventListener('DOMContentLoaded', () => {
    limpiarCapasYTrampas();
    acelerarReproduccion();
  });
})();
