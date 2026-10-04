// Hydra TV Shield - Interceptor Global en el contexto de página (MAIN world)
(function() {
  'use strict';

  const host = window.location.hostname.toLowerCase();
  
  // No intervenir en localhost, YouTube oficial o páginas de configuración
  if (host === 'localhost' || host === '127.0.0.1' || window.location.port === '5000' ||
      host.includes('brave') || host.includes('google') || host.includes('youtube') || host.includes('github')) {
    return;
  }

  // 1. Anular window.open incondicionalmente en todos los reproductores y frames
  const dummyWindow = {
    closed: false,
    name: '',
    location: { href: '' },
    document: { readyState: 'complete' },
    focus: function() {},
    blur: function() {},
    close: function() {},
    postMessage: function() {},
    addEventListener: function() {},
    removeEventListener: function() {},
    opener: window
  };

  try {
    Object.defineProperty(window, 'open', {
      value: function(url, target, features) {
        console.warn('[Hydra Shield MAIN] window.open bloqueado:', url);
        return dummyWindow;
      },
      writable: false,
      configurable: false
    });
  } catch(e) {
    window.open = function() { return dummyWindow; };
  }

  // 2. Neutralizar alertas intrusivas que bloquean la pantalla
  window.alert = function() {};
  window.confirm = function() { return true; };
  window.prompt = function() { return null; };
  window.onbeforeunload = null;

  // 3. Neutralizar llamadas sintéticas a click() en enlaces publicitarios con target="_blank"
  try {
    const originalAnchorClick = HTMLAnchorElement.prototype.click;
    HTMLAnchorElement.prototype.click = function() {
      const target = (this.getAttribute('target') || '').toLowerCase();
      const href = (this.getAttribute('href') || '').toLowerCase();
      if (target === '_blank' || target === '_new' || href.startsWith('javascript:')) {
        if (!href.startsWith(window.location.origin) && !href.startsWith('/') && !href.startsWith('#')) {
          console.warn('[Hydra Shield MAIN] Enlace publicitario simulado bloqueado:', href);
          return;
        }
      }
      return originalAnchorClick.apply(this, arguments);
    };
  } catch(e) {}

  // 4. Neutralizar scripts de frame-busting que intentan redirigir fuera del reproductor de Hydra TV
  try {
    if (window.top !== window.self) {
      Object.defineProperty(window, 'top', {
        get: function() { return window.self; },
        set: function() {}
      });
    }
  } catch(e) {}
})();
