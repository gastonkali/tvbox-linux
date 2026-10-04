#!/usr/bin/env bash
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EXT_DIR="$DIR/hydra-shield"

echo "=== Configurando Hydra TV Shield en Brave Browser (Ubuntu TV Box) ==="

# 1. Asegurar permisos correctos
chmod -R 755 "$EXT_DIR"

# 2. Configurar lanzadores de escritorio para Brave Browser (tanto standard como Wayland/GNOME)
mkdir -p "$HOME/.local/share/applications"
for DESKTOP_NAME in "brave-browser.desktop" "com.brave.Browser.desktop"; do
cat << EOF > "$HOME/.local/share/applications/$DESKTOP_NAME"
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
chmod +x "$HOME/.local/share/applications/$DESKTOP_NAME"
done

# 3. Configurar scripts wrappers en ~/.local/bin/
mkdir -p "$HOME/.local/bin"
cat << EOF > "$HOME/.local/bin/brave-browser"
#!/usr/bin/env bash
EXT_DIR="$EXT_DIR"
exec /usr/bin/brave-browser-stable --load-extension="\$EXT_DIR" "\$@"
EOF
chmod +x "$HOME/.local/bin/brave-browser"
cp -f "$HOME/.local/bin/brave-browser" "$HOME/.local/bin/brave-browser-stable"
cp -f "$HOME/.local/bin/brave-browser" "$HOME/.local/bin/brave"

# Asegurar ~/.local/bin en PATH
if ! grep -q '\.local/bin' "$HOME/.bashrc" 2>/dev/null; then
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.bashrc"
fi
if ! grep -q '\.local/bin' "$HOME/.profile" 2>/dev/null; then
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.profile"
fi

# 4. Asegurar bloqueo nativo estricto de popups en perfiles de Brave
python3 -c "
import json, os
for p in ['$HOME/.config/tvbox-brave', '$HOME/.config/BraveSoftware/Brave-Browser']:
    d = os.path.expanduser(p)
    def_dir = os.path.join(d, 'Default')
    os.makedirs(def_dir, exist_ok=True)
    pref_file = os.path.join(def_dir, 'Preferences')
    data = {}
    if os.path.exists(pref_file):
        try:
            with open(pref_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception:
            data = {}
    profile = data.setdefault('profile', {})
    cds = profile.setdefault('default_content_setting_values', {})
    cds['popups'] = 2
    cds['notifications'] = 2
    cds['automatic_downloads'] = 2
    try:
        with open(pref_file, 'w', encoding='utf-8') as f:
            json.dump(data, f)
    except Exception as e:
        pass
" 2>/dev/null || true

# 5. Actualizar permisos de ejecutar.sh
if [ -f "$DIR/ejecutar.sh" ]; then
    chmod +x "$DIR/ejecutar.sh"
fi

echo "=== Hydra TV Shield configurado con éxito en todo el entorno de Brave ==="
