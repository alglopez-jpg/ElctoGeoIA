"""Herramientas del agente experto ElctoGeoIA.

Cada función recibe argumentos simples (lo que el LLM extrae de la pregunta)
y devuelve un diccionario con cifras listas para redactar la respuesta.

Estas funciones NO dependen de ningún LLM: también se pueden usar directo
desde Python o desde la consola de demostración (agente/orquestador.py --demo).
"""
from __future__ import annotations

import pandas as pd

from . import panel as P

ESCENARIOS = ["inercia_intermedia", "oficialismo_resistente", "oposicion_recupera"]
TIPOS_MAPA_TOOL = ["tipologia", "ganador", "oficialismo", "participacion", "margen"]


def _resumen_territorio(df: pd.DataFrame, nombre: str) -> dict:
    """Cifras núcleo de un territorio (ya filtrado a sus secciones)."""
    if df.empty:
        return {"error": f"Sin secciones para {nombre}"}
    # NOTA de unidades: las columnas pct_*, participacion_*, margen_2024 y
    # volatilidad_18_24 YA están en porcentaje (0-100). Las columnas de
    # escenarios 2027 sí son fracciones (0-1) y se multiplican por 100.
    out = {
        "territorio": nombre,
        "secciones": int(len(df)),
        "lista_nominal_2024": int(df["lista_nominal_2024"].sum()),
        "participacion_2024": round(float(df["participacion_2024"].mean()), 1),
        "participacion_2021": round(float(df["participacion_2021"].mean()), 1),
    }
    # voto 2024 agregado (participación ponderada simple por sección),
    # ordenado de mayor a menor para que quede claro quién ganó
    voto24 = {p: round(float(df[f"pct_{p}_2024"].mean()), 1) for p in P.PARTIDOS}
    ganador = max(voto24, key=voto24.get)
    out["voto_2024_por_partido_pct"] = dict(sorted(voto24.items(), key=lambda kv: -kv[1]))
    out["ganador_2024"] = ganador
    out["nota_ganador"] = (f"El partido con más voto en 2024 fue {ganador.upper()} "
                            f"({voto24[ganador]}%); los demás van detrás en el orden listado.")
    # tipología
    tip = df["tipologia_2024"].value_counts().to_dict()
    out["tipologia"] = {k: int(v) for k, v in tip.items()}
    # categoría SAR (desviación vs perfil socioeconómico, notebook 07)
    if "categoria_sar" in df:
        sar = df["categoria_sar"].value_counts().to_dict()
        out["desviacion_sar"] = {k: int(v) for k, v in sar.items()
                                if k != "sin_sar"}
    out["margen_2024"] = {"valor_promedio_pts": round(float(df["margen_2024"].mean()), 1),
                           "definicion": "diferencia en puntos entre el 1er y 2do lugar de la sección"}
    out["volatilidad_18_24"] = {"valor_promedio_pts": round(float(df["volatilidad_18_24"].mean()), 1),
                                 "definicion": "cambio absoluto combinado PAN+Morena+MC entre 2018 y 2024, en puntos"}
    # socioeconomía (ya en porcentaje), con etiquetas explícitas
    etiquetas = {"pct_rural": "poblacion_rural_pct",
                 "pct_sin_basica": "sin_educacion_basica_pct",
                 "pct_auto": "hogares_con_auto_pct",
                 "pct_internet": "hogares_con_internet_pct",
                 "pct_60ymas": "poblacion_60ymas_pct",
                 "pct_18a24": "poblacion_18a24_pct"}
    for v, nueva in etiquetas.items():
        if v in df:
            out[nueva] = round(float(df[v].mean()), 1)
    return out


def radiografia_municipio(nombre_municipio: str, estado: str | None = None) -> dict:
    """Radiografía electoral de un municipio.

    Args:
        nombre_municipio: nombre del municipio, ej. "León"
        estado: nombre del estado o clave INEGI de 2 dígitos, ej. "Guanajuato" o "11"
    """
    hits = P.buscar_municipio(nombre_municipio, estado)
    if not hits:
        return {"error": f"No encontré el municipio '{nombre_municipio}'"
                + (f" en {estado}" if estado else "") + ". ¿Puedes verificar el nombre?"}
    if len(hits) > 1 and estado is None:
        return {"ambiguo": True, "coincidencias": hits,
                "mensaje": "Hay varios municipios con ese nombre; dime el estado o elige uno."}
    h = hits[0]
    df = P.secciones_de_municipio(h["ent"], h["mun"])
    out = _resumen_territorio(df, f"{h['nom_mun']}, {h['nom_ent']}")
    out["claves"] = h
    return out


def radiografia_distrito(estado: str, distrito: int | str) -> dict:
    """Radiografía electoral de un distrito federal (marco 2024).

    Args:
        estado: nombre del estado o clave INEGI de 2 dígitos
        distrito: número de distrito federal (1-300)
    """
    cat = P.cargar_catalogo()
    ent = P._resolver_estado(str(estado))
    if ent is None:
        return {"error": f"No encontré el estado '{estado}'."}
    nom_ent = cat.loc[cat["ent"] == ent, "nom_ent"].iloc[0]
    df = P.secciones_de_distrito(ent, distrito)
    out = _resumen_territorio(df, f"Distrito {int(distrito)}, {nom_ent}")
    if "error" not in out:
        out["claves"] = {"ent": ent, "distrito_f": str(distrito).zfill(2), "nom_ent": nom_ent}
    return out


def pronostico_2027(nombre_municipio: str, estado: str | None = None,
                    escenario: str = "inercia_intermedia") -> dict:
    """Pronóstico 2027 por escenario para un municipio.

    Args:
        escenario: uno de 'inercia_intermedia', 'oficialismo_resistente', 'oposicion_recupera'
    """
    if escenario not in ESCENARIOS:
        return {"error": f"Escenario inválido. Opciones: {ESCENARIOS}"}
    hits = P.buscar_municipio(nombre_municipio, estado)
    if not hits:
        return {"error": f"No encontré el municipio '{nombre_municipio}'."}
    if len(hits) > 1 and estado is None:
        return {"ambiguo": True, "coincidencias": hits}
    h = hits[0]
    df = P.secciones_de_municipio(h["ent"], h["mun"])
    if df.empty:
        return {"error": "Sin secciones para ese municipio."}
    # nombres completos para que el LLM no confunda siglas (PRI vs PRD)
    nombres = {"pan": "PAN", "pri": "PRI", "prd": "PRD", "pvem": "PVEM (Verde)",
               "pt": "PT", "mc": "MC (Movimiento Ciudadano)",
               "morena": "Morena", "otros": "otros", "nulos": "votos nulos",
               "abstencion": "abstencion"}
    out = {"territorio": f"{h['nom_mun']}, {h['nom_ent']}", "escenario": escenario,
           "unidad": "porcentaje sobre lista nominal (partidos + nulos + abstencion suman 100)",
           "advertencia": "Estas cifras son porcentaje de la lista nominal, NO del "
                          "voto emitido. Para % del voto emitido, excluye la abstencion "
                          "y renormaliza. Presenta siempre la abstencion por separado."}
    for partido in P.PARTIDOS + ["nulos", "abstencion"]:
        col = f"{escenario}_{partido}"
        if col in df:
            out[nombres[partido]] = round(float(df[col].mean()) * 100, 1)  # fracción -> %
    # secciones competitivas bajo el escenario
    oficialismo = P.PARTIDOS[:6] + ["otros"]
    cols_of = [f"{escenario}_{p}" for p in oficialismo if f"{escenario}_{p}" in df]
    morena = df[f"{escenario}_morena"]
    resto = df[cols_of].sum(axis=1)
    margen = (morena - resto).abs()
    out["secciones_competitivas_2027"] = int((margen < 0.05).sum())
    return out


def secciones_prioritarias(nombre_municipio: str, estado: str | None = None, top: int = 10) -> dict:
    """Ranking de secciones donde la campaña rinde más: competitivas y con mayor lista nominal."""
    hits = P.buscar_municipio(nombre_municipio, estado)
    if not hits:
        return {"error": f"No encontré el municipio '{nombre_municipio}'."}
    if len(hits) > 1 and estado is None:
        return {"ambiguo": True, "coincidencias": hits}
    h = hits[0]
    df = P.secciones_de_municipio(h["ent"], h["mun"])
    if df.empty:
        return {"error": "Sin secciones."}
    d = df[df["tipologia_2024"] == "competitiva"].copy()
    if d.empty:
        d = df.nsmallest(20, "margen_2024").copy()
    d = d.nlargest(int(top), "lista_nominal_2024")
    cols = ["id", "lista_nominal_2024", "pct_morena_2024", "margen_2024", "volatilidad_18_24"]
    res = d[cols].copy()
    for c in ["pct_morena_2024", "margen_2024", "volatilidad_18_24"]:
        res[c] = res[c].round(1)  # ya en porcentaje
    res = res.rename(columns={"id": "seccion", "lista_nominal_2024": "lista_nominal",
                              "pct_morena_2024": "pct_morena_2024", "margen_2024": "margen_pts",
                              "volatilidad_18_24": "volatilidad_pts"})
    return {
        "territorio": f"{h['nom_mun']}, {h['nom_ent']}",
        "criterio": "tipología competitiva 2024, ordenadas por lista nominal",
        "secciones": res.to_dict("records"),
    }


def generar_mapa(nombre_municipio: str | None = None, estado: str | None = None,
                 tipo: str = "tipologia", escenario: str = "inercia_intermedia",
                 distrito: int | None = None) -> dict:
    """Genera un mapa PNG del territorio consultado y devuelve la ruta del archivo.

    Args:
        tipo: 'tipologia', 'ganador', 'oficialismo', 'participacion' o 'margen'
        escenario: solo para tipo='oficialismo': 'inercia_intermedia',
                   'oficialismo_resistente' u 'oposicion_recupera'
        distrito: si se da, mapea ese distrito federal (con estado)
    """
    from . import mapas
    return mapas.generar_mapa(nombre_municipio=nombre_municipio, estado=estado,
                              tipo=tipo, escenario=escenario, distrito=distrito)


# Registro de herramientas para el orquestador (esquema tipo Ollama/OpenAI tools)
ESPECIFICACIONES = [
    {
        "type": "function",
        "function": {
            "name": "radiografia_municipio",
            "description": "Radiografía electoral de un municipio: tipología de secciones, voto por partido 2024, participación, márgenes, volatilidad y socioeconomía.",
            "parameters": {
                "type": "object",
                "properties": {
                    "nombre_municipio": {"type": "string", "description": "Nombre del municipio, ej. 'León'"},
                    "estado": {"type": "string", "description": "Estado o clave INEGI de 2 dígitos. Opcional pero recomendado si el nombre es ambiguo."},
                },
                "required": ["nombre_municipio"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "radiografia_distrito",
            "description": "Radiografía electoral de un distrito federal (marco 2024).",
            "parameters": {
                "type": "object",
                "properties": {
                    "estado": {"type": "string", "description": "Estado o clave INEGI de 2 dígitos"},
                    "distrito": {"type": "integer", "description": "Número de distrito federal"},
                },
                "required": ["estado", "distrito"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "pronostico_2027",
            "description": "Pronóstico 2027 para un municipio bajo un escenario (inercia_intermedia, oficialismo_resistente u oposicion_recupera).",
            "parameters": {
                "type": "object",
                "properties": {
                    "nombre_municipio": {"type": "string"},
                    "estado": {"type": "string"},
                    "escenario": {"type": "string", "enum": ESCENARIOS},
                    "distrito": {"type": "integer", "description": "Distrito federal (requiere estado); opcional"},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "secciones_prioritarias",
            "description": "Ranking de secciones competitivas con mayor lista nominal, donde cada peso de campaña rinde más.",
            "parameters": {
                "type": "object",
                "properties": {
                    "nombre_municipio": {"type": "string"},
                    "estado": {"type": "string"},
                    "top": {"type": "integer", "description": "Cuántas secciones devolver (default 10)"},
                },
                "required": ["nombre_municipio"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "generar_mapa",
            "description": "Genera un mapa PNG del territorio consultado y devuelve la ruta del archivo. Úsala cuando el usuario pida un mapa o cuando la respuesta se beneficie de visualización.",
            "parameters": {
                "type": "object",
                "properties": {
                    "nombre_municipio": {"type": "string"},
                    "estado": {"type": "string"},
                    "tipo": {"type": "string", "enum": TIPOS_MAPA_TOOL,
                              "description": "tipologia | ganador | oficialismo | participacion | margen"},
                    "escenario": {"type": "string", "enum": ESCENARIOS},
                    "distrito": {"type": "integer", "description": "Distrito federal (requiere estado); opcional"},
                },
                "required": [],
            },
        },
    },
]

FUNCIONES = {
    "radiografia_municipio": radiografia_municipio,
    "radiografia_distrito": radiografia_distrito,
    "pronostico_2027": pronostico_2027,
    "secciones_prioritarias": secciones_prioritarias,
    "generar_mapa": generar_mapa,
}
