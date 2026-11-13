"""Descarga de datos brutos para el análisis geoespacial electoral.

Fuentes:
- INE, Cómputos Distritales 2024 (resultados por casilla, elección presidencial).
- INE, Catálogo de casillas PEF 2024 (mapeo casilla -> municipio).
- CONAPO, Índice de marginación municipal 2020 (indicadores socioeconómicos).
- INEGI, servicio gaia (cartografía de áreas geoestadísticas municipales).

Uso: python src/descarga_datos.py
"""

import os
import sys
import zipfile

import requests

RAW = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
GEO = os.path.join(os.path.dirname(__file__), "..", "data", "geo")
HEADERS = {"User-Agent": "Mozilla/5.0 (analisis geoespacial electoral)"}

COMPUTOS_URL = "https://computos2024.ine.mx/20240608_2030_COMPUTOS.zip"
CATALOGO_URL = "https://computos2024.ine.mx/20240602_CATALOGO_CASILLAS_PEF24.zip"
CONAPO_URL = (
    "https://conapo.segob.gob.mx/work/models/CONAPO/"
    "Datos_Abiertos/Municipio/IMM_2020.xls"
)
GAIA_MGEM = "https://gaia.inegi.org.mx/wscatgeo/v2/geo/mgem/{}"

ENTIDADES = [
    "01", "02", "03", "04", "05", "06", "07", "08", "09",
    "10", "11", "12", "13", "14", "15", "16", "17", "18", "19",
    "20", "21", "22", "23", "24", "25", "26", "27", "28", "29",
    "30", "31", "32",
]


def descargar(url, destino):
    if os.path.exists(destino):
        print(f"[ok] ya existe: {destino}")
        return
    print(f"[descarga] {url}")
    r = requests.get(url, timeout=300, headers=HEADERS)
    r.raise_for_status()
    with open(destino, "wb") as f:
        f.write(r.content)
    print(f"[listo] {destino} ({len(r.content):,} bytes)")


def main():
    os.makedirs(RAW, exist_ok=True)
    os.makedirs(GEO, exist_ok=True)

    computos_zip = os.path.join(RAW, "20240608_2030_COMPUTOS.zip")
    descargar(COMPUTOS_URL, computos_zip)
    with zipfile.ZipFile(computos_zip) as z:
        z.extract("20240608_2030_COMPUTOS_PRES.zip", RAW)
    pres_zip = os.path.join(RAW, "20240608_2030_COMPUTOS_PRES.zip")
    with zipfile.ZipFile(pres_zip) as z:
        z.extract("PRES_2024.csv", RAW)
        z.extract("PRES_CANDIDATURAS_2024.csv", RAW)

    catalogo_zip = os.path.join(RAW, "CATALOGO_CASILLAS.zip")
    descargar(CATALOGO_URL, catalogo_zip)
    with zipfile.ZipFile(catalogo_zip) as z:
        z.extract("20240602_CATALOGO_CASILLAS_PEF24.csv", RAW)

    descargar(CONAPO_URL, os.path.join(RAW, "IMM_2020.xls"))

    for ent in ENTIDADES:
        destino = os.path.join(GEO, f"mgem_{ent}.json")
        descargar(GAIA_MGEM.format(ent), destino)

    print("\nDescarga completa.")


if __name__ == "__main__":
    sys.exit(main())
