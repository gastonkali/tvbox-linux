#!/usr/bin/env python3
"""
Auditor Autónomo e Independiente de Catálogo para Hydra TV.
Recorre los títulos de catalogo_maestro.json, audita y valida sus servidores y cyberlockers,
descarta enlaces caídos, guarda los servidores funcionales en modificaciones.json,
y opcionalmente purga automáticamente los títulos sin video funcional hacia eliminados.json.
"""

import os
import sys
import json
import time
import argparse
import signal
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CATALOGO_MAESTRO_FILE = os.path.join(BASE_DIR, "catalogo_maestro.json")
MODIFICACIONES_FILE = os.path.join(BASE_DIR, "modificaciones.json")
ELIMINADOS_FILE = os.path.join(BASE_DIR, "eliminados.json")
ESTADO_FILE = os.path.join(BASE_DIR, "auditoria_estado.json")
REPORTE_FILE = os.path.join(BASE_DIR, "auditoria_reporte.json")
STOP_FLAG_FILE = os.path.join(BASE_DIR, "auditoria_stop.flag")

if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

# Importar motor de verificación
from verificador_cyberlockers import (
    resolver_servidores_inteligente,
    verificar_url_cyberlocker,
    extraer_cyberlockers_poseidon,
    verificar_conexion_internet
)

_stop_solicitado = False

def manejar_interrupcion(sig, frame):
    global _stop_solicitado
    print("\n[Auditor] Detención solicitada por el usuario... Terminando tareas en curso.")
    _stop_solicitado = True

signal.signal(signal.SIGINT, manejar_interrupcion)
signal.signal(signal.SIGTERM, manejar_interrupcion)

def cargar_json(ruta, por_defecto):
    if not os.path.exists(ruta):
        return por_defecto
    try:
        with open(ruta, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return por_defecto

def guardar_json(ruta, datos):
    tmp = ruta + ".tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(datos, f, ensure_ascii=False, indent=2)
        os.replace(tmp, ruta)
    except Exception as e:
        print(f"[Auditor] Error guardando {ruta}: {e}")

class AuditorCatalogo:
    def __init__(self, workers=4, auto_clean=False, resume=True, limit=None, delay=0.2):
        self.workers = max(1, min(12, workers))
        self.auto_clean = auto_clean
        self.resume = resume
        self.limit = limit
        self.delay = delay
        
        self.catalogo = []
        self.modificaciones = {}
        self.eliminados = {}
        self.reporte_caidos = []
        self.estado = {}
        
        self.lock = threading.Lock()
        self.activo = False
        self.fallos_red_consecutivos = 0

    def inicializar(self):
        print("[Auditor] Cargando catálogo maestro y estados previos...")
        self.catalogo = cargar_json(CATALOGO_MAESTRO_FILE, [])
        self.modificaciones = cargar_json(MODIFICACIONES_FILE, {})
        self.eliminados = cargar_json(ELIMINADOS_FILE, {})
        self.reporte_caidos = cargar_json(REPORTE_FILE, [])
        self.estado = cargar_json(ESTADO_FILE, {})

        if os.path.exists(STOP_FLAG_FILE):
            try: os.remove(STOP_FLAG_FILE)
            except Exception: pass

    def esperar_conexion_internet(self):
        """
        Circuito de seguridad: si la conexión a internet cae, pausa de inmediato la auditoría
        y espera a que regrese antes de auditar ningún título. Previene falsas eliminaciones masivas.
        """
        if not verificar_conexion_internet():
            with self.lock:
                self.estado["pausado_por_red"] = True
                self.estado["ultimo_resultado"] = "⚠️ En pausa (esperando reconexión a Internet...)"
                guardar_json(ESTADO_FILE, self.estado)

            print("\n" + "="*70)
            print("🚨 [CIRCUITO DE SEGURIDAD] ¡CONEXIÓN A INTERNET INTERRUMPIDA!")
            print("   Pausando auditoría inmediatamente...")
            print("   Ningún título será eliminado ni marcado como caído durante el corte.")
            print("="*70 + "\n")

            tiempo_espera = 0
            while not verificar_conexion_internet():
                if _stop_solicitado or os.path.exists(STOP_FLAG_FILE):
                    return False
                time.sleep(5)
                tiempo_espera += 5
                if tiempo_espera % 30 == 0:
                    print(f"[Auditor] Aún esperando reconexión a Internet ({tiempo_espera}s transcurridos)...")

            # Doble confirmación de estabilidad
            time.sleep(3)
            if not verificar_conexion_internet():
                return self.esperar_conexion_internet()

            print("\n" + "="*70)
            print("✅ [CIRCUITO DE SEGURIDAD] ¡CONEXIÓN A INTERNET RESTABLECIDA!")
            print("   Reanudando auditoría de forma segura.")
            print("="*70 + "\n")

            with self.lock:
                self.fallos_red_consecutivos = 0
                self.estado["pausado_por_red"] = False
                guardar_json(ESTADO_FILE, self.estado)
            return True
        return True

    def guardar_progreso(self, indice, total, titulo, resultado_txt, es_vivo):
        with self.lock:
            vivos = self.estado.get("vivos", 0) + (1 if es_vivo is True else 0)
            caidos = self.estado.get("caidos", 0) + (1 if es_vivo is False else 0)
            
            self.estado = {
                "activo": True,
                "pausado_por_red": False,
                "indice_actual": indice,
                "total": total,
                "porcentaje": round((indice / total) * 100, 2) if total > 0 else 0,
                "vivos": vivos,
                "caidos": caidos,
                "ultimo_titulo": titulo,
                "ultimo_resultado": resultado_txt,
                "auto_clean": self.auto_clean,
                "actualizado": time.strftime("%Y-%m-%dT%H:%M:%S%z")
            }
            guardar_json(ESTADO_FILE, self.estado)

    def auditar_item(self, item, indice, total):
        global _stop_solicitado
        if _stop_solicitado or os.path.exists(STOP_FLAG_FILE):
            return None

        # Circuito de seguridad: esperar si no hay internet activo
        if not self.esperar_conexion_internet():
            return None

        item_id = item.get("id")
        titulo = item.get("titulo", "Sin título")

        # Verificar si ya estaba resuelto y vigente en modificaciones
        id_str = str(item_id)
        if id_str in self.modificaciones:
            mod = self.modificaciones[id_str]
            if mod.get("servidores_detalle") and len(mod["servidores_detalle"]) > 0:
                res_txt = f"{len(mod['servidores_detalle'])} servidor(es) en caché"
                self.guardar_progreso(indice, total, titulo, res_txt, True)
                return {"id": item_id, "titulo": titulo, "vivo": True, "detalle": res_txt}

        # Resolver exhaustivamente con el motor inteligente
        resultado = resolver_servidores_inteligente(item, catalogo_cache=self.catalogo)
        
        if resultado.get("disponible") and resultado.get("servidores"):
            with self.lock:
                self.fallos_red_consecutivos = 0
            srvs = resultado["servidores"]
            res_txt = f"{srvs[0]['nombre']} (+{len(srvs)-1} alt)" if len(srvs) > 1 else srvs[0]['nombre']
            
            with self.lock:
                self.modificaciones[id_str] = {
                    "item_id": item_id,
                    "titulo": titulo,
                    "url": resultado["mejor_url"],
                    "opciones": [s["url"] for s in srvs],
                    "servidores_detalle": srvs,
                    "fecha": time.strftime("%Y-%m-%dT%H:%M:%S%z")
                }
                guardar_json(MODIFICACIONES_FILE, self.modificaciones)
                
            self.guardar_progreso(indice, total, titulo, res_txt, True)
            return {"id": item_id, "titulo": titulo, "vivo": True, "detalle": res_txt}
        else:
            motivo = resultado.get("motivo", "Sin servidores disponibles")
            es_error_red = resultado.get("error_red", False)

            # Si es un fallo de red o socket/DNS, NO marcar como caído, NUNCA auto-limpiar
            if es_error_red or any(k in motivo.lower() for k in ['conexión fallida', 'error de red', 'timeout', 'name resolution', 'unreachable']):
                with self.lock:
                    self.fallos_red_consecutivos += 1
                    disparar_pausa = self.fallos_red_consecutivos >= 3

                if disparar_pausa:
                    self.esperar_conexion_internet()

                return {
                    "id": item_id,
                    "titulo": titulo,
                    "vivo": None,
                    "detalle": f"⚠️ Error temporal de red ({motivo})",
                    "error_red": True
                }

            # Enlace realmente caído comprobado con internet activo
            with self.lock:
                self.fallos_red_consecutivos = 0
                self.reporte_caidos.append({
                    "id": item_id,
                    "titulo": titulo,
                    "url": item.get("url"),
                    "motivo": motivo,
                    "fecha": time.strftime("%Y-%m-%dT%H:%M:%S%z")
                })
                guardar_json(REPORTE_FILE, self.reporte_caidos)

                if self.auto_clean and not es_error_red and str(item_id) not in self.eliminados:
                    self.eliminados[str(item_id)] = {
                        "item_id": item_id,
                        "titulo": titulo,
                        "url": item.get("url"),
                        "motivo": motivo,
                        "fecha": time.strftime("%Y-%m-%dT%H:%M:%S%z")
                    }
                    guardar_json(ELIMINADOS_FILE, self.eliminados)

            self.guardar_progreso(indice, total, titulo, f"❌ Caído ({motivo})", False)
            return {"id": item_id, "titulo": titulo, "vivo": False, "detalle": motivo}

    def ejecutar(self):
        global _stop_solicitado
        self.inicializar()
        total_catalogo = len(self.catalogo)
        if total_catalogo == 0:
            print("[Auditor] Catálogo vacío. Nada para auditar.")
            return

        eliminados_set = {int(k) for k in self.eliminados.keys() if str(k).isdigit()} if isinstance(self.eliminados, dict) else set(self.eliminados)
        vistos_ids = set()
        items_a_revisar = []
        for it in self.catalogo:
            iid = it.get("id")
            if iid and iid not in eliminados_set and iid not in vistos_ids:
                vistos_ids.add(iid)
                items_a_revisar.append(it)

        # Determinar índice de partida
        inicio_idx = 0
        if self.resume and self.estado.get("indice_actual"):
            inicio_idx = self.estado.get("indice_actual", 0)
            if inicio_idx >= len(items_a_revisar):
                print(f"[Auditor] Catálogo ya auditado por completo ({inicio_idx}/{len(items_a_revisar)}). Reiniciando...")
                inicio_idx = 0
                self.estado["vivos"] = 0
                self.estado["caidos"] = 0

        items_pendientes = items_a_revisar[inicio_idx:]
        if self.limit:
            items_pendientes = items_pendientes[:self.limit]

        total_a_procesar = len(items_a_revisar)
        print(f"[Auditor] Iniciando auditoría: {len(items_pendientes)} títulos pendientes de {total_a_procesar} consolidados.")
        print(f"[Auditor] Concurrencia: {self.workers} hilos | Auto-Purga: {'Activada' if self.auto_clean else 'Desactivada'}")

        self.activo = True
        self.estado["activo"] = True
        self.estado["pausado_por_red"] = False
        self.estado["inicio"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
        guardar_json(ESTADO_FILE, self.estado)

        procesados_sesion = 0
        t0 = time.time()

        try:
            with ThreadPoolExecutor(max_workers=self.workers) as executor:
                item_iter = enumerate(items_pendientes)
                futures = {}
                max_inflight = self.workers * 2

                def rellenar_cola():
                    nonlocal item_iter
                    while len(futures) < max_inflight and not _stop_solicitado and not os.path.exists(STOP_FLAG_FILE):
                        try:
                            offset, item = next(item_iter)
                            idx_global = inicio_idx + offset + 1
                            f = executor.submit(self.auditar_item, item, idx_global, total_a_procesar)
                            futures[f] = (item, idx_global)
                        except StopIteration:
                            break

                rellenar_cola()

                while futures:
                    if _stop_solicitado or os.path.exists(STOP_FLAG_FILE):
                        print("[Auditor] Detención solicitada. Cancelando tareas pendientes...")
                        executor.shutdown(wait=False, cancel_futures=True)
                        break

                    import concurrent.futures as cf
                    done, _ = cf.wait(futures.keys(), return_when=cf.FIRST_COMPLETED)
                    for f in done:
                        item, idx_global = futures.pop(f)
                        try:
                            res = f.result()
                            if res:
                                if res.get("vivo") is None:
                                    print(f"[{idx_global}/{total_a_procesar}] ⚠️ {res['titulo'][:36]} -> {res['detalle']}")
                                else:
                                    procesados_sesion += 1
                                    simbolo = "[OK]" if res["vivo"] else "[X]"
                                    pct = round((idx_global / total_a_procesar) * 100, 1)
                                    print(f"[{idx_global}/{total_a_procesar}] ({pct}%) {simbolo} {res['titulo'][:36]} -> {res['detalle']}")
                                    
                                    if procesados_sesion % 500 == 0:
                                        import gc
                                        gc.collect()
                        except Exception as err:
                            print(f"[{idx_global}] Error auditando {item.get('titulo')}: {err}")

                    rellenar_cola()
                    if self.delay > 0:
                        time.sleep(self.delay)

        finally:
            self.activo = False
            self.estado["activo"] = False
            self.estado["fin"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
            guardar_json(ESTADO_FILE, self.estado)
            
            if os.path.exists(STOP_FLAG_FILE):
                try: os.remove(STOP_FLAG_FILE)
                except Exception: pass

            dt = round(time.time() - t0, 1)
            print(f"\n[Auditor] Finalizado. Procesados en esta sesión: {procesados_sesion} títulos en {dt}s.")
            print(f"[Auditor] Totales globales: {self.estado.get('vivos', 0)} vivos, {self.estado.get('caidos', 0)} caídos.")

def main():
    parser = argparse.ArgumentParser(description="Auditor Autónomo de Catálogo Hydra TV")
    parser.add_argument("--workers", "-w", type=int, default=4, help="Número de hilos concurrentes (default: 4)")
    parser.add_argument("--auto-clean", "-c", action="store_true", help="Ocultar automáticamente títulos sin video agregándolos a eliminados.json")
    parser.add_argument("--no-resume", action="store_true", help="Iniciar desde el principio sin reanudar progreso previo")
    parser.add_argument("--limit", "-l", type=int, default=None, help="Límite de títulos a revisar en esta ejecución")
    parser.add_argument("--delay", "-d", type=float, default=0.2, help="Pausa entre peticiones (segundos)")
    
    args = parser.parse_args()
    
    auditor = AuditorCatalogo(
        workers=args.workers,
        auto_clean=args.auto_clean,
        resume=not args.no_resume,
        limit=args.limit,
        delay=args.delay
    )
    auditor.ejecutar()

if __name__ == "__main__":
    main()
