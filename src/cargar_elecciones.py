"""Carga de elecciones federales (diputados MR) 2012-2024 y agregación
de votos por PARTIDO a nivel sección electoral.

Aplica los supuestos de redistribución de coaliciones de config_coaliciones.
Salida por año: DataFrame indexado por id_seccion con votos por partido,
nulos, total y lista nominal.
"""
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from config_coaliciones import COALICIONES, PARTIDOS, PARTIDOS_PANEL

BASE = os.path.join(os.path.dirname(__file__), "..")
UPLOAD = os.path.join(BASE, "data", "upload")
PROCESSED = os.path.join(BASE, "data", "processed")

META = {
    2018: dict(ruta=os.path.join(UPLOAD, "cw2018", "dip",
                                 "20180708_2130_CW_diputaciones",
                                 "diputaciones.csv"),
               skip=6, col_ent="ID_ESTADO", col_ln="LISTA_NOMINAL_CASILLA",
               col_nulos="VN"),
    2021: dict(ruta=os.path.join(UPLOAD, "cw2021", "dip",
                                 "20210611_1000_CW_diputaciones",
                                 "diputaciones.csv"),
               skip=6, col_ent="ID_ESTADO", col_ln="LISTA_NOMINAL_CASILLA",
               col_nulos="VOTOS NULOS"),
    2024: dict(ruta=os.path.join(BASE, "data", "raw", "DIP_FED_2024.csv"),
               skip=7, col_ent="ID_ENTIDAD", col_ln="LISTA_NOMINAL",
               col_nulos="VOTOS NULOS"),
}


def limpiar_cve(s):
    return s.astype(str).str.replace("=", "", regex=False).str.strip('"') \
             .str.strip("'").str.strip()


def id_seccion(ent, sec):
    ent = limpiar_cve(ent)
    sec = limpiar_cve(sec)
    return ent.str.zfill(2) + sec.str.zfill(4)


def redistribuir(votos_df, anio):
    """De columnas por partido/coalición -> votos por partido canónico."""
    coal = COALICIONES[anio]
    map_partido = PARTIDOS[anio]
    out = pd.DataFrame(0.0, index=votos_df.index, columns=PARTIDOS_PANEL)
    for col in votos_df.columns:
        vals = pd.to_numeric(votos_df[col], errors="coerce").fillna(0)
        if col in coal:
            for partido, peso in coal[col].items():
                out[partido] += vals * peso
        elif col in map_partido:
            out[map_partido[col]] += vals
    return out


def cargar_2012_2015(anio):
    """elecRetrns: dip{anio}.csv, columnas edon, seccion, casilla y votos."""
    f = os.path.join(UPLOAD, f"dip{anio}.csv")
    d = pd.read_csv(f, low_memory=False)
    d = d.dropna(subset=["edon", "seccion"])
    d = d[d["casilla"].astype(str).str.upper().str.strip().str[0].isin(
        list("BCEGSP"))]
    d["id"] = id_seccion(d["edon"], d["seccion"])
    no_voto = {"edon", "seccion", "casilla", "disn", "inegi", "ife", "mun",
               "status", "tepjf", "nota", "nota.emm", "latitude",
               "longitude", "tot", "nul", "nr", "lisnom", "id"}
    cols_voto = [c for c in d.columns if c not in no_voto]
    agrupado = d.groupby("id")[cols_voto + ["tot", "nul", "nr", "lisnom"]] \
        .sum(numeric_only=True)
    cols_voto = [c for c in cols_voto if c in agrupado.columns]
    votos = redistribuir(agrupado[cols_voto], anio)
    votos["nulos"] = agrupado["nul"]
    votos["nr"] = agrupado["nr"]
    votos["total_votos"] = agrupado["tot"]
    votos["lista_nominal"] = agrupado["lisnom"]
    return votos


def cargar_cw(anio):
    """Cómputos INE 2018/2021/2024: sep='|' con preámbulo."""
    meta = META[anio]
    d = pd.read_csv(meta["ruta"], sep="|", encoding="latin-1",
                    skiprows=meta["skip"], low_memory=False)
    d = d.dropna(subset=["CLAVE_CASILLA"])
    tipo = d["TIPO_CASILLA"].astype(str).str.upper().str.strip()
    d = d[~tipo.str.startswith("S")]
    d["id"] = id_seccion(d[meta["col_ent"]], d["SECCION"])
    excluidos = {"CLAVE_CASILLA", "CLAVE_ACTA", "ID_ESTADO", "NOMBRE_ESTADO",
                 "ID_ENTIDAD", "ENTIDAD", "ID_DISTRITO", "NOMBRE_DISTRITO",
                 "ID_DISTRITO_FEDERAL", "DISTRITO_FEDERAL", "SECCION",
                 "ID_CASILLA", "TIPO_CASILLA", "EXT_CONTIGUA", "CASILLA",
                 "NUM_ACTA_IMPRESO", "TIPO_ACTA",
                 "TOTAL_VOTOS_CALCULADOS", "OBSERVACIONES",
                 "MECANISMOS_TRASLADO", "FECHA_HORA", "id",
                 "CANDIDATO/A NO REGISTRADO/A", "VOTOS NULOS",
                 "CNR", "VN", "CANDIDATO/A INDEPENDIENTE"}
    col_ln = meta["col_ln"]
    cols_voto = [c for c in d.columns if c not in excluidos and c != col_ln]
    col_nulos = meta["col_nulos"]
    for c in cols_voto + ["TOTAL_VOTOS_CALCULADOS", col_nulos, col_ln]:
        d[c] = pd.to_numeric(d[c], errors="coerce").fillna(0)
    agrupado = d.groupby("id")[cols_voto + ["TOTAL_VOTOS_CALCULADOS",
                                            col_nulos, col_ln]].sum()
    votos = redistribuir(agrupado[cols_voto], anio)
    votos["nulos"] = agrupado[col_nulos]
    votos["nr"] = 0
    votos["total_votos"] = agrupado["TOTAL_VOTOS_CALCULADOS"]
    votos["lista_nominal"] = agrupado[col_ln]
    return votos


def cargar_todos():
    os.makedirs(PROCESSED, exist_ok=True)
    out = {}
    for anio in (2012, 2015):
        print(f"[{anio}] cargando elecRetrns...")
        out[anio] = cargar_2012_2015(anio)
        print(f"    {len(out[anio]):,} secciones")
    for anio in (2018, 2021, 2024):
        print(f"[{anio}] cargando cómputos INE...")
        out[anio] = cargar_cw(anio)
        print(f"    {len(out[anio]):,} secciones")
    for anio, df in out.items():
        df.to_csv(os.path.join(PROCESSED, f"votos_seccion_{anio}.csv"),
                  encoding="utf-8")
    return out


if __name__ == "__main__":
    cargar_todos()
    print("Listo.")
