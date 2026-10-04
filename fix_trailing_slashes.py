import json

with open('catalogo_maestro.json', 'r', encoding='utf-8') as f:
    catalog = json.load(f)

fixed_count = 0
for item in catalog:
    url = item.get('url', '')
    if url.endswith('.html/'):
        item['url'] = url[:-1]
        fixed_count += 1
    elif url.endswith('.php/'):
        item['url'] = url[:-1]
        fixed_count += 1

    # También en opciones
    new_opts = []
    for opt in item.get('opciones', []):
        if opt.endswith('.html/'):
            new_opts.append(opt[:-1])
        elif opt.endswith('.php/'):
            new_opts.append(opt[:-1])
        else:
            new_opts.append(opt)
    item['opciones'] = new_opts

print(f"Total URLs corregidas (eliminado slash tras extensión): {fixed_count}")

with open('catalogo_maestro.json', 'w', encoding='utf-8') as f:
    json.dump(catalog, f, ensure_ascii=False, indent=2)

print("catalogo_maestro.json actualizado exitosamente.")
