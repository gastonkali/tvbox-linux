// Hydra TV Shield - Content Script para neutralizar capas invisibles y enlaces trampa
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
    return; // No intervenir en la navegación cotidiana del usuario
  }

  // 1. Interceptar clics trampa solo si abren publicidad externa
  window.addEventListener('click', function(e) {
    const link = e.target.closest('a');
    if (link) {
      const target = (link.getAttribute('target') || '').toLowerCase();
      const href = (link.getAttribute('href') || '').toLowerCase();

      // Si abre en pestaña nueva o es un enlace publicitario de apuestas/ads
      if (target === '_blank' || href.includes('ad') || href.includes('bet') || href.includes('pop') || href.includes('click')) {
        try {
          const targetUrl = new URL(link.href, window.location.href);
          if (targetUrl.hostname !== window.location.hostname) {
            e.preventDefault();
            e.stopPropagation();
            e.stopImmediatePropagation();
            console.warn('[Hydra Shield] Clic en enlace publicitario interceptado:', link.href);
            return false;
          }
        } catch(err) {}
      }
    }
  }, true);

  // 2. Destructor de capas invisibles superpuestas (Clickjacking Overlays)
  function eliminarCapasTransparentes() {
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
            console.warn('[Hydra Shield] Capa invisible de publicidad destruida:', el);
            el.remove();
          }
        }
      }

      // 3. Forzar revelación inmediata del reproductor de video
      const playerContainers = document.querySelectorAll('#player, #reproductor, .player, .play-box, .video-player, iframe[src*="embed"], iframe[src*="stream"]');
      playerContainers.forEach(el => {
        if (el.style.display === 'none') el.style.display = 'block';
        if (el.style.visibility === 'hidden') el.style.visibility = 'visible';
        if (el.style.opacity === '0') el.style.opacity = '1';
      });

      // Auto-clic en botones de salto de cuenta regresiva o continuar ("Saltar", "Omitir", "Ver video")
      const buttons = document.querySelectorAll('button, a, div[role="button"]');
      for (const b of buttons) {
        const text = (b.innerText || '').trim().toLowerCase();
        if (text.includes('saltar') || text.includes('skip') || text.includes('continuar al video') || text.includes('ver pelicula')) {
          if (b.offsetParent !== null) {
            console.log('[Hydra Shield] Auto-clic en botón continuar:', text);
            b.click();
            break;
          }
        }
      }
    } catch(e) {}
  }

  const interval = setInterval(eliminarCapasTransparentes, 500);
  setTimeout(() => clearInterval(interval), 15000);
  document.addEventListener('DOMContentLoaded', eliminarCapasTransparentes);
})();
