// Hydra TV Shield - Interceptor Global en el contexto de página (MAIN world)
(function() {
  'use strict';

  const host = window.location.hostname.toLowerCase();
  
  // No intervenir en localhost, YouTube oficial o páginas de configuración
  if (host === 'localhost' || host === '127.0.0.1' || window.location.port === '5000' ||
      host.includes('brave') || host.includes('google') || host.includes('youtube') || host.includes('github')) {
    return;
  }

  // No intervenir en reproductores de video embebidos para no romper descifrado ni controles
  if (window.self !== window.top && (
      host.includes('streamwish') || host.includes('vidhide') || host.includes('voe') ||
      host.includes('dood') || host.includes('filemoon') || host.includes('streamtape') ||
      host.includes('waaw') || host.includes('netu') || host.includes('player.poseidon')
  )) {
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
      // Solo neutralizar si es target="_blank" hacia redes de anuncios conocidas
      if ((target === '_blank' || target === '_new') && href && !href.startsWith('javascript:')) {
        const esAdUrl = ['adsterra', 'popcash', 'popads', 'propeller', 'onclick', 'monetag', 'exoclick', 'doubleclick', 'ad-maven', 'richpush', 'trafficjunky'].some(ad => href.includes(ad));
        if (esAdUrl) {
          console.warn('[Hydra Shield MAIN] Enlace publicitario simulado bloqueado:', href);
          return;
        }
      }
      return originalAnchorClick.apply(this, arguments);
    };
  } catch(e) {}

  // 5. Interceptar y filtrar temporadas vacías (Temporada 0) en Next.js (PoseidonHD, etc.)
  function sanitizarNextData(data) {
    try {
      if (!data || !data.props || !data.props.pageProps) return data;
      const serie = data.props.pageProps.thisSerie || data.props.pageProps.thisMovie;
      if (serie && Array.isArray(serie.seasons)) {
        // Filtrar temporadas que tengan 0 episodios (ej. Temporada 0 vacía)
        const conEpisodios = serie.seasons.filter(s => Array.isArray(s.episodes) && s.episodes.length > 0);
        if (conEpisodios.length > 0) {
          serie.seasons = conEpisodios;
        }
      }
    } catch(e) {}
    return data;
  }

  let _nextDataVal = undefined;
  try {
    Object.defineProperty(window, '__NEXT_DATA__', {
      get: function() {
        return _nextDataVal;
      },
      set: function(val) {
        _nextDataVal = sanitizarNextData(val);
      },
      configurable: true
    });
  } catch(e) {}

  if (window.__NEXT_DATA__) {
    sanitizarNextData(window.__NEXT_DATA__);
  }
})();
