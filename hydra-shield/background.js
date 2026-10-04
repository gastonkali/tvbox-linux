// Hydra TV Shield - Motor Definitivo Anti-Popups y Absorbedor de Ventanas
'use strict';

console.log('[Hydra Shield] Service worker iniciado y vigilando en segundo plano.');

// Dominios e identificadores conocidos de redes publicitarias, popunders y trackers
const AD_PATTERNS = [
  'adsterra', 'popcash', 'popads', 'propeller', 'onclick', 'monetag',
  'exoclick', 'hilltopads', 'clickadu', 'ad-maven', 'richpush', 'adkeeper',
  'juicyads', 'bet365', '1xbet', 'betwinner', 'melbet', 'casino', 'betting',
  'track', 'traffic', 'syndication', 'doubleclick', 'adnxs', 'smartadserver',
  'creative', 'landing', 'redirect', 'offer', 'bonus', 'dating', 'cleaner',
  'streamwish.to/ads', 'popunder', 'histats', 'alwingulla', 'whomever', 'deloplen'
];

function esUrlPublicitaria(url) {
  if (!url) return false;
  const u = url.toLowerCase();
  if (u.startsWith('brave://') || u.startsWith('chrome://')) return false;
  if (u.includes('youtube.com') || u.includes('youtu.be') || u.includes(':5000')) return false;
  return AD_PATTERNS.some(p => u.includes(p));
}

// 1. Escuchar creación de pestañas (NUEVAS PESTAÑAS)
chrome.tabs.onCreated.addListener(async (tab) => {
  const nuevaUrl = (tab.url || tab.pendingUrl || '').toLowerCase();

  // Si la URL inicial ya delata que es un anuncio -> CERRAR AL INSTANTE
  if (esUrlPublicitaria(nuevaUrl)) {
    console.warn('[Hydra Shield] Pestaña publicitaria neutralizada de inmediato:', nuevaUrl);
    try { await chrome.tabs.remove(tab.id); } catch(e) {}
    return;
  }

  // En modo TV Kiosk / Reproductor de streaming:
  // Si ya hay pestañas abiertas y se crea una nueva pestaña hija o ventana emergente sin ser navegación manual:
  try {
    const todas = await chrome.tabs.query({});
    if (todas.length > 1) {
      if (nuevaUrl.startsWith('brave://') || nuevaUrl.startsWith('chrome://')) {
        return;
      }
      
      // Si tiene openerTabId O fue abierta en el contexto de un reproductor:
      if (tab.openerTabId) {
        const opener = await chrome.tabs.get(tab.openerTabId);
        const openerUrl = (opener?.url || '').toLowerCase();
        // Si el padre no es la interfaz base :5000, cerrarlo (es un popup de streaming)
        if (!openerUrl.includes(':5000/api') && !openerUrl.endsWith(':5000/')) {
          console.warn('[Hydra Shield] Pestaña hija bloqueada en reproductor:', tab.id);
          await chrome.tabs.remove(tab.id);
          return;
        }
      }
    }
  } catch(e) {}
});

// 2. Escuchar cambios de URL en pestañas (Redirecciones o cargas dinámicas)
chrome.tabs.onUpdated.addListener(async (tabId, changeInfo, tab) => {
  const url = (changeInfo.url || tab.url || tab.pendingUrl || '').toLowerCase();
  if (url && esUrlPublicitaria(url)) {
    console.warn('[Hydra Shield] Redirección publicitaria abortada:', url);
    try {
      await chrome.tabs.remove(tabId);
    } catch(e) {}
  }
});

// 3. Absorber y cerrar de inmediato cualquier VENTANA EMERGENTE (Pop-up windows)
chrome.windows.onCreated.addListener(async (win) => {
  if (win.type === 'popup') {
    console.warn('[Hydra Shield] Ventana emergente (popup window) interceptada y destruida:', win.id);
    try {
      await chrome.windows.remove(win.id);
    } catch (err) {}
  }
});
