# 🛡️ Guía de Configuración: VPS Offshore + FRP (Túnel Privado Seguro)

Esta guía explica cómo conectar tu servidor **TV Box (Ubuntu en casa)** a un **VPS Offshore en el extranjero (por ejemplo, Rusia o Moldavia)** mediante **FRP** (*Fast Reverse Proxy*).

Con esta configuración:
* **Tu IP real de casa queda 100% oculta:** Los usuarios, curiosos o escaneos solo ven la IP pública del VPS en el extranjero.
* **0 Puertos abiertos en tu router:** Tu PC crea un túnel saliente cifrado hacia el VPS.
* **Fuera de la jurisdicción de EE.UU.:** Control total sin intermediarios corporativos ni registros.

---

## 🗺️ Diagrama de Conexión

```text
📱 Dispositivo (Móvil / 4G / Fuera de casa)
   │
   ▼  Acceso público: http://<IP_DE_TU_VPS>:8080
┌──────────────────────────────────────────────┐
│  🇷🇺 VPS OFFSHORE (Rusia / Moldavia)          │
│  - Servicio frps (FRP Server) en puerto 7000 │
│  - Expone el puerto público 8080             │
└──────────────────────┬───────────────────────┘
                       │  🔒 Túnel cifrado con Token privado
                       ▼
┌──────────────────────────────────────────────┐
│  🏠 TU CASA (Ubuntu)                         │
│  - Servicio frpc (FRP Client)                │
│  - App TV Box corriendo en 127.0.0.1:5000    │
│  - Tu IP real NUNCA se expone                │
└──────────────────────────────────────────────┘
```

---

## 📌 PARTE 1: Configurar el VPS (Servidor en el Extranjero)

Una vez contratado tu VPS (por ejemplo en AlexHost, VDSina, etc.) y conectado por SSH con usuario `root`:

### 1. Descargar e instalar FRP Server
Ejecuta en la terminal de tu VPS:

```bash
mkdir -p ~/frp && cd ~/frp

# Descargar la versión más reciente de FRP (Linux 64-bit)
curl -s https://api.github.com/repos/fatedier/frp/releases/latest \
  | grep "browser_download_url.*linux_amd64.tar.gz" \
  | cut -d : -f 2,3 \
  | tr -d \" \
  | wget -qi -

tar -zxvf frp_*_linux_amd64.tar.gz --strip-components=1
```

### 2. Configurar `frps.toml`
Crea o edita el archivo de configuración:

```bash
nano ~/frp/frps.toml
```

Pega el siguiente contenido:

```toml
# Puerto donde frps escucha las conexiones privadas desde tu casa
bindPort = 7000

# Token de autenticación (Crea una contraseña larga y aleatoria)
auth.method = "token"
auth.token = "CAMBIA_ESTO_POR_TU_TOKEN_SECRETO_SEGURO_123"

# Puerto público por el que accederás desde tu teléfono o navegador
vhostHttpPort = 8080
```

### 3. Crear servicio systemd para que arranque siempre
```bash
sudo tee /etc/systemd/system/frps.service > /dev/null <<EOF
[Unit]
Description=FRP Server Service (Offshore)
After=network.target

[Service]
Type=simple
User=root
ExecStart=/root/frp/frps -c /root/frp/frps.toml
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=multi-user.target
EOF
```

Inicia y activa el servicio:
```bash
sudo systemctl daemon-reload
sudo systemctl enable --now frps
sudo systemctl status frps
```

*(Si tienes firewall activado en el VPS, permite los puertos 7000 y 8080: `sudo ufw allow 7000 && sudo ufw allow 8080`)*

---

## 📌 PARTE 2: Configurar tu PC de Casa (Ubuntu)

En tu computadora local donde corre la TV Box:

### 1. Descargar FRP Client
Abre una terminal en Ubuntu:

```bash
mkdir -p ~/frp && cd ~/frp

curl -s https://api.github.com/repos/fatedier/frp/releases/latest \
  | grep "browser_download_url.*linux_amd64.tar.gz" \
  | cut -d : -f 2,3 \
  | tr -d \" \
  | wget -qi -

tar -zxvf frp_*_linux_amd64.tar.gz --strip-components=1
```

### 2. Configurar `frpc.toml`
Edita la configuración del cliente:

```bash
nano ~/frp/frpc.toml
```

Pega el siguiente contenido (reemplaza con la IP real de tu VPS y tu token secreto):

```toml
# Dirección IP pública de tu VPS en Rusia y puerto de enlace
serverAddr = "IP_DE_TU_VPS_AQUI"
serverPort = 7000

# El mismo token que pusiste en el VPS
auth.method = "token"
auth.token = "CAMBIA_ESTO_POR_TU_TOKEN_SECRETO_SEGURO_123"

# Configuración del túnel hacia tu app TV Box
[[proxies]]
name = "tvbox"
type = "tcp"
localIP = "127.0.0.1"
localPort = 5000       # El puerto de app.py
remotePort = 8080      # El puerto en el VPS al que te conectarás
```

### 3. Probar la conexión
```bash
cd ~/frp
./frpc -c frpc.toml
```
Si todo es correcto, verás:
`[tvbox] start proxy success`

*(Presiona `Ctrl + C` para detener la prueba).*

---

## 📌 PARTE 3: Automatizar el arranque en `ejecutar.sh`

Para que el túnel se conecte automáticamente cada vez que abres tu app en Ubuntu y se cierre al salir, tu archivo `ejecutar.sh` en `tvbox-linux/` puede llamar a `frpc` en segundo plano:

```bash
#!/usr/bin/env bash

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

if [ -d "$DIR/.venv" ]; then
    source "$DIR/.venv/bin/activate"
fi

# 1. Iniciar el servidor Flask
python3 app.py > /dev/null 2>&1 &
SERVER_PID=$!

# 2. Iniciar el túnel FRP hacia el VPS si está configurado
if [ -f "$HOME/frp/frpc" ] && [ -f "$HOME/frp/frpc.toml" ]; then
    $HOME/frp/frpc -c $HOME/frp/frpc.toml > /dev/null 2>&1 &
    FRP_PID=$!
fi

sleep 1.2

# 3. Abrir la ventana de la app en Ubuntu
brave-browser \
  --user-data-dir="$HOME/.config/tvbox-brave" \
  --app="http://localhost:5000" \
  --autoplay-policy=no-user-gesture-required \
  --disable-session-crashed-bubble \
  --no-first-run

# 4. Limpieza al cerrar la app
kill $SERVER_PID 2>/dev/null
if [ -n "$FRP_PID" ]; then
    kill $FRP_PID 2>/dev/null
fi
```

---

## 🌐 ¿Cuál es la URL para acceder desde cualquier dispositivo?

La dirección que usarás en tu teléfono, tablet o laptop desde cualquier parte del mundo (incluso con datos móviles 4G/5G) es:

```text
http://<IP_DE_TU_VPS>:8080
```

*Donde `<IP_DE_TU_VPS>` es la dirección IP pública que te asigna tu proveedor de hosting (por ejemplo: `http://185.220.101.45:8080`).*

Nadie en internet podrá ver tu dirección real de casa ni tu proveedor de internet doméstico.
