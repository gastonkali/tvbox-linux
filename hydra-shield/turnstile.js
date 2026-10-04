// Hydra TV Shield - Auto-resolución de Cloudflare Turnstile
(function() {
  'use strict';

  console.log('[Hydra Shield] Monitor de Cloudflare Turnstile activo en iframe.');

  function simularClicHumano(element) {
    if (!element) return;
    
    const rect = element.getBoundingClientRect();
    const x = rect.left + (rect.width / 2) || 20;
    const y = rect.top + (rect.height / 2) || 20;

    const opts = {
      bubbles: true,
      cancelable: true,
      composed: true,
      view: window,
      clientX: x,
      clientY: y,
      screenX: x + window.screenX,
      screenY: y + window.screenY
    };

    try {
      element.dispatchEvent(new PointerEvent('pointerover', opts));
      element.dispatchEvent(new PointerEvent('pointerenter', opts));
      element.dispatchEvent(new PointerEvent('pointerdown', opts));
      element.dispatchEvent(new MouseEvent('mousedown', opts));
      element.focus();
      element.dispatchEvent(new PointerEvent('pointerup', opts));
      element.dispatchEvent(new MouseEvent('mouseup', opts));
      element.dispatchEvent(new MouseEvent('click', opts));
      console.log('[Hydra Shield] Clic simulado en Turnstile enviado con éxito.');
    } catch (e) {
      console.error('[Hydra Shield] Error enviando clic a Turnstile:', e);
      try { element.click(); } catch (err) {}
    }
  }

  function intentarVerificar() {
    // Buscar checkbox o etiqueta de Turnstile
    const targets = [
      document.querySelector('input[type="checkbox"]'),
      document.querySelector('.ctp-checkbox-label'),
      document.querySelector('#challenge-stage input'),
      document.querySelector('label.ctp-checkbox-label input'),
      document.querySelector('#cf-stage input')
    ];

    for (const el of targets) {
      if (el && !el.checked) {
        console.log('[Hydra Shield] Casilla de verificación Cloudflare encontrada. Intentando resolver...');
        // Pequeño retardo aleatorio de 500-1200ms para emular reacción humana
        setTimeout(() => {
          simularClicHumano(el);
        }, 600);
        return true;
      }
    }
    return false;
  }

  // Comprobar periódicamente hasta que desaparezca el reto
  let intentos = 0;
  const timer = setInterval(() => {
    intentos++;
    if (intentarVerificar() || intentos > 30) {
      clearInterval(timer);
    }
  }, 800);

  // Ejecutar también cuando cargue el DOM
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', intentarVerificar);
  } else {
    intentarVerificar();
  }
})();
