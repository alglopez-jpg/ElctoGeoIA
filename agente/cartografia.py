"""Cartografía de secciones para el agente.

Busca el shapefile de secciones (MGS/MGSAN del INE) en las rutas conocidas
y, si no existe, lo descarga automáticamente desde el espejo público
(Google Storage / mapoteca) y extrae solo los archivos SECCION.*.

Esto permite que el agente genere mapas sin que el usuario mueva archivos
a mano. La descarga (~86 MB) ocurre una sola vez.
"""
from __future__ import annotations

import glob
import os
import sys
import urllib.request
import zipfile

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MIRROR = "https://storage.googleapis.com/mapoteca/MGS_CCL/SHAPEFILE.7z"

_CANDIDATOS = [
    os.path.join(RAIZ, "data", "upload", "mgsan_ext", "SECCION.shp"),
    os.path.join(RAIZ, "data", "upload", "mgsan", "SECCION.shp"),
    os.path.join(RAIZ, "data", "upload", "mgsan_2024", "SECCION.shp"),
]
DEST_DIR = os.path.join(RAIZ, "data", "upload", "mgsan_ext")

_gdf = None


def ruta_cartografia() -> str | None:
    for c in _CANDIDATOS:
        if os.path.exists(c):
            return c
    for pat in (os.path.join(RAIZ, "data", "upload", "**", "SECCION.shp"),):
        hits = glob.glob(pat, recursive=True)
        if hits:
            return hits[0]
    return None


def descargar_cartografia(dest_dir: str = DEST_DIR) -> str:
    """Descarga el shapefile de secciones desde el espejo público y extrae SECCION.*"""
    import py7zr
    os.makedirs(dest_dir, exist_ok=True)
    zip_path = os.path.join(dest_dir, "MGS.7z")
    print(f"Descargando cartografía de secciones (~86 MB, una sola vez)...", file=sys.stderr)
    urllib.request.urlretrieve(MIRROR, zip_path)
    with py7zr.SevenZipFile(zip_path) as z:
        for nombre in z.getnames():
            if nombre.startswith("SECCION."):
                z.extract(dest_dir, [nombre])
    os.remove(zip_path)
    salida = os.path.join(dest_dir, "SECCION.shp")
    if not os.path.exists(salida):
        raise RuntimeError("La descarga no produjo SECCION.shp")
    return salida


def cargar_secciones():
    """Devuelve un GeoDataFrame de las 71,541 secciones (crs original INE)."""
    global _gdf
    if _gdf is not None:
        return _gdf
    import geopandas as gpd
    ruta = ruta_cartografia()
    if ruta is None:
        ruta = descargar_cartografia()
    _gdf = gpd.read_file(ruta)
    # el driver shapefile no siempre respeta dtype: convertir explícitamente
    for c in ("ENTIDAD", "MUNICIPIO", "SECCION", "DISTRITO_F"):
        if c in _gdf:
            _gdf[c] = _gdf[c].astype(str).str.strip()
    _gdf["id"] = (_gdf["ENTIDAD"].str.zfill(2) + _gdf["SECCION"].str.zfill(4)).str.zfill(6)
    return _gdf
