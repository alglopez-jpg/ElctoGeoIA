"""Genera los mapas PNG del pronóstico 2027 por sección (un panel por figura).

Lee data/processed/pronostico_2027_seccion.csv y produce, por escenario:
- % de voto oficialista sobre voto emitido
- partido más votado por sección
- participación pronosticada (% de la lista nominal)
"""
import os

import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd

BASE = os.path.join(os.path.dirname(__file__), "..")
UPLOAD = os.path.join(BASE, "data", "upload")
PROCESSED = os.path.join(BASE, "data", "processed")
FIGURAS = os.path.join(BASE, "figuras")

PARTIDOS = ["pan", "pri", "prd", "pvem", "pt", "mc", "morena", "otros"]
ESCENARIOS = ["inercia_intermedia", "oficialismo_resistente",
              "oposicion_recupera"]


def cargar():
    pron = pd.read_csv(os.path.join(PROCESSED, "pronostico_2027_seccion.csv"),
                       dtype={"id": str}).set_index("id")
    sec = gpd.read_file(os.path.join(UPLOAD, "mgsan_ext", "SECCION.shp"))
    sec["id"] = sec["ENTIDAD"].astype(int).astype(str).str.zfill(2) + \
        sec["SECCION"].astype(int).astype(str).str.zfill(4)
    g = sec.merge(pron, on="id", how="inner")
    g["geometry"] = g.geometry.simplify(0.001, preserve_topology=True)
    for esc in ESCENARIOS:
        emitido = 1 - g[f"{esc}_abstencion"] - g[f"{esc}_nulos"]
        g[f"{esc}_oficialismo"] = 100 * (
            g[f"{esc}_morena"] + g[f"{esc}_pvem"] + g[f"{esc}_pt"]) / \
            emitido.replace(0, float("nan"))
        g[f"{esc}_participacion"] = 100 * emitido
        cols = [f"{esc}_{p}" for p in PARTIDOS]
        g[f"{esc}_ganador"] = g[cols].idxmax(axis=1).str.replace(f"{esc}_", "")
    return g


def mapa(g, columna, titulo, archivo, cmap=None, categorico=False):
    fig, ax = plt.subplots(figsize=(10, 7))
    if categorico:
        g.plot(column=columna, ax=ax, categorical=True, legend=True,
               cmap=cmap or "tab10",
               legend_kwds={"loc": "lower left", "fontsize": 7},
               missing_kwds={"color": "lightgrey"})
    else:
        g.plot(column=columna, ax=ax, legend=True, cmap=cmap or "RdYlBu_r",
               legend_kwds={"shrink": 0.6},
               missing_kwds={"color": "lightgrey"})
    ax.set_title(titulo, fontsize=12)
    ax.set_axis_off()
    plt.savefig(os.path.join(FIGURAS, archivo), dpi=110, bbox_inches="tight")
    plt.close("all")
    print(f"ok: {archivo}", flush=True)


def main():
    g = cargar()
    print(f"{len(g):,} secciones con pronóstico", flush=True)
    for esc in ESCENARIOS:
        bonito = esc.replace("_", " ")
        mapa(g, f"{esc}_oficialismo",
             f"Pronóstico 2027 ({bonito}): % oficialista del voto emitido",
             f"pronostico_2027_{esc}_oficialismo.png")
        mapa(g, f"{esc}_ganador",
             f"Pronóstico 2027 ({bonito}): partido más votado por sección",
             f"pronostico_2027_{esc}_ganador.png", categorico=True)
        mapa(g, f"{esc}_participacion",
             f"Pronóstico 2027 ({bonito}): participación % de la lista nominal",
             f"pronostico_2027_{esc}_participacion.png", cmap="viridis")


if __name__ == "__main__":
    main()
