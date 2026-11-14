"""Construye el panel maestro: una fila por sección electoral 2024 con
votos armonizados 2012-2024, composición sobre lista nominal e
indicadores censales 2020.
"""
import os

import geopandas as gpd
import numpy as np
import pandas as pd

BASE = os.path.join(os.path.dirname(__file__), "..")
UPLOAD = os.path.join(BASE, "data", "upload")
PROCESSED = os.path.join(BASE, "data", "processed")

PARTIDOS = ["pan", "pri", "prd", "pvem", "pt", "mc", "morena", "otros"]
ANIOS = [2012, 2015, 2018, 2021, 2024]


def cargar_maestro():
    g = gpd.read_file(os.path.join(UPLOAD, "mgsan_ext", "SECCION.shp"))
    g["ent"] = g["ENTIDAD"].astype(int).astype(str).str.zfill(2)
    g["mun"] = g["MUNICIPIO"].astype(int).astype(str).str.zfill(3)
    g["distrito_f"] = g["DISTRITO_F"].astype(int).astype(str).str.zfill(2)
    g["id"] = g["ent"] + g["SECCION"].astype(int).astype(str).str.zfill(4)
    return g[["id", "ent", "mun", "distrito_f", "geometry"]]


def main():
    print("[1/3] Cartografía maestra...")
    master = cargar_maestro()
    panel = master.drop(columns="geometry").set_index("id")

    print("[2/3] Votos armonizados por año...")
    for anio in ANIOS:
        v = pd.read_csv(
            os.path.join(PROCESSED, f"votos_seccion_{anio}_m2024.csv"),
            index_col=0)
        v.index = v.index.astype(str).str.zfill(6)
        total_partidos = v[PARTIDOS].sum(axis=1)
        for p in PARTIDOS:
            panel[f"{p}_{anio}"] = v[p]
            panel[f"pct_{p}_{anio}"] = 100 * v[p] / \
                total_partidos.replace(0, np.nan)
        panel[f"nulos_{anio}"] = v["nulos"]
        panel[f"total_votos_{anio}"] = v["total_votos"]
        panel[f"lista_nominal_{anio}"] = v["lista_nominal"]
        panel[f"participacion_{anio}"] = 100 * v["total_votos"] / \
            v["lista_nominal"].replace(0, np.nan)

    print("[3/3] Indicadores censales 2020...")
    ind = pd.read_csv(os.path.join(PROCESSED, "censo2020_seccion_indicadores_total.csv"),
                      index_col=0)
    ind.index = ind.index.astype(str).str.zfill(6)
    panel = panel.join(ind)

    panel.to_csv(os.path.join(PROCESSED, "panel_secciones.csv"),
                 encoding="utf-8")
    master.merge(panel.reset_index(), on="id").to_file(
        os.path.join(PROCESSED, "panel_secciones.gpkg"), driver="GPKG")
    print(f"Panel: {panel.shape[0]:,} secciones x {panel.shape[1]} columnas")
    print("Listo.")


if __name__ == "__main__":
    main()
