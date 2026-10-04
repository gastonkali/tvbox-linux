import json
import os
import subprocess
import unicodedata
import re
from collections import defaultdict
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

# Estructuras para búsqueda difusa (Fuzzy Search) ultrarrápida
VOCAB_INDEX = defaultdict(set)      # palabra -> set(indices en CATALOGO_CACHE)
WORDS_BY_LEN = defaultdict(list)    # longitud -> lista de palabras únicas
WORDS_BY_PREFIX = defaultdict(list) # prefijo de 2 letras -> lista de palabras únicas

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

def normalizar_texto(texto):
    """Elimina tildes, diacríticos, caracteres especiales y convierte a minúsculas."""
    if not texto:
        return ""
    texto = texto.replace("\n", " ").replace("\r", " ")
    texto = unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode('utf-8').lower()
    return re.sub(r'[^a-z0-9\s]', ' ', texto)

def limpiar_titulo_para_mostrar(titulo):
    """Limpia números de calificación o etiquetas residuales de scraping al inicio de títulos."""
    if not titulo:
        return ""
    lines = [l.strip() for l in titulo.splitlines() if l.strip()]
    if not lines:
        return titulo.strip()
    while len(lines) > 1 and (lines[0].isdigit() or lines[0].lower() in ['serie', 'pelicula', 'estreno', 'completa'] or re.match(r'^\d+(\.\d+)?$', lines[0])):
        lines.pop(0)
    res = " ".join(lines)
    # Arreglar símbolos de episodios como 1×6 o 16 -> 1x6
    res = re.sub(r'(\d+)[\ufffd\xd7](\d+)', r'\1x\2', res)
    return res

def damerau_levenshtein_1(s1, s2):
    """Comprueba si la distancia de edición Damerau-Levenshtein es <= 1 (inserción, eliminación, sustitución o transposición)."""
    len1, len2 = len(s1), len(s2)
    if len1 == len2:
        diffs = [i for i in range(len1) if s1[i] != s2[i]]
        if len(diffs) == 1:
            return True
        if len(diffs) == 2 and diffs[0] + 1 == diffs[1]:
            if s1[diffs[0]] == s2[diffs[1]] and s1[diffs[1]] == s2[diffs[0]]:
                return True
        return False
    elif len1 + 1 == len2:
        for i in range(len2):
            if s2[:i] + s2[i+1:] == s1:
                return True
        return False
    elif len1 == len2 + 1:
        for i in range(len1):
            if s1[:i] + s1[i+1:] == s2:
                return True
        return False
    return False

def inicializar_catalogo():
    """Carga canales.json y catalogo_maestro.json en memoria y construye el índice de búsqueda fuzzy."""
    global CATALOGO_CACHE, ITEMS_BY_ID, CATEGORIAS_CACHE, PROVEEDORES_CACHE
    global VOCAB_INDEX, WORDS_BY_LEN, WORDS_BY_PREFIX

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
                            if not m.get("poster") or not str(m.get("poster")).strip() or "ultrapeli.com" in m.get("poster", ""):
                                continue
                            m["url_resuelta"] = m.get("url", "")
                            items_combinados.append(m)
                            ids_registrados.add(m_id)
        except Exception as e:
            print(f"[Aviso] Error leyendo catalogo_maestro.json: {e}")

    # 3. Construir estructuras de indexación para búsqueda fuzzy ultraveloz
    vocab = defaultdict(set)
    words_by_len = defaultdict(list)
    words_by_prefix = defaultdict(list)

    for idx, item in enumerate(items_combinados):
        raw_title = item.get("titulo", "")
        titulo_limpio = limpiar_titulo_para_mostrar(raw_title)
        clean_title = " ".join(normalizar_texto(titulo_limpio).split())
        clean_nospace = clean_title.replace(" ", "")

        item["titulo_limpio"] = titulo_limpio
        item["clean_title"] = clean_title
        item["clean_nospace"] = clean_nospace
        tokens = clean_title.split()
        item["tokens"] = tokens

        for tok in tokens:
            vocab[tok].add(idx)

    for w in vocab.keys():
        words_by_len[len(w)].append(w)
        if len(w) >= 2:
            words_by_prefix[w[:2]].append(w)

    CATALOGO_CACHE = items_combinados
    ITEMS_BY_ID = {item["id"]: item for item in items_combinados}
    PROVEEDORES_CACHE = proveedores
    VOCAB_INDEX = vocab
    WORDS_BY_LEN = words_by_len
    WORDS_BY_PREFIX = words_by_prefix

    # Extraer categorías únicas limpias
    categorias_set = set()
    for item in items_combinados:
        cat = item.get("categoria")
        if cat and isinstance(cat, str) and cat.strip():
            categorias_set.add(cat.strip())

    lista_cat = sorted(list(categorias_set))
    CATEGORIAS_CACHE = ["Todos"] + lista_cat

    print(f"[OK] Catálogo cargado: {len(CATALOGO_CACHE)} títulos, {len(vocab)} palabras indexadas, {len(CATEGORIAS_CACHE)} categorías.")

# Cargar catálogo en memoria al arrancar
inicializar_catalogo()

def obtener_candidatos_palabra(palabra_query):
    """Encuentra palabras del catálogo exactas, por prefijo o con 1 error tipográfico (typo)."""
    candidatos = {}
    if palabra_query in VOCAB_INDEX:
        candidatos[palabra_query] = 1.0  # Coincidencia exacta

    q_len = len(palabra_query)
    # Búsqueda por prefijo (ej. residen -> resident)
    if q_len >= 3 and palabra_query[:2] in WORDS_BY_PREFIX:
        for w in WORDS_BY_PREFIX[palabra_query[:2]]:
            if w.startswith(palabra_query) and w not in candidatos:
                candidatos[w] = 0.85

    # Búsqueda difusa por distancia de edición (tolerancia a 1 letra cambiada/faltante/sobrante)
    if q_len >= 3:
        for l in range(max(2, q_len - 1), q_len + 2):
            for w in WORDS_BY_LEN[l]:
                if w in candidatos:
                    continue
                if damerau_levenshtein_1(palabra_query, w):
                    candidatos[w] = 0.70

    return candidatos

def buscar_catalogo(query_str, categoria_filtro=None):
    """Motor de búsqueda difusa, tolerante a fallos, acentos y orden de palabras."""
    clean_q = " ".join(normalizar_texto(query_str).split())
    if not clean_q:
        if categoria_filtro and categoria_filtro != "Todos":
            cat_lower = categoria_filtro.lower()
            return [it for it in CATALOGO_CACHE if it.get("categoria", "").strip().lower() == cat_lower]
        return CATALOGO_CACHE

    clean_q_nospace = clean_q.replace(" ", "")
    q_tokens = clean_q.split()
    num_tokens = len(q_tokens)

    # 1. Obtener candidatos por tokens (palabras clave)
    candidate_indices = set()
    token_item_weights = []

    for qt in q_tokens:
        word_cands = obtener_candidatos_palabra(qt)
        tok_map = defaultdict(float)
        for w, weight in word_cands.items():
            for idx in VOCAB_INDEX[w]:
                if weight > tok_map[idx]:
                    tok_map[idx] = weight
        token_item_weights.append(tok_map)

    if token_item_weights:
        all_sets = [set(m.keys()) for m in token_item_weights]
        strict_matches = set.intersection(*all_sets)
        if strict_matches:
            candidate_indices.update(strict_matches)
        else:
            candidate_indices.update(set.union(*all_sets))

    # 2. Candidatos por subcadena directa o sin espacios (ej. 'spiderman' o 'resident evil')
    for idx, item in enumerate(CATALOGO_CACHE):
        ct = item["clean_title"]
        cn = item["clean_nospace"]
        if clean_q in ct or (len(clean_q_nospace) >= 4 and clean_q_nospace in cn):
            candidate_indices.add(idx)

    # 3. Filtrar por categoría si se especificó
    if categoria_filtro and categoria_filtro != "Todos":
        cat_lower = categoria_filtro.lower()
        candidate_indices = {i for i in candidate_indices if CATALOGO_CACHE[i].get("categoria", "").strip().lower() == cat_lower}

    # 4. Puntuación y Ranking inteligente de relevancia
    scored = []
    for idx in candidate_indices:
        item = CATALOGO_CACHE[idx]
        title = item["clean_title"]
        title_nospace = item["clean_nospace"]
        score = 0.0

        # Coincidencia exacta total del título
        if title == clean_q:
            score += 3000
        elif title.startswith(clean_q):
            score += 2000
        elif clean_q in title:
            score += 1500
        elif len(clean_q_nospace) >= 4 and clean_q_nospace in title_nospace:
            score += 1200

        # Ponderación por tokens coincidentes
        tokens_hit = 0
        for m in token_item_weights:
            w = m.get(idx, 0.0)
            if w > 0:
                tokens_hit += 1
                score += w * 150

        if tokens_hit == num_tokens and num_tokens > 1:
            score += 800  # Gran bono si todos los términos de búsqueda están presentes

        # Penalización suave por longitud excesiva para favorecer títulos más concisos
        score -= min(100, len(title) * 0.3)
        scored.append((score, item))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [x[1] for x in scored]

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/api/categorias")
def api_categorias():
    return jsonify(CATEGORIAS_CACHE)

@app.route("/api/canales")
def api_canales():
    """Búsqueda difusa y paginación ultra rápida en memoria (en menos de 30ms)."""
    query = request.args.get("q", "").strip()
    categoria = request.args.get("categoria", "").strip()
    page = max(1, int(request.args.get("page", 1)))
    limit = min(100, max(1, int(request.args.get("limit", 60))))

    filtrados = buscar_catalogo(query, categoria)

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
            "titulo": item.get("titulo_limpio", item.get("titulo")),
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
        final_launch_url = f"http://localhost:5000/reproductor?url={target_url}&titulo={canal.get('titulo_limpio', canal.get('titulo', ''))}"
    else:
        final_launch_url = target_url

    # Cerrar video en reproducción anterior
    if brave_process and brave_process.poll() is None:
        try:
            brave_process.terminate()
        except Exception:
            pass

    user_data_dir = os.path.expanduser("~/.config/tvbox-brave")
    extension_dir = os.path.join(BASE_DIR, "hydra-shield")

    cmd = [
        "brave-browser",
        f"--user-data-dir={user_data_dir}",
        f"--load-extension={extension_dir}",
        "--disable-popup-blocking=false",
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
            "titulo": canal.get("titulo_limpio", canal.get("titulo")),
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
