"""Armonización espacial: lleva los votos por sección de cada año a la
cartografía maestra de secciones del INE 2024 (MGSAN).

Estrategia:
1. Match directo por id (entidad+sección) cuando la sección existe en 2024.
2. Para secciones desaparecidas: crosswalk areal contra la cartografía 2018
   (intersección de polígonos, pesos por área) y realocación de votos.
3. Reporta tasas de cobertura por año.
"""
import glob
import os
import sys

import geopandas as gpd
import pandas as pd

BASE = os.path.join(os.path.dirname(__file__), "..")
UPLOAD = os.path.join(BASE, "data", "upload")
PROCESSED = os.path.join(BASE, "data", "processed")
CRS_MX = "EPSG:6372"


def cargar_maestro():
    g = gpd.read_file(os.path.join(UPLOAD, "mgsan_ext", "SECCION.shp"))
    g["ent"] = g["ENTIDAD"].astype(int).astype(str).str.zfill(2)
    g["sec"] = g["SECCION"].astype(int).astype(str).str.zfill(4)
    g["id"] = g["ent"] + g["sec"]
    return g[["id", "ent", "geometry"]]


def cargar_2018():
    frames = []
    for path in sorted(glob.glob(os.path.join(
            UPLOAD, "seccion2018_estados", "*", "SECCION.shp"))):
        g = gpd.read_file(path)
        g["id"] = g["entidad"].astype(int).astype(str).str.zfill(2) + \
            g["seccion"].astype(int).astype(str).str.zfill(4)
        g = g.to_crs("EPSG:4326")
        frames.append(g[["id", "geometry"]])
    return pd.concat(frames, ignore_index=True)


def crosswalk_areal(g18, master):
    """Pesos de intersección área: sección 2018 -> sección 2024."""
    o = g18.to_crs(CRS_MX)
    n = master.to_crs(CRS_MX)
    ov = gpd.overlay(o, n, how="intersection", keep_geom_type=True)
    ov = ov.rename(columns={"id_1": "id_old", "id_2": "id_new"})
    ov["a"] = ov.geometry.area
    ov["w"] = ov["a"] / ov.groupby("id_old")["a"].transform("sum")
    return ov[["id_old", "id_new", "w"]]


def realocar(votos, xw):
    cols = [c for c in votos.columns]
    m = xw.merge(votos, left_on="id_old", right_index=True)
    m[cols] = m[cols].mul(m["w"], axis=0)
    return m.groupby("id_new")[cols].sum()


def main():
    print("[1/3] Cargando cartografías...")
    master = cargar_maestro()
    ids_master = set(master["id"])
    g18 = cargar_2018()
    print(f"    maestro 2024: {len(master):,} secciones | 2018: {len(g18):,}")

    print("[2/3] Crosswalk areal (solo secciones desaparecidas)...")
    viejas = set(g18["id"]) - ids_master
    g18_orf = g18[g18["id"].isin(viejas)]
    print(f"    secciones 2018 sin equivalente directo en 2024: {len(g18_orf):,}")
    xw = crosswalk_areal(g18_orf, master)
    xw.to_csv(os.path.join(PROCESSED, "crosswalk_2018_2024.csv"), index=False)
    print(f"    pares de equivalencia: {len(xw):,}")

    print("[3/3] Realocando votos por año...")
    resumen = []
    for anio in (2012, 2015, 2018, 2021, 2024):
        v = pd.read_csv(os.path.join(PROCESSED, f"votos_seccion_{anio}.csv"),
                        index_col=0)
        v.index = v.index.astype(str).str.zfill(6)
        directas = v[v.index.isin(ids_master)]
        huerfanas = v[~v.index.isin(ids_master)]
        via_xw = huerfanas[huerfanas.index.isin(set(xw["id_old"]))]
        perdidas = huerfanas[~huerfanas.index.isin(set(xw["id_old"]))]
        realocadas = realocar(via_xw, xw) if len(via_xw) else None
        final = directas.copy()
        if realocadas is not None:
            final = final.add(realocadas, fill_value=0).fillna(0)
        final.to_csv(os.path.join(
            PROCESSED, f"votos_seccion_{anio}_m2024.csv"), encoding="utf-8")
        resumen.append({
            "anio": anio,
            "secciones_origen": len(v),
            "directas": len(directas),
            "via_crosswalk": len(via_xw),
            "sin_cobertura": len(perdidas),
            "cobertura_votos_%": 100 * final["total_votos"].sum() /
            v["total_votos"].sum(),
            "secciones_destino": len(final),
        })
        print(f"    {anio}: {len(v):,} -> {len(final):,} "
              f"(cobertura {resumen[-1]['cobertura_votos_%']:.2f}%)")
    pd.DataFrame(resumen).to_csv(
        os.path.join(PROCESSED, "resumen_armonizacion.csv"), index=False)
    print("Listo.")


if __name__ == "__main__":
    main()
