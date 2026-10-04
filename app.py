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

HOME_FEED_CACHE = {}

def es_serie(item):
    if not item:
        return False
    cat = str(item.get("categoria", "")).lower()
    url = str(item.get("url", "")).lower()
    return "serie" in cat or "tvshow" in cat or "/serie/" in url

def extraer_anio(item):
    if not item:
        return 0
    t = str(item.get("titulo", ""))
    m = re.search(r'\b(202[0-9]|201[0-9]|19[0-9]{2})\b', t)
    return int(m.group(1)) if m else 0

def formatear_item_api(item):
    if not item:
        return {}
    return {
        "id": item.get("id"),
        "titulo": item.get("titulo_limpio", item.get("titulo")),
        "tipo": item.get("tipo", "web"),
        "categoria": item.get("categoria", ""),
        "poster": item.get("poster", ""),
        "url": item.get("url_resuelta", item.get("url", "")),
        "opciones": item.get("opciones", []),
        "anio": extraer_anio(item),
        "es_serie": es_serie(item)
    }

def construir_home_feed():
    global HOME_FEED_CACHE
    series = []
    peliculas = []
    estrenos = []

    for x in CATALOGO_CACHE:
        if es_serie(x):
            series.append(x)
        else:
            peliculas.append(x)

        anio = extraer_anio(x)
        if anio in [2026, 2025, 2024]:
            estrenos.append(x)

    estrenos.sort(key=lambda x: (extraer_anio(x), x.get("id", 0)), reverse=True)

    KEYWORDS_ACCION = ['john wick', 'mision imposible', 'rapidos', 'furious', 'bad boys', 'venganza', 'batman', 'spider', 'avengers', 'gladiador', 'furia', 'rescat', 'arma', 'policia']
    KEYWORDS_TERROR = ['resident evil', 'saw', 'exorcista', 'warren', 'muerte', 'miedo', 'panico', 'insidious', 'pesadilla', 'demonio', 'siniestro', 'monstruo', 'zombie', 'halloween']
    KEYWORDS_SCIFI = ['alien', 'matrix', 'star wars', 'avatar', 'jurassic', 'transformers', 'dune', 'planeta', 'interstellar', 'marvel', 'dc', 'cyber', 'futuro']
    KEYWORDS_ANIMACION = ['toy story', 'shrek', 'minions', 'kung fu', 'dragon', 'frozen', 'mario', 'pixar', 'disney', 'intensamente', 'moana', 'spiderman']

    def filtrar_palabras(pool, kws, limit=25):
        out = []
        vistos = set()
        for it in pool:
            t = it.get("titulo", "").lower()
            if any(k in t for k in kws) and it["id"] not in vistos:
                vistos.add(it["id"])
                out.append(formatear_item_api(it))
                if len(out) >= limit:
                    break
        return out

    # Candidatos a portada principal (Estrenos taquilleros reconocidos)
    hero_candidates = [
        it for it in estrenos 
        if any(b in it.get("titulo", "").lower() for b in ['resident evil', 'bad boys', 'deadpool', 'spider', 'alien', 'gladiator', 'dune', 'avengers', 'transformers'])
    ]
    if not hero_candidates and estrenos:
        hero_candidates = estrenos[:5]

    hero_item = formatear_item_api(hero_candidates[0]) if hero_candidates else (formatear_item_api(CATALOGO_CACHE[0]) if CATALOGO_CACHE else {})

    HOME_FEED_CACHE = {
        "hero": hero_item,
        "hero_slides": [formatear_item_api(h) for h in hero_candidates[:5]],
        "filas": [
            {
                "id": "estrenos",
                "titulo": "🔥 Últimos Estrenos (2026 - 2025)",
                "subtitulo": "Los lanzamientos más recientes del cine y streaming",
                "items": [formatear_item_api(x) for x in estrenos[:25]]
            },
            {
                "id": "series_populares",
                "titulo": "📺 Series Recomendadas",
                "subtitulo": "Temporadas completas para maratonear",
                "items": [formatear_item_api(x) for x in series[:25]]
            },
            {
                "id": "peliculas_populares",
                "titulo": "🍿 Películas Destacadas",
                "subtitulo": "Los grandes éxitos del cine",
                "items": [formatear_item_api(x) for x in peliculas[:25]]
            },
            {
                "id": "accion",
                "titulo": "💥 Adrenalina y Acción",
                "subtitulo": "Persecuciones, combates y héroes",
                "items": filtrar_palabras(peliculas, KEYWORDS_ACCION, 25)
            },
            {
                "id": "terror",
                "titulo": "👻 Noche de Terror y Suspenso",
                "subtitulo": "Pesadillas, suspenso y misterio",
                "items": filtrar_palabras(peliculas, KEYWORDS_TERROR, 25)
            },
            {
                "id": "scifi",
                "titulo": "🚀 Ciencia Ficción y Futuro",
                "subtitulo": "Universos lejanos y tecnología",
                "items": filtrar_palabras(peliculas, KEYWORDS_SCIFI, 25)
            },
            {
                "id": "animacion",
                "titulo": "🎨 Animación y Familia",
                "subtitulo": "Diversión para todas las edades",
                "items": filtrar_palabras(peliculas, KEYWORDS_ANIMACION, 25)
            }
        ]
    }

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
                            raw_u = m.get("url", "")
                            if raw_u.endswith(".html/"):
                                raw_u = raw_u[:-1]
                            elif raw_u.endswith(".php/"):
                                raw_u = raw_u[:-1]
                            m["url"] = raw_u
                            m["url_resuelta"] = raw_u
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

    construir_home_feed()
    print(f"[OK] Catálogo cargado: {len(CATALOGO_CACHE)} títulos, {len(vocab)} palabras indexadas, {len(CATEGORIAS_CACHE)} categorías, {len(HOME_FEED_CACHE.get('filas', []))} filas temáticas de inicio.")

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

        # Bonus por año reciente (los estrenos y versiones modernas se posicionan primero)
        year_match = re.search(r'\b(19\d\d|20\d\d)\b', item.get("titulo", ""))
        if year_match:
            year_val = int(year_match.group(1))
            if 1970 <= year_val <= 2030:
                score += (year_val - 1970) * 20

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

@app.route("/api/inicio")
def api_inicio():
    return jsonify(HOME_FEED_CACHE)

@app.route("/api/canales")
def api_canales():
    """Búsqueda difusa y paginación ultra rápida en memoria (en menos de 30ms)."""
    query = request.args.get("q", "").strip()
    categoria = request.args.get("categoria", "").strip()
    seccion = request.args.get("seccion", "todos").strip().lower()
    page = max(1, int(request.args.get("page", 1)))
    limit = min(100, max(1, int(request.args.get("limit", 36))))

    filtrados = buscar_catalogo(query, categoria)

    if seccion == "series":
        filtrados = [x for x in filtrados if es_serie(x)]
    elif seccion == "peliculas":
        filtrados = [x for x in filtrados if not es_serie(x)]
    elif seccion == "estrenos":
        filtrados = [x for x in filtrados if extraer_anio(x) in [2026, 2025, 2024]]
    elif seccion in ["accion", "terror", "scifi", "animacion"]:
        keywords_map = {
            "accion": ['john wick', 'mision imposible', 'rapidos', 'furious', 'bad boys', 'venganza', 'batman', 'spider', 'avengers', 'gladiador', 'furia', 'rescat', 'arma', 'policia'],
            "terror": ['resident evil', 'saw', 'exorcista', 'warren', 'muerte', 'miedo', 'panico', 'insidious', 'pesadilla', 'demonio', 'siniestro', 'monstruo', 'zombie', 'halloween'],
            "scifi": ['alien', 'matrix', 'star wars', 'avatar', 'jurassic', 'transformers', 'dune', 'planeta', 'interstellar', 'marvel', 'dc', 'cyber', 'futuro'],
            "animacion": ['toy story', 'shrek', 'minions', 'kung fu', 'dragon', 'frozen', 'mario', 'pixar', 'disney', 'intensamente', 'moana', 'spiderman']
        }
        kws = keywords_map[seccion]
        filtrados = [x for x in filtrados if any(k in x.get("titulo", "").lower() for k in kws)]

    total = len(filtrados)
    total_pages = (total + limit - 1) // limit if total > 0 else 1
    start = (page - 1) * limit
    end = start + limit

    items_pagina = filtrados[start:end]
    resultado = [formatear_item_api(it) for it in items_pagina]

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
    if target_url.endswith(".html/"):
        target_url = target_url[:-1]
    elif target_url.endswith(".php/"):
        target_url = target_url[:-1]

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
