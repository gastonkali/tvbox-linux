#!/usr/bin/env bash
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EXT_DIR="$DIR/hydra-shield"

echo "=== Configurando Hydra TV Shield en Brave Browser (Ubuntu TV Box) ==="

# 1. Asegurar permisos correctos
chmod -R 755 "$EXT_DIR"

# 2. Configurar lanzador de escritorio para Brave Browser
mkdir -p "$HOME/.local/share/applications"
cat << EOF > "$HOME/.local/share/applications/brave-browser.desktop"
[Desktop Entry]
Version=1.0
Name=Brave Web Browser
Comment=Access the Internet with Hydra Shield
GenericName=Web Browser
Exec=/usr/bin/brave-browser-stable --load-extension=$EXT_DIR %U
StartupNotify=true
Terminal=false
Icon=brave-browser
Type=Application
Categories=Network;WebBrowser;
MimeType=application/pdf;application/rdf+xml;application/rss+xml;application/xhtml+xml;application/xhtml_xml;application/xml;image/gif;image/jpeg;image/png;image/webp;text/html;text/xml;x-scheme-handler/http;x-scheme-handler/https;
Actions=new-window;new-private-window;

[Desktop Action new-window]
Name=New Window
Exec=/usr/bin/brave-browser-stable --load-extension=$EXT_DIR

[Desktop Action new-private-window]
Name=New Incognito Window
Exec=/usr/bin/brave-browser-stable --incognito --load-extension=$EXT_DIR
EOF
chmod +x "$HOME/.local/share/applications/brave-browser.desktop"

# 3. Configurar script wrapper en ~/.local/bin/brave-browser
mkdir -p "$HOME/.local/bin"
cat << EOF > "$HOME/.local/bin/brave-browser"
#!/usr/bin/env bash
EXT_DIR="$EXT_DIR"
exec /usr/bin/brave-browser-stable --load-extension="\$EXT_DIR" "\$@"
EOF
chmod +x "$HOME/.local/bin/brave-browser"
cp -f "$HOME/.local/bin/brave-browser" "$HOME/.local/bin/brave-browser-stable"

# 4. Actualizar ejecutar.sh
if [ -f "$DIR/ejecutar.sh" ]; then
    chmod +x "$DIR/ejecutar.sh"
fi

# 5. Generar paquete .crx empaquetado para instalación opcional
/usr/bin/brave-browser-stable --pack-extension="$EXT_DIR" 2>/dev/null || true

echo "=== Hydra TV Shield configurado con éxito en todo el entorno de Brave ==="
