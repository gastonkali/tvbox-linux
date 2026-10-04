// Hydra TV Shield - Absorbedor y Asesino de pestañas emergentes en segundo plano
'use strict';

console.log('[Hydra Shield] Service worker iniciado y vigilando pestañas.');

// Escuchar creación de cualquier pestaña nueva
chrome.tabs.onCreated.addListener(async (tab) => {
  // Si la pestaña tiene una pestaña padre (fue abierta por otra página)
  if (tab.openerTabId) {
    try {
      const opener = await chrome.tabs.get(tab.openerTabId);
      if (opener && opener.url) {
        const openerUrl = opener.url.toLowerCase();
        
        // Si el padre fue Hydra Tv (el usuario hizo clic en una película desde el catálogo), PERMITIR
        const isFromHydraTv = openerUrl.includes('localhost:5000') ||
                              openerUrl.includes('127.0.0.1:5000') ||
                              openerUrl.includes(':5000');

        if (isFromHydraTv) {
          console.log('[Hydra Shield] Película abierta legítimamente desde Hydra TV:', tab.url || tab.pendingUrl);
          return;
        }

        // Si el padre NO es Hydra Tv (es un sitio de películas abriendo publicidad), DESTRUIR
        console.warn('[Hydra Shield] ¡Pestaña publicitaria emergente absorbida y destruida!', {
          tabId: tab.id,
          origen: openerUrl
        });
        
        await chrome.tabs.remove(tab.id);
      }
    } catch (err) {
      console.error('[Hydra Shield] Error al evaluar pestaña emergente:', err);
    }
  }
});

// Escuchar creación de ventanas emergentes (popups independientes)
chrome.windows.onCreated.addListener(async (win) => {
  if (win.type === 'popup') {
    try {
      // Obtener la pestaña activa de esa ventana
      const [tab] = await chrome.tabs.query({ windowId: win.id, active: true });
      if (tab && tab.openerTabId) {
        const opener = await chrome.tabs.get(tab.openerTabId);
        if (opener && opener.url && !opener.url.includes(':5000')) {
          console.warn('[Hydra Shield] Ventana emergente (popup) cerrada inmediatamente:', win.id);
          await chrome.windows.remove(win.id);
        }
      }
    } catch(err) {}
  }
});
