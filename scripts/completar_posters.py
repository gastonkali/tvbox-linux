import asyncio
import json
import os
import re
import urllib.parse
from playwright.async_api import async_playwright

CATALOGO_MAESTRO_PATHS = [
    os.path.join(os.path.dirname(__file__), "catalogo_maestro.json"),
    os.path.abspath(r"..\tvbox-linux\catalogo_maestro.json")
]

def buscar_ruta_brave():
    rutas = [
        r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
        r"C:\Program Files (x86)\BraveSoftware\Brave-Browser\Application\brave.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\BraveSoftware\Brave-Browser\Application\brave.exe"),
        os.path.expandvars(r"%PROGRAMFILES%\BraveSoftware\Brave-Browser\Application\brave.exe")
    ]
    for r in rutas:
        if os.path.exists(r):
            return r
    return None

async def extraer_poster_de_pagina(page, url):
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=25000)
        await page.wait_for_timeout(1000)

        poster = await page.evaluate('''() => {
            // 1. Meta og:image (Estándar de calidad en páginas de películas)
            const ogImg = document.querySelector('meta[property="og:image"]');
            if (ogImg && ogImg.content && ogImg.content.startsWith('http') && !ogImg.content.includes('logo') && !ogImg.content.includes('default')) {
                return ogImg.content;
            }

            // 2. Selectores habituales de póster
            const selectores = [
                '.poster img', '.s-cover img', '.entry-thumb img', 
                '.movie-poster img', 'article img', '.thumb img',
                'img[src*="tmdb.org"]', 'img[data-src*="tmdb.org"]'
            ];
            for (let sel of selectores) {
                const img = document.querySelector(sel);
                if (img) {
                    const src = img.currentSrc || img.getAttribute('data-src') || img.src;
                    if (src && src.startsWith('http') && !src.includes('logo')) {
                        return src;
                    }
                }
            }
            return '';
        }''')
        return poster or ""
    except Exception as e:
        return ""

async def main():
    print("=" * 65)
    print("EXTRACTOR DE PÓSTERES RESTANTES CON BRAVE Y PLAYWRIGHT")
    print("=" * 65)

    ruta_maestro = CATALOGO_MAESTRO_PATHS[0]
    if not os.path.exists(ruta_maestro):
        print(f"❌ No se encontró: {ruta_maestro}")
        return

    with open(ruta_maestro, "r", encoding="utf-8") as f:
        catalogo = json.load(f)

    # Filtrar elementos sin póster
    pendientes = [item for item in catalogo if not item.get("poster") or not item.get("poster").strip()]
    total_pendientes = len(pendientes)
    print(f"🎯 Títulos pendientes de póster: {total_pendientes} de {len(catalogo)}")

    if total_pendientes == 0:
        print("🎉 ¡Todos los títulos ya tienen póster!")
        return

    ruta_brave = buscar_ruta_brave()
    if not ruta_brave:
        print("❌ No se encontró Brave Browser instalado en las rutas estándar.")
        return

    perfil_dir = os.path.join(os.path.dirname(__file__), "perfil_brave_scraper")
    print(f"🚀 Iniciando Brave con perfil: {perfil_dir}")

    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir=perfil_dir,
            executable_path=ruta_brave,
            headless=False,
            args=["--disable-blink-features=AutomationControlled", "--start-minimized"],
            locale="es-ES"
        )
        page = context.pages[0] if context.pages else await context.new_page()

        exitos = 0
        fallidos = 0

        for idx, item in enumerate(pendientes, 1):
            url = item.get("url", "")
            titulo = item.get("titulo", "")
            print(f"[{idx}/{total_pendientes}] Extrayendo póster para: {titulo[:35]}...", end=" ", flush=True)

            poster_encontrado = await extraer_poster_de_pagina(page, url)

            if poster_encontrado:
                item["poster"] = poster_encontrado
                exitos += 1
                print(f"✅ OK")
            else:
                fallidos += 1
                print(f"⚠️ No detectado")

            # Guardar progreso cada 15 elementos para no perder avances
            if idx % 15 == 0 or idx == total_pendientes:
                for path in CATALOGO_MAESTRO_PATHS:
                    if os.path.exists(os.path.dirname(path)):
                        with open(path, "w", encoding="utf-8") as f:
                            json.dump(catalogo, f, ensure_ascii=False, indent=2)
                print(f"   💾 Progreso guardado ({exitos} recuperados hasta ahora).")

        await context.close()

    print("\n" + "=" * 65)
    print("✨ EXTRACCIÓN FINALIZADA")
    print(f"• Pósteres recuperados : {exitos}")
    print(f"• No encontrados       : {fallidos}")
    print("=" * 65)

if __name__ == "__main__":
    asyncio.run(main())
