import json

def clean_catalog():
    with open('catalogo_maestro.json', 'r', encoding='utf-8') as f:
        items = json.load(f)

    print(f"Total inicial: {len(items)}")

    cleaned = []
    removed = []

    for it in items:
        titulo = str(it.get('titulo', '')).strip()
        url = str(it.get('url', '')).strip().lower()
        opts = it.get('opciones', [])

        # Detectar basura evidente de raspado
        es_basura = False
        if any(titulo.lower().startswith(p) for p in ['cam 20', 'hd 20', 'dvd 20', 'ts 20']):
            es_basura = True
        elif 'ingrese a su cuenta' in titulo.lower():
            es_basura = True
        elif '/genre/' in url or '/movies/page/' in url or '/category/' in url or '/series/pagina/' in url:
            es_basura = True
        elif len(opts) > 15:
            # Si tiene más de 15 opciones es casi seguro un listado/categoría raspado por error
            es_basura = True
        elif not titulo:
            es_basura = True

        if es_basura:
            removed.append((it.get('id'), titulo, url, len(opts)))
            continue

        # Si las opciones son muchas o contienen URLs repetidas / sospechosas, sanearlas
        if isinstance(opts, list) and len(opts) > 1:
            # Eliminar duplicados manteniendo orden
            seen = set()
            clean_opts = []
            for o in opts:
                o_str = str(o).strip()
                if o_str and o_str not in seen:
                    seen.add(o_str)
                    clean_opts.append(o_str)
            
            # Si hay más de 5 servidores, limitar o dejar solo la URL principal si las otras parecen enlaces a otras pelis
            if len(clean_opts) > 6:
                clean_opts = clean_opts[:5]
            it['opciones'] = clean_opts

        cleaned.append(it)

    print(f"Eliminados: {len(removed)}")
    for r in removed:
        print(f"  Removido ID {r[0]}: {r[1]} ({r[2]}) - {r[3]} opts")

    print(f"Total final: {len(cleaned)}")

    with open('catalogo_maestro.json', 'w', encoding='utf-8') as f:
        json.dump(cleaned, f, ensure_ascii=False, indent=2)
    print("Guardado con éxito catalogo_maestro.json")

if __name__ == '__main__':
    clean_catalog()
