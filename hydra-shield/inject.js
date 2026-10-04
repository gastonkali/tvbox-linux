// Hydra TV Shield - Interceptor en el contexto principal de la página (MAIN world)
(function() {
  'use strict';

  const host = window.location.hostname.toLowerCase();
  
  // No intervenir en páginas del sistema, buscadores o localhost
  if (host === 'localhost' || host === '127.0.0.1' || window.location.port === '5000' ||
      host.includes('brave') || host.includes('google') || host.includes('youtube') || host.includes('github')) {
    return;
  }

  // Lista de patrones de sitios de streaming y reproductores
  const STREAMING_KEYWORDS = [
    'pelicine', 'poseidon', 'series24', 'repelis', 'cinemitas', 
    'ultrapeli', 'dramafuntv', 'gnula', 'maspelicula', 'argflix',
    'stream', 'movie', 'pelicula', 'serie', 'watch', 'play', 'embed',
    'wish', 'moon', 'dood', 'voe', 'netu', 'waaw', 'uqload', 'mixdrop'
  ];

  const esSitioStreaming = STREAMING_KEYWORDS.some(k => host.includes(k) || window.location.pathname.includes(k));
  if (!esSitioStreaming) {
    return; // Dejar la navegación cotidiana del usuario 100% normal
  }

  console.log('[Hydra Shield] Protección de video activa en:', host);

  // Anular window.open para scripts publicitarios en sitios de películas
  window.open = function(url, target, features) {
    console.warn('[Hydra Shield] Ventana emergente bloqueada en reproductor:', url);

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

  window.onbeforeunload = null;
})();
