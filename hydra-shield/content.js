// Hydra TV Shield - Acelerador, Neutralizador de Trampas y Máscara de Marca Oficial
(function() {
  'use strict';

  const host = window.location.hostname.toLowerCase();
  
  if (host === 'localhost' || host === '127.0.0.1' || window.location.port === '5000' ||
      host.includes('brave') || host.includes('google') || host.includes('youtube') || host.includes('github')) {
    return;
  }

  // 1. Inyectar Estilos de Camuflaje Oficial Hydra TV (Oculta logos y menús de terceros)
  function inyectarEstilosHydraTV() {
    if (document.getElementById('hydra-brand-cloak-style')) return;
    const style = document.createElement('style');
    style.id = 'hydra-brand-cloak-style';
    style.textContent = `
      /* Ocultar marcas de terceros, barras de navegación y publicidad específica */
      #menu_top, header#menu_top, .menu_top,
      header.Header, header.site-header,
      #main_nav, nav#main_nav, nav.Menu, nav.navbar, nav.nav-menu,
      .header-container, .barColor, #nav_toggle, .nav_menu,

      #logo, a#logo, .logo, a.logo, .logo-ft, [id*="logo" i], [class*="logo" i],
      img[alt*="Poseidon" i], img[alt*="Cinemitas" i], img[alt*="Pelicine" i], img[alt*="Pelicula" i],
      img[alt*="Repelis" i], img[alt*="Argflix" i], img[src*="logo" i],
      a[href*="maspeliculashd" i][id*="logo" i], a[href*="poseidon" i][class*="logo" i],
      a[href="/"][class*="logo"], a[href="/"][id*="logo"], a[href="/"][title*="Poseidon" i],
      a[href="/"][title*="Peliculas" i],
      a:has(i.fa-plus), h1:has(i.fa-plus),

      #search_form, .search-form, form[action*="search" i], form[action*="buscar" i],
      .alert-danger, .adang, .alert, .notice, .warning-box, .aviso, .notice-box, .tip,
      .share, .social, .btn-share, .compartir, a[href*="facebook" i], a[href*="twitter" i],
      .comments, #comments, .disqus, #disqus_thread,
      footer, .footer, #footer, .copyright,

      aside.movie-sidebar-right, .movie-sidebar-right, .col-right,
      .related-movies, .top-movies, .s-related, .movie-stats {
        display: none !important;
        visibility: hidden !important;
        opacity: 0 !important;
        height: 0 !important;
        max-height: 0 !important;
        margin: 0 !important;
        padding: 0 !important;
        overflow: hidden !important;
        pointer-events: none !important;
      }

      /* Grid perfecto de dos columnas para MasPeliculasHD: Poster a la izquierda, Contenido a la derecha */
      .movie-layout {
        display: grid !important;
        grid-template-columns: 280px 1fr !important;
        gap: 32px !important;
        max-width: 1200px !important;
        margin: 0 auto !important;
        padding: 20px !important;
      }

      .movie-sidebar {
        display: block !important;
        width: 280px !important;
        max-width: 280px !important;
        position: static !important;
      }

      .movie-sidebar .movie-poster img {
        width: 100% !important;
        max-width: 280px !important;
        border-radius: 16px !important;
        display: block !important;
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.6) !important;
      }

      .movie-main {
        display: block !important;
        width: 100% !important;
        min-width: 0 !important;
      }

      .movie-header {
        display: block !important;
        margin-bottom: 24px !important;
        padding: 30px 40px !important;
        border-radius: 16px !important;
      }

      .movie-title {
        display: block !important;
        font-size: 2.2rem !important;
        font-weight: 800 !important;
        color: #fff !important;
        margin-bottom: 8px !important;
      }

      .movie-content {
        display: block !important;
      }

      .movie-content p {
        font-size: 1.05rem !important;
        line-height: 1.7 !important;
        color: #d1d5db !important;
      }

      .player-placeholder, #video, #player, #reproductor, .player-container {
        width: 100% !important;
        min-height: 480px !important;
        background: #000 !important;
        border-radius: 12px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
        overflow: hidden !important;
        box-shadow: 0 12px 40px rgba(0, 0, 0, 0.8) !important;
        position: relative !important;
      }

      #video iframe, #player iframe, #reproductor iframe, .player-placeholder iframe {
        width: 100% !important;
        height: 100% !important;
        min-height: 480px !important;
        border: none !important;
        display: block !important;
      }

      .play-button {
        background: #e50914 !important;
        color: #fff !important;
        font-size: 1.25rem !important;
        font-weight: 800 !important;
        padding: 16px 42px !important;
        border-radius: 50px !important;
        box-shadow: 0 6px 25px rgba(229, 9, 20, 0.6) !important;
        cursor: pointer !important;
        display: inline-flex !important;
        align-items: center !important;
        gap: 10px !important;
        transition: transform 0.2s ease, background 0.2s ease !important;
        z-index: 10 !important;
      }

      .play-button:hover {
        background: #b80710 !important;
        transform: scale(1.06) !important;
      }

      /* Idiomas y opciones de MasPeliculasHD */
      .lang {
        display: flex !important;
        gap: 10px !important;
        margin-bottom: 12px !important;
      }

      .lang div {
        background: rgba(255, 255, 255, 0.08) !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        color: #d1d5db !important;
        padding: 8px 18px !important;
        border-radius: 8px !important;
        cursor: pointer !important;
        font-weight: 700 !important;
        font-size: 0.9rem !important;
        transition: all 0.2s ease !important;
      }

      .lang div.active, .lang div:hover {
        background: #e50914 !important;
        border-color: #e50914 !important;
        color: #fff !important;
      }

      .player-options {
        display: block !important;
        margin-top: 14px !important;
      }

      .player-options ul {
        display: flex !important;
        gap: 10px !important;
        padding: 0 !important;
        list-style: none !important;
        flex-wrap: wrap !important;
      }

      .player-options li {
        background: rgba(255, 255, 255, 0.08) !important;
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
        color: #e5e7eb !important;
        padding: 8px 16px !important;
        border-radius: 8px !important;
        cursor: pointer !important;
        font-size: 0.85rem !important;
        font-weight: 600 !important;
        display: inline-flex !important;
        align-items: center !important;
        gap: 8px !important;
        transition: all 0.2s ease !important;
      }

      .player-options li.active, .player-options li:hover {
        background: #e50914 !important;
        border-color: #e50914 !important;
        color: #fff !important;
      }

      /* Presentación limpia, legible y atractiva en PoseidonHD */
      .TPost.movtv-info {
        display: flex !important;
        align-items: flex-start !important;
        gap: 28px !important;
        max-width: 1200px !important;
        margin: 20px auto 16px auto !important;
        padding: 0 24px !important;
        box-sizing: border-box !important;
      }

      .TPost.movtv-info .Image {
        width: 180px !important;
        min-width: 180px !important;
        flex-shrink: 0 !important;
        display: block !important;
      }

      .TPost.movtv-info .Image img {
        width: 100% !important;
        height: auto !important;
        border-radius: 14px !important;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.7) !important;
        display: block !important;
      }

      .TPost.movtv-info header {
        display: block !important;
        flex: 1 !important;
      }

      .TPost.movtv-info .Title {
        font-size: 2.3rem !important;
        font-weight: 800 !important;
        color: #ffffff !important;
        margin: 0 0 6px 0 !important;
        line-height: 1.2 !important;
      }

      .TPost.movtv-info .SubTitle {
        font-size: 1.1rem !important;
        color: #94a3b8 !important;
        display: block !important;
        margin-bottom: 12px !important;
      }

      .TPost.movtv-info .meta {
        display: flex !important;
        gap: 12px !important;
        color: #e50914 !important;
        font-weight: 700 !important;
        font-size: 0.95rem !important;
        margin-top: 8px !important;
      }

      .TPost.movtv-info .VotesCn, .TPost.movtv-info .ListPOpt, .TPost.movtv-info footer ul {
        display: none !important;
      }

      .hydra-injected-desc {
        color: #d1d5db !important;
        font-size: 1.05rem !important;
        line-height: 1.7 !important;
        margin-top: 14px !important;
        max-width: 850px !important;
        text-shadow: 0 1px 3px rgba(0, 0, 0, 0.8) !important;
      }

      body, html {
        background: #0a0b0e !important;
        color: #fff !important;
      }

      body.has-hydra-topbar {
        padding-top: 52px !important;
      }

      /* Barra Superior Oficial de Hydra TV (Solo modo Kiosk TV top-level) */
      #hydra-tv-topbar {
        position: fixed !important;
        top: 0 !important;
        left: 0 !important;
        right: 0 !important;
        height: 52px !important;
        background: rgba(10, 11, 14, 0.98) !important;
        backdrop-filter: blur(12px) !important;
        -webkit-backdrop-filter: blur(12px) !important;
        border-bottom: 1px solid rgba(255, 255, 255, 0.12) !important;
        display: flex !important;
        align-items: center !important;
        justify-content: space-between !important;
        padding: 0 20px !important;
        z-index: 2147483647 !important;
        font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.8) !important;
      }

      #hydra-btn-back {
        background: rgba(255, 255, 255, 0.12) !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        color: #ffffff !important;
        padding: 8px 18px !important;
        border-radius: 8px !important;
        cursor: pointer !important;
        font-weight: 700 !important;
        font-size: 0.95rem !important;
        display: inline-flex !important;
        align-items: center !important;
        gap: 8px !important;
        transition: all 0.2s ease !important;
        outline: none !important;
      }

      #hydra-btn-back:hover, #hydra-btn-back:focus {
        background: #e50914 !important;
        border-color: #e50914 !important;
        transform: scale(1.03) !important;
      }

      #hydra-brand-info {
        display: inline-flex !important;
        align-items: center !important;
        gap: 8px !important;
        font-weight: 900 !important;
        font-size: 1.15rem !important;
        color: #ffffff !important;
        letter-spacing: -0.5px !important;
        user-select: none !important;
      }

      #hydra-brand-info .hydra-logo-icon {
        color: #e50914 !important;
        font-size: 1.3rem !important;
      }
    `;
    (document.head || document.documentElement).appendChild(style);
  }

  // 1.1 Limpieza y Reemplazo de Textos de Terceros (Poseidon, PeliculasHD, Cinemitas, etc.)
  function camuflarTextos() {
    try {
      if (document.title) {
        document.title = document.title
          .replace(/peliculashd/gi, 'Hydra TV')
          .replace(/maspeliculashd/gi, 'Hydra TV')
          .replace(/poseidonhd\s*2?/gi, 'Hydra TV')
          .replace(/poseidon/gi, 'Hydra TV')
          .replace(/cinemitas\s*(hd)?/gi, 'Hydra TV')
          .replace(/pelicinehd/gi, 'Hydra TV')
          .replace(/pelicine/gi, 'Hydra TV')
          .replace(/repelishd/gi, 'Hydra TV')
          .replace(/repelis/gi, 'Hydra TV')
          .replace(/argflix/gi, 'Hydra TV')
          .replace(/verpel[ií]culas/gi, 'Hydra TV')
          .replace(/cuevana\s*\d*/gi, 'Hydra TV');
      }

      if (!document.body) return;

      const walker = document.createTreeWalker(
        document.body,
        NodeFilter.SHOW_TEXT,
        null,
        false
      );

      const bannedRegexes = [
        /peliculashd/gi,
        /maspeliculashd/gi,
        /poseidonhd\s*2?/gi,
        /cinemitas\s*(hd)?/gi,
        /pelicinehd/gi,
        /repelishd/gi,
        /repelis/gi,
        /argflix/gi,
        /verpel[ií]culas/gi,
        /cuevana\s*\d*/gi,
        /tuanime/gi
      ];
      let node;
      while (node = walker.nextNode()) {
        const val = node.nodeValue;
        if (!val || val.length < 3) continue;

        const lower = val.toLowerCase();
        if (lower.includes('no guardamos tus contraseñas') ||
            lower.includes('recuerda que no') ||
            lower.includes('servidores gratuitos de terceros') ||
            lower.includes('reportar link caido') ||
            lower.includes('donaciones') ||
            lower.includes('donar') ||
            lower.includes('bienvenido a verpelículas') ||
            lower.includes('tuanime.net')) {
          const parent = node.parentElement;
          if (parent && !parent.closest('#player') && !parent.closest('#reproductor') && !parent.closest('#video') && !parent.closest('.movie-header') && !parent.closest('.movie-content') && !parent.closest('.movie-main')) {
            parent.style.display = 'none';
          }
          continue;
        }

        let updatedVal = val;
        for (const reg of bannedRegexes) {
          if (reg.test(updatedVal)) {
            updatedVal = updatedVal.replace(reg, 'Hydra TV');
          }
        }
        if (updatedVal !== val) {
          node.nodeValue = updatedVal;
        }
      }
    } catch(e) {}
  }

  // 1.2 Purgador físico de elementos de marcas y cabeceras de terceros
  function purgarMarcasTerceros() {
    try {
      const selectores = [
        '#menu_top', '.header-container', '#logo', 'a#logo', '#main_nav', '#search_form', '.barColor',
        '#nav_toggle', '.movie-sidebar-right', 'aside.movie-sidebar-right', '.related-movies', '.top-movies',
        '.movie-stats', '.s-related', 'header.Header', 'footer', '#footer'
      ];
      for (const sel of selectores) {
        const elems = document.querySelectorAll(sel);
        elems.forEach(el => {
          if (el.id === 'hydra-tv-topbar' || el.closest('#hydra-tv-topbar')) return;
          if (el.id === 'player' || el.id === 'video' || el.id === 'reproductor' || el.closest('#video')) return;
          if (el.closest('.movie-header') || el.closest('.movie-main') || el.closest('.movie-sidebar')) return;
          el.remove();
        });
      }
    } catch(e) {}
  }

  // 2. Inyectar Barra Superior Interactiva de Hydra TV con botón Volver (Solo modo Kiosk TV top-level)
  function inyectarBarraSuperiorHydra() {
    // Si estamos dentro de un iframe (SPA de Hydra TV), el padre ya tiene la barra y los controles
    if (window.self !== window.top) {
      // Capturar Escape y Backspace para avisar al reproductor padre que cierre
      window.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' || (e.key === 'Backspace' && !['INPUT', 'TEXTAREA'].includes(document.activeElement?.tagName))) {
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
    bar.innerHTML = `
      <button id="hydra-btn-back" title="Volver al catálogo (Esc o Retroceso)">
        ← Volver al Inicio
      </button>
      <div id="hydra-brand-info">
        <span class="hydra-logo-icon">⚡</span>
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
      adIframes.forEach(f => {
        if (f.id !== 'hydra-player-iframe') f.remove();
      });
    } catch(e) {}
  }

  // 4. Interceptor de clics en la fase de captura
  window.addEventListener('click', function(e) {
    const el = e.target;
    if (!el) return;
    if (el.id === 'hydra-btn-back' || el.closest('#hydra-tv-topbar')) return;

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
            e.preventDefault();
            e.stopPropagation();
            e.stopImmediatePropagation();
            el.remove();
          }
        }
      }
    } catch(err) {}
  }, true);

  // 1.3 Enriquecer ficha y sinopsis en PoseidonHD
  function enriquecerFichaPoseidon() {
    if (!host.includes('poseidon')) return;
    try {
      const tpost = document.querySelector('.TPost.movtv-info');
      if (tpost && !tpost.querySelector('.hydra-injected-desc')) {
        const metaDesc = document.querySelector('meta[property="og:description"]')?.getAttribute('content') ||
                         document.querySelector('meta[name="description"]')?.getAttribute('content');
        if (metaDesc && metaDesc.trim().length > 20) {
          let descClean = metaDesc.replace(/poseidonhd\s*2?/gi, 'Hydra TV').trim();
          const p = document.createElement('p');
          p.className = 'hydra-injected-desc';
          p.innerText = descClean;
          const header = tpost.querySelector('header') || tpost;
          header.appendChild(p);
        }
      }
    } catch(e) {}
  }

  // 5. Acelerador de Reproducción Inmediata
  function acelerarReproduccion() {
    try {
      // A. PoseidonHD: Selección automática inicial una sola vez sin parpadeo de pestaña
      if (host.includes('poseidon')) {
        const primerServidor = document.querySelector('li.clili[data-tr]');
        if (primerServidor && !primerServidor.dataset.hydraSelected) {
          primerServidor.dataset.hydraSelected = 'true';
          primerServidor.click();
          setTimeout(() => {
            const subTabs = document.querySelectorAll('.sub-tab-lang');
            subTabs.forEach(st => st.classList.add('hide'));
          }, 120);
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
      // A. Dropdown de temporadas (<select id="select-season"> en PoseidonHD o similares)
      const selectSeasons = document.querySelectorAll('#select-season, select[name*="season" i], select[class*="season" i]');
      selectSeasons.forEach(selectEl => {
        const options = Array.from(selectEl.options);
        if (!options.length) return;

        // Buscar si existe opción 0 o vacía
        const optCero = options.find(o => o.value === '0' || o.text.toLowerCase().includes('temporada 0') || o.text.toLowerCase().includes('season 0'));
        const optValida = options.find(o => o.value === '1' || o.text.toLowerCase().includes('temporada 1') || o.text.toLowerCase().includes('season 1'))
                          || options.find(o => o !== optCero);

        // Contenedor de episodios en pantalla
        const epContainer = document.querySelector('.all-episodes, .episodes, ul.MovieList, #episodes, .episode-list');
        const tieneEpisodios = epContainer && epContainer.querySelectorAll('li, .episode-item, article, a').length > 0;

        // Si la temporada actual seleccionada es 0 o está vacía y existe una temporada con contenido
        if (optCero && optValida) {
          if (selectEl.value === optCero.value || !tieneEpisodios) {
            console.warn('[Hydra Shield] Temporada 0 vacía detectada. Cambiando automáticamente a:', optValida.text);

            // Cambiar usando setter nativo para activar el observer de React/Next.js
            const valueSetter = Object.getOwnPropertyDescriptor(window.HTMLSelectElement.prototype, 'value')?.set;
            if (valueSetter) {
              valueSetter.call(selectEl, optValida.value);
            } else {
              selectEl.value = optValida.value;
            }

            selectEl.dispatchEvent(new Event('input', { bubbles: true }));
            selectEl.dispatchEvent(new Event('change', { bubbles: true }));

            // Eliminar la opción 0 vacía del menú desplegable para que no aparezca
            optCero.remove();
          } else if (tieneEpisodios && selectEl.value !== optCero.value) {
            // Ya estamos en la temporada 1, eliminar opción 0 residual
            optCero.remove();
          }
        }
      });

      // B. Botones o pestañas de temporada (ej. [data-season="0"], .season-tab)
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

  inyectarEstilosHydraTV();
  inyectarBarraSuperiorHydra();
  purgarMarcasTerceros();
  camuflarTextos();
  corregirTemporadas();
  enriquecerFichaPoseidon();
  limpiarCapasYTrampas();
  acelerarReproduccion();

  const intervalId = setInterval(() => {
    inyectarEstilosHydraTV();
    inyectarBarraSuperiorHydra();
    purgarMarcasTerceros();
    camuflarTextos();
    corregirTemporadas();
    enriquecerFichaPoseidon();
    limpiarCapasYTrampas();
    acelerarReproduccion();
  }, 250);

  setTimeout(() => {
    clearInterval(intervalId);
    const slowInterval = setInterval(() => {
      inyectarBarraSuperiorHydra();
      purgarMarcasTerceros();
      camuflarTextos();
      corregirTemporadas();
      enriquecerFichaPoseidon();
      limpiarCapasYTrampas();
      acelerarReproduccion();
    }, 1200);
    setTimeout(() => clearInterval(slowInterval), 20000);
  }, 4000);

  document.addEventListener('DOMContentLoaded', () => {
    inyectarEstilosHydraTV();
    inyectarBarraSuperiorHydra();
    purgarMarcasTerceros();
    camuflarTextos();
    corregirTemporadas();
    enriquecerFichaPoseidon();
    limpiarCapasYTrampas();
    acelerarReproduccion();
  });
})();
