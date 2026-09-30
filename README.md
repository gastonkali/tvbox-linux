# 📺 Mi TV Box (Linux Edition)

Plataforma ligera para transformar tu PC con **Ubuntu / Linux** en una experiencia de **Smart TV / TV Box**, manteniendo el uso normal de tu ordenador como una aplicación independiente de escritorio.

Diseñada para reproducir tanto enlaces directos de video (`.m3u8`, `.mp4`) como páginas de streaming complejas, aprovechando el bloqueo agresivo de publicidad de **Brave Browser**.

---

## ✨ Características

- 🎯 **Aplicación independiente:** Funciona como un programa normal en tu menú de aplicaciones de Ubuntu. Al cerrarse la ventana, apaga todos sus procesos en segundo plano.
- 🛡️ **Perfil aislado de Brave:** Corre con su propio perfil (`~/.config/tvbox-brave`), evitando interferir con tus pestañas, historial o extensiones personales.
- 🚫 **Sin publicidad en videos:** Bloqueo de redirecciones y anuncios agresivos.
- ⚡ **Soporte de múltiples fuentes:**
  - `directo`: Streams HLS (`.m3u8`) o archivos `.mp4` reproducidos al instante en un reproductor interno ultraligero.
  - `web`: Páginas de streaming abiertas en modo Kiosk.
- 🔍 **Buscador en tiempo real:** Encuentra cualquier canal o video al instante (atajo `/`).
- 🎮 **Navegación 10-foot UI:** Navegable mediante teclado (flechas `←` `→` y `Enter`) o control remoto inalámbrico.
- 🤖 **Auto-Play:** Script para hacer clic automático en botones de reproducción rebeldes.
- 🛡️ **Acceso Remoto Seguro (Último Paso):** Posibilidad de conectar a un VPS offshore mediante FRP para acceder desde fuera de casa con tu IP 100% oculta.

---

## 🗺️ Hoja de Ruta de Puesta en Marcha

Para garantizar que todo funcione sin problemas, el proyecto se divide en **2 Fases bien diferenciadas**:

```text
┌────────────────────────────────────────────────────────┐
│  FASE 1: VERIFICACIÓN LOCAL (Comenzar Aquí)            │
│  - Instalar dependencias en Ubuntu                     │
│  - Probar que la app abra desde el menú                │
│  - Probar reproducción de canales locales y webs      │
│  - Verificar que Brave bloquee anuncios correctamente  │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼ ¡Todo funciona perfecto en tu PC!
┌────────────────────────────────────────────────────────┐
│  FASE 2: CONEXIÓN REMOTA SEGURA (El Último Paso)       │
│  - Contratar un VPS barato (Rusia / Moldavia)          │
│  - Configurar el túnel privado con FRP                 │
│  - Conectar tu teléfono/tablet desde fuera de casa     │
└────────────────────────────────────────────────────────┘
```

---

## 🟢 FASE 1: Puesta en Marcha y Verificación Local

> 💡 **Objetivo:** Asegurarse de que el catálogo, los videos y la app funcionen al 100% en tu propia computadora antes de pensar en conexiones externas.

### 1. Clonar el repositorio
Abre una terminal en tu Ubuntu y ejecuta:
```bash
git clone https://github.com/gastonkali/tvbox-linux.git
cd tvbox-linux
```

### 2. Ejecutar el instalador automático
```bash
chmod +x instalar.sh
./instalar.sh
```
*El script creará el entorno virtual de Python, instalará las dependencias y creará el acceso directo "Mi TV Box" en tu menú de aplicaciones.*

### 3. Probar la aplicación
Puedes abrirla de dos formas:
* **Desde el menú de Ubuntu:** Presiona la tecla `Super` (Windows), escribe **Mi TV Box** y pulsa Enter.
* **Desde la terminal:**
  ```bash
  ./ejecutar.sh
  ```

### 4. Controles básicos en la interfaz:
* **`Tab` o Flechas `←` / `→`:** Moverte entre las tarjetas de canales.
* **`/` (Barra inclinada):** Saltar al buscador en tiempo real para escribir el nombre de un video.
* **`Enter`:** Reproducir el canal seleccionado.
* **`Esc` o `Alt + F4`:** Cerrar el video y volver de inmediato al catálogo.
* **Cerrar ventana (`X`):** Cierra la app y apaga el servidor en segundo plano.

### 5. Personalizar tus propios videos (`canales.json`)
Edita el archivo `canales.json` para agregar tus enlaces y páginas favoritas:

```json
[
  {
    "id": 1,
    "titulo": "Noticias 24h",
    "tipo": "directo",
    "url": "https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8",
    "categoria": "Noticias",
    "poster": "https://images.unsplash.com/photo-1585829365295-ab7cd400c167?w=600"
  },
  {
    "id": 2,
    "titulo": "Deportes en Vivo Web",
    "tipo": "web",
    "url": "https://sitio-streaming.com/partido",
    "categoria": "Deportes",
    "poster": "https://images.unsplash.com/photo-1508098682722-e99c43a406b2?w=600"
  }
]
```

### 6. Automatización de Play en Sitios Web (Opcional)
Si quieres que las páginas web hagan clic automático en el botón de reproducción:
1. Abre el perfil de la app en Brave:
   ```bash
   brave-browser --user-data-dir="$HOME/.config/tvbox-brave"
   ```
2. Instala la extensión **Violentmonkey** desde la Chrome Web Store.
3. Agrega el script ubicado en `scripts/autoplay.user.js`.

---

## 🔒 FASE 2: Conexión Remota Segura con VPS + FRP (El Último Paso)

Una vez que hayas verificado que toda la app funciona a la perfección en tu Ubuntu localmente, es momento de habilitar el acceso desde tu teléfono o tablet fuera de casa **sin exponer jamás tu IP real ni tu red doméstica**.

👉 **Sigue el instructivo paso a paso detallado en:**  
[📘 docs/CONFIGURAR_VPS_FRP.md](docs/CONFIGURAR_VPS_FRP.md)

En esa guía aprenderás:
1. Dónde contratar un VPS barato (~€3/mes en Moldavia o Rusia).
2. Cómo configurar el servidor `frps` en el VPS.
3. Cómo conectar tu PC con `frpc`.
4. Cómo acceder desde tu móvil con `http://IP_DEL_VPS:8080` de forma 100% blindada.

---

## 📄 Licencia

MIT
