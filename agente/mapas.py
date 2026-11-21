"""Quinta herramienta del agente: mapas PNG del territorio consultado.

Lecciones aprendidas del proyecto aplicadas aquí:
- figuras de UN panel (71k polígonos con subplots es patológicamente lento)
- geometry.simplify(0.001) antes de graficar
- orden savefig -> show -> close (nunca close antes de savefig)
- sin tight_layout sobre GeoAxes con colorbar
"""
from __future__ import annotations

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SALIDAS = os.path.join(RAIZ, "salidas_agente")

TIPOS_MAPA = ["tipologia", "ganador", "oficialismo", "participacion", "margen"]

_UA_OSM = {"User-Agent": "ElctoGeoIA-agente/1.0 (https://github.com/alglopez-jpg/ElctoGeoIA)"}


def _fondo_disponible() -> str | None:
    """Importa contextily; devuelve mensaje de error si no está disponible."""
    try:
        import contextily  # noqa: F401
        return None
    except ImportError:
        return ("contextily no está instalado (pip install contextily); "
                "genero el mapa sin fondo.")


_COLORES_GANADOR = {
    "morena": "#8f1c1c", "pan": "#2255aa", "pri": "#11aa44",
    "otros": "#888888", "empate": "#cccccc",
}


def _territorio(nombre_municipio: str, estado: str | None, distrito: int | None = None):
    """Resuelve claves + dataframe del panel + geografía del territorio."""
    from . import panel as P
    from . import cartografia as C
    sec = C.cargar_secciones()
    if distrito is not None:
        cat = P.cargar_catalogo()
        e = str(estado)
        if e.isdigit() and len(e) == 2:
            ent = e.zfill(2)
        else:
            m = cat["nom_ent_norm"] == P._norm(estado)
            ent = cat.loc[m, "ent"].iloc[0]
        df = P.secciones_de_distrito(ent, distrito)
        nombre = f"distrito{int(distrito):02d}_{ent}"
        ids = set(df["id"])
    else:
        hits = P.buscar_municipio(nombre_municipio, estado)
        if not hits:
            return None, None, None, f"No encontré el municipio '{nombre_municipio}'."
        if len(hits) > 1 and estado is None:
            return None, None, None, "Municipio ambiguo: indica el estado."
        h = hits[0]
        df = P.secciones_de_municipio(h["ent"], h["mun"])
        import unicodedata as _ud
        nom_norm = _ud.normalize("NFKD", h["nom_mun"]).encode("ascii", "ignore").decode().lower()
        nombre = f"mun_{h['ent']}{h['mun']}_{nom_norm.replace(' ', '_')}"
        ids = set(df["id"])
    geo = sec[sec["id"].isin(ids)].copy()
    geo = geo.merge(df, on="id", how="inner")
    return geo, df, nombre, None


def _guardar(fig, nombre_archivo: str) -> str:
    os.makedirs(SALIDAS, exist_ok=True)
    ruta = os.path.join(SALIDAS, nombre_archivo)
    fig.savefig(ruta, dpi=110, bbox_inches="tight")
    plt.close(fig)
    return ruta


def _agregar_fondo(ax, nota: list[str]):
    """Superpone el mapa base de OpenStreetMap; degrada en silencio si falla."""
    try:
        import contextily as ctx
        ctx.add_basemap(ax, source=ctx.providers.OpenStreetMap.Mapnik,
                        headers=_UA_OSM)
    except Exception as e:
        nota.append(f"No pude descargar el mapa base de OpenStreetMap ({e}); "
                    "el mapa quedó sin fondo. Revisa tu conexión.")


def generar_mapa(nombre_municipio: str | None = None, estado: str | None = None,
                 distrito: int | None = None, tipo: str = "tipologia",
                 escenario: str = "inercia_intermedia",
                 fondo: bool = False) -> dict:
    """Genera un mapa PNG del territorio consultado.

    Args:
        tipo: 'tipologia', 'ganador', 'oficialismo', 'participacion' o 'margen'
        escenario: escenario 2027 (solo aplica a 'oficialismo' y 'margen')
        fondo: si True, agrega mapa base de OpenStreetMap (requiere internet y
               contextily); si no está disponible, el mapa se genera sin fondo
    """
    tipo = tipo.strip().lower()
    if tipo not in TIPOS_MAPA:
        return {"error": f"tipo inválido; opciones: {TIPOS_MAPA}"}
    geo, df, nombre, err = _territorio(nombre_municipio, estado, distrito)
    if err:
        return {"error": err}
    if geo is None or geo.empty:
        return {"error": "Sin geometría o datos para ese territorio."}

    nota: list[str] = []
    alpha_fondo = 1.0
    if fondo:
        err_ctx = _fondo_disponible()
        if err_ctx:
            nota.append(err_ctx)
        else:
            geo = geo.to_crs(epsg=3857)
            alpha_fondo = 0.78

    geo["geometry"] = geo.geometry.simplify(0.001)
    fig, ax = plt.subplots(figsize=(8, 8))

    if tipo == "tipologia":
        cats = ["bastion_oficialista", "dominante_moderada", "competitiva", "bastion_oposicion"]
        colores = {"bastion_oficialista": "#7d1d1d", "dominante_moderada": "#d98181",
                   "competitiva": "#f2c14e", "bastion_oposicion": "#2c5f8a"}
        for c in cats:
            g = geo[geo["tipologia_2024"] == c]
            if len(g):
                g.plot(ax=ax, color=colores[c], label=c.replace("_", " "),
                       linewidth=0.1, alpha=alpha_fondo)
        ax.legend(title="Tipología 2024", loc="lower left", fontsize=8)
        titulo = "Tipología de secciones 2024"
    elif tipo == "ganador":
        for g_ in geo["ganador_2024"].dropna().unique():
            g = geo[geo["ganador_2024"] == g_]
            g.plot(ax=ax, color=_COLORES_GANADOR.get(g_, "#888888"), label=g_,
                   linewidth=0.1, alpha=alpha_fondo)
        ax.legend(title="Ganador 2024", loc="lower left", fontsize=8)
        titulo = "Ganador por sección, 2024"
    elif tipo == "oficialismo":
        col = f"{escenario}_morena"
        if col not in geo:
            return {"error": f"Escenario inválido para 'oficialismo': {escenario}"}
        geo[col] = geo[col] * 100
        geo.plot(column=col, ax=ax, cmap="RdBu_r", legend=True, linewidth=0.1,
                 alpha=alpha_fondo,
                 legend_kwds={"label": "% voto Morena 2027", "shrink": 0.7})
        titulo = f"Pronóstico 2027 · voto al oficialismo ({escenario})"
    elif tipo == "participacion":
        geo.plot(column="participacion_2024", ax=ax, cmap="viridis", legend=True,
                 linewidth=0.1, alpha=alpha_fondo,
                 legend_kwds={"label": "% participación 2024", "shrink": 0.7})
        titulo = "Participación 2024"
    else:  # margen
        geo.plot(column="margen_2024", ax=ax, cmap="plasma", legend=True, linewidth=0.1,
                 alpha=alpha_fondo,
                 legend_kwds={"label": "margen (pts) 2024", "shrink": 0.7})
        titulo = "Margen de victoria 2024"

    if fondo and alpha_fondo < 1.0:
        _agregar_fondo(ax, nota)
    ax.set_title(f"{titulo}\n{df['id'].iloc[0][:2]} · {nombre.split('_', 1)[-1] if '_' in nombre else nombre}",
                 fontsize=11)
    ax.set_axis_off()
    sufijo = "_osm" if fondo and alpha_fondo < 1.0 else ""
    archivo = f"mapa_{nombre}_{tipo}{sufijo}.png"
    ruta = _guardar(fig, archivo)
    resultado = {"mapa": os.path.relpath(ruta, RAIZ), "secciones": int(len(geo)),
                "tipo": tipo, "fondo": "OpenStreetMap" if fondo and not nota else None,
                "escenario": escenario if tipo == "oficialismo" else None}
    if nota:
        resultado["nota"] = " ".join(nota)
    return resultado
