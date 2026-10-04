// Hydra TV Shield - Interceptor en el contexto principal de la página (MAIN world)
(function() {
  'use strict';

  // No interceptar dentro de Hydra Tv local
  if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1' || window.location.port === '5000') {
    return;
  }

  console.log('[Hydra Shield] Activo en:', window.location.href);

  // 1. Anular window.open para scripts publicitarios
  const originalWindowOpen = window.open;
  window.open = function(url, target, features) {
    console.warn('[Hydra Shield] Intento de ventana emergente bloqueado (window.open):', url, target);

    // Devolver objeto dummy para no romper la ejecución de los reproductores
    return {
      closed: true,
      name: target || '',
      location: { href: url || '' },
      document: {},
      focus: function() {},
      blur: function() {},
      close: function() {},
      postMessage: function() {},
      addEventListener: function() {},
      removeEventListener: function() {}
    };
  };

  // 2. Prevenir que los scripts secuestren window.alert o onbeforeunload
  window.onbeforeunload = null;

})();
