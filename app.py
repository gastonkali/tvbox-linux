import json
import os
import subprocess
import signal
from flask import Flask, render_template, jsonify, request

app = Flask(__name__)
brave_process = None

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CANALES_FILE = os.path.join(BASE_DIR, "canales.json")

def resolver_url(canal, proveedores):
    """
    Resuelve la URL final del canal.
    - Si tiene 'url' directa, la respeta (canales directos M3U8, YouTube, etc.).
    - Si tiene 'proveedor' y 'ruta', concatena el dominio base dinámico con la ruta.
    """
    if canal.get("url"):
        return canal["url"]

    proveedor_key = canal.get("proveedor")
    ruta = canal.get("ruta", "")
    base_url = proveedores.get(proveedor_key, "")

    if not base_url:
        return ruta

    return base_url.rstrip("/") + "/" + ruta.lstrip("/")

def cargar_catalogo():
    """
    Carga el catálogo soportando:
    1. Nuevo formato dinámico: { "proveedores": {...}, "canales": [...] }
    2. Formato clásico: [ {...}, {...} ]
    """
    if not os.path.exists(CANALES_FILE):
        return {}, []

    with open(CANALES_FILE, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            return {}, []

    if isinstance(data, dict):
        proveedores = data.get("proveedores", {})
        canales = data.get("canales", [])
    elif isinstance(data, list):
        proveedores = {}
        canales = data
    else:
        proveedores, canales = {}, []

    # Asignar la URL final resuelta a cada canal
    for c in canales:
        c["url_resuelta"] = resolver_url(c, proveedores)

    return proveedores, canales

@app.route("/")
def home():
    proveedores, canales = cargar_catalogo()
    return render_template("index.html", canales=canales, proveedores=proveedores)

@app.route("/reproductor")
def reproductor():
    stream_url = request.args.get("url", "")
    titulo = request.args.get("titulo", "Reproductor")
    return render_template("player.html", stream_url=stream_url, titulo=titulo)

@app.route("/play/<int:canal_id>", methods=["POST"])
def play(canal_id):
    global brave_process
    proveedores, canales = cargar_catalogo()
    canal = next((c for c in canales if c.get("id") == canal_id), None)

    if not canal:
        return jsonify({"error": "Canal no encontrado"}), 404

    target_url = canal.get("url_resuelta") or canal.get("url", "")

    # Determinar si abrir en el reproductor interno o en la web
    if canal.get("tipo") == "directo":
        final_launch_url = f"http://localhost:5000/reproductor?url={target_url}&titulo={canal['titulo']}"
    else:
        final_launch_url = target_url

    # Cerrar video en reproducción si ya existe uno abierto
    if brave_process and brave_process.poll() is None:
        try:
            brave_process.terminate()
        except Exception:
            pass

    # Perfil aislado para no mezclar con sesiones personales de Brave
    user_data_dir = os.path.expanduser("~/.config/tvbox-brave")

    cmd = [
        "brave-browser",
        f"--user-data-dir={user_data_dir}",
        "--kiosk",
        f"--app={final_launch_url}",
        "--autoplay-policy=no-user-gesture-required",
        "--no-first-run",
        "--disable-session-crashed-bubble"
    ]

    try:
        brave_process = subprocess.Popen(cmd)
        return jsonify({
            "status": "ok", 
            "tipo": canal.get("tipo"), 
            "proveedor": canal.get("proveedor"),
            "url": final_launch_url
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/stop", methods=["POST"])
def stop():
    global brave_process
    if brave_process and brave_process.poll() is None:
        try:
            brave_process.terminate()
            brave_process = None
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    return jsonify({"status": "detenido"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
