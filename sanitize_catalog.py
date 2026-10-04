import json
import re
from urllib.parse import urlparse
from collections import Counter

BLOCKED_DOMAINS = {
    'www.gnularetro.cc', 'gnularetro.cc',
    'www.series24.sbs', 'series24.sbs',
    'dah.dramafuntv.com',
    'ultrapeli.com'
}

def clean_title(t):
    if not t:
        return ''
    # remove text in parentheses (e.g. (2026), (Serie 2022))
    t = re.sub(r'\(.*?\)', '', t)
    # remove alternative titles after pipe or slash
    t = re.sub(r'\|.*', '', t)
    t = re.sub(r'/.*', '', t)
    # remove non-alphanumeric
    t = re.sub(r'[^a-zA-Z0-9\s]', '', t)
    return ' '.join(t.lower().split())

def is_clean_url(url):
    if not url:
        return False
    netloc = urlparse(url).netloc
    return netloc not in BLOCKED_DOMAINS

def main():
    with open('catalogo_maestro.json', 'r', encoding='utf-8') as f:
        catalog = json.load(f)

    print(f"Catálogo original: {len(catalog)} títulos.")

    # 1. Construir un pool de títulos limpios para mapeo
    clean_pool = {}
    for item in catalog:
        if is_clean_url(item.get('url')):
            norm = clean_title(item.get('titulo'))
            if norm and norm not in clean_pool:
                clean_pool[norm] = item

    print(f"Títulos limpios únicos para referencia: {len(clean_pool)}")

    sanitized = []
    recovered_count = 0
    discarded_blocked_count = 0

    for item in catalog:
        url = item.get('url', '')
        
        if is_clean_url(url):
            # Limpiar opciones bloqueadas para no tener basura
            clean_opts = [opt for opt in item.get('opciones', []) if is_clean_url(opt)]
            if url not in clean_opts:
                clean_opts.insert(0, url)
            item['opciones'] = clean_opts
            sanitized.append(item)
        else:
            # Buscar si tiene alternativa limpia en sus propias opciones
            alt_clean = None
            for opt in item.get('opciones', []):
                if is_clean_url(opt):
                    alt_clean = opt
                    break

            if alt_clean:
                item['url'] = alt_clean
                item['opciones'] = [opt for opt in item.get('opciones', []) if is_clean_url(opt)]
                sanitized.append(item)
                recovered_count += 1
            else:
                # Buscar si el título coincide con un título limpio en clean_pool
                norm = clean_title(item.get('titulo'))
                if norm in clean_pool:
                    match_item = clean_pool[norm]
                    item['url'] = match_item['url']
                    item['opciones'] = [opt for opt in match_item.get('opciones', []) if is_clean_url(opt)]
                    sanitized.append(item)
                    recovered_count += 1
                else:
                    # Título solo existente en sitio con Cloudflare Turnstile
                    # En una TV Smart esto es 100% inútil/roto. Descartar.
                    discarded_blocked_count += 1

    # Asegurar que ID 12019 (Resident Evil 2002) esté impecable
    for item in sanitized:
        if item.get('id') == 12019:
            item['url'] = "https://www.poseidonhd2.co/pelicula/1576/resident-evil-el-huesped-maldito/"
            item['opciones'] = [
                "https://www.poseidonhd2.co/pelicula/1576/resident-evil-el-huesped-maldito/",
                "https://pelicinehd.com/movies/resident-evil/"
            ]

    print(f"Recuperados vía opciones o catálogo limpio: {recovered_count}")
    print(f"Descartados por bloqueo Cloudflare permanente: {discarded_blocked_count}")
    print(f"Catálogo sanitizado final: {len(sanitized)} títulos 100% LIBRES DE CLOUDFLARE.")

    # Guardar catálogo sanitizado
    with open('catalogo_maestro.json', 'w', encoding='utf-8') as f:
        json.dump(sanitized, f, ensure_ascii=False, indent=2)

    print("catalogo_maestro.json guardado con éxito.")

if __name__ == '__main__':
    main()
