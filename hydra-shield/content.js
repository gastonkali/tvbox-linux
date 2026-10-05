// Hydra TV Shield - Acelerador, Neutralizador de Trampas y Máscara de Marca Oficial
(function() {
  'use strict';

  const host = window.location.hostname.toLowerCase();
  
  if (host === 'localhost' || host === '127.0.0.1' || window.location.port === '5000' ||
      host.includes('brave') || host.includes('google') || host.includes('youtube') || host.includes('github')) {
    return;
  }

  // Detectar si estamos embebidos dentro de un iframe (como el reproductor de Hydra TV)
  const isEmbedded = (window.self !== window.top);
  if (isEmbedded) {
    try {
      document.documentElement.classList.add('in-hydra-frame');
      if (document.body) {
        document.body.classList.add('in-hydra-frame');
      } else {
        document.addEventListener('DOMContentLoaded', () => {
          if (document.body) document.body.classList.add('in-hydra-frame');
        });
      }
    } catch(e) {}
  }

  // No modificar DOM ni estilos en reproductores de streaming directos (cyberlockers de video crudo)
  if (isEmbedded && (
      host.includes('streamwish') || host.includes('vidhide') || host.includes('voe') ||
      host.includes('dood') || host.includes('filemoon') || host.includes('streamtape') ||
      host.includes('waaw') || host.includes('netu')
  )) {
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

      /* ==========================================================================
         MODO EMBEBIDO HYDRA TV (html.in-hydra-frame / body.in-hydra-frame)
         Convierte el sitio del proveedor en un REPRODUCTOR DE VIDEO PURO a pantalla completa
         ========================================================================== */
      html.in-hydra-frame,
      body.in-hydra-frame {
        margin: 0 !important;
        padding: 0 !important;
        width: 100vw !important;
        height: 100vh !important;
        max-width: 100vw !important;
        max-height: 100vh !important;
        min-width: 100vw !important;
        min-height: 100vh !important;
        overflow: hidden !important;
        background: #000 !important;
      }

      /* Resetear contenedores intermedios para que no restrinjan el tamaño */
      html.in-hydra-frame #__next,
      html.in-hydra-frame .body,
      html.in-hydra-frame .body.slider,
      html.in-hydra-frame #aa-wp,
      html.in-hydra-frame .bd,
      html.in-hydra-frame .cont,
      html.in-hydra-frame .EcBgA,
      html.in-hydra-frame .video,
      html.in-hydra-frame .video.cont {
        margin: 0 !important;
        padding: 0 !important;
        width: 100vw !important;
        height: 100vh !important;
        max-width: 100vw !important;
        max-height: 100vh !important;
        min-width: 100vw !important;
        min-height: 100vh !important;
        background: #000 !important;
        transform: none !important;
        filter: none !important;
        perspective: none !important;
        contain: none !important;
      }

      /* Ocultar ABSOLUTAMENTE TODA la interfaz externa, fichas, listas de episodios y recomendaciones */
      html.in-hydra-frame header,
      html.in-hydra-frame footer,
      html.in-hydra-frame #header,
      html.in-hydra-frame #footer,
      html.in-hydra-frame nav,
      html.in-hydra-frame aside,
      html.in-hydra-frame .site-header,
      html.in-hydra-frame .Header,
      html.in-hydra-frame .ft,
      html.in-hydra-frame .backdrop > h1,
      html.in-hydra-frame .backdrop > h2,
      html.in-hydra-frame h1.Title,
      html.in-hydra-frame h2.SubTitle,
      html.in-hydra-frame .Title,
      html.in-hydra-frame .SubTitle,
      html.in-hydra-frame .TPost,
      html.in-hydra-frame .movtv-info,
      html.in-hydra-frame .movie-layout,
      html.in-hydra-frame .movie-header,
      html.in-hydra-frame .movie-main,
      html.in-hydra-frame .movie-sidebar,
      html.in-hydra-frame .movie-sidebar-right,
      html.in-hydra-frame .movie-content,
      html.in-hydra-frame .Description,
      html.in-hydra-frame .InfoList,
      html.in-hydra-frame .VotesCn,
      html.in-hydra-frame .Prct,
      html.in-hydra-frame .meta,
      html.in-hydra-frame .MvTbCn,
      html.in-hydra-frame .all-episodes,
      html.in-hydra-frame .episodes,
      html.in-hydra-frame .episodes-nav,
      html.in-hydra-frame .select-season,
      html.in-hydra-frame #select-season,
      html.in-hydra-frame .mb3,
      html.in-hydra-frame .cont.mb3,
      html.in-hydra-frame .TpRwCont,
      html.in-hydra-frame .MovieList,
      html.in-hydra-frame .top-movies,
      html.in-hydra-frame .s-related,
      html.in-hydra-frame .related-movies,
      html.in-hydra-frame .modal,
      html.in-hydra-frame #mdl-downloads,
      html.in-hydra-frame .comments,
      html.in-hydra-frame #comments,
      html.in-hydra-frame .disqus,
      html.in-hydra-frame .share,
      html.in-hydra-frame .social,
      html.in-hydra-frame .bannerAds,
      html.in-hydra-frame .banner_bannerAds__PHIkK,
      html.in-hydra-frame ins,
      html.in-hydra-frame .lgtbx-lnk,
      html.in-hydra-frame .fa-lightbulb,
      html.in-hydra-frame [class*="destacadas" i],
      html.in-hydra-frame [class*="relacionadas" i],
      html.in-hydra-frame #hydra-tv-topbar {
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

      /* Expandir el contenedor del reproductor al 100vw x 100vh */
      html.in-hydra-frame .video-container,
      html.in-hydra-frame .TPlayer,
      html.in-hydra-frame .TPlayerCn,
      html.in-hydra-frame .embed_div,
      html.in-hydra-frame #video,
      html.in-hydra-frame #player,
      html.in-hydra-frame #reproductor,
      html.in-hydra-frame .player-placeholder,
      html.in-hydra-frame .player-container,
      html.in-hydra-frame .play-box,
      html.in-hydra-frame #play-video,
      html.in-hydra-frame .video-content,
      html.in-hydra-frame .player_content,
      html.in-hydra-frame .player-holder {
        position: fixed !important;
        top: 0 !important;
        left: 0 !important;
        right: 0 !important;
        bottom: 0 !important;
        width: 100vw !important;
        height: 100vh !important;
        max-width: 100vw !important;
        max-height: 100vh !important;
        min-width: 100vw !important;
        min-height: 100vh !important;
        margin: 0 !important;
        padding: 0 !important;
        padding-bottom: 0 !important; /* Neutraliza padding-bottom: 56.25% */
        border: none !important;
        border-radius: 0 !important;
        box-shadow: none !important;
        background: #000 !important;
        z-index: 2147483640 !important;
        overflow: hidden !important;
      }

      /* Iframe o video interno ocupando exactamente el 100% */
      html.in-hydra-frame .video-container iframe,
      html.in-hydra-frame .TPlayer iframe,
      html.in-hydra-frame .TPlayerCn iframe,
      html.in-hydra-frame .embed_div iframe,
      html.in-hydra-frame #video iframe,
      html.in-hydra-frame #player iframe,
      html.in-hydra-frame #reproductor iframe,
      html.in-hydra-frame .player-placeholder iframe,
      html.in-hydra-frame .player-container iframe,
      html.in-hydra-frame .play-box iframe,
      html.in-hydra-frame #play-video iframe,
      html.in-hydra-frame video {
        position: absolute !important;
        top: 0 !important;
        left: 0 !important;
        width: 100vw !important;
        height: 100vh !important;
        max-width: 100vw !important;
        max-height: 100vh !important;
        min-width: 100vw !important;
        min-height: 100vh !important;
        border: none !important;
        border-radius: 0 !important;
        margin: 0 !important;
        padding: 0 !important;
        background: #000 !important;
        z-index: 2147483641 !important;
      }

      /* Botón de inicio Play previo a la carga (overlay PoseidonHD) */
      html.in-hydra-frame .video-container > div:not(iframe) {
        position: absolute !important;
        top: 0 !important;
        left: 0 !important;
        width: 100vw !important;
        height: 100vh !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        background: rgba(0, 0, 0, 0.7) !important;
        z-index: 2147483642 !important;
      }

      /* Selector de Idiomas / Servidores flotante y limpio en la esquina superior */
      html.in-hydra-frame ul.TPlayerNv,
      html.in-hydra-frame .tab_language_movie,
      html.in-hydra-frame .lang,
      html.in-hydra-frame .player-options {
        position: fixed !important;
        top: 12px !important;
        left: 14px !important;
        z-index: 2147483645 !important;
        background: rgba(10, 11, 14, 0.85) !important;
        backdrop-filter: blur(10px) !important;
        -webkit-backdrop-filter: blur(10px) !important;
        padding: 4px 8px !important;
        border-radius: 8px !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.8) !important;
        opacity: 0.85 !important;
        transition: opacity 0.2s ease !important;
        margin: 0 !important;
      }

      html.in-hydra-frame ul.TPlayerNv:hover,
      html.in-hydra-frame .tab_language_movie:hover,
      html.in-hydra-frame .lang:hover,
      html.in-hydra-frame .player-options:hover {
        opacity: 1 !important;
      }

      /* Publicidad flotante específica de player.poseidonhd2.co */
      .floating-banner,
      .ribbon-1,
      [class*="floating-banner"] {
        display: none !important;
        visibility: hidden !important;
        pointer-events: none !important;
      }

      /* Cuando se visualiza en modo completo / pestaña directa, limpiar elementos de votación y redes */
      .TPost.movtv-info .VotesCn,
      .TPost.movtv-info .ListPOpt,
      .TPost.movtv-info footer ul {
        display: none !important;
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

  // 1.1 Limpieza de Título (Hydra TV)
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
      // Capturar Backspace para avisar al reproductor padre que cierre (sin atrapar Escape para permitir salir de pantalla completa)
      window.addEventListener('keydown', (e) => {
        if (e.key === 'Backspace' && !['INPUT', 'TEXTAREA'].includes(document.activeElement?.tagName)) {
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

  // 2.1 Forzar dimensiones exactas y neutralizar estilos inline en Modo Embebido
  function optimizarModoEmbebido() {
    if (!isEmbedded) return;
    try {
      const playerHolders = document.querySelectorAll(
        '.video-container, .TPlayer, .TPlayerCn, .embed_div, #video, #player, #reproductor, .player-placeholder, .player-container, .play-box, #play-video, .video-content, .player_content, .player-holder'
      );
      playerHolders.forEach(el => {
        el.style.setProperty('position', 'fixed', 'important');
        el.style.setProperty('top', '0px', 'important');
        el.style.setProperty('left', '0px', 'important');
        el.style.setProperty('right', '0px', 'important');
        el.style.setProperty('bottom', '0px', 'important');
        el.style.setProperty('width', '100vw', 'important');
        el.style.setProperty('height', '100vh', 'important');
        el.style.setProperty('max-width', '100vw', 'important');
        el.style.setProperty('max-height', '100vh', 'important');
        el.style.setProperty('margin', '0px', 'important');
        el.style.setProperty('padding', '0px', 'important');
        el.style.setProperty('padding-bottom', '0px', 'important');
        el.style.setProperty('border', 'none', 'important');
        el.style.setProperty('border-radius', '0px', 'important');
        el.style.setProperty('z-index', '2147483640', 'important');
      });

      const iframes = document.querySelectorAll(
        '.video-container iframe, .TPlayer iframe, .TPlayerCn iframe, .embed_div iframe, #video iframe, #player iframe, #reproductor iframe, .player-placeholder iframe, .player-container iframe'
      );
      iframes.forEach(f => {
        f.style.setProperty('position', 'absolute', 'important');
        f.style.setProperty('top', '0px', 'important');
        f.style.setProperty('left', '0px', 'important');
        f.style.setProperty('width', '100vw', 'important');
        f.style.setProperty('height', '100vh', 'important');
        f.style.setProperty('max-width', '100vw', 'important');
        f.style.setProperty('max-height', '100vh', 'important');
        f.style.setProperty('border', 'none', 'important');
        f.style.setProperty('border-radius', '0px', 'important');
      });
    } catch(e) {}
  }

  // 3. Destructor de capas invisibles superpuestas (Clickjacking Overlays)
  function limpiarCapasYTrampas() {
    try {
      const elements = document.querySelectorAll('div, a, span, section');
      for (const el of elements) {
        if (el.id === 'hydra-tv-topbar' || el.closest('#hydra-tv-topbar')) continue;
        if (el.id === 'start' || el.id === 'container' || el.id === 'player' || el.id === 'video' ||
            el.closest('#player') || el.closest('#video') || el.closest('#container') || el.closest('.TPlayer')) continue;

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

      // Eliminar únicamente iframes publicitarios confirmados externos (NUNCA reproductores)
      const adIframes = document.querySelectorAll('iframe');
      adIframes.forEach(f => {
        if (f.id === 'playerIframe' || f.id === 'hydra-player-iframe') return;
        if (f.closest('#player') || f.closest('#video') || f.closest('#reproductor') ||
            f.closest('.video-container') || f.closest('.TPlayer') || f.closest('#container')) return;

        const src = (f.src || '').toLowerCase();
        const esAdUrl = ['adsterra', 'popcash', 'popads', 'propeller', 'onclick', 'monetag', 'exoclick', 'doubleclick', 'ad-maven', 'richpush', 'trafficjunky'].some(ad => src.includes(ad));
        if (esAdUrl) {
          f.remove();
        }
      });
    } catch(e) {}
  }

  // 4. Interceptor de clics en la fase de captura
  window.addEventListener('click', function(e) {
    const el = e.target;
    if (!el) return;
    if (el.id === 'hydra-btn-back' || el.closest('#hydra-tv-topbar')) return;

    // Si el usuario o un script hace clic en un enlace con target="_blank" o target="_new"
    const a = el.closest('a');
    if (a) {
      const target = (a.getAttribute('target') || '').toLowerCase();
      const href = (a.getAttribute('href') || '').toLowerCase();
      if (target === '_blank' || target === '_new') {
        // En sitios de streaming NINGÚN enlace target="_blank" es legítimo (todos son popups o anuncios)
        console.warn('[Hydra Shield CAPTURE] target="_blank" en sitio de streaming neutralizado:', href);
        a.removeAttribute('target');
        a.target = '';
        if (href && !href.startsWith('javascript:') && !href.includes(window.location.hostname)) {
          e.preventDefault();
          e.stopPropagation();
          e.stopImmediatePropagation();
          return;
        }
      }
    }

    // Si el clic fue en un overlay transparente gigante
    try {
      const style = window.getComputedStyle(el);
      if ((style.position === 'fixed' || style.position === 'absolute') && parseInt(style.zIndex, 10) > 90) {
        if (el.id === 'start' || el.id === 'container' || el.id === 'player' || el.id === 'video' ||
            el.closest('#player') || el.closest('#video') || el.closest('#container') || el.closest('.TPlayer')) return;

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


  // 5. Acelerador de Reproducción Inmediata
  function acelerarReproduccion() {
    // Permitir interacción 100% manual y limpia en PoseidonHD sin desplegar menús solos
    if (host.includes('poseidon')) return;
    try {

      // B. Cinemitas: Clic en primer servidor REAL (excluyendo estrictamente trailers)
      if (host.includes('cinemitas') || document.querySelector('#playeroptionsul')) {
        const opciones = document.querySelectorAll('#playeroptionsul li');
        let servidorReal = null;
        for (const opt of opciones) {
          const texto = (opt.innerText || opt.textContent || '').toLowerCase();
          const dataType = (opt.getAttribute('data-type') || '').toLowerCase();
          const optId = (opt.id || '').toLowerCase();
          if (texto.includes('trailer') || dataType.includes('trailer') || optId.includes('trailer')) {
            continue;
          }
          servidorReal = opt;
          break;
        }

        const optActiva = document.querySelector('#playeroptionsul li.active');
        const activaEsTrailer = optActiva && (
          (optActiva.innerText || '').toLowerCase().includes('trailer') ||
          (optActiva.getAttribute('data-type') || '').toLowerCase().includes('trailer') ||
          (optActiva.id || '').toLowerCase().includes('trailer')
        );

        if (servidorReal && (!servidorReal.classList.contains('active') || activaEsTrailer)) {
          console.log('[Hydra Shield] Seleccionando servidor real en Cinemitas (evitando trailer)');
          servidorReal.click();
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
  optimizarModoEmbebido();
  purgarMarcasTerceros();
  camuflarTextos();
  corregirTemporadas();
  limpiarCapasYTrampas();
  acelerarReproduccion();

  const intervalId = setInterval(() => {
    inyectarEstilosHydraTV();
    inyectarBarraSuperiorHydra();
    optimizarModoEmbebido();
    purgarMarcasTerceros();
    camuflarTextos();
    corregirTemporadas();
    limpiarCapasYTrampas();
    acelerarReproduccion();
  }, 250);

  setTimeout(() => {
    clearInterval(intervalId);
    const slowInterval = setInterval(() => {
      inyectarBarraSuperiorHydra();
      optimizarModoEmbebido();
      purgarMarcasTerceros();
      camuflarTextos();
      corregirTemporadas();
      limpiarCapasYTrampas();
      acelerarReproduccion();
    }, 1200);
    setTimeout(() => clearInterval(slowInterval), 20000);
  }, 4000);

  document.addEventListener('DOMContentLoaded', () => {
    inyectarEstilosHydraTV();
    inyectarBarraSuperiorHydra();
    optimizarModoEmbebido();
    purgarMarcasTerceros();
    camuflarTextos();
    corregirTemporadas();
    limpiarCapasYTrampas();
    acelerarReproduccion();
  });
})();
