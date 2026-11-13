"""Procesamiento: agrega resultados presidenciales 2024 por municipio,
combina con indicadores socioeconómicos CONAPO 2020 y con la cartografía.

Uso: python src/procesamiento.py
"""

import glob
import json
import os
import sys

import geopandas as gpd
import pandas as pd

BASE = os.path.join(os.path.dirname(__file__), "..")
RAW = os.path.join(BASE, "data", "raw")
GEO = os.path.join(BASE, "data", "geo")
PROCESSED = os.path.join(BASE, "data", "processed")

COALICIONES = {
    "sheinbaum": ["PVEM", "PT", "MORENA",
                  "PVEM_PT_MORENA", "PVEM_PT", "PVEM_MORENA", "PT_MORENA"],
    "galvez": ["PAN", "PRI", "PRD", "PAN_PRI_PRD", "PAN_PRI", "PAN_PRD",
               "PRI_PRD"],
    "maynez": ["MC"],
}


def leer_resultados():
    df = pd.read_csv(
        os.path.join(RAW, "PRES_2024.csv"),
        sep="|", encoding="latin-1", skiprows=lambda i: i < 7,
        thousands=",", quotechar="'",
    )
    df = df.dropna(subset=["CLAVE_CASILLA"])
    df["CLAVE_CASILLA"] = df["CLAVE_CASILLA"].astype(str).str.strip("'")
    for c in ["ID_ENTIDAD", "ID_DISTRITO_FEDERAL", "SECCION"]:
        df[c] = df[c].astype(str).str.replace("=", "").str.strip('"').str.strip("'")
    columnas_votos = ["PAN", "PRI", "PRD", "PVEM", "PT", "MC", "MORENA",
                      "PAN_PRI_PRD", "PAN_PRI", "PAN_PRD", "PRI_PRD",
                      "PVEM_PT_MORENA", "PVEM_PT", "PVEM_MORENA", "PT_MORENA",
                      "TOTAL_VOTOS_CALCULADOS", "LISTA_NOMINAL"]
    for c in columnas_votos:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
    return df


def leer_catalogo():
    cat = pd.read_csv(
        os.path.join(RAW, "20240602_CATALOGO_CASILLAS_PEF24.csv"),
        sep="|", encoding="latin-1", skiprows=1, quotechar="'",
    )
    cat["CLAVE_CASILLA"] = cat["CLAVE_CASILLA"].astype(str).str.strip("'")
    for c in ["ID_ENTIDAD", "ID_MUNICIPIO"]:
        cat[c] = cat[c].astype(str).str.replace("=", "").str.strip('"').str.strip("'")
    return cat[["CLAVE_CASILLA", "ID_ENTIDAD", "ID_MUNICIPIO", "MUNICIPIO"]]


def leer_conapo():
    df = pd.read_excel(os.path.join(RAW, "IMM_2020.xls"), header=3)
    df = df.dropna(subset=["Clave del municipio", "Nombre del municipio"])
    df = df[pd.to_numeric(df["Clave del municipio"], errors="coerce").notna()]
    df = df.iloc[:, :-1]
    df.columns = [
        "cve_ent", "nom_ent", "cve_mun", "nom_mun", "pob_total",
        "pct_analfabeta", "pct_sin_basica", "pct_sin_drenaje",
        "pct_sin_electricidad", "pct_sin_agua", "pct_piso_tierra",
        "pct_hacinamiento", "pct_rural", "pct_ingresos_bajos",
        "im_2020", "gm_2020", "imn_2020",
    ]
    df["cve_mun"] = df["cve_mun"].astype(int).map("{:05d}".format)
    df["cvegeo"] = df["cve_mun"]
    df["cve_ent"] = df["cvegeo"].str[:2].astype(int)
    return df


def agregar_por_municipio(res, cat):
    res = res.merge(cat, on="CLAVE_CASILLA", how="left",
                    suffixes=("", "_cat"))
    res["cvegeo"] = res["ID_ENTIDAD_cat"] + res["ID_MUNICIPIO"]
    res = res.dropna(subset=["cvegeo"])

    for candidata, columnas in COALICIONES.items():
        res[candidata] = res[columnas].fillna(0).sum(axis=1)

    votos = ["sheinbaum", "galvez", "maynez"]
    res["total_votos_candidaturas"] = res[votos].sum(axis=1)
    res["total_votos"] = pd.to_numeric(
        res["TOTAL_VOTOS_CALCULADOS"], errors="coerce").fillna(0)
    res["lista_nominal"] = pd.to_numeric(
        res["LISTA_NOMINAL"], errors="coerce").fillna(0)

    agg = res.groupby("cvegeo").agg(
        sheinbaum=("sheinbaum", "sum"),
        galvez=("galvez", "sum"),
        maynez=("maynez", "sum"),
        total_votos_candidaturas=("total_votos_candidaturas", "sum"),
        total_votos=("total_votos", "sum"),
        lista_nominal=("lista_nominal", "sum"),
        n_casillas=("CLAVE_CASILLA", "count"),
    ).reset_index()

    for c in votos:
        agg[f"pct_{c}"] = 100 * agg[c] / agg["total_votos_candidaturas"]
    agg["pct_participacion"] = 100 * agg["total_votos"] / agg["lista_nominal"]
    agg = agg[agg["total_votos_candidaturas"] > 0].copy()
    agg["pct_mas_votado"] = agg[[f"pct_{c}" for c in votos]].max(axis=1)
    agg["ganador"] = agg[[f"pct_{c}" for c in votos]].idxmax(axis=1).str.replace(
        "pct_", "", regex=False)
    return agg


def main():
    os.makedirs(PROCESSED, exist_ok=True)

    print("[1/4] Leyendo resultados por casilla...")
    res = leer_resultados()
    print(f"     {len(res):,} casillas")

    print("[2/4] Leyendo catálogo de casillas...")
    cat = leer_catalogo()

    print("[3/4] Agregando por municipio...")
    mun = agregar_por_municipio(res, cat)
    print(f"     {len(mun):,} municipios")

    print("[4/4] Integrando CONAPO y cartografía...")
    conapo = leer_conapo()
    mun["cvegeo"] = mun["cvegeo"].str.zfill(5)
    base = conapo.merge(mun, on="cvegeo", how="left")
    base.to_csv(os.path.join(PROCESSED, "municipios_electoral_social.csv"),
                index=False, encoding="utf-8-sig")
    print(f"     datos integrados: {base.shape}")

    gdfs = []
    for path in sorted(glob.glob(os.path.join(GEO, "mgem_*.json"))):
        gdfs.append(gpd.read_file(path))
    gdf = gpd.GeoDataFrame(pd.concat(gdfs, ignore_index=True))
    gdf["cvegeo"] = gdf["cvegeo"].astype(str).str.zfill(5)
    gdf = gdf[["cvegeo", "nomgeo", "geometry"]].to_crs("EPSG:4326")
    gdf["geometry"] = gdf.geometry.simplify(0.005, preserve_topology=True)
    gdf.to_file(os.path.join(PROCESSED, "municipios_cartografia_simplificada.gpkg"),
                driver="GPKG")

    print("\nProcesamiento completo.")
    print(f"- {os.path.join(PROCESSED, 'municipios_electoral_social.csv')}")
    print(f"- {os.path.join(PROCESSED, 'municipios_cartografia_simplificada.gpkg')}")


if __name__ == "__main__":
    sys.exit(main())
