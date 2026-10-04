// Hydra TV Shield - Content Script para neutralizar capas invisibles y enlaces trampa
(function() {
  'use strict';

  if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1' || window.location.port === '5000') {
    return;
  }

  // 1. Interceptar clics trampa (enlaces target="_blank" o clickjacking)
  window.addEventListener('click', function(e) {
    const link = e.target.closest('a');
    if (link) {
      const target = (link.getAttribute('target') || '').toLowerCase();
      const href = link.getAttribute('href') || '';

      // Si abre en pestaña nueva o es un enlace javascript sospechoso
      if (target === '_blank' || href.includes('ad') || href.includes('bet') || href.includes('pop') || href.includes('click')) {
        try {
          const targetUrl = new URL(link.href, window.location.href);
          // Si no pertenece al mismo dominio o es un dominio de publicidad
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
  }, true); // Fase de captura para actuar antes que los scripts del sitio

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

          // Si es un div gigante transparente por encima de todo, es un clickjack de publicidad
          if (esGigante && esTransparente && !el.querySelector('video') && !el.querySelector('iframe')) {
            console.warn('[Hydra Shield] Capa invisible de publicidad destruida:', el);
            el.remove();
          }
        }
      }
    } catch(e) {}
  }

  // Ejecutar periódicamente durante los primeros 10 segundos de carga
  const interval = setInterval(eliminarCapasTransparentes, 800);
  setTimeout(() => clearInterval(interval), 15000);

  document.addEventListener('DOMContentLoaded', eliminarCapasTransparentes);
})();
