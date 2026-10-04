#!/usr/bin/env bash

# Obtener directorio del proyecto
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

# Activar entorno virtual si existe
if [ -d "$DIR/.venv" ]; then
    source "$DIR/.venv/bin/activate"
fi

# 1. Iniciar servidor Flask en segundo plano
python3 app.py > /dev/null 2>&1 &
SERVER_PID=$!

# 2. Iniciar túnel FRP hacia el VPS si está configurado
FRP_PID=""
if [ -f "$HOME/frp/frpc" ] && [ -f "$HOME/frp/frpc.toml" ]; then
    "$HOME/frp/frpc" -c "$HOME/frp/frpc.toml" > /dev/null 2>&1 &
    FRP_PID=$!
fi

# Esperar a que el servidor esté listo
sleep 1.2

# 2. Abrir la ventana de la aplicación con perfil aislado y Hydra Shield
brave-browser \
  --user-data-dir="$HOME/.config/tvbox-brave" \
  --load-extension="$DIR/hydra-shield" \
  --app="http://localhost:5000" \
  --autoplay-policy=no-user-gesture-required \
  --disable-session-crashed-bubble \
  --disable-features=Translate \
  --no-first-run

# 3. Al cerrar la ventana principal, terminar los procesos
if kill -0 $SERVER_PID 2>/dev/null; then
    kill $SERVER_PID
fi
if [ -n "$FRP_PID" ] && kill -0 $FRP_PID 2>/dev/null; then
    kill $FRP_PID
fi
