# 📺 Mi TV Box (Linux Edition)

Plataforma ligera para transformar tu PC con **Ubuntu / Linux** en una experiencia de **Smart TV / TV Box**, manteniendo el uso normal de tu ordenador como una aplicación independiente.

Diseñada para reproducir tanto enlaces directos de video (`.m3u8`, `.mp4`) como páginas de streaming complejas, aprovechando el bloqueo agresivo de publicidad de **Brave Browser**.

---

## ✨ Características

- 🎯 **Aplicación independiente:** Funciona como un programa normal en tu menú de aplicaciones de Ubuntu. Al cerrarse, apaga todos sus procesos en segundo plano.
- 🛡️ **Perfil aislado de Brave:** Corre con su propio perfil (`~/.config/tvbox-brave`), evitando interferir con tus pestañas, historial o extensiones personales.
- 🚫 **Sin publicidad en videos:** Bloqueo de redirecciones y anuncios agresivos.
- ⚡ **Soporte de múltiples fuentes:**
  - `directo`: Streams HLS (`.m3u8`) o archivos `.mp4` reproducidos al instante en un reproductor interno ultraligero.
  - `web`: Páginas de streaming abiertas en modo Kiosk.
- 🎮 **Navegación 10-foot UI:** Navegable mediante teclado (flechas `←` `→` y `Enter`) o control remoto inalámbrico.
- 🔍 **Buscador en tiempo real:** Encuentra cualquier canal o video al instante (atajo `/`).
- 🤖 **Auto-Play:** Script para hacer clic automático en botones de reproducción rebeldes.
- 🛡️ **Acceso Remoto Seguro (Offshore VPS + FRP):** [Ver guía de configuración](docs/CONFIGURAR_VPS_FRP.md) para ocultar 100% tu IP de casa usando un túnel privado hacia un VPS fuera de EE.UU.

---

## 🚀 Instalación en Ubuntu

1. **Clonar el repositorio:**
   ```bash
   git clone https://github.com/gastonkali/tvbox-linux.git
   cd tvbox-linux
   ```

2. **Ejecutar el instalador automático:**
   ```bash
   chmod +x instalar.sh
   ./instalar.sh
   ```
   *El instalador creará el entorno virtual de Python, instalará las dependencias y agregará el acceso directo "Mi TV Box" en tu menú de aplicaciones.*

---

## 🎮 Cómo usar

Puedes abrir la aplicación de dos formas:
1. **Desde el menú de Ubuntu:** Presiona la tecla `Super` (Windows), escribe **Mi TV Box** y pulsa Enter.
2. **Desde la terminal:**
   ```bash
   ./ejecutar.sh
   ```

### Controles:
- **Flechas `←` / `→` o `Tab`:** Moverse entre canales.
- **`Enter`:** Reproducir el canal seleccionado.
- **`Esc` / `Alt + F4`:** Cerrar el video y volver al catálogo.
- **Cerrar ventana (`X`):** Cierra la app y detiene el servidor en segundo plano.

---

## 📝 Configuración de Canales (`canales.json`)

Edita el archivo `canales.json` para añadir tus propios canales o películas:

```json
[
  {
    "id": 1,
    "titulo": "Canal 24h Noticias",
    "tipo": "directo",
    "url": "https://servidor.com/live/stream.m3u8",
    "categoria": "Noticias",
    "poster": "https://url-de-la-imagen.jpg"
  },
  {
    "id": 2,
    "titulo": "Fútbol en Vivo (Web)",
    "tipo": "web",
    "url": "https://sitio-streaming.com/partido",
    "categoria": "Deportes",
    "poster": "https://url-de-la-imagen.jpg"
  }
]
```

---

## ⚡ Automatización de Play en Sitios Web

Si quieres que las páginas de streaming inicien el video sin tener que hacer clic en el botón de reproducción:

1. Abre el perfil de la app en Brave:
   ```bash
   brave-browser --user-data-dir="$HOME/.config/tvbox-brave"
   ```
2. Instala la extensión **Violentmonkey** desde la Chrome Web Store.
3. Agrega el script ubicado en la carpeta `scripts/autoplay.user.js`.
4. ¡Listo! Brave recordará esta configuración para todas las reproducciones futuras de la TV Box.

---

## 📄 Licencia

MIT
