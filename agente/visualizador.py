"""Sexta herramienta del agente: visualizador HTML interactivo del territorio.

Genera un HTML (folium/Leaflet) con:
- mapa base de OpenStreetMap (se carga al abrir; la geometría va embebida)
- una capa por sección electoral coloreada por criterio (tipología, ganador
  o participación 2024), con ficha al clic: población, lista nominal,
  votos por partido con barras, participación, ganador y margen
- contorno del municipio y del distrito federal consultados
- tarjeta de resumen del territorio en la esquina

La consulta es por municipio o por distrito federal (como generar_mapa).
El archivo se guarda en salidas_agente/ y se abre en cualquier navegador.
"""
from __future__ import annotations

import html as _html
import os

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SALIDAS = os.path.join(RAIZ, "salidas_agente")

PARTIDOS = ["morena", "pan", "pri", "prd", "pvem", "pt", "mc", "otros"]

_COLORES_TIPO = {
    "bastion_oficialista": "#7d1d1d",
    "dominante_moderada": "#d98181",
    "competitiva": "#f2c14e",
    "bastion_oposicion": "#2c5f8a",
}
_COLORES_GANADOR = {
    "morena": "#8f1c1c", "pan": "#2255aa", "pri": "#11aa44",
    "prd": "#ffcc00", "pvem": "#4caf50", "pt": "#c62828",
    "mc": "#ff7f27", "otros": "#888888",
}
_ETIQUETAS_TIPO = {
    "bastion_oficialista": "Basti\u00f3n oficialista (voto duro)",
    "dominante_moderada": "Dominante moderada",
    "competitiva": "Competitiva (disputa)",
    "bastion_oposicion": "Basti\u00f3n de oposici\u00f3n",
}


def _esc(v) -> str:
    return _html.escape(str(v))


def _ficha(row) -> str:
    """Ficha HTML de una sección con tabla + barras de voto por partido."""
    total = row.get("total_votos_2024") or 0
    barras = []
    for p in PARTIDOS:
        v = row.get(f"{p}_2024")
        if not v or v <= 0:
            continue
        pct = 100 * v / total if total else 0
        color = _COLORES_GANADOR.get(p, "#888888")
        barras.append(
            f'<div style="display:flex;align-items:center;gap:6px;margin:1px 0;">'
            f'<span style="width:52px;font-size:11px;">{p.upper()}</span>'
            f'<div style="flex:1;background:#eee;height:10px;border-radius:3px;">'
            f'<div style="width:{pct:.1f}%;height:10px;background:{color};'
            f'border-radius:3px;"></div></div>'
            f'<span style="width:56px;font-size:11px;text-align:right;">'
            f'{v:,.0f} ({pct:.1f}%)</span></div>')
    tipo = row.get("tipologia_2024", "")
    cond = _ETIQUETAS_TIPO.get(tipo, tipo)
    ganador = str(row.get("ganador_2024", "")).upper() or "-"
    return f"""
    <div style="font-family:sans-serif;min-width:340px;">
      <div style="background:#1d3557;color:#fff;padding:6px 10px;border-radius:6px 6px 0 0;">
        <b>Secci\u00f3n {_esc(row['id'])}</b> &middot; {cond}
      </div>
      <table style="border-collapse:collapse;width:100%;font-size:12px;">
        <tr><td style="padding:3px 10px;color:#555;">Poblaci\u00f3n (Censo 2020)</td>
            <td style="padding:3px 10px;text-align:right;">{row.get('pob_total', 0):,.0f}</td></tr>
        <tr><td style="padding:3px 10px;color:#555;">Lista nominal 2024</td>
            <td style="padding:3px 10px;text-align:right;">{row.get('lista_nominal_2024', 0):,.0f}</td></tr>
        <tr><td style="padding:3px 10px;color:#555;">Participaci\u00f3n 2024</td>
            <td style="padding:3px 10px;text-align:right;"><b>{row.get('participacion_2024', float('nan')):.1f}%</b></td></tr>
        <tr><td style="padding:3px 10px;color:#555;">Ganador</td>
            <td style="padding:3px 10px;text-align:right;"><b>{ganador}</b></td></tr>
        <tr><td style="padding:3px 10px;color:#555;">Margen de victoria</td>
            <td style="padding:3px 10px;text-align:right;">{row.get('margen_2024', float('nan')):.1f} pts</td></tr>
      </table>
      <div style="background:#f7f7f7;padding:6px 10px;border-radius:0 0 6px 6px;">
        <div style="font-size:11px;color:#555;margin-bottom:3px;">
          Votos por partido 2024 (total {total:,.0f}):</div>
        {''.join(barras) or '<i style="font-size:11px;">sin voto registrado</i>'}
      </div>
    </div>"""


def _interpolar_color(v, vmin, vmax, paleta):
    """Interpola v en una paleta de colores hex (viridis-like)."""
    import matplotlib.colors as mc
    import matplotlib.pyplot as plt
    cmap = mc.LinearSegmentedColormap.from_list(
        "temp", [mc.to_rgb(c) for c in paleta])
    x = 0.5 if vmax <= vmin else (v - vmin) / (vmax - vmin)
    x = min(max(x, 0.0), 1.0)
    return mc.to_hex(cmap(x))


def _capa_estilo(criterio, row, vmin=None, vmax=None):
    if criterio == "tipologia":
        fill = _COLORES_TIPO.get(row.get("tipologia_2024", ""), "#cccccc")
    elif criterio == "ganador":
        fill = _COLORES_GANADOR.get(row.get("ganador_2024", ""), "#cccccc")
    else:
        v = row.get("participacion_2024")
        fill = _interpolar_color(
            v, vmin, vmax,
            ["#3b0f70", "#8c2981", "#de4968", "#fe9f6d", "#fcfdbf"]) if v == v else "#eeeeee"
    return {"fillColor": fill, "color": "#333333",
            "weight": 0.6, "fillOpacity": 0.55}


def generar_visualizador(nombre_municipio: str | None = None,
                         estado: str | None = None,
                         distrito: int | None = None,
                         criterio: str = "tipologia") -> dict:
    """Genera un visualizador HTML interactivo del territorio consultado.

    Args:
        criterio: coloreado de las secciones: 'tipologia', 'ganador' o
            'participacion'
        distrito: si se da, visualiza ese distrito federal (con estado)
    """
    criterio = (criterio or "tipologia").strip().lower()
    if criterio not in ("tipologia", "ganador", "participacion"):
        return {"error": "criterio inv\u00e1lido; opciones: tipologia, "
                          "ganador, participacion"}

    try:
        import folium
        from folium import Popup
    except ImportError:
        return {"error": "folium no est\u00e1 instalado "
                         "(pip install folium); el visualizador lo necesita."}

    from . import mapas as M
    from . import cartografia as C

    geo, df, nombre, err = M._territorio(nombre_municipio, estado, distrito)
    if err:
        return {"error": err}
    if geo is None or geo.empty:
        return {"error": "Sin geometr\u00eda o datos para ese territorio."}

    cdmx = geo.to_crs(epsg=4326).copy()
    cdmx["geometry"] = cdmx.geometry.simplify(0.001, preserve_topology=True)
    centro = [cdmx.geometry.unary_union.centroid.y,
              cdmx.geometry.unary_union.centroid.x]

    m = folium.Map(location=centro, zoom_start=12,
                   tiles="OpenStreetMap", control_scale=True)

    vmin = vmax = None
    if criterio == "participacion":
        vmin = float(cdmx["participacion_2024"].min())
        vmax = float(cdmx["participacion_2024"].max())
        import branca.colormap as cm
        cm.LinearColormap(
            ["#3b0f70", "#8c2981", "#de4968", "#fe9f6d", "#fcfdbf"],
            vmin=vmin, vmax=vmax,
            caption="% participaci\u00f3n 2024").add_to(m)

    mostradas = 0
    for _, row in cdmx.iterrows():
        d = row.drop(labels=["geometry"]).where(row.notna(), None).to_dict()
        if d.get("tipologia_2024") is None and \
                row.get("tipologia_2024") != row.get("tipologia_2024"):
            continue
        fg = folium.GeoJson(
            row.geometry.__geo_interface__,
            style_function=lambda _, d=d: _capa_estilo(
                criterio,
                {"tipologia_2024": d.get("tipologia_2024"),
                 "ganador_2024": d.get("ganador_2024"),
                 "participacion_2024": d.get("participacion_2024")},
                vmin, vmax),
            tooltip=f"Secci\u00f3n {row['id']}")
        fg.add_child(Popup(_ficha(row), max_width=420))
        m.add_child(fg)
        mostradas += 1
    if mostradas == 0:
        return {"error": "Ninguna secci\u00f3n con datos para visualizar."}

    contorno = cdmx.geometry.unary_union.convex_hull
    folium.GeoJson(
        contorno.__geo_interface__,
        style_function=lambda _: {"fill": False, "color": "#111111",
                                  "weight": 2.5, "dashArray": "6,4"}).add_to(m)

    titulo_territorio = nombre.split("_", 1)[-1].replace("_", " ") \
        if "_" in nombre else nombre
    pob = float(cdmx["pob_total"].sum())
    ln = float(cdmx["lista_nominal_2024"].sum())
    part = 100 * float(cdmx["total_votos_2024"].sum()) / ln if ln else float("nan")
    resumen = f"""
    <div style="position:fixed;top:10px;left:10px;z-index:9999;background:#fff;
                padding:10px 14px;border-radius:8px;box-shadow:0 2px 8px rgba(0,0,0,.25);
                font-family:sans-serif;font-size:13px;line-height:1.5;">
      <b style="font-size:15px;">{_esc(titulo_territorio)}</b><br>
      Poblaci\u00f3n: <b>{pob:,.0f}</b><br>
      Lista nominal 2024: <b>{ln:,.0f}</b><br>
      Participaci\u00f3n: <b>{part:.1f}%</b><br>
      Secciones: <b>{len(cdmx):,}</b><br>
      <span style="color:#666;font-size:11px;">
        Clic en una secci\u00f3n para su ficha completa</span>
    </div>"""
    m.get_root().html.add_child(folium.Element(resumen))

    os.makedirs(SALIDAS, exist_ok=True)
    archivo = f"visualizador_{nombre}.html"
    ruta = os.path.join(SALIDAS, archivo)
    m.save(ruta)
    mb = os.path.getsize(ruta) / 1e6
    return {"visualizador": os.path.relpath(ruta, RAIZ),
            "secciones": mostradas, "criterio": criterio,
            "tamano_mb": round(mb, 1),
            "nota": "abre el HTML en tu navegador; el mapa base requiere "
                    "internet, las fichas y geometr\u00eda van embebidas"}
