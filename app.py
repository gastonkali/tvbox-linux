import json
import os
import subprocess
import signal
from flask import Flask, render_template, jsonify, request

app = Flask(__name__)
brave_process = None

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CANALES_FILE = os.path.join(BASE_DIR, "canales.json")

def cargar_catalogo():
    if not os.path.exists(CANALES_FILE):
        return []
    with open(CANALES_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

@app.route("/")
def home():
    canales = cargar_catalogo()
    return render_template("index.html", canales=canales)

@app.route("/reproductor")
def reproductor():
    stream_url = request.args.get("url", "")
    titulo = request.args.get("titulo", "Reproductor")
    return render_template("player.html", stream_url=stream_url, titulo=titulo)

@app.route("/play/<int:canal_id>", methods=["POST"])
def play(canal_id):
    global brave_process
    canales = cargar_catalogo()
    canal = next((c for c in canales if c.get("id") == canal_id), None)

    if not canal:
        return jsonify({"error": "Canal no encontrado"}), 404

    # Determinar qué URL abrir
    if canal.get("tipo") == "directo":
        target_url = f"http://localhost:5000/reproductor?url={canal['url']}&titulo={canal['titulo']}"
    else:
        target_url = canal["url"]

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
        f"--app={target_url}",
        "--autoplay-policy=no-user-gesture-required",
        "--no-first-run",
        "--disable-session-crashed-bubble"
    ]

    try:
        brave_process = subprocess.Popen(cmd)
        return jsonify({"status": "ok", "tipo": canal.get("tipo"), "url": target_url})
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
