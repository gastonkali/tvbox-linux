"""
Verificador y Purgador Automático de Servidores y Cyberlockers para Hydra TV.
Verifica códigos HTTP 200 y descarta enlaces caídos (404, eliminados, rotos).
"""

import urllib.request
import urllib.error
import re
import json
import os
import sys
import time
import concurrent.futures

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CATALOGO_MAESTRO_FILE = os.path.join(BASE_DIR, "catalogo_maestro.json")
MODIFICACIONES_FILE = os.path.join(BASE_DIR, "modificaciones.json")

HEADERS_STD = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8'
}

DEAD_KEYWORDS = [
    'video not found', 'file was deleted', 'file not found', 'has been removed',
    'video was removed', 'file has been expired', 'video deleted', '404 not found',
    'deleted for copyright', 'borrado por derechos', 'archivo no encontrado',
    'no se encuentra el video', 'el archivo ha sido eliminado', 'error 404'
]

def verificar_url_cyberlocker(embed_url, timeout=5):
    """
    Verifica si una URL de cyberlocker (voe, doodstream, streamtape, waaw, etc.) está viva.
    Devuelve un diccionario con { 'alive': bool, 'status_code': int, 'motivo': str, 'tiempo_ms': int }
    """
    t0 = time.time()
    try:
        req = urllib.request.Request(embed_url, headers=HEADERS_STD)
        resp = urllib.request.urlopen(req, timeout=timeout)
        code = resp.getcode()
        
        # Leer primeros 8KB para detectar mensajes de archivo borrado
        content = resp.read(8192).decode('utf-8', errors='ignore').lower()
        t_ms = int((time.time() - t0) * 1000)
        
        for kw in DEAD_KEYWORDS:
            if kw in content:
                return {
                    'alive': False,
                    'status_code': code,
                    'motivo': f'Archivo eliminado ({kw})',
                    'tiempo_ms': t_ms
                }
                
        return {
            'alive': True,
            'status_code': code,
            'motivo': '200 OK',
            'tiempo_ms': t_ms
        }
    except urllib.error.HTTPError as he:
        t_ms = int((time.time() - t0) * 1000)
        return {
            'alive': False,
            'status_code': he.code,
            'motivo': f'HTTP Error {he.code}',
            'tiempo_ms': t_ms
        }
    except urllib.error.URLError as ue:
        t_ms = int((time.time() - t0) * 1000)
        return {
            'alive': False,
            'status_code': 0,
            'motivo': f'Conexión fallida ({ue.reason})',
            'tiempo_ms': t_ms
        }
    except Exception as e:
        t_ms = int((time.time() - t0) * 1000)
        return {
            'alive': False,
            'status_code': 0,
            'motivo': f'Error ({str(e)})',
            'tiempo_ms': t_ms
        }

def extraer_cyberlockers_poseidon(page_url, timeout=6):
    """
    Extrae la lista completa de opciones y servidores de una página de PoseidonHD (__NEXT_DATA__).
    """
    try:
        req = urllib.request.Request(page_url, headers=HEADERS_STD)
        html = urllib.request.urlopen(req, timeout=timeout).read().decode('utf-8', errors='ignore')
        
        m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html)
        if not m:
            return []
            
        data = json.loads(m.group(1))
        movie = data.get('props', {}).get('pageProps', {}).get('thisMovie') or \
                data.get('props', {}).get('pageProps', {}).get('thisSerie') or {}
                
        videos = movie.get('videos', {})
        enlaces_encontrados = []
        
        for idioma, servers in videos.items():
            if not isinstance(servers, list):
                continue
            for s in servers:
                locker = s.get('cyberlocker', 'reproductor')
                player_url = s.get('result', '')
                calidad = s.get('quality', 'HD')
                if player_url:
                    enlaces_encontrados.append({
                        'idioma': idioma,
                        'locker': locker,
                        'calidad': calidad,
                        'player_url': player_url,
                        'fuente': 'poseidon'
                    })
                    
        return enlaces_encontrados
    except Exception as e:
        print(f"[Verificador] Error extrayendo PoseidonHD {page_url}: {e}")
        return []

def resolver_enlace_destino_player(player_url, timeout=5):
    """
    Dada una URL intermedia tipo player.php?h=..., extrae el embed real de cyberlocker.
    """
    try:
        req = urllib.request.Request(player_url, headers=HEADERS_STD)
        html = urllib.request.urlopen(req, timeout=timeout).read().decode('utf-8', errors='ignore')
        m = re.search(r"var\s+url\s*=\s*['\"]([^'\"]+)['\"]", html)
        if m:
            return m.group(1)
        m2 = re.search(r"<iframe[^>]*src=['\"]([^'\"]+)['\"]", html, re.I)
        if m2:
            return m2.group(1)
        return player_url
    except Exception:
        return player_url

def detectar_nombre_locker(url):
    """Identifica un nombre legible para el cyberlocker o servidor."""
    u = url.lower()
    if 'dood' in u: return 'Doodstream'
    if 'waaw' in u or 'netu' in u: return 'Netu / Waaw'
    if 'voe' in u: return 'VOE'
    if 'streamtape' in u: return 'Streamtape'
    if 'streamwish' in u: return 'Streamwish'
    if 'filelions' in u: return 'Filelions'
    if 'cinemitas' in u: return 'Cinemitas'
    if 'pelicine' in u: return 'Pelicine'
    if 'repelis' in u: return 'Repelis'
    if 'argflix' in u: return 'Argflix'
    return 'Servidor Directo'

def buscar_item_original_catalogo(item_id):
    """Busca el item original en catalogo_maestro.json por ID."""
    if not item_id or not os.path.exists(CATALOGO_MAESTRO_FILE):
        return None
    try:
        with open(CATALOGO_MAESTRO_FILE, 'r', encoding='utf-8') as f:
            catalogo = json.load(f)
        for it in catalogo:
            if it.get('id') == item_id:
                return it
    except Exception as e:
        print(f"[Verificador] Error buscando original: {e}")
    return None

def auditar_item_completo(item, catalogo_cache=None):
    """
    Audita exhaustivamente todas las fuentes de un título en paralelo.
    Devuelve un reporte detallado con los servidores vivos y caídos.
    """
    item_id = item.get('id') or item.get('item_id')
    titulo = item.get('titulo', 'Sin título')
    url_actual = item.get('url', '')
    
    # Buscar original si la URL actual ya es un reproductor resuelto
    url_original_cat = url_actual
    opciones_originales = list(item.get('opciones', []))
    
    item_original = None
    if catalogo_cache:
        for it in catalogo_cache:
            if (it.get('id') or it.get('item_id')) == item_id:
                item_original = it
                break
    if not item_original and item_id:
        item_original = buscar_item_original_catalogo(item_id)
        
    if item_original:
        url_original_cat = item_original.get('url', url_actual)
        for opt in item_original.get('opciones', []):
            if opt not in opciones_originales:
                opciones_originales.append(opt)

    reporte = {
        'id': item_id,
        'titulo': titulo,
        'url_original': url_original_cat,
        'servidores': [],
        'total': 0,
        'vivos': 0,
        'caidos': 0,
        'mejor_opcion': None
    }
    
    candidatos = []
    vistos = set()
    
    # 1. Si la URL original o actual es PoseidonHD (página de película/serie), extraer cyberlockers
    poseidon_page = None
    if 'poseidon' in url_original_cat and ('/pelicula/' in url_original_cat or '/serie/' in url_original_cat):
        poseidon_page = url_original_cat
    elif 'poseidon' in url_actual and ('/pelicula/' in url_actual or '/serie/' in url_actual):
        poseidon_page = url_actual
        
    if poseidon_page:
        poseidon_lockers = extraer_cyberlockers_poseidon(poseidon_page)
        for pl in poseidon_lockers:
            p_url = pl['player_url']
            if p_url and p_url not in vistos:
                vistos.add(p_url)
                candidatos.append({
                    'nombre': f"{pl['locker'].capitalize()} ({pl['idioma'].capitalize()} {pl['calidad']})",
                    'locker': pl['locker'],
                    'url_player': p_url,
                    'fuente': 'poseidon'
                })
                
    # 2. Agregar opciones existentes
    for opt in opciones_originales:
        if opt and opt not in vistos:
            # Si ya extrajimos cyberlockers de Poseidon, ignorar la URL de la página web de Poseidon
            if poseidon_page and ('poseidon' in opt and ('/pelicula/' in opt or '/serie/' in opt)):
                continue
            vistos.add(opt)
            nombre = detectar_nombre_locker(opt)
            candidatos.append({
                'nombre': nombre,
                'locker': 'web',
                'url_player': opt,
                'fuente': 'catalogo'
            })
            
    # 3. Si no hay candidatos, añadir URL actual
    if not candidatos and url_actual:
        candidatos.append({
            'nombre': detectar_nombre_locker(url_actual),
            'locker': 'directo',
            'url_player': url_actual,
            'fuente': 'principal'
        })
        
    # Función auxiliar para chequear un candidato individual
    def chequear_candidato(cand):
        url_player = cand['url_player']
        if 'player.poseidon' in url_player:
            url_embed = resolver_enlace_destino_player(url_player)
        else:
            url_embed = url_player
            
        nombre = cand['nombre']
        if cand['locker'] == 'web' or nombre == 'Servidor Directo':
            nombre_detectado = detectar_nombre_locker(url_embed)
            if nombre_detectado != 'Servidor Directo':
                nombre = nombre_detectado

        check = verificar_url_cyberlocker(url_embed)
        return {
            'nombre': nombre,
            'locker': cand['locker'],
            'url_reproductor': url_player,
            'url_embed_real': url_embed,
            'alive': check['alive'],
            'status_code': check['status_code'],
            'motivo': check['motivo'],
            'tiempo_ms': check['tiempo_ms'],
            'fuente': cand['fuente']
        }
        
    # Ejecutar chequeos concurrentemente en paralelo
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
        resultados = list(executor.map(chequear_candidato, candidatos))
        
    for res in resultados:
        reporte['servidores'].append(res)
        if res['alive']:
            reporte['vivos'] += 1
            if not reporte['mejor_opcion']:
                reporte['mejor_opcion'] = res
        else:
            reporte['caidos'] += 1
            
    reporte['total'] = len(reporte['servidores'])
    return reporte

def purgar_item_a_vivos(item, reporte=None, guardar_en_archivo=True):
    """
    Toma un reporte auditado (o audita al vuelo) y actualiza el item con únicamente los servidores vivos.
    Si hay al menos una opción viva, asigna la mejor opción como URL principal.
    Persiste en modificaciones.json para que tenga efecto inmediato.
    """
    if reporte is None:
        reporte = auditar_item_completo(item)
        
    vivos = [s for s in reporte.get('servidores', []) if s.get('alive')]
    if not vivos:
        return False, "No se encontraron servidores vivos para este título.", item
        
    mejor = vivos[0]
    nuevas_opciones = [v['url_reproductor'] for v in vivos]
    
    item_id = item.get('id') or item.get('item_id')
    item['id'] = item_id
    item['url'] = mejor['url_reproductor']
    item['url_resuelta'] = mejor['url_reproductor']
    item['opciones'] = nuevas_opciones
    
    if guardar_en_archivo and item_id:
        try:
            modificaciones = {}
            if os.path.exists(MODIFICACIONES_FILE):
                with open(MODIFICACIONES_FILE, "r", encoding="utf-8") as f:
                    modificaciones = json.load(f)
                    
            modificaciones[str(item_id)] = {
                "item_id": item_id,
                "titulo": item.get('titulo'),
                "url": mejor['url_reproductor'],
                "opciones": nuevas_opciones,
                "fecha": time.strftime("%Y-%m-%dT%H:%M:%S%z")
            }
            
            with open(MODIFICACIONES_FILE, "w", encoding="utf-8") as f:
                json.dump(modificaciones, f, ensure_ascii=False, indent=2)
                
            print(f"[Purgador] Item {item_id} ({item.get('titulo')}) purgado con éxito. Opciones vivas: {len(nuevas_opciones)}")
            return True, f"Actualizado con {len(nuevas_opciones)} servidores vivos. Principal: {mejor['nombre']}.", item
        except Exception as e:
            return False, f"Error guardando modificaciones: {e}", item
            
    return True, f"Encontrados {len(nuevas_opciones)} servidores vivos.", item

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description="Auditor y Purgador de Servidores")
    parser.add_argument('--id', type=int, help="ID del título en el catálogo")
    parser.add_argument('--query', type=str, help="Nombre del título a buscar")
    parser.add_argument('--purgar', action='store_true', help="Purgar caídos y guardar solo vivos")
    args = parser.parse_args()
    
    if not os.path.exists(CATALOGO_MAESTRO_FILE):
        print("No se encontró catalogo_maestro.json")
        sys.exit(1)
        
    with open(CATALOGO_MAESTRO_FILE, "r", encoding="utf-8") as f:
        catalogo = json.load(f)
        
    target_item = None
    if args.id:
        for it in catalogo:
            if it.get('id') == args.id:
                target_item = it
                break
    elif args.query:
        q = args.query.lower()
        for it in catalogo:
            if q in it.get('titulo', '').lower():
                target_item = it
                break
    else:
        # Por defecto, Battlefield 2025 (ID 25553)
        for it in catalogo:
            if 'battlefield 2025' in it.get('titulo', '').lower():
                target_item = it
                break
                
    if not target_item:
        print("Título no encontrado.")
        sys.exit(1)
        
    print(f"\n==================================================")
    print(f"AUDITANDO SERVIDORES: {target_item.get('titulo')} (ID: {target_item.get('id')})")
    print(f"URL: {target_item.get('url')}")
    print(f"==================================================")
    
    t0 = time.time()
    rep = auditar_item_completo(target_item)
    t_total = time.time() - t0
    
    for idx, s in enumerate(rep['servidores'], 1):
        estado_ico = "[VIVO] " if s['alive'] else "[CAIDO]"
        print(f"[{idx}] {estado_ico} | {s['nombre']:<25} | HTTP {s['status_code']} ({s['motivo']}) | {s['tiempo_ms']}ms")
        print(f"    Reproductor: {s['url_reproductor']}")
        print(f"    Embed Real:  {s['url_embed_real']}\n")
        
    print(f"RESUMEN: {rep['vivos']} vivos de {rep['total']} servidores probados en {t_total:.2f}s.")
    if rep['mejor_opcion']:
        print(f"MEJOR OPCION: {rep['mejor_opcion']['nombre']} ({rep['mejor_opcion']['url_reproductor']})")
        
    if args.purgar and rep['vivos'] > 0:
        ok, msg, _ = purgar_item_a_vivos(target_item, rep, guardar_en_archivo=True)
        print(f"\n[ACCION]: {msg}")
