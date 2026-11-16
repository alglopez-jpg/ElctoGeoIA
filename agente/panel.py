"""Acceso al panel de secciones y catálogo de municipios para el agente.

Carga perezosa (lazy) y con caché: el panel (~71,541 filas × 150 columnas)
se carga una sola vez y queda en memoria (~150-200 MB), suficiente para 16 GB RAM.
"""
from __future__ import annotations

import glob
import os
import unicodedata

import pandas as pd

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

_CANDIDATOS_PANEL = [
    os.path.join(RAIZ, "data", "processed", "panel_secciones.csv"),
    os.path.join(RAIZ, "data", "processed", "comprimidos", "panel_secciones.csv.gz"),
]

_panel: pd.DataFrame | None = None
_catalogo: pd.DataFrame | None = None

PARTIDOS = ["pan", "pri", "prd", "pvem", "pt", "mc", "morena", "otros"]
ANIOS = [2012, 2015, 2018, 2021, 2024]


def _norm(s: str) -> str:
    """Minúsculas y sin acentos, para búsqueda tolerante."""
    return unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower().strip()


def cargar_panel() -> pd.DataFrame:
    """Carga el panel maestro (csv o csv.gz) con claves como texto (id de 6 dígitos)."""
    global _panel
    if _panel is not None:
        return _panel
    for ruta in _CANDIDATOS_PANEL:
        if os.path.exists(ruta):
            _panel = pd.read_csv(
                ruta,
                dtype={"id": str, "ent": str, "mun": str, "distrito_f": str},
            )
            _panel["id"] = _panel["id"].str.zfill(6)
            _panel["ent"] = _panel["ent"].str.zfill(2)
            _panel["mun"] = _panel["mun"].str.zfill(3)
            return _panel
    raise FileNotFoundError(
        "No se encontró panel_secciones.csv ni panel_secciones.csv.gz en data/processed/. "
        "Ejecuta src/panel_maestro.py o descomprime el panel."
    )


def cargar_catalogo() -> pd.DataFrame:
    global _catalogo
    if _catalogo is not None:
        return _catalogo
    ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)), "datos", "catalogo_municipios.csv")
    cat = pd.read_csv(ruta, dtype=str)
    cat["ent"] = cat["ent"].str.zfill(2)
    cat["mun"] = cat["mun"].str.zfill(3)
    _catalogo = cat
    return cat


def _resolver_estado(estado: str) -> str | None:
    """Convierte nombre/abreviatura/clave de estado a clave INEGI de 2 dígitos.

    Tolerante a acentos, mayúsculas, abreviaturas ('GJ', 'Gto', 'Qroo') y
    prefijos parciales ('guana'). Devuelve None si no hay coincidencia.
    """
    cat = cargar_catalogo()
    e = _norm(estado)
    if e.isdigit() and len(e) <= 2:
        return e.zfill(2)
    # abreviaturas comunes de 2-5 letras que el LLM puede inventar
    alias = {"gj": "11", "gto": "11", "qroo": "23", "qro": "22", "edomex": "15",
             "cdmx": "09", "df": "09", "bc": "02", "bcs": "03", "nl": "19",
             "jal": "14", "pue": "21", "mich": "16", "yuc": "31", "chis": "07",
             "coah": "05", "tamps": "28", "sin": "25", "ver": "30"}
    if e in alias:
        return alias[e]
    exactos = cat.loc[cat["nom_ent_norm"] == e, "ent"].unique()
    if len(exactos) == 1:
        return exactos[0]
    # coincidencia por prefijo (mínimo 3 letras para evitar falsos positivos)
    if len(e) >= 3:
        parciales = cat.loc[cat["nom_ent_norm"].str.startswith(e), "ent"].unique()
        if len(parciales) == 1:
            return parciales[0]
    return None


def buscar_municipio(nombre: str, estado: str | None = None) -> list[dict]:
    """Busca municipios por nombre (tolerante a acentos/mayúsculas).

    Devuelve lista de coincidencias: [{'ent','mun','nom_mun','nom_ent'}]
    Si `estado` se da, filtra por él (tolerante: nombre, abreviatura o clave).
    """
    cat = cargar_catalogo()
    n = _norm(nombre)
    m = cat["nom_mun_norm"] == n
    if not m.any():
        m = cat["nom_mun_norm"].str.contains(n, regex=False)
    if estado:
        ent = _resolver_estado(estado)
        if ent is None:
            return []
        m &= cat["ent"] == ent
    out = cat.loc[m, ["ent", "mun", "nom_mun", "nom_ent"]].to_dict("records")
    return out[:10]


def secciones_de_municipio(ent: str, mun: str) -> pd.DataFrame:
    p = cargar_panel()
    return p[(p["ent"] == ent.zfill(2)) & (p["mun"] == mun.zfill(3))].copy()


def secciones_de_distrito(ent: str, distrito: str) -> pd.DataFrame:
    """Distrito federal (marco 2024)."""
    p = cargar_panel()
    return p[(p["ent"] == ent.zfill(2)) & (p["distrito_f"] == str(distrito).zfill(2))].copy()
