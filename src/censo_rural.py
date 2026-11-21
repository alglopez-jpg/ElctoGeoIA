"""Cobertura rural del panel: resultados por localidad (ITER 2020) de las
localidades rurales, asignadas a sección electoral por centroide.

Complementa censo_seccion.py (manzanas urbanas): la unión de ambos cubre
población urbana (manzana) y rural (localidad).

- ITER: INEGI, Principales resultados por localidad, Censo 2020.
- Localidades rurales: servicio gaia (INEGI), filtradas por ámbito Rural
  para no duplicar la población urbana ya cubierta por manzanas.
"""
import glob
import os

import geopandas as gpd
import numpy as np
import pandas as pd

BASE = os.path.join(os.path.dirname(__file__), "..")
UPLOAD = os.path.join(BASE, "data", "upload")
PROCESSED = os.path.join(BASE, "data", "processed")

import censo_seccion as cs


def cargar_maestro():
    g = gpd.read_file(os.path.join(UPLOAD, "mgsan_ext", "SECCION.shp"))
    g["id"] = g["ENTIDAD"].astype(int).astype(str).str.zfill(2) + \
        g["SECCION"].astype(int).astype(str).str.zfill(4)
    return g[["id", "geometry"]].to_crs("EPSG:4326")


def iter_localidades():
    f = os.path.join(UPLOAD, "iter_00_cpv2020", "conjunto_de_datos",
                     "conjunto_de_datos_iter_00CSV20.csv")
    d = pd.read_csv(f, low_memory=False)
    d = d[(d["ENTIDAD"] > 0) & (d["MUN"] > 0) &
          (~d["LOC"].isin([0, 9998, 9999]))].copy()
    cols = list(cs.VARS_CONTEO)
    for c in cols:
        d[c] = pd.to_numeric(d[c], errors="coerce").fillna(0)
    d["ENTIDAD"] = d["ENTIDAD"].astype(int).astype(str).str.zfill(2)
    d["MUN"] = d["MUN"].astype(int).astype(str).str.zfill(3)
    d["LOC"] = d["LOC"].astype(int).astype(str).str.zfill(4)
    d["clave"] = d["ENTIDAD"] + d["MUN"] + d["LOC"]
    return d.groupby("clave")[cols].sum().reset_index()


def localidades_rurales(ent):
    f = os.path.join(UPLOAD, "localidades2020", f"loc_{ent}.json")
    if not os.path.exists(f):
        return None
    g = gpd.read_file(f)
    g["clave"] = g["cvegeo"].astype(str).str.zfill(9)
    amb = g.get("ambito")
    if amb is not None:
        g = g[g["ambito"].astype(str).str.lower() == "rural"]
    return g[["clave", "geometry"]]


def main():
    print("[1/3] ITER y maestro...")
    it = iter_localidades()
    maestro = cargar_maestro()
    print(f"    localidades ITER: {len(it):,}")

    print("[2/3] Asignación localidad rural -> sección...")
    partes = []
    for e in range(1, 33):
        ent = f"{e:02d}"
        loc = localidades_rurales(ent)
        if loc is None:
            print(f"    [{ent}] sin descarga")
            continue
        m = loc.merge(it, on="clave", how="inner")
        if len(m) == 0:
            continue
        m = gpd.GeoDataFrame(m, geometry="geometry")
        m["geometry"] = m.geometry.centroid
        j = gpd.sjoin(m, maestro, predicate="within", how="inner")
        agg = j.groupby("id")[list(cs.VARS_CONTEO)].sum()
        partes.append(agg)
    rural = pd.concat(partes).groupby(level=0).sum()
    rural = rural.rename(columns=cs.VARS_CONTEO)
    rural.to_csv(os.path.join(PROCESSED, "censo2020_seccion_rural.csv"))
    print(f"    secciones con población rural: {len(rural):,} "
          f"| pob rural asignada: {rural['pob_total'].sum():,.0f}")

    print("[3/3] Indicadores combinados (urbano + rural)...")
    urb = pd.read_csv(os.path.join(PROCESSED, "censo2020_seccion_conteos.csv"),
                      index_col=0)
    urb.index = urb.index.astype(str).str.zfill(6)
    rural = rural.reindex(urb.index, fill_value=0)
    tot = urb.add(rural, fill_value=0).fillna(0)
    tot.to_csv(os.path.join(PROCESSED, "censo2020_seccion_conteos_total.csv"))

    ratios = pd.DataFrame(index=tot.index)
    ratios["pob_total"] = tot["pob_total"]
    ratios["pob_rural"] = rural["pob_total"]
    ratios["pct_rural"] = 100 * rural["pob_total"] / \
        tot["pob_total"].replace(0, np.nan)
    ratios["pct_sin_basica"] = 100 * (tot["pob15_sin_escolar"] +
                                      tot["pob15_primaria_incompleta"]) / \
        tot["pob_15ymas"].replace(0, np.nan)
    ratios["pct_analfabeta"] = 100 * tot["pob15_sin_escolar"] / \
        tot["pob_15ymas"].replace(0, np.nan)
    ratios["pct_piso_tierra"] = 100 * (tot["viviendas_habitadas"] -
                                      tot["viv_piso_firme"]) / \
        tot["viviendas_habitadas"].replace(0, np.nan)
    ratios["pct_sin_drenaje"] = 100 * tot["viv_sin_drenaje"] / \
        tot["viviendas_habitadas"].replace(0, np.nan)
    ratios["pct_sin_bienes"] = 100 * tot["viv_sin_bienes"] / \
        tot["viviendas_habitadas"].replace(0, np.nan)
    ratios["pct_auto"] = 100 * tot["viv_auto"] / \
        tot["viviendas_habitadas"].replace(0, np.nan)
    ratios["pct_internet"] = 100 * tot["viv_internet"] / \
        tot["viviendas_habitadas"].replace(0, np.nan)
    ratios["pct_sin_salud"] = 100 * tot["pob_sin_salud"] / \
        tot["pob_total"].replace(0, np.nan)
    ratios["pct_60ymas"] = 100 * tot["pob_60ymas"] / \
        tot["pob_total"].replace(0, np.nan)
    ratios["pct_18a24"] = 100 * tot["pob_18a24"] / \
        tot["pob_total"].replace(0, np.nan)
    ratios.to_csv(os.path.join(
        PROCESSED, "censo2020_seccion_indicadores_total.csv"))
    print(f"    secciones con censo: {ratios['pob_total'].gt(0).sum():,}")
    print(f"    población cubierta: {tot['pob_total'].sum():,.0f}")


if __name__ == "__main__":
    main()
