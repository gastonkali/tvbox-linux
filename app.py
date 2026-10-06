import json
import os
import subprocess
import unicodedata
import re
import urllib.request
import urllib.parse
import time
import datetime
import threading
from collections import defaultdict
from flask import Flask, render_template, jsonify, request
from verificador_cyberlockers import auditar_item_completo, purgar_item_a_vivos, resolver_servidores_inteligente

app = Flask(__name__)
brave_process = None

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CANALES_FILE = os.path.join(BASE_DIR, "canales.json")
CATALOGO_MAESTRO_FILE = os.path.join(BASE_DIR, "catalogo_maestro.json")
REPORTES_FILE = os.path.join(BASE_DIR, "reportes.json")
ELIMINADOS_FILE = os.path.join(BASE_DIR, "eliminados.json")
MODIFICACIONES_FILE = os.path.join(BASE_DIR, "modificaciones.json")

def cargar_json_seguro(path, default_val):
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[Aviso] Error leyendo {path}: {e}")
    return default_val

def guardar_json_seguro(path, data):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"[Error] Error guardando {path}: {e}")
        return False

# Memoria caché global para búsquedas instantáneas
CATALOGO_CACHE = []
ITEMS_BY_ID = {}
CATEGORIAS_CACHE = []
PROVEEDORES_CACHE = {}

# Estructuras para búsqueda difusa (Fuzzy Search) ultrarrápida, sinopsis y filmografías de actores
SINOPSIS_CACHE = {}
VOCAB_INDEX = defaultdict(set)      # palabra -> set(indices en CATALOGO_CACHE)
PHONETIC_INDEX = defaultdict(set)   # palabra_fonetica -> set(palabras reales del vocabulario)
WORDS_BY_LEN = defaultdict(list)    # longitud -> lista de palabras únicas
WORDS_BY_PREFIX = defaultdict(list) # prefijo -> lista de palabras únicas
TMDB_TO_ITEMS = defaultdict(list)   # tmdb_id -> lista de indices en CATALOGO_CACHE
ACTORES_CACHE_FILE = os.path.join(BASE_DIR, "actores_cache.json")
ACTORES_CACHE = {}                  # nombre_normalizado -> lista de tmdb_ids

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

def normalizar_fonetica(w):
    """Normaliza variaciones fonéticas y ortográficas comunes (ej. jhon->jon, whic->wik, balerina/bailarina->balerina)."""
    if not w:
        return ""
    w = w.lower().strip()
    w = w.replace('jh', 'j').replace('wh', 'w').replace('ph', 'f')
    w = w.replace('ll', 'l').replace('v', 'b').replace('y', 'i')
    w = w.replace('ck', 'k')
    w = re.sub(r'c([eiy])', r's\1', w)
    w = w.replace('c', 'k').replace('z', 's')
    w = w.replace('bailar', 'baler').replace('baller', 'baler')
    w = w.replace('john', 'jon').replace('jhon', 'jon')
    return w

def lev_dist_2(s1, s2):
    """Calcula si la distancia de edición Damerau-Levenshtein es <= 2."""
    len1, len2 = len(s1), len(s2)
    if abs(len1 - len2) > 2:
        return 99
    d = [[0] * (len2 + 1) for _ in range(len1 + 1)]
    for i in range(len1 + 1):
        d[i][0] = i
    for j in range(len2 + 1):
        d[0][j] = j
    for i in range(1, len1 + 1):
        for j in range(1, len2 + 1):
            cost = 0 if s1[i-1] == s2[j-1] else 1
            d[i][j] = min(d[i-1][j] + 1, d[i][j-1] + 1, d[i-1][j-1] + cost)
            if i > 1 and j > 1 and s1[i-1] == s2[j-2] and s1[i-2] == s2[j-1]:
                d[i][j] = min(d[i-1][j], d[i-2][j-2] + 1)
    return d[len1][len2]

def damerau_levenshtein_1(s1, s2):
    return lev_dist_2(s1, s2) <= 1

STOP_WORDS_DEDUP = {
    'el', 'la', 'los', 'las', 'del', 'de', 'en', 'un', 'una', 'y', 'image',
    'pelicula', 'serie', 'online', 'espanol', 'latino', 'hd', 'para', 'por',
    'completa', 'subtitulado'
}

def extraer_anio_str(t):
    m = re.search(r'\b(202[0-9]|201[0-9]|19[0-9]{2})\b', str(t))
    return m.group(1) if m else ''

def slug_from_url(url):
    m = re.search(r'/(?:movies|series|pelicula/\d+|serie/\d+|ver-pelicula/\d+-)/?([^/?#]+)', str(url))
    if not m:
        return ''
    s = m.group(1).lower().replace('_', '-').replace('.html', '').replace('.php', '')
    s = re.sub(r'^\d+-', '', s)
    return s.strip('-')

def dedup_signature(text):
    parts = re.split(r'[^a-zA-Z0-9]+', str(text))
    words = [normalizar_fonetica(p) for p in parts if p.lower() not in STOP_WORDS_DEDUP and len(p) > 0]
    return '_'.join(sorted(words))

def fusionar_cluster(items_cluster):
    if len(items_cluster) == 1:
        return items_cluster[0]

    def score_item(it):
        s = 0
        u = it.get('url', '').lower()
        p = it.get('poster', '').lower()
        t = it.get('titulo', '')
        if 'poseidon' in u:
            s += 50
        if 'image.tmdb.org' in p:
            s += 30
        elif p and 'pelicine' not in p:
            s += 10
        if t.startswith('Image '):
            s -= 40
        if len(t) > 5 and not t.isdigit():
            s += 10
        return s

    items_sorted = sorted(items_cluster, key=score_item, reverse=True)
    primario = dict(items_sorted[0])

    mejores_titulos = [it.get('titulo') for it in items_sorted if not it.get('titulo', '').startswith('Image ')]
    if mejores_titulos:
        cands = sorted(mejores_titulos, key=lambda x: (len(x) if len(x) < 50 else 0), reverse=True)
        primario['titulo'] = cands[0]

    posters = [it.get('poster') for it in items_sorted if it.get('poster') and 'image.tmdb.org' in it.get('poster')]
    if posters:
        primario['poster'] = posters[0]

    opciones_unificadas = []
    urls_vistas = set()
    for it in items_sorted:
        cands_urls = [it.get('url', '')] + it.get('opciones', [])
        for u in cands_urls:
            if not u:
                continue
            u_clean = u.rstrip('/')
            if u_clean not in urls_vistas:
                urls_vistas.add(u_clean)
                opciones_unificadas.append(u)

    opciones_unificadas.sort(key=lambda u: (0 if 'poseidon' in u.lower() else (1 if 'cinemitas' in u.lower() else 2)))
    primario['opciones'] = opciones_unificadas
    primario['url'] = opciones_unificadas[0] if opciones_unificadas else primario.get('url', '')
    primario['url_resuelta'] = primario['url']

    todos_los_titulos = set()
    for it in items_cluster:
        todos_los_titulos.add(it.get('titulo', ''))
    primario['titulos_alternativos'] = list(todos_los_titulos)
    return primario

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

def limpiar_poster_url(poster):
    if not poster:
        return ""
    if "gnularetro" in poster or "wp-content" in poster:
        m = re.search(r'/([a-zA-Z0-9]{20,40})(?:-\d+x\d+)?\.(?:jpg|png|webp)', str(poster))
        if m:
            return f"https://image.tmdb.org/t/p/w500/{m.group(1)}.jpg"
    return poster

def formatear_item_api(item):
    if not item:
        return {}
    return {
        "id": item.get("id"),
        "titulo": item.get("titulo_limpio", item.get("titulo")),
        "tipo": item.get("tipo", "web"),
        "categoria": item.get("categoria", ""),
        "poster": limpiar_poster_url(item.get("poster", "")),
        "url": item.get("url_resuelta", item.get("url", "")),
        "opciones": item.get("opciones", []),
        "anio": extraer_anio(item),
        "es_serie": es_serie(item)
    }

GENRES_MAP = {
    "accion": [
        "mision imposible", "mission impossible", "mision rescate", "extraction",
        "rapidos y furiosos", "rapido y furioso", "fast & furious", "bad boys",
        "venganza", "revenge", "gladiador", "gladiator", "arma mortal", "lethal weapon",
        "john wick", "hitman", "fuerzas especiales", "fuerza delta", "comando",
        "operacion rescate", "operacion especial", "operacion militar", "black ops",
        "fuego cruzado", "bajo fuego", "golpe letal", "golpe maestro", "artes marciales",
        "combate mortal", "mortal kombat", "mercenario", "die hard", "duro de matar",
        "busqueda implacable", "el justiciero", "the equalizer", "los indestructibles",
        "the expendables", "rambo", "top gun", "mad max", "terminator", "francotirador",
        "sniper", "sicario", "swat", "tiroteo", "peligro inminente", "transporter",
        "transportador", "deadpool", "wolverine"
    ],
    "ciencia-ficcion": [
        "alien", "matrix", "star wars", "avatar", "jurassic", "transformers", "dune",
        "interstellar", "cyber", "futuro", "future", "espacio", "space",
        "galaxia", "galaxy", "robot", "cyborg", "maquina", "clon", "mutante",
        "viaje en el tiempo", "apocalipsis", "distopia",
        "quantum", "gravedad", "invasion alien", "scifi", "sci-fi",
        "multiverso", "terminator", "predator", "depredador", "interestelar"
    ],
    "terror": [
        "resident evil", "saw", "exorcista", "exorcist", "warren", "insidious",
        "pesadilla en la calle", "nightmare on elm", "demonio", "siniestro",
        "zombie", "terror", "horror", "grito", "scream", "noche sangrienta",
        "noche de los muertos", "maldicion", "posesion demoniaca", "bruja de blair",
        "infierno", "paranormal", "gore", "carnicero", "dracula", "vampir", "licantropo",
        "el conjuro", "the conjuring", "anabelle", "annabelle", "la monja", "the nun",
        "hereditary", "midsommar", "un lugar en silencio", "a quiet place", "silent hill"
    ],
    "comedia": [
        "comedia", "comedy", "risa", "loco", "fiesta", "tonto",
        "broma", "vacaciones", "parodia", "boda",
        "chistoso", "divertido", "funny", "ted", "hangover", "desmadre",
        "juerga", "locura americana"
    ],
    "drama": [
        "drama", "vida real", "historia real", "vida o muerte", "dolor", "destino",
        "promesa", "recuerdos", "perdon", "lagrimas", "justicia", "juicio", "tribunal",
        "enfermedad", "hospital", "amor imposible", "esperanza", "triste"
    ],
    "animacion": [
        "toy story", "shrek", "minions", "kung fu panda", "frozen", "mario bros", "pixar", "disney",
        "intensamente", "moana", "animacion", "animation", "anime", "infantil", "dibujo",
        "cartoon", "pokemon", "naruto", "dragon ball", "encanto", "coco", "nemo", "dory", "cars",
        "monsters inc", "era de hielo", "ice age", "madagascar", "sonic", "mickey",
        "peter pan", "aladdin", "cenicienta", "pinocho", "mulan", "castor", "bob esponja",
        "spongebob", "mi villano favorito", "paw patrol", "zootopia", "zootropolis", "garfield",
        "spidey", "thunderman", "peppa pig", "looney tunes", "scooby", "tom y jerry"
    ],
    "crimen-suspenso": [
        "crimen", "misterio", "mafia", "detective", "robo", "heist",
        "estafa", "cartel", "investigacion criminal", "sospechoso",
        "testigo protegido", "abogado", "prision", "carcel", "narco",
        "mafioso", "gangster", "thriller", "suspenso", "psicopata", "desaparicion", "secuestro",
        "padrino", "corrupcion"
    ],
    "romance": [
        "amor", "romance", "romantic", "enamorado", "beso", "corazon",
        "boda", "matrimonio", "cita a ciegas", "cancion de amor", "san valentin",
        "primer amor"
    ],
    "aventura-fantasia": [
        "aventura", "fantasia", "fantasy", "magia", "espada y brujeria",
        "tesoro perdido", "leyenda", "caballero del zodiaco", "castillo",
        "isla misteriosa", "piratas del caribe", "hobbit", "senor de los anillos",
        "lord of the rings", "harry potter", "narnia"
    ]
}

# Palabras clave exclusivas de animación/infantil para evitar falsos positivos en Acción, Terror, Crimen y Ciencia Ficción
KEYWORDS_ANIMACION_EXCLUSION = [
    "pixar", "disney", "minions", "minion", "shrek", "toy story", "kung fu panda", "castor",
    "dibujo", "dibujos", "cartoon", "cartoons", "infantil", "infantiles", "animacion", "animada",
    "animado", "animated", "animation", "anime", "nemo", "dory", "frozen", "moana", "encanto",
    "coco", "intensamente", "inside out", "cars", "era de hielo", "ice age", "madagascar",
    "aladdin", "pinocho", "cenicienta", "mario bros", "super mario", "bob esponja", "spongebob",
    "peppa pig", "peppa", "mi villano favorito", "despicable me", "paw patrol", "patrulla canina",
    "zootopia", "zootropolis", "garfield", "mascotas", "secret life of pets", "dora", "barbie",
    "ben 10", "looney tunes", "bugs bunny", "scooby", "tom y jerry", "tom and jerry", "pocoyo",
    "baby shark", "chuggington", "trolls", "hotel transylvania", "sing ven y canta", "los pitufos",
    "smurfs", "boss baby", "un jefe en pañales", "ladybug", "miraculous", "playmobil",
    "my little pony", "wallace y gromit", "wallace & gromit", "los simpson", "the simpsons",
    "dragon ball", "naruto", "one piece", "pokemon", "digimon", "spidey", "thunderman",
    "thundermans", "junior", "lego", "halloween", "nickelodeon", "popeye", "plazasamo",
    "teletubbies", "doraemon", "shin chan", "sailor moon"
]

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
        if anio in (2025, 2026):
            estrenos.append(x)

    estrenos.sort(key=lambda x: (1 if extraer_anio(x) == 2025 else 0, x.get("id", 0)), reverse=True)

    ultimos_agregados = [x for x in CATALOGO_CACHE if x.get("poster") and "ultrapeli" not in x.get("poster", "")]
    ultimos_agregados.sort(key=lambda x: x.get("id", 0), reverse=True)

    def filtrar_palabras(pool, kws, limit=25, excl=None):
        out = []
        vistos = set()
        for it in pool:
            t = (it.get("titulo", "") + " " + it.get("url", "")).lower()
            if excl and any(e in t for e in excl):
                continue
            if any(k in t for k in kws) and it["id"] not in vistos:
                vistos.add(it["id"])
                out.append(formatear_item_api(it))
                if len(out) >= limit:
                    break
        return out

    # Candidatos a portada principal (Superproducciones taquilleras reconocidas disponibles)
    hero_blockbusters = [
        'gladiador ii', 'deadpool & wolverine', 'bad boys hasta la muerte',
        'alien romulus', 'furiosa de la saga mad max', 'dune parte dos', 'dune'
    ]
    hero_candidates = []
    for b in hero_blockbusters:
        for x in CATALOGO_CACHE:
            if b in x.get("titulo", "").lower() and x.get("poster") and "image.tmdb.org" in x.get("poster"):
                if not any(e in x.get("titulo", "").lower() for e in KEYWORDS_ANIMACION_EXCLUSION):
                    hero_candidates.append(x)
                    break

    if not hero_candidates and estrenos:
        hero_candidates = [it for it in estrenos if not any(e in it.get("titulo", "").lower() for e in KEYWORDS_ANIMACION_EXCLUSION)][:5]
    if not hero_candidates:
        hero_candidates = estrenos[:5]

    hero_item = formatear_item_api(hero_candidates[0]) if hero_candidates else (formatear_item_api(CATALOGO_CACHE[0]) if CATALOGO_CACHE else {})

    HOME_FEED_CACHE = {
        "hero": hero_item,
        "hero_slides": [formatear_item_api(h) for h in hero_candidates[:5]],
        "filas": [
            {
                "id": "estrenos",
                "titulo": "🔥 Últimos Estrenos (2026)",
                "subtitulo": "Lanzamientos del año en cines y plataformas",
                "items": [formatear_item_api(x) for x in estrenos[:25]]
            },
            {
                "id": "ultimos_agregados",
                "titulo": "✨ Agregados Recientemente",
                "subtitulo": "Nuevas incorporaciones añadidas al catálogo",
                "items": [formatear_item_api(x) for x in ultimos_agregados[:25]]
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
                "items": filtrar_palabras(peliculas, GENRES_MAP["accion"], 25, KEYWORDS_ANIMACION_EXCLUSION)
            },
            {
                "id": "terror",
                "titulo": "👻 Noche de Terror y Suspenso",
                "subtitulo": "Pesadillas, suspenso y misterio",
                "items": filtrar_palabras(peliculas, GENRES_MAP["terror"], 25, KEYWORDS_ANIMACION_EXCLUSION)
            },
            {
                "id": "scifi",
                "titulo": "🚀 Ciencia Ficción y Futuro",
                "subtitulo": "Universos lejanos y tecnología",
                "items": filtrar_palabras(peliculas, GENRES_MAP["ciencia-ficcion"], 25, KEYWORDS_ANIMACION_EXCLUSION)
            },
            {
                "id": "animacion",
                "titulo": "🎨 Animación y Familia",
                "subtitulo": "Diversión para todas las edades",
                "items": filtrar_palabras(peliculas, GENRES_MAP["animacion"], 25)
            }
        ]
    }

def inicializar_catalogo():
    """Carga canales.json y catalogo_maestro.json en memoria, deduplica entradas y construye el índice fuzzy-fonético."""
    global CATALOGO_CACHE, ITEMS_BY_ID, CATEGORIAS_CACHE, PROVEEDORES_CACHE
    global VOCAB_INDEX, PHONETIC_INDEX, WORDS_BY_LEN, WORDS_BY_PREFIX, TMDB_TO_ITEMS, ACTORES_CACHE

    items_combinados = []
    ids_registrados = set()
    proveedores = {}

    eliminados = cargar_json_seguro(ELIMINADOS_FILE, {})
    modificaciones = cargar_json_seguro(MODIFICACIONES_FILE, {})

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
                        c_id_str = str(c_id)
                        if c_id_str in eliminados or c.get("url") in eliminados:
                            continue
                        if c_id_str in modificaciones:
                            override = modificaciones[c_id_str]
                            c.update({k: v for k, v in override.items() if k in ["url", "opciones", "titulo"]})
                        c["url_resuelta"] = resolver_url(c, proveedores)
                        items_combinados.append(c)
                        ids_registrados.add(c_id)
        except Exception as e:
            print(f"[Aviso] Error leyendo canales.json: {e}")

    # 2. Cargar catalogo_maestro.json y deduplicar inteligentemente agrupando servidores
    if os.path.exists(CATALOGO_MAESTRO_FILE):
        try:
            with open(CATALOGO_MAESTRO_FILE, "r", encoding="utf-8") as f:
                maestro = json.load(f)
                if isinstance(maestro, list):
                    clusters = []
                    tmdb_to_cluster = {}
                    sig_to_cluster = {}

                    for m in maestro:
                        m_id = m.get("id")
                        if m_id is None or m_id in ids_registrados:
                            continue
                        if not m.get("poster") or not str(m.get("poster")).strip() or "ultrapeli.com" in m.get("poster", ""):
                            continue
                        raw_u = m.get("url", "")
                        if raw_u.endswith(".html/"):
                            raw_u = raw_u[:-1]
                        elif raw_u.endswith(".php/"):
                            raw_u = raw_u[:-1]
                        m["url"] = raw_u
                        m["url_resuelta"] = raw_u

                        is_ser = es_serie(m)
                        type_pfx = 's:' if is_ser else 'm:'

                        m_tmdb = re.search(r'/(?:pelicula|serie)/(\d+)', raw_u)
                        tmdb_key = (type_pfx + m_tmdb.group(1)) if m_tmdb else None

                        slug = slug_from_url(raw_u)
                        slug_sig = dedup_signature(slug) if slug else ''
                        title_sig = dedup_signature(m.get('titulo', ''))
                        yr = extraer_anio_str(m.get('titulo', ''))

                        c_idx = None
                        if tmdb_key and tmdb_key in tmdb_to_cluster:
                            c_idx = tmdb_to_cluster[tmdb_key]
                        elif slug_sig and len(slug_sig.split('_')) >= 2 and (type_pfx + 's:' + slug_sig) in sig_to_cluster:
                            c_idx = sig_to_cluster[type_pfx + 's:' + slug_sig]
                        elif title_sig and len(title_sig.split('_')) >= 2:
                            tk = type_pfx + 't:' + title_sig + (':' + yr if yr else '')
                            if tk in sig_to_cluster:
                                c_idx = sig_to_cluster[tk]

                        if c_idx is None:
                            c_idx = len(clusters)
                            clusters.append([m])
                        else:
                            clusters[c_idx].append(m)

                        if tmdb_key:
                            tmdb_to_cluster[tmdb_key] = c_idx
                        if slug_sig and len(slug_sig.split('_')) >= 2:
                            sig_to_cluster[type_pfx + 's:' + slug_sig] = c_idx
                        if title_sig and len(title_sig.split('_')) >= 2:
                            tk = type_pfx + 't:' + title_sig + (':' + yr if yr else '')
                            sig_to_cluster[tk] = c_idx

                    print(f"[OK] Catálogo deduplicado: {len(maestro)} entradas agrupadas en {len(clusters)} títulos consolidados.")
                    for c in clusters:
                        fused_item = fusionar_cluster(c)
                        f_id_str = str(fused_item.get("id"))
                        if f_id_str in eliminados or fused_item.get("url") in eliminados:
                            continue
                        if f_id_str in modificaciones:
                            override = modificaciones[f_id_str]
                            if "url" in override:
                                fused_item["url"] = override["url"]
                                fused_item["url_resuelta"] = override["url"]
                            if "opciones" in override:
                                fused_item["opciones"] = override["opciones"]
                            if "titulo" in override:
                                fused_item["titulo"] = override["titulo"]
                        items_combinados.append(fused_item)
                        ids_registrados.add(fused_item["id"])
        except Exception as e:
            print(f"[Aviso] Error leyendo catalogo_maestro.json: {e}")

    # 3. Construir estructuras de indexación para búsqueda fuzzy y fonética ultraveloz
    vocab = defaultdict(set)
    phonetic_map = defaultdict(set)
    words_by_len = defaultdict(list)
    words_by_prefix = defaultdict(list)

    for idx, item in enumerate(items_combinados):
        raw_title = item.get("titulo", "")
        titulo_limpio = limpiar_titulo_para_mostrar(raw_title)
        clean_title = " ".join(normalizar_texto(titulo_limpio).split())
        clean_nospace = clean_title.replace(" ", "")

        tokens = list(clean_title.split())
        for alt in item.get("titulos_alternativos", []):
            tokens.extend(normalizar_texto(limpiar_titulo_para_mostrar(alt)).split())

        slug = slug_from_url(item.get("url", ""))
        if slug:
            tokens.extend(normalizar_texto(slug).split())

        unique_tokens = set(tokens)
        item["titulo_limpio"] = titulo_limpio
        item["clean_title"] = clean_title
        item["clean_nospace"] = clean_nospace
        item["phonetic_title"] = " ".join(normalizar_fonetica(tok) for tok in clean_title.split())
        item["tokens"] = list(unique_tokens)

        for tok in unique_tokens:
            vocab[tok].add(idx)

    for w in vocab.keys():
        pw = normalizar_fonetica(w)
        phonetic_map[pw].add(w)
        words_by_len[len(w)].append(w)
        if len(w) >= 2:
            words_by_prefix[w[:2]].append(w)
        if len(w) >= 1:
            words_by_prefix[w[:1]].append(w)

    CATALOGO_CACHE = items_combinados
    ITEMS_BY_ID = {item["id"]: item for item in items_combinados}
    PROVEEDORES_CACHE = proveedores
    VOCAB_INDEX = vocab
    PHONETIC_INDEX = phonetic_map
    WORDS_BY_LEN = words_by_len
    WORDS_BY_PREFIX = words_by_prefix

    # 4. Construir índice inverso de IDs de TMDb para búsqueda por actor/director
    tmdb_map = defaultdict(list)
    tmdb_regex = re.compile(r'/(?:pelicula|serie)/(\d+)')
    for idx, item in enumerate(items_combinados):
        urls = [str(item.get("url", ""))]
        for opt in item.get("opciones", []):
            urls.append(opt.get("url", "") if isinstance(opt, dict) else str(opt))
        for u in urls:
            m = tmdb_regex.search(u)
            if m:
                try:
                    tid = int(m.group(1))
                    if idx not in tmdb_map[tid]:
                        tmdb_map[tid].append(idx)
                except ValueError:
                    pass
    TMDB_TO_ITEMS = tmdb_map

    # 5. Cargar caché de actores si existe
    if os.path.exists(ACTORES_CACHE_FILE):
        try:
            with open(ACTORES_CACHE_FILE, "r", encoding="utf-8") as f:
                ACTORES_CACHE = json.load(f)
            print(f"[OK] Caché de actores cargada: {len(ACTORES_CACHE)} entradas indexadas.")
        except Exception as e:
            print(f"[Aviso] Error leyendo actores_cache.json: {e}")

    # Extraer categorías únicas limpias
    categorias_set = set()
    for item in items_combinados:
        cat = item.get("categoria")
        if cat and isinstance(cat, str) and cat.strip():
            categorias_set.add(cat.strip())

    lista_cat = sorted(list(categorias_set))
    CATEGORIAS_CACHE = ["Todos"] + lista_cat

    construir_home_feed()
    print(f"[OK] Catálogo cargado: {len(CATALOGO_CACHE)} títulos, {len(vocab)} palabras indexadas ({len(phonetic_map)} raíces fonéticas), {len(TMDB_TO_ITEMS)} IDs TMDb mapeados, {len(CATEGORIAS_CACHE)} categorías.")

# Cargar catálogo en memoria al arrancar
inicializar_catalogo()

FILM_PERSON_KEYWORDS = [
    "actor", "actress", "actriz", "filmmaker", "director", "cineasta", "guionista",
    "producer", "productor", "film", "película", "pelicula", "cinema", "cine"
]

def buscar_persona_wikidata(nombre):
    """Consulta Wikidata en 2 pasos rápidos (búsqueda de entidad + SPARQL de IDs de TMDb)."""
    norm_nombre = " ".join(normalizar_texto(nombre).split())
    if not norm_nombre:
        return []

    try:
        url = f"https://www.wikidata.org/w/api.php?action=wbsearchentities&search={urllib.parse.quote(nombre)}&language=es&format=json&limit=5"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 TVBoxCatalog/2.0 (mailto:admin@tvbox.lan)'})
        with urllib.request.urlopen(req, timeout=3.5) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            results = data.get('search', [])

        if not results:
            return []

        chosen_qid = None
        for r in results:
            desc = (r.get('description', '') or '').lower()
            if any(k in desc for k in FILM_PERSON_KEYWORDS):
                chosen_qid = r.get('id')
                break

        if not chosen_qid:
            chosen_qid = results[0].get('id')

        if not chosen_qid or not chosen_qid.startswith('Q'):
            return []

        sparql = f"""
        SELECT DISTINCT ?film ?tmdbId WHERE {{
          {{ ?film wdt:P161 wd:{chosen_qid} }} UNION {{ ?film wdt:P57 wd:{chosen_qid} }}
          ?film wdt:P4947 ?tmdbId .
        }}
        LIMIT 200
        """
        sparql_url = 'https://query.wikidata.org/sparql?' + urllib.parse.urlencode({'query': sparql, 'format': 'json'})
        sparql_req = urllib.request.Request(sparql_url, headers={'User-Agent': 'Mozilla/5.0 TVBoxCatalog/2.0 (mailto:admin@tvbox.lan)'})
        with urllib.request.urlopen(sparql_req, timeout=3.5) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            bindings = data.get('results', {}).get('bindings', [])
            tmdb_ids = set()
            for b in bindings:
                tid = b.get('tmdbId', {}).get('value')
                if tid:
                    try:
                        tmdb_ids.add(int(tid))
                    except ValueError:
                        pass
            return list(tmdb_ids)
    except Exception as e:
        print(f"[Aviso] Wikidata lookup falló para '{nombre}': {e}")
        return []

def guardar_actores_cache():
    try:
        with open(ACTORES_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(ACTORES_CACHE, f, ensure_ascii=False)
    except Exception as e:
        print(f"[Aviso] No se pudo persistir actores_cache.json: {e}")

def buscar_persona_filmografia(query_str):
    """Busca en caché o consulta Wikidata para devolver los TMDb IDs de la filmografía de un actor/director."""
    global ACTORES_CACHE
    norm_q = " ".join(normalizar_texto(query_str).split())
    if not norm_q:
        return []

    # 1. Comprobar en caché de memoria (ultraveloz 0ms)
    if norm_q in ACTORES_CACHE:
        return ACTORES_CACHE[norm_q]

    # 2. Consultar Wikidata si parece nombre de persona (al menos 2 palabras o >= 4 letras)
    tokens = norm_q.split()
    if len(tokens) >= 2 or len(norm_q) >= 4:
        tmdb_ids = buscar_persona_wikidata(query_str)
        ACTORES_CACHE[norm_q] = tmdb_ids
        if tmdb_ids:
            guardar_actores_cache()
        return tmdb_ids

    return []

def obtener_candidatos_palabra(palabra_query):
    """Encuentra palabras del catálogo exactas, fonéticas, por prefijo o con hasta 2 errores tipográficos."""
    candidatos = {}
    if palabra_query in VOCAB_INDEX:
        candidatos[palabra_query] = 1.0  # Coincidencia exacta

    # Coincidencia fonética (ej. jhon -> john, whic -> wick, balerina -> ballerina)
    pw = normalizar_fonetica(palabra_query)
    if pw in PHONETIC_INDEX:
        for w in PHONETIC_INDEX[pw]:
            if w not in candidatos:
                candidatos[w] = 0.90

    q_len = len(palabra_query)
    # Búsqueda por prefijo (ej. residen -> resident, w -> wick, wi -> wick)
    if q_len >= 2 and palabra_query[:2] in WORDS_BY_PREFIX:
        for w in WORDS_BY_PREFIX[palabra_query[:2]]:
            if w.startswith(palabra_query) and w not in candidatos:
                candidatos[w] = 0.85
    elif q_len == 1 and palabra_query in WORDS_BY_PREFIX:
        for w in WORDS_BY_PREFIX[palabra_query]:
            if w.startswith(palabra_query) and w not in candidatos:
                candidatos[w] = 0.80

    # Búsqueda difusa por distancia de edición (tolerancia a 1 o 2 letras cambiadas/faltantes/sobrantes)
    if q_len >= 4:
        for l in range(max(2, q_len - 2), q_len + 3):
            for w in WORDS_BY_LEN[l]:
                if w in candidatos:
                    continue
                d = lev_dist_2(palabra_query, w)
                if d == 1:
                    candidatos[w] = 0.75
                elif d == 2:
                    candidatos[w] = 0.65
    elif q_len == 3:
        for l in range(2, 5):
            for w in WORDS_BY_LEN[l]:
                if w in candidatos:
                    continue
                if lev_dist_2(palabra_query, w) == 1:
                    candidatos[w] = 0.70

    return candidatos

def buscar_catalogo(query_str, categoria_filtro=None):
    """Motor de búsqueda difusa, fonética y tolerante a fallos, acentos, actores y directores."""
    clean_q = " ".join(normalizar_texto(query_str).split())
    if not clean_q:
        if categoria_filtro and categoria_filtro != "Todos":
            cat_lower = categoria_filtro.lower()
            return [it for it in CATALOGO_CACHE if it.get("categoria", "").strip().lower() == cat_lower]
        return CATALOGO_CACHE

    clean_q_nospace = clean_q.replace(" ", "")
    q_tokens = clean_q.split()
    num_tokens = len(q_tokens)
    ph_q = " ".join(normalizar_fonetica(t) for t in q_tokens)

    # 1. Búsqueda por Filmografía de Actor / Director
    actor_item_indices = set()
    actor_tmdb_ids = buscar_persona_filmografia(query_str)
    if actor_tmdb_ids:
        for tid in actor_tmdb_ids:
            if tid in TMDB_TO_ITEMS:
                actor_item_indices.update(TMDB_TO_ITEMS[tid])

    candidate_indices = set(actor_item_indices)
    token_item_weights = []

    # 2. Obtener candidatos por tokens (palabras clave del título)
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
        elif not actor_item_indices:
            # Si NO se encontró actor y es búsqueda de una sola palabra, permitir candidatos difusos
            if num_tokens == 1:
                candidate_indices.update(set.union(*all_sets))
            else:
                # Si tiene más de una palabra y no es actor, buscar títulos que coincidan con la mayoría de términos
                counts = defaultdict(int)
                for s in all_sets:
                    for idx in s:
                        counts[idx] += 1
                min_req = max(1, num_tokens - 1)
                candidate_indices.update({idx for idx, cnt in counts.items() if cnt >= min_req})

    # 3. Candidatos por subcadena directa, sin espacios o fonética
    for idx, item in enumerate(CATALOGO_CACHE):
        ct = item["clean_title"]
        cn = item["clean_nospace"]
        pt = item.get("phonetic_title", "")
        if clean_q in ct or (len(clean_q_nospace) >= 4 and clean_q_nospace in cn) or (ph_q and len(ph_q) >= 3 and ph_q in pt):
            candidate_indices.add(idx)

    # 4. Filtrar por categoría si se especificó
    if categoria_filtro and categoria_filtro != "Todos":
        cat_lower = categoria_filtro.lower()
        candidate_indices = {i for i in candidate_indices if CATALOGO_CACHE[i].get("categoria", "").strip().lower() == cat_lower}

    # 5. Puntuación y Ranking inteligente de relevancia
    scored = []
    for idx in candidate_indices:
        item = CATALOGO_CACHE[idx]
        title = item["clean_title"]
        title_nospace = item["clean_nospace"]
        ph_title = item.get("phonetic_title", "")
        score = 0.0

        # Máxima prioridad si es obra del actor/director buscado
        if idx in actor_item_indices:
            score += 5000.0

        # Coincidencia exacta total del título o fonética
        if title == clean_q or (ph_q and ph_title == ph_q):
            score += 3500
        elif ph_q and ph_q in ph_title:
            score += 2500
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
                score += w * 200

        if tokens_hit == num_tokens and num_tokens > 1:
            score += 1000  # Gran bono si todos los términos de búsqueda están presentes

        # Bonus por año reciente (los estrenos y versiones modernas se posicionan primero)
        year_match = re.search(r'\b(19\d\d|20\d\d)\b', item.get("titulo", ""))
        if year_match:
            year_val = int(year_match.group(1))
            if 1970 <= year_val <= 2030:
                score += (year_val - 1970) * 20

        # Penalización suave por longitud excesiva para favorecer títulos más concisos
        score -= min(100, len(title) * 0.2)
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

@app.route("/api/generos")
def api_generos():
    """Devuelve los géneros temáticos disponibles para Películas y Series."""
    return jsonify({
        "peliculas": [
            {"id": "todos", "label": "Todas las Películas", "icon": "🎬"},
            {"id": "accion", "label": "Acción", "icon": "💥"},
            {"id": "ciencia-ficcion", "label": "Ciencia Ficción", "icon": "🚀"},
            {"id": "terror", "label": "Terror y Suspenso", "icon": "👻"},
            {"id": "comedia", "label": "Comedia", "icon": "😂"},
            {"id": "drama", "label": "Drama", "icon": "🎭"},
            {"id": "aventura-fantasia", "label": "Aventura y Fantasía", "icon": "⚔️"},
            {"id": "animacion", "label": "Animación y Familia", "icon": "🎨"},
            {"id": "crimen-suspenso", "label": "Crimen y Misterio", "icon": "🔍"},
            {"id": "romance", "label": "Romance", "icon": "❤️"}
        ],
        "series": [
            {"id": "todos", "label": "Todas las Series", "icon": "📺"},
            {"id": "accion", "label": "Acción y Aventura", "icon": "💥"},
            {"id": "ciencia-ficcion", "label": "Ciencia Ficción", "icon": "🚀"},
            {"id": "terror", "label": "Terror y Misterio", "icon": "👻"},
            {"id": "drama", "label": "Drama", "icon": "🎭"},
            {"id": "comedia", "label": "Comedia", "icon": "😂"},
            {"id": "crimen-suspenso", "label": "Crimen y Policial", "icon": "🔍"},
            {"id": "animacion", "label": "Animación y Anime", "icon": "🎨"},
            {"id": "romance", "label": "Romance", "icon": "❤️"}
        ]
    })

@app.route("/api/canales")
def api_canales():
    """Búsqueda difusa y paginación ultra rápida en memoria (en menos de 30ms)."""
    query = request.args.get("q", "").strip()
    categoria = request.args.get("categoria", "").strip()
    seccion = request.args.get("seccion", "todos").strip().lower()
    genero = request.args.get("genero", "todos").strip().lower()
    page = max(1, int(request.args.get("page", 1)))
    limit = min(100, max(1, int(request.args.get("limit", 36))))

    filtrados = buscar_catalogo(query, categoria)

    # 1. Filtro por sección principal
    if seccion == "series":
        filtrados = [x for x in filtrados if es_serie(x)]
    elif seccion == "peliculas":
        filtrados = [x for x in filtrados if not es_serie(x)]
    elif seccion == "estrenos":
        filtrados = [x for x in filtrados if extraer_anio(x) in (2025, 2026)]
        filtrados.sort(key=lambda x: (1 if extraer_anio(x) == 2025 else 0, x.get("id", 0)), reverse=True)
    elif seccion == "ultimos_agregados":
        filtrados = sorted(filtrados, key=lambda x: x.get("id", 0), reverse=True)

    # 2. Filtro por género específico si se seleccionó
    if genero and genero != "todos" and genero in GENRES_MAP:
        kws = GENRES_MAP[genero]
        filtrados = [x for x in filtrados if any(k in (x.get("titulo", "") + " " + x.get("url", "")).lower() for k in kws)]

        # Si el usuario busca acción, terror, crimen o ciencia ficción, excluir películas puramente infantiles o animadas
        if genero in ["accion", "terror", "crimen-suspenso", "ciencia-ficcion"]:
            filtrados = [x for x in filtrados if not any(k in (x.get("titulo", "") + " " + x.get("url", "")).lower() for k in KEYWORDS_ANIMACION_EXCLUSION)]

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
        "seccion": seccion,
        "genero": genero,
        "items": resultado
    })

TRAILERS_CACHE = {}

@app.route("/api/trailer")
def api_trailer():
    """Devuelve el ID y URL del trailer oficial de YouTube en español latino."""
    query = request.args.get("q", "").strip()
    anio = request.args.get("anio", "").strip()
    if not query:
        return jsonify({"videoId": None, "error": "Query requerido"}), 400

    cache_key = f"{query.lower()}_{anio}"
    if cache_key in TRAILERS_CACHE:
        return jsonify(TRAILERS_CACHE[cache_key])

    q_search = f"{query} {anio} trailer oficial latino" if anio else f"{query} trailer oficial latino"
    yt_url = "https://www.youtube.com/results?search_query=" + urllib.parse.quote(q_search)
    req = urllib.request.Request(
        yt_url,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "es-419,es;q=0.9,en;q=0.8"
        }
    )
    try:
        html = urllib.request.urlopen(req, timeout=4).read().decode("utf-8", errors="ignore")
        vids = list(dict.fromkeys(re.findall(r'\/watch\?v=([a-zA-Z0-9_-]{11})', html)))
        if vids:
            video_id = vids[0]
            res_data = {
                "videoId": video_id,
                "watchUrl": f"https://www.youtube.com/watch?v={video_id}",
                "embedUrl": f"https://www.youtube.com/embed/{video_id}",
                "query": query
            }
            TRAILERS_CACHE[cache_key] = res_data
            return jsonify(res_data)
        else:
            return jsonify({"videoId": None, "error": "No se encontró trailer"})
    except Exception as e:
        return jsonify({"videoId": None, "error": str(e)})

def asegurar_perfil_brave(user_data_dir):
    """Asegura que el perfil de Brave para TV tenga bloqueo estricto de popups y sin bloqueos residuales."""
    try:
        # 1. Limpiar locks residuales si Brave previo fue cerrado o murió
        for lock_file in ["SingletonLock", "SingletonCookie", "SingletonSocket"]:
            lp = os.path.join(user_data_dir, lock_file)
            if os.path.lexists(lp):
                try:
                    os.unlink(lp)
                except Exception:
                    pass

        # 2. Configurar Preferences para bloqueo estricto de popups y anuncios
        default_dir = os.path.join(user_data_dir, "Default")
        os.makedirs(default_dir, exist_ok=True)
        pref_file = os.path.join(default_dir, "Preferences")
        prefs = {}
        if os.path.exists(pref_file):
            try:
                with open(pref_file, "r", encoding="utf-8") as f:
                    prefs = json.load(f)
            except Exception:
                prefs = {}

        profile_sec = prefs.setdefault("profile", {})
        content_settings = profile_sec.setdefault("default_content_setting_values", {})
        content_settings["popups"] = 2  # 2 = Blocked
        content_settings["notifications"] = 2
        content_settings["automatic_downloads"] = 2

        with open(pref_file, "w", encoding="utf-8") as f:
            json.dump(prefs, f)
    except Exception as e:
        print(f"[Hydra] Error configurando preferencias de Brave: {e}")

def cerrar_brave():
    """Cierra limpiamente cualquier proceso de Brave en ejecución del reproductor TV."""
    global brave_process
    if brave_process:
        try:
            brave_process.terminate()
        except Exception:
            pass
    try:
        subprocess.run(["pkill", "-f", "tvbox-brave"], check=False)
    except Exception:
        pass
    brave_process = None

def lanzar_brave(url):
    """Lanza Brave Browser en modo TV Kiosk con Hydra TV Shield activo y bloqueo total de popups."""
    global brave_process
    cerrar_brave()

    user_data_dir = os.path.expanduser("~/.config/tvbox-brave")
    asegurar_perfil_brave(user_data_dir)

    extension_dir = os.path.join(BASE_DIR, "hydra-shield")

    cmd = [
        "brave-browser",
        "--ozone-platform=wayland",
        f"--user-data-dir={user_data_dir}",
        f"--load-extension={extension_dir}",
        "--kiosk",
        f"--app={url}",
        "--autoplay-policy=no-user-gesture-required",
        "--no-first-run",
        "--disable-session-crashed-bubble",
        "--no-default-browser-check",
        "--disable-features=Translate,OptimizationHints"
    ]

    env = os.environ.copy()
    env.setdefault("XDG_RUNTIME_DIR", "/run/user/1000")
    env.setdefault("WAYLAND_DISPLAY", "wayland-0")
    env.setdefault("DISPLAY", ":0")
    env.setdefault("DBUS_SESSION_BUS_ADDRESS", "unix:path=/run/user/1000/bus")

    brave_process = subprocess.Popen(cmd, env=env)
    return brave_process

@app.route("/api/detalle/<int:item_id>")
def api_detalle(item_id):
    """Devuelve los detalles de una película o serie, enriqueciendo la sinopsis y backdrop si están disponibles."""
    item = ITEMS_BY_ID.get(item_id)
    if not item:
        return jsonify({"error": "No encontrado"}), 404

    res = formatear_item_api(item)
    sinopsis = item.get("sinopsis") or item.get("descripcion")

    if not sinopsis and item.get("url"):
        cache_key = f"sin_{item_id}"
        if cache_key in SINOPSIS_CACHE:
            sinopsis = SINOPSIS_CACHE[cache_key]
        else:
            try:
                target_url = item.get("url_resuelta", item["url"])
                req = urllib.request.Request(target_url, headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                })
                html = urllib.request.urlopen(req, timeout=3).read().decode("utf-8", errors="ignore")
                m = re.search(r'<meta\s+[^>]*(?:property|name)=["\'](?:og:description|description)["\'][^>]*content=["\']([^"\']+)["\']', html, re.IGNORECASE)
                if not m:
                    m = re.search(r'<meta\s+[^>]*content=["\']([^"\']+)["\'][^>]*(?:property|name)=["\'](?:og:description|description)["\']', html, re.IGNORECASE)
                if m:
                    desc_raw = m.group(1).strip()
                    if len(desc_raw) > 25 and not any(k in desc_raw.lower() for k in ["cuevana", "cinetux", "descargar gratis"]):
                        sinopsis = desc_raw
                        SINOPSIS_CACHE[cache_key] = sinopsis
            except Exception:
                pass

    if not sinopsis:
        cat_txt = f" de {res.get('categoria').capitalize()}" if res.get('categoria') else ""
        sinopsis = f"Disfruta de {res.get('titulo')} ({res.get('anio') or 2026}){cat_txt} en calidad Full HD y audio latino sin cortes ni publicidad, disponible en Hydra TV."

    res["sinopsis"] = sinopsis
    return jsonify(res)

@app.route("/api/reproductor/servidores/<int:item_id>")
def api_reproductor_servidores(item_id):
    """Resuelve en vivo y filtra los mejores servidores funcionales para un título al reproducirlo."""
    global CATALOGO_CACHE, ITEMS_BY_ID
    item = ITEMS_BY_ID.get(item_id)
    if not item:
        for it in CATALOGO_CACHE:
            if it.get("id") == item_id:
                item = it
                break
    if not item:
        return jsonify({"disponible": False, "motivo": "Título no encontrado"}), 404

    resultado = resolver_servidores_inteligente(item, catalogo_cache=CATALOGO_CACHE)
    
    # Si se resolvieron servidores y no estaban en memoria, sincronizar memoria
    if resultado.get("disponible") and resultado.get("servidores"):
        item["url"] = resultado["mejor_url"]
        item["url_resuelta"] = resultado["mejor_url"]
        item["opciones"] = [s["url"] for s in resultado["servidores"]]
        ITEMS_BY_ID[item_id] = item

    return jsonify(resultado)

@app.route("/play_url", methods=["POST"])
def play_url():
    """Reproduce cualquier URL directa (como un trailer de YouTube) en pantalla completa en Brave en la TV."""
    datos = request.get_json(silent=True) or {}
    url = datos.get("url", "").strip()
    titulo = datos.get("titulo", "Video")
    if not url:
        return jsonify({"error": "URL requerida"}), 400

    try:
        lanzar_brave(url)
        return jsonify({"status": "ok", "url": url, "titulo": titulo})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/reproductor")
def reproductor():
    stream_url = request.args.get("url", "")
    titulo = request.args.get("titulo", "Reproductor")
    return render_template("player.html", stream_url=stream_url, titulo=titulo)

@app.route("/play/<int:canal_id>", methods=["POST"])
def play(canal_id):
    canal = ITEMS_BY_ID.get(canal_id)

    if not canal:
        return jsonify({"error": "Canal o película no encontrado"}), 404

    datos = request.get_json(silent=True) or {}
    opcion_url = datos.get("opcion_url")

    target_url = opcion_url or canal.get("url_resuelta") or canal.get("url", "")
    if target_url.endswith(".html/"):
        target_url = target_url[:-1]
    elif target_url.endswith(".php/"):
        target_url = target_url[:-1]

    if not target_url:
        return jsonify({"error": "El título no tiene URL válida"}), 400

    if canal.get("tipo") == "directo":
        final_launch_url = f"http://localhost:5000/reproductor?url={target_url}&titulo={canal.get('titulo_limpio', canal.get('titulo', ''))}"
    else:
        final_launch_url = target_url

    try:
        lanzar_brave(final_launch_url)
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
    try:
        cerrar_brave()
        return jsonify({"status": "detenido"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# =========================================================================
# RUTAS DE ADMINISTRACIÓN, MODIFICACIÓN Y REPORTE DE ERRORES
# =========================================================================

@app.route("/api/admin/reportes", methods=["GET"])
def api_admin_reportes():
    """Devuelve la lista de reportes registrados (más recientes primero)."""
    reportes = cargar_json_seguro(REPORTES_FILE, [])
    reportes.sort(key=lambda r: r.get("fecha", ""), reverse=True)
    return jsonify({
        "status": "ok",
        "total": len(reportes),
        "reportes": reportes
    })

@app.route("/api/admin/reportar", methods=["POST"])
def api_admin_reportar():
    """Registra un reporte de video / servidor caído o con problemas."""
    data = request.get_json(silent=True) or {}
    item_id = data.get("item_id")
    titulo = data.get("titulo", "Desconocido")
    motivo = data.get("motivo", "No especificado")
    detalle = data.get("detalle", "")
    servidor = data.get("servidor", "")
    url_activa = data.get("url_activa", "")

    if not item_id and not url_activa:
        return jsonify({"error": "Identificador o URL requerida"}), 400

    reportes = cargar_json_seguro(REPORTES_FILE, [])
    nuevo_reporte = {
        "id": f"rep_{int(time.time() * 1000)}",
        "item_id": item_id,
        "titulo": titulo,
        "servidor": servidor,
        "url_activa": url_activa,
        "motivo": motivo,
        "detalle": detalle,
        "fecha": datetime.datetime.now().astimezone().isoformat(),
        "estado": "pendiente"
    }
    reportes.append(nuevo_reporte)
    guardar_json_seguro(REPORTES_FILE, reportes)
    print(f"[Admin] Reporte registrado para '{titulo}' ({motivo})")
    return jsonify({"status": "ok", "success": True, "reporte": nuevo_reporte})

@app.route("/api/admin/reportes/<report_id>/resolver", methods=["POST"])
def api_admin_resolver_reporte(report_id):
    """Marca un reporte como resuelto."""
    reportes = cargar_json_seguro(REPORTES_FILE, [])
    encontrado = False
    for r in reportes:
        if r.get("id") == report_id:
            r["estado"] = "resuelto"
            r["fecha_resolucion"] = datetime.datetime.now().astimezone().isoformat()
            encontrado = True
            break
    if encontrado:
        guardar_json_seguro(REPORTES_FILE, reportes)
        return jsonify({"status": "ok", "message": "Reporte marcado como resuelto"})
    return jsonify({"error": "Reporte no encontrado"}), 404

@app.route("/api/admin/reportes/<report_id>", methods=["DELETE"])
def api_admin_eliminar_reporte(report_id):
    """Elimina un reporte del archivo."""
    reportes = cargar_json_seguro(REPORTES_FILE, [])
    filtrados = [r for r in reportes if r.get("id") != report_id]
    guardar_json_seguro(REPORTES_FILE, filtrados)
    return jsonify({"status": "ok", "eliminados": len(reportes) - len(filtrados)})

@app.route("/api/admin/modificar_item", methods=["POST"])
def api_admin_modificar_item():
    """Permite al administrador cambiar la URL, servidores u opciones de un título."""
    global CATALOGO_CACHE, ITEMS_BY_ID
    data = request.get_json(silent=True) or {}
    item_id = data.get("item_id")
    if not item_id or int(item_id) not in ITEMS_BY_ID:
        return jsonify({"error": "Título no encontrado"}), 404

    item_id = int(item_id)
    nueva_url = data.get("url", "").strip()
    nuevas_opciones = data.get("opciones")
    nuevo_titulo = data.get("titulo", "").strip()

    item = ITEMS_BY_ID[item_id]
    if nueva_url:
        item["url"] = nueva_url
        item["url_resuelta"] = nueva_url
    if nuevas_opciones is not None and isinstance(nuevas_opciones, list):
        item["opciones"] = [u.strip() for u in nuevas_opciones if u.strip()]
        if item["opciones"] and not nueva_url:
            item["url"] = item["opciones"][0]
            item["url_resuelta"] = item["opciones"][0]
    if nuevo_titulo:
        item["titulo"] = nuevo_titulo
        item["titulo_limpio"] = nuevo_titulo

    # Persistir en modificaciones.json
    modificaciones = cargar_json_seguro(MODIFICACIONES_FILE, {})
    modificaciones[str(item_id)] = {
        "item_id": item_id,
        "titulo": item.get("titulo"),
        "url": item.get("url"),
        "opciones": item.get("opciones", []),
        "fecha": datetime.datetime.now().astimezone().isoformat()
    }
    guardar_json_seguro(MODIFICACIONES_FILE, modificaciones)
    construir_home_feed()
    print(f"[Admin] Título modificado: {item.get('titulo')} -> {item.get('url')}")
    return jsonify({"status": "ok", "success": True, "item": formatear_item_api(item)})

@app.route("/api/admin/verificar_servidores", methods=["POST"])
def api_admin_verificar_servidores():
    """Audita en vivo el estado HTTP y disponibilidad de todos los servidores y cyberlockers de un título."""
    global CATALOGO_CACHE, ITEMS_BY_ID
    data = request.get_json(silent=True) or {}
    item_id = data.get("item_id")
    if not item_id:
        return jsonify({"error": "Falta item_id"}), 400
        
    try:
        item_id = int(item_id)
    except (ValueError, TypeError):
        return jsonify({"error": "ID inválido"}), 400
        
    item = ITEMS_BY_ID.get(item_id)
    if not item:
        for it in CATALOGO_CACHE:
            if it.get("id") == item_id:
                item = it
                break
                
    if not item:
        return jsonify({"error": "Título no encontrado"}), 404
        
    reporte = auditar_item_completo(item, catalogo_cache=CATALOGO_CACHE)
    return jsonify({
        "status": "ok",
        "success": True,
        "reporte": reporte
    })

@app.route("/api/admin/purgar_servidores", methods=["POST"])
def api_admin_purgar_servidores():
    """Purga automáticamente servidores caídos (404/rotos) y deja únicamente opciones vivas y funcionando."""
    global CATALOGO_CACHE, ITEMS_BY_ID
    data = request.get_json(silent=True) or {}
    item_id = data.get("item_id")
    if not item_id:
        return jsonify({"error": "Falta item_id"}), 400
        
    try:
        item_id = int(item_id)
    except (ValueError, TypeError):
        return jsonify({"error": "ID inválido"}), 400
        
    item = ITEMS_BY_ID.get(item_id)
    if not item:
        return jsonify({"error": "Título no encontrado"}), 404
        
    reporte = data.get("reporte")
    if not reporte:
        reporte = auditar_item_completo(item, catalogo_cache=CATALOGO_CACHE)
        
    ok, msg, item_actualizado = purgar_item_a_vivos(item, reporte, guardar_en_archivo=True)
    if not ok:
        return jsonify({"status": "error", "message": msg}), 400
        
    ITEMS_BY_ID[item_id] = item_actualizado
    for i, it in enumerate(CATALOGO_CACHE):
        if it.get("id") == item_id:
            CATALOGO_CACHE[i] = item_actualizado
            break
            
    construir_home_feed()
    print(f"[Admin Purgador] Item {item_id} ({item.get('titulo')}) purgado: {msg}")
    return jsonify({
        "status": "ok",
        "success": True,
        "message": msg,
        "item": formatear_item_api(item_actualizado),
        "reporte": reporte
    })

@app.route("/api/admin/eliminar_item", methods=["POST"])
def api_admin_eliminar_item():
    """Elimina/oculta un título del catálogo de forma permanente."""
    global CATALOGO_CACHE, ITEMS_BY_ID
    data = request.get_json(silent=True) or {}
    item_id = data.get("item_id")
    motivo = data.get("motivo", "Eliminado por administrador")

    if not item_id or int(item_id) not in ITEMS_BY_ID:
        return jsonify({"error": "Título no encontrado"}), 404

    item_id = int(item_id)
    item = ITEMS_BY_ID[item_id]
    titulo = item.get("titulo", "Título")
    url = item.get("url", "")

    # 1. Guardar en eliminados.json
    eliminados = cargar_json_seguro(ELIMINADOS_FILE, {})
    eliminados[str(item_id)] = {
        "item_id": item_id,
        "titulo": titulo,
        "url": url,
        "motivo": motivo,
        "fecha": datetime.datetime.now().astimezone().isoformat()
    }
    guardar_json_seguro(ELIMINADOS_FILE, eliminados)

    # 2. Registrar en reportes.json para auditoría
    reportes = cargar_json_seguro(REPORTES_FILE, [])
    reportes.append({
        "id": f"rep_{int(time.time() * 1000)}",
        "item_id": item_id,
        "titulo": titulo,
        "url_activa": url,
        "servidor": "N/A",
        "motivo": f"[ELIMINADO] {motivo}",
        "detalle": "Título removido del catálogo permanentemente.",
        "fecha": datetime.datetime.now().astimezone().isoformat(),
        "estado": "eliminado"
    })
    guardar_json_seguro(REPORTES_FILE, reportes)

    # 3. Remover de la memoria activa
    del ITEMS_BY_ID[item_id]
    CATALOGO_CACHE = [x for x in CATALOGO_CACHE if x.get("id") != item_id]
    construir_home_feed()

    print(f"[Admin] Título eliminado del catálogo: {titulo} (ID {item_id})")
    return jsonify({"status": "ok", "success": True, "message": f"'{titulo}' eliminado del catálogo"})

# ==============================================================================
# AUDITOR DE CATÁLOGO EN SEGUNDO PLANO
# ==============================================================================
AUDITOR_THREAD = None
AUDITOR_ESTADO_FILE = os.path.join(BASE_DIR, "auditoria_estado.json")
AUDITOR_STOP_FLAG = os.path.join(BASE_DIR, "auditoria_stop.flag")

from auditor_catalogo import AuditorCatalogo

def _ejecutar_auditor_hilo(workers=4, auto_clean=False, resume=True, limit=None):
    global AUDITOR_THREAD
    try:
        auditor = AuditorCatalogo(workers=workers, auto_clean=auto_clean, resume=resume, limit=limit)
        auditor.ejecutar()
    except Exception as e:
        print(f"[Auditor Hilo] Error en ejecución: {e}")
    finally:
        AUDITOR_THREAD = None

@app.route("/api/admin/auditor/estado")
def api_admin_auditor_estado():
    """Consulta el progreso en tiempo real de la auditoría de catálogo."""
    global AUDITOR_THREAD
    estado = cargar_json_seguro(AUDITOR_ESTADO_FILE, {
        "activo": False,
        "indice_actual": 0,
        "total": 0,
        "porcentaje": 0,
        "vivos": 0,
        "caidos": 0,
        "ultimo_titulo": "",
        "ultimo_resultado": "",
        "auto_clean": False
    })
    hilo_vivo = AUDITOR_THREAD is not None and AUDITOR_THREAD.is_alive()
    estado["activo"] = hilo_vivo
    return jsonify(estado)

@app.route("/api/admin/auditor/iniciar", methods=["POST"])
def api_admin_auditor_iniciar():
    """Inicia el auditor de catálogo en un hilo en segundo plano."""
    global AUDITOR_THREAD
    if AUDITOR_THREAD and AUDITOR_THREAD.is_alive():
        return jsonify({"status": "warning", "message": "El auditor ya se encuentra en ejecución"}), 400

    data = request.get_json(silent=True) or {}
    workers = int(data.get("workers", 4))
    auto_clean = bool(data.get("auto_clean", False))
    resume = bool(data.get("resume", True))
    limit = data.get("limit")
    if limit is not None:
        limit = int(limit)

    if os.path.exists(AUDITOR_STOP_FLAG):
        try: os.remove(AUDITOR_STOP_FLAG)
        except Exception: pass

    AUDITOR_THREAD = threading.Thread(
        target=_ejecutar_auditor_hilo,
        kwargs={"workers": workers, "auto_clean": auto_clean, "resume": resume, "limit": limit},
        daemon=True
    )
    AUDITOR_THREAD.start()
    return jsonify({
        "status": "ok",
        "message": f"Auditor iniciado ({workers} hilos, auto-purga: {'ON' if auto_clean else 'OFF'})"
    })

@app.route("/api/admin/auditor/detener", methods=["POST"])
def api_admin_auditor_detener():
    """Envía la señal de detención al auditor en segundo plano."""
    try:
        with open(AUDITOR_STOP_FLAG, "w", encoding="utf-8") as f:
            f.write("stop")
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

    return jsonify({"status": "ok", "message": "Señal de detención enviada al auditor."})

@app.route("/api/admin/auditor/reiniciar", methods=["POST"])
def api_admin_auditor_reiniciar():
    """Reinicia las estadísticas de auditoría a cero."""
    global AUDITOR_THREAD
    if AUDITOR_THREAD and AUDITOR_THREAD.is_alive():
        return jsonify({"status": "error", "message": "Detenga la auditoría antes de reiniciar el progreso"}), 400

    estado_inicial = {
        "activo": False,
        "indice_actual": 0,
        "total": len(CATALOGO_CACHE),
        "porcentaje": 0,
        "vivos": 0,
        "caidos": 0,
        "ultimo_titulo": "",
        "ultimo_resultado": "",
        "auto_clean": False,
        "actualizado": datetime.datetime.now().astimezone().isoformat()
    }
    guardar_json_seguro(AUDITOR_ESTADO_FILE, estado_inicial)
    return jsonify({"status": "ok", "message": "Progreso de auditoría reiniciado a 0."})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
