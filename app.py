import json
import os
import subprocess
from flask import Flask, render_template, jsonify, request

app = Flask(__name__)
brave_process = None

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CANALES_FILE = os.path.join(BASE_DIR, "canales.json")
CATALOGO_MAESTRO_FILE = os.path.join(BASE_DIR, "catalogo_maestro.json")

# Memoria caché global para búsquedas instantáneas
CATALOGO_CACHE = []
ITEMS_BY_ID = {}
CATEGORIAS_CACHE = []
PROVEEDORES_CACHE = {}

def resolver_url(canal, proveedores):
    """Resuelve la URL final según si tiene ruta+proveedor o URL fija."""
    if canal.get("url"):
        return canal["url"]

    proveedor_key = canal.get("proveedor")
    ruta = canal.get("ruta", "")
    base_url = proveedores.get(proveedor_key, "")

    if not base_url:
        return ruta

    return base_url.rstrip("/") + "/" + ruta.lstrip("/")

def inicializar_catalogo():
    """Carga canales.json y catalogo_maestro.json en memoria para búsquedas instantáneas."""
    global CATALOGO_CACHE, ITEMS_BY_ID, CATEGORIAS_CACHE, PROVEEDORES_CACHE
    items_combinados = []
    ids_registrados = set()
    proveedores = {}

    # 1. Cargar canales.json si existe (canales personalizados / TV en vivo)
    if os.path.exists(CANALES_FILE):
        try:
            with open(CANALES_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    proveedores = data.get("proveedores", {})
                    canales_custom = data.get("canales", [])
                elif isinstance(data, list):
                    canales_custom = data
                else:
                    canales_custom = []

                for c in canales_custom:
                    c_id = c.get("id")
                    if c_id is not None and c_id not in ids_registrados:
                        c["url_resuelta"] = resolver_url(c, proveedores)
                        c["titulo_lower"] = c.get("titulo", "").lower()
                        items_combinados.append(c)
                        ids_registrados.add(c_id)
        except Exception as e:
            print(f"[Aviso] Error leyendo canales.json: {e}")

    # 2. Cargar catalogo_maestro.json (Base de datos de 38k+ títulos)
    if os.path.exists(CATALOGO_MAESTRO_FILE):
        try:
            with open(CATALOGO_MAESTRO_FILE, "r", encoding="utf-8") as f:
                maestro = json.load(f)
                if isinstance(maestro, list):
                    for m in maestro:
                        m_id = m.get("id")
                        if m_id is not None and m_id not in ids_registrados:
                            m["url_resuelta"] = m.get("url", "")
                            m["titulo_lower"] = m.get("titulo", "").lower()
                            items_combinados.append(m)
                            ids_registrados.add(m_id)
        except Exception as e:
            print(f"[Aviso] Error leyendo catalogo_maestro.json: {e}")

    CATALOGO_CACHE = items_combinados
    ITEMS_BY_ID = {item["id"]: item for item in items_combinados}
    PROVEEDORES_CACHE = proveedores

    # Extraer categorías únicas limpias
    categorias_set = set()
    for item in items_combinados:
        cat = item.get("categoria")
        if cat and isinstance(cat, str) and cat.strip():
            categorias_set.add(cat.strip())

    # Ordenar categorías con 'Todos' primero
    lista_cat = sorted(list(categorias_set))
    CATEGORIAS_CACHE = ["Todos"] + lista_cat

    print(f"[OK] Catalogo inicializado con {len(CATALOGO_CACHE)} titulos y {len(CATEGORIAS_CACHE)} categorias.")

# Cargar en memoria al iniciar la app
inicializar_catalogo()

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/api/categorias")
def api_categorias():
    return jsonify(CATEGORIAS_CACHE)

@app.route("/api/canales")
def api_canales():
    """Búsqueda y paginación ultra rápida en memoria (en menos de 10ms)."""
    query = request.args.get("q", "").strip().lower()
    categoria = request.args.get("categoria", "").strip()
    page = max(1, int(request.args.get("page", 1)))
    limit = min(100, max(1, int(request.args.get("limit", 60))))

    filtrados = CATALOGO_CACHE

    if query:
        # Búsqueda por subcadena en título
        filtrados = [x for x in filtrados if query in x["titulo_lower"]]

    if categoria and categoria != "Todos":
        filtrados = [x for x in filtrados if x.get("categoria", "").strip().lower() == categoria.lower()]

    total = len(filtrados)
    total_pages = (total + limit - 1) // limit if total > 0 else 1
    start = (page - 1) * limit
    end = start + limit

    items_pagina = filtrados[start:end]

    # Limpiar campos internos antes de enviar al frontend
    resultado = []
    for item in items_pagina:
        resultado.append({
            "id": item.get("id"),
            "titulo": item.get("titulo"),
            "tipo": item.get("tipo", "web"),
            "categoria": item.get("categoria", ""),
            "poster": item.get("poster", ""),
            "url": item.get("url_resuelta", item.get("url", "")),
            "opciones": item.get("opciones", [])
        })

    return jsonify({
        "total": total,
        "page": page,
        "limit": limit,
        "total_pages": total_pages,
        "items": resultado
    })

@app.route("/reproductor")
def reproductor():
    stream_url = request.args.get("url", "")
    titulo = request.args.get("titulo", "Reproductor")
    return render_template("player.html", stream_url=stream_url, titulo=titulo)

@app.route("/play/<int:canal_id>", methods=["POST"])
def play(canal_id):
    global brave_process
    canal = ITEMS_BY_ID.get(canal_id)

    if not canal:
        return jsonify({"error": "Canal o película no encontrado"}), 404

    # Permitir al cliente especificar qué opción o servidor desea reproducir
    datos = request.get_json(silent=True) or {}
    opcion_url = datos.get("opcion_url")

    target_url = opcion_url or canal.get("url_resuelta") or canal.get("url", "")

    if not target_url:
        return jsonify({"error": "El título no tiene URL válida"}), 400

    # Si es directo (.m3u8 / .mp4), usamos el reproductor interno
    if canal.get("tipo") == "directo":
        final_launch_url = f"http://localhost:5000/reproductor?url={target_url}&titulo={canal.get('titulo', '')}"
    else:
        final_launch_url = target_url

    # Cerrar video en reproducción anterior
    if brave_process and brave_process.poll() is None:
        try:
            brave_process.terminate()
        except Exception:
            pass

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
            "titulo": canal.get("titulo"),
            "tipo": canal.get("tipo"),
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
