#!/usr/bin/env bash

set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

echo "============================================="
echo "   Instalador de Mi TV Box para Ubuntu/Linux "
echo "============================================="

# 1. Comprobar Python3 y venv
echo "[1/4] Verificando entorno de Python..."
if ! command -v python3 &> /dev/null; then
    echo "Instalando python3..."
    sudo apt update && sudo apt install -y python3 python3-pip python3-venv
fi

# Crear entorno virtual si no existe
if [ ! -d "$DIR/.venv" ]; then
    echo "Creando entorno virtual en $DIR/.venv..."
    python3 -m venv "$DIR/.venv"
fi

# Instalar dependencias
echo "Instalando dependencias de Python..."
"$DIR/.venv/bin/pip" install --upgrade pip
"$DIR/.venv/bin/pip" install -r "$DIR/requirements.txt"

# 2. Comprobar Brave Browser
echo "[2/4] Verificando Brave Browser..."
if ! command -v brave-browser &> /dev/null; then
    echo "Brave no parece estar instalado por APT."
    echo "¿Deseas instalar Brave automáticamente desde su repositorio oficial? (s/n)"
    read -r respuesta
    if [[ "$respuesta" =~ ^[sS]$ ]]; then
        sudo apt install -y curl
        sudo curl -fsSLo /usr/share/keyrings/brave-browser-archive-keyring.gpg https://brave-browser-apt-release.s3.brave.com/brave-browser-archive-keyring.gpg
        echo "deb [signed-by=/usr/share/keyrings/brave-browser-archive-keyring.gpg] https://brave-browser-apt-release.s3.brave.com/ stable main" | sudo tee /etc/apt/sources.list.d/brave-browser-release.list
        sudo apt update
        sudo apt install -y brave-browser
        echo "Brave instalado correctamente."
    else
        echo "Asegúrate de instalar Brave manualmente para que la app funcione."
    fi
else
    echo "Brave Browser detectado correctamente."
fi

# 3. Dar permisos al script ejecutable
echo "[3/4] Configurando permisos de ejecución..."
chmod +x "$DIR/ejecutar.sh"

# 4. Crear acceso directo en el sistema (.desktop)
echo "[4/4] Creando acceso directo en el menú de aplicaciones..."
APPLICATIONS_DIR="$HOME/.local/share/applications"
mkdir -p "$APPLICATIONS_DIR"

DESKTOP_FILE="$APPLICATIONS_DIR/tvbox.desktop"

cat <<EOF > "$DESKTOP_FILE"
[Desktop Entry]
Version=1.0
Type=Application
Name=Mi TV Box
Comment=Plataforma de streaming y canales para PC
Exec=$DIR/ejecutar.sh
Icon=video-television
Terminal=false
Categories=AudioVideo;Video;Player;
StartupNotify=true
EOF

chmod +x "$DESKTOP_FILE"

echo ""
echo "============================================="
echo "   ¡Instalación completada con éxito! 🎉     "
echo "============================================="
echo "Ya puedes buscar 'Mi TV Box' en tus aplicaciones"
echo "o ejecutar directamente: $DIR/ejecutar.sh"
echo "============================================="
