"""Asignación del Censo 2020 (manzana urbana) a secciones electorales.

Flujo por entidad:
1. Lee el CSV censal a nivel manzana (INEGI, datos abiertos CPV2020).
2. Une con los polígonos de manzana del servicio gaia (INEGI) por clave
   ENTIDAD+MUN+LOC+AGEB+MZA.
3. Asigna cada manzana a la sección electoral 2024 (MGSAN) por centroide.
4. Agrega conteos por sección y calcula razones (nunca promedios de razones).

Limitación documentada: solo cubre manzanas urbanas (~79% de la población).
Las secciones rurales quedan con covariables nulas.
"""
import glob
import os
import sys
import zipfile

import geopandas as gpd
import numpy as np
import pandas as pd

BASE = os.path.join(os.path.dirname(__file__), "..")
UPLOAD = os.path.join(BASE, "data", "upload")
PROCESSED = os.path.join(BASE, "data", "processed")

VARS_CONTEO = {
    "POBTOT": "pob_total",
    "P_15YMAS": "pob_15ymas",
    "P15YM_SE": "pob15_sin_escolar",
    "P15PRI_IN": "pob15_primaria_incompleta",
    "P15SEC_IN": "pob15_secundaria_incompleta",
    "PEA": "pea",
    "PSINDER": "pob_sin_salud",
    "TVIVHAB": "viviendas_habitadas",
    "VPH_PISODT": "viv_piso_firme",
    "VPH_NODREN": "viv_sin_drenaje",
    "VPH_S_ELEC": "viv_sin_luz",
    "VPH_AGUAFV": "viv_sin_agua",
    "VPH_SNBIEN": "viv_sin_bienes",
    "VPH_REFRI": "viv_refri",
    "VPH_AUTOM": "viv_auto",
    "VPH_INTER": "viv_internet",
    "VPH_CEL": "viv_celular",
    "P_60YMAS": "pob_60ymas",
    "P_18A24": "pob_18a24",
}


def cargar_maestro():
    g = gpd.read_file(os.path.join(UPLOAD, "mgsan_ext", "SECCION.shp"))
    g["id"] = g["ENTIDAD"].astype(int).astype(str).str.zfill(2) + \
        g["SECCION"].astype(int).astype(str).str.zfill(4)
    return g[["id", "geometry"]].to_crs("EPSG:4326")


def procesar_entidad(ent, maestro):
    csv_zip = os.path.join(UPLOAD, "censo2020_ageb",
                           f"ageb_mza_urbana_{ent}_cpv2020_csv.zip")
    mza_json = os.path.join(UPLOAD, "manzanas2020", f"mza_{ent}.json")
    if not (os.path.exists(csv_zip) and os.path.exists(mza_json)):
        return None
    z = zipfile.ZipFile(csv_zip)
    name = [n for n in z.namelist() if n.endswith(".csv")
            and "conjunto" in n and "bitacora" not in n
            and "diccionario" not in n][0]
    try:
        cen = pd.read_csv(z.open(name), low_memory=False)
    except UnicodeDecodeError:
        cen = pd.read_csv(z.open(name), low_memory=False,
                          encoding="latin-1")
    cen = cen[cen["MZA"].astype(str).str.strip() != "000"]
    cen["MZA"] = cen["MZA"].astype(str).str.strip().str.zfill(3)
    cen["AGEB"] = cen["AGEB"].astype(str).str.strip()
    cen["LOC"] = cen["LOC"].astype(str).str.strip().str.zfill(4)
    cen["MUN"] = cen["MUN"].astype(str).str.strip().str.zfill(3)
    cen["ENTIDAD"] = cen["ENTIDAD"].astype(str).str.zfill(2)
    cen["clave"] = cen["ENTIDAD"] + cen["MUN"] + cen["LOC"] + cen["AGEB"] + \
        cen["MZA"]

    mz = gpd.read_file(mza_json)
    mz["clave"] = mz["cvegeo"].astype(str).str.zfill(16)

    cols = list(VARS_CONTEO)
    for c in cols:
        cen[c] = pd.to_numeric(cen[c], errors="coerce").fillna(0)
    cen_s = cen.groupby("clave")[cols].sum().reset_index()
    mz = mz[["clave", "geometry"]].merge(cen_s, on="clave", how="inner")
    if len(mz) == 0:
        return None
    mz["geometry"] = mz.geometry.centroid
    j = gpd.sjoin(mz, maestro, predicate="within", how="inner")
    agg = j.groupby("id")[cols].sum(numeric_only=True)
    return agg


def main():
    maestro = cargar_maestro()
    partes = []
    for e in range(1, 33):
        ent = f"{e:02d}"
        try:
            r = procesar_entidad(ent, maestro)
            if r is None:
                print(f"[{ent}] sin datos (descarga pendiente)")
                continue
            partes.append(r)
            print(f"[{ent}] {len(r):,} secciones con censo urbano")
        except Exception as ex:
            print(f"[{ent}] ERROR: {str(ex)[:80]}")
    censo = pd.concat(partes).groupby(level=0).sum()
    censo = censo.rename(columns=VARS_CONTEO)
    censo.to_csv(os.path.join(PROCESSED, "censo2020_seccion_conteos.csv"))
    print(f"\nTotal: {len(censo):,} secciones con censo urbano")

    ratios = pd.DataFrame(index=censo.index)
    ratios["pob_total"] = censo["pob_total"]
    ratios["pct_sin_basica"] = 100 * (censo["pob15_sin_escolar"] +
                                      censo["pob15_primaria_incompleta"]) / \
        censo["pob_15ymas"].replace(0, np.nan)
    ratios["pct_analfabeta"] = 100 * censo["pob15_sin_escolar"] / \
        censo["pob_15ymas"].replace(0, np.nan)
    ratios["pct_piso_tierra"] = 100 * (censo["viviendas_habitadas"] -
                                      censo["viv_piso_firme"]) / \
        censo["viviendas_habitadas"].replace(0, np.nan)
    ratios["pct_sin_drenaje"] = 100 * censo["viv_sin_drenaje"] / \
        censo["viviendas_habitadas"].replace(0, np.nan)
    ratios["pct_sin_bienes"] = 100 * censo["viv_sin_bienes"] / \
        censo["viviendas_habitadas"].replace(0, np.nan)
    ratios["pct_auto"] = 100 * censo["viv_auto"] / \
        censo["viviendas_habitadas"].replace(0, np.nan)
    ratios["pct_internet"] = 100 * censo["viv_internet"] / \
        censo["viviendas_habitadas"].replace(0, np.nan)
    ratios["pct_sin_salud"] = 100 * censo["pob_sin_salud"] / \
        censo["pob_total"].replace(0, np.nan)
    ratios["pct_60ymas"] = 100 * censo["pob_60ymas"] / \
        censo["pob_total"].replace(0, np.nan)
    ratios["pct_18a24"] = 100 * censo["pob_18a24"] / \
        censo["pob_total"].replace(0, np.nan)
    ratios["pct_sin_secundaria"] = 100 * (censo["pob15_sin_escolar"] +
                                          censo["pob15_primaria_incompleta"] +
                                          censo["pob15_secundaria_incompleta"]) / \
        censo["pob_15ymas"].replace(0, np.nan)
    ratios["pct_pea"] = 100 * censo["pea"] / \
        censo["pob_15ymas"].replace(0, np.nan)
    ratios["pct_celular"] = 100 * censo["viv_celular"] / \
        censo["viviendas_habitadas"].replace(0, np.nan)
    ratios["pct_refri"] = 100 * censo["viv_refri"] / \
        censo["viviendas_habitadas"].replace(0, np.nan)
    ratios["pct_sin_luz"] = 100 * censo["viv_sin_luz"] / \
        censo["viviendas_habitadas"].replace(0, np.nan)
    ratios["pct_sin_agua"] = 100 * censo["viv_sin_agua"] / \
        censo["viviendas_habitadas"].replace(0, np.nan)
    ratios.to_csv(os.path.join(PROCESSED, "censo2020_seccion_indicadores.csv"))
    print(f"Indicadores: {ratios.shape}")


if __name__ == "__main__":
    main()
