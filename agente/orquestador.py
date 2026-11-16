"""Orquestador del agente experto ElctoGeoIA.

Conecta un modelo local (Ollama) con las herramientas del proyecto.
Requiere Ollama corriendo en http://localhost:11434 (por defecto).

Uso:
    python -m agente.orquestador                  # chat con el modelo local
    python -m agente.orquestador --modelo qwen2.5:7b
    python -m agente.orquestador --demo           # modo sin LLM: prueba las herramientas
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request

from .herramientas import FUNCIONES, ESPECIFICACIONES

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")

SISTEMA = """Eres ElctoGeoIA, un analista experto en geografía electoral mexicana.
Tienes acceso a un panel validado de 71,541 secciones electorales con 5 elecciones federales
(2012-2024), indicadores censales 2020 a nivel sección, tipología de secciones y pronósticos
2027 por escenario.

REGLAS:
1. Para cualquier pregunta sobre un municipio o distrito específico, USA LAS HERRAMIENTAS
   (radiografia_municipio, radiografia_distrito, pronostico_2027, secciones_prioritarias).
   NUNCA inventes cifras: si la herramienta devuelve un error o ambigüedad, dilo al usuario.
2. Si un nombre de municipio es ambiguo (hay varios con ese nombre), pide el estado.
   Al llamar a las herramientas, pasa el estado con su NOMBRE COMPLETO tal como lo
   escribió el usuario (ej. 'Guanajuato', 'Querétaro'), nunca abreviaturas como 'GJ'.
3. Responde en español, claro y directo, como un analista político que explica a un
   cliente: primero la conclusión, luego las cifras de apoyo.
4. Cita siempre el año y el escenario de las cifras que uses.
5. FIDELIDAD ABSOLUTA A LAS HERRAMIENTAS:
   - Usa EXCLUSIVAMENTE los números que devuelven las herramientas. Nunca inventes,
     calcules de memoria ni agregues cifras que no aparezcan en el resultado.
   - El ganador lo dice el campo 'ganador_2024' (y el orden del dict
     'voto_2024_por_partido_pct' es de mayor a menor): NO lo deduzcas tú.
   - Usa las definiciones incluidas en los resultados: 'margen_2024' es la diferencia
     entre 1er y 2do lugar, NO participación; 'volatilidad_18_24' es cambio entre años.
   - Si un dato no viene en el resultado, di que no está disponible; no lo estimes.
   - Menciona TODAS las cifras de partidos que devuelva la herramienta (no omitas
     ninguna); usa los nombres de partido tal como vienen en el resultado.
   - Los pronósticos 2027 son % sobre lista nominal: presenta la abstención por
     separado y aclara que no son % del voto emitido.
   - NUNCA expandas siglas de partidos desde tu memoria: si el resultado trae un
     campo 'nombres_completos', usa ESE mapeo. Si solo hay siglas, deja las siglas.
   - No calcules derivados que la herramienta ya entrega (p. ej.
     'participacion_esperada_pct'); usa el valor provisto.
5. Sé honesto con la incertidumbre: los pronósticos 2027 son escenarios, no certezas;
   la validación (backtest) mostró que el swing uniforme es la mejor referencia.
"""


def _chat(mensajes: list, modelo: str, herramientas: list | None = None) -> dict:
    """Llamada a la API de Ollama (/api/chat) con soporte de tools."""
    cuerpo = {"model": modelo, "messages": mensajes, "stream": False}
    if herramientas:
        cuerpo["tools"] = herramientas
    req = urllib.request.Request(
        OLLAMA_URL.rstrip("/") + "/api/chat",
        data=json.dumps(cuerpo).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=300) as r:
        return json.loads(r.read().decode("utf-8"))


def ollama_activo() -> bool:
    try:
        with urllib.request.urlopen(OLLAMA_URL.rstrip("/") + "/api/tags", timeout=3) as r:
            return True
    except Exception:
        return False


def ejecutar_herramienta(nombre: str, args: dict) -> dict:
    fn = FUNCIONES.get(nombre)
    if fn is None:
        return {"error": f"Herramienta desconocida: {nombre}"}
    try:
        return fn(**args)
    except Exception as e:  # el agente debe fallar con gracia
        return {"error": f"{type(e).__name__}: {e}"}


def bucle_chat(modelo: str):
    print(f"ElctoGeoIA · agente experto · modelo: {modelo}")
    print("Escribe tu consulta (o 'salir' para terminar).\n")
    mensajes = [{"role": "system", "content": SISTEMA}]
    while True:
        try:
            texto = input("Tú > ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not texto:
            continue
        if texto.lower() in ("salir", "exit", "quit"):
            break
        mensajes.append({"role": "user", "content": texto})
        # bucle de herramientas: el modelo puede pedir varias en secuencia
        for _ in range(5):
            resp = _chat(mensajes, modelo, ESPECIFICACIONES)
            msg = resp.get("message", {})
            llamadas = msg.get("tool_calls") or []
            if not llamadas:
                contenido = msg.get("content", "").strip()
                print(f"\nElctoGeoIA > {contenido}\n")
                mensajes.append({"role": "assistant", "content": contenido})
                break
            mensajes.append(msg)
            for lc in llamadas:
                fn = lc.get("function", {})
                nombre = fn.get("name", "")
                args_crudos = fn.get("arguments", {})
                # Ollama puede devolver arguments como dict ya procesado
                # o como texto JSON, según versión del modelo/plantilla
                if isinstance(args_crudos, dict):
                    args = args_crudos
                else:
                    try:
                        args = json.loads(args_crudos or "{}")
                    except (json.JSONDecodeError, TypeError):
                        args = {}
                print(f"  [herramienta] {nombre}({args})")
                resultado = ejecutar_herramienta(nombre, args)
                mensajes.append({"role": "tool", "content": json.dumps(resultado, ensure_ascii=False)})
        else:
            print("  (límite de herramientas por turno alcanzado)")
            break


def modo_demo():
    """Prueba las herramientas sin LLM: útil para verificar la instalación."""
    print("Modo demostración (sin LLM). Probando herramientas:\n")
    pruebas = [
        ("radiografia_municipio", {"nombre_municipio": "León", "estado": "Guanajuato"}),
        ("pronostico_2027", {"nombre_municipio": "León", "estado": "Guanajuato"}),
        ("secciones_prioritarias", {"nombre_municipio": "León", "estado": "Guanajuato", "top": 5}),
        ("radiografia_distrito", {"estado": "Guanajuato", "distrito": 4}),
    ]
    for nombre, args in pruebas:
        print(f"--- {nombre}({args})")
        res = ejecutar_herramienta(nombre, args)
        print(json.dumps(res, ensure_ascii=False, indent=2)[:2000])
        print()


def main():
    ap = argparse.ArgumentParser(description="Agente experto ElctoGeoIA")
    ap.add_argument("--modelo", default=os.environ.get("AGENTE_MODELO", "qwen2.5:7b"))
    ap.add_argument("--demo", action="store_true", help="modo sin LLM: prueba de herramientas")
    args = ap.parse_args()
    if args.demo:
        modo_demo()
        return
    if not ollama_activo():
        print("No se detectó Ollama en", OLLAMA_URL)
        print("Instálalo desde https://ollama.com/download y ejecuta: ollama pull", args.modelo)
        print("Mientras tanto puedes probar las herramientas con: python -m agente.orquestador --demo")
        sys.exit(1)
    bucle_chat(args.modelo)


if __name__ == "__main__":
    main()
