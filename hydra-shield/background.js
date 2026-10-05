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
  'streamwish.to/ads', 'popunder', 'histats', 'alwingulla', 'whomever', 'deloplen',
  '.cfd', 'cineflowdigital', 'cineshow', '.online/ver', 'cloudflare-verify'
];

function esUrlPublicitaria(url) {
  if (!url) return false;
  const u = url.toLowerCase();
  if (u.startsWith('brave://') || u.startsWith('chrome://')) return false;
  if (u.includes('youtube.com') || u.includes('youtu.be') || u.includes(':5000')) return false;
  if (u.includes('streamwish') || u.includes('vidhide') || u.includes('voe.sx') ||
      u.includes('dood') || u.includes('poseidonhd') || u.includes('cinemitas') ||
      u.includes('pelicine') || u.includes('maspeliculashd')) return false;
  return AD_PATTERNS.some(p => u.includes(p));
}

// 1. Escuchar creación de pestañas (NUEVAS PESTAÑAS)
chrome.tabs.onCreated.addListener(async (tab) => {
  const nuevaUrl = (tab.url || tab.pendingUrl || '').toLowerCase();
  if (nuevaUrl.startsWith('brave://') || nuevaUrl.startsWith('chrome://')) return;

  // Si la URL inicial ya delata que es un anuncio -> CERRAR AL INSTANTE
  if (esUrlPublicitaria(nuevaUrl)) {
    console.warn('[Hydra Shield] Pestaña publicitaria neutralizada de inmediato:', nuevaUrl);
    try { await chrome.tabs.remove(tab.id); } catch(e) {}
    return;
  }

  // En modo TV Kiosk / Reproductor de streaming:
  // Si la pestaña tiene un openerTabId, fue disparada por un clic o script en otra pestaña
  if (tab.openerTabId) {
    try {
      const opener = await chrome.tabs.get(tab.openerTabId);
      const openerUrl = (opener?.url || '').toLowerCase();
      // Si fue abierta desde la app de Hydra (:5000) o desde cualquier sitio de streaming / reproductor:
      // ES UN POPUP PUBLICITARIO NO DESEADO (Hydra TV es Kiosk y nunca abre pestañas externas)
      if (openerUrl.includes(':5000') || openerUrl.includes('poseidon') ||
          openerUrl.includes('cinemitas') || openerUrl.includes('pelicine') ||
          openerUrl.includes('streamwish') || openerUrl.includes('vidhide') ||
          openerUrl.includes('maspeliculashd') || openerUrl.includes('repelishd')) {
        console.warn('[Hydra Shield] Popup publicitario bloqueado y destruido:', tab.id, nuevaUrl);
        await chrome.tabs.remove(tab.id);
        return;
      }
    } catch(e) {}
  }
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
