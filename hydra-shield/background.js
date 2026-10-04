// Hydra TV Shield - Absorbedor Inteligente de pestañas emergentes en segundo plano
'use strict';

console.log('[Hydra Shield] Service worker iniciado y vigilando pestañas.');

// Registro dinámico de pestañas que reproducen contenido de Hydra TV
const streamingTabs = new Set();

// Proveedores y dominios de streaming reconocidos
const STREAMING_DOMAINS = [
  'pelicinehd', 'poseidonhd', 'series24', 'repelishd', 'cinemitas', 
  'ultrapeli', 'dramafuntv', 'gnularetro', 'maspeliculashd', 'argflix',
  'streamwish', 'filemoon', 'dood', 'voe', 'netu', 'waaw', 'uqload', 'mixdrop'
];

function esDominioStreaming(url) {
  if (!url) return false;
  const u = url.toLowerCase();
  return STREAMING_DOMAINS.some(d => u.includes(d));
}

// 1. Escuchar creación de pestañas
chrome.tabs.onCreated.addListener(async (tab) => {
  if (!tab.openerTabId) return;

  try {
    const opener = await chrome.tabs.get(tab.openerTabId);
    if (!opener || !opener.url) return;

    const openerUrl = opener.url.toLowerCase();

    // Caso A: Hydra TV (:5000) abre una película -> Registrar la pestaña como reproductor protegido
    if (openerUrl.includes(':5000') || openerUrl.includes('localhost') || openerUrl.includes('127.0.0.1')) {
      console.log('[Hydra Shield] Pestaña de streaming registrada:', tab.id);
      streamingTabs.add(tab.id);
      return;
    }

    // Caso B: El padre es una pestaña de streaming registrada O un dominio de streaming
    const padreEsStreaming = streamingTabs.has(tab.openerTabId) || esDominioStreaming(openerUrl);

    if (padreEsStreaming) {
      // Si la pestaña hija es de navegación propia del usuario (pestaña nueva manual), no cerrar
      const nuevaUrl = (tab.url || tab.pendingUrl || '').toLowerCase();
      if (nuevaUrl.startsWith('brave://') || nuevaUrl.startsWith('chrome://')) {
        return;
      }

      console.warn('[Hydra Shield] Anuncio emergente absorbido desde reproductor de streaming:', {
        tabId: tab.id,
        origen: openerUrl,
        destino: nuevaUrl
      });
      await chrome.tabs.remove(tab.id);
      return;
    }

    // Caso C: Navegación normal del usuario en cualquier otra web -> NO INTERVENIR
  } catch (err) {}
});

// 2. Limpiar pestañas cerradas del registro
chrome.tabs.onRemoved.addListener((tabId) => {
  streamingTabs.delete(tabId);
});

// 3. Manejo de ventanas emergentes (popups independientes)
chrome.windows.onCreated.addListener(async (win) => {
  if (win.type === 'popup') {
    try {
      const [tab] = await chrome.tabs.query({ windowId: win.id, active: true });
      if (tab && tab.openerTabId) {
        const opener = await chrome.tabs.get(tab.openerTabId);
        if (opener && (streamingTabs.has(tab.openerTabId) || esDominioStreaming(opener.url))) {
          console.warn('[Hydra Shield] Ventana emergente publicitaria cerrada:', win.id);
          await chrome.windows.remove(win.id);
        }
      }
    } catch(err) {}
  }
});
