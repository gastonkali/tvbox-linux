# 🛡️ Guía de Configuración: VPS Offshore + FRP (Túnel Privado Seguro)

> ⚠️ **IMPORTANTE: ESTE ES EL ÚLTIMO PASO (FASE 2)**  
> **Antes de realizar esta configuración, asegúrate de haber probado y verificado la aplicación en modo local en tu PC con Ubuntu (Fase 1 del README).**  
> Primero comprueba que el catálogo cargue, que tus videos se reproduzcan sin publicidad y que el buscador funcione en tu computadora. Cuando todo esté 100% listo y probado, realiza este paso para habilitar el acceso remoto seguro desde otros dispositivos fuera de casa.

---

## 🎯 ¿Para qué sirve este paso final?

Por defecto, tu TV Box funciona en tu PC y en tu red Wi-Fi de casa. Si quieres acceder desde tu teléfono móvil con 4G en la calle o desde otra casa sin exponer jamás tu dirección IP real ni tu hogar, conectamos tu Ubuntu a un **servidor VPS Offshore** (por ejemplo, en Moldavia o Rusia).

* **Tu IP real de casa queda 100% oculta:** Curiosos, escáneres o proveedores solo ven la IP pública del VPS en el extranjero.
* **0 Puertos abiertos en tu router:** Tu PC crea un túnel saliente cifrado hacia el VPS con **FRP** (*Fast Reverse Proxy*).
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

## 📌 PARTE 0: Dónde y cómo contratar el VPS

No necesitas un servidor costoso. Como el VPS solo hace de "puente" o túnel, el plan más económico es más que suficiente.

### Proveedores recomendados:
1. **[AlexHost](https://alexhost.com/):**
   * **Ubicación:** Moldavia (centro de datos en un antiguo búnker militar).
   * **Fama:** Muy conocido por ignorar reclamos de EE.UU. (*DMCA Ignore*) y por alta privacidad.
   * **Precio:** Desde ~€3.50 al mes.
   * **Pago:** Tarjetas internacionales, PayPal, o Criptomonedas (Bitcoin/Monero).
2. **[PQ.Hosting](https://pq.hosting/es/):**
   * **Ubicación:** Servidores físicos en **Rusia (Moscú)** o **Moldavia**.
   * **Precio:** Desde ~€4 al mes.
   * **Soporte:** En español.

### Especificaciones a elegir durante la compra:
* **Plan:** El más básico (1 vCPU, 1 GB de RAM, 10-20 GB SSD).
* **Sistema Operativo:** Selecciona **Ubuntu 22.04 LTS** o **Ubuntu 24.04 LTS**.
* **Ubicación:** Rusia o Moldavia.

### Conectarte a tu VPS por primera vez:
Una vez pagado, recibirás por correo la **IP del servidor** y la **contraseña de root**. Conéctate desde la terminal de tu PC con:
```bash
ssh root@IP_DE_TU_VPS
```

---

## 📌 PARTE 1: Configurar el VPS (Servidor en el Extranjero)

Conectado por SSH a tu VPS como `root`:

### 1. Descargar e instalar FRP Server
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
Crea o edita el archivo:
```bash
nano ~/frp/frps.toml
```

Pega el siguiente contenido (puedes usar de referencia el archivo `config/frps.example.toml`):
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

*(Si usas firewall en el VPS, permite los puertos 7000 y 8080: `sudo ufw allow 7000 && sudo ufw allow 8080`)*

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

Pega lo siguiente (reemplaza con la IP real de tu VPS y tu token secreto):
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

### 3. Probar la conexión manual
```bash
cd ~/frp
./frpc -c frpc.toml
```
Si todo es correcto, verás:
`[tvbox] start proxy success`

*(Presiona `Ctrl + C` para detener la prueba).*

---

## 📌 PARTE 3: Automatización integrada con la App

El archivo `ejecutar.sh` del proyecto ya viene configurado para detectar automáticamente si existe `~/frp/frpc`. 

Si el archivo existe, **el túnel se conectará automáticamente al abrir la app** y se desconectará al cerrarla, sin que tengas que ejecutar ningún comando adicional.

---

## 🌐 ¿Cuál es la URL final para conectarte desde otros dispositivos?

Desde tu teléfono (con datos móviles 4G/5G), tablet o laptop en cualquier parte del mundo, abre el navegador y escribe:

$$\text{http://} \mathbf{\langle IP\_DE\_TU\_VPS \rangle} \mathbf{:8080}$$

*(Por ejemplo: `http://185.174.136.25:8080`)*

Nadie en internet podrá ver tu dirección real de casa, tu proveedor de internet doméstico ni tu red local.
