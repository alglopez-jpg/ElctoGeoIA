"""Publica visualizadores HTML como página web (GitHub Pages).

Copia los visualizadores de salidas_agente/ a docs/web/ para que GitHub
Pages los sirva como sitio estático. Uso:

    python -m agente.publicar                          # todos los HTML
    python -m agente.publicar leon irapuato            # por patrón en el nombre

Pasos activación (solo la primera vez, en github.com):
    Settings > Pages > Deploy from a branch > main > /docs > Save

La página queda en https://alglopez-jpg.github.io/ElctoGeoIA/web/
"""
from __future__ import annotations

import glob
import os
import shutil
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SALIDAS = os.path.join(RAIZ, "salidas_agente")
DESTINO = os.path.join(RAIZ, "docs", "web")

INDICE = """<!doctype html>
<html lang="es"><head><meta charset="utf-8">
<title>ElctoGeoIA \u00b7 visualizadores</title>
<style>
 body{{font-family:sans-serif;max-width:900px;margin:40px auto;padding:0 20px;color:#222}}
 h1{{color:#1d3557}} li{{margin:8px 0}} a{{color:#1d3557}}
</style></head><body>
<h1>ElctoGeoIA \u00b7 visualizadores electorales</h1>
<p>Mapas interactivos por territorio: secciones clicables con poblaci\u00f3n,
lista nominal, votos por partido y tipolog\u00eda.</p>
<ul>
{bl}
</ul>
<p style="font-size:12px;color:#777">Cartograf\u00eda INE (MGS) \u00b7 datos INE/INEGI
\u00b7 mapa base \u00a9 OpenStreetMap contributors</p>
</body></html>
"""


def publicar(patrones: list[str] | None = None) -> list[str]:
    """Copia visualizadores a docs/web/ y regenera el indice.html."""
    os.makedirs(DESTINO, exist_ok=True)
    archivos = sorted(glob.glob(os.path.join(SALIDAS, "visualizador_*.html")))
    if patrones:
        archivos = [a for a in archivos
                    if any(p.lower() in os.path.basename(a).lower()
                           for p in patrones)]
    if not archivos:
        print("No hay visualizadores en salidas_agente/ con ese patr\u00f3n.")
        return []
    publicados = []
    for a in archivos:
        shutil.copy2(a, os.path.join(DESTINO, os.path.basename(a)))
        publicados.append(os.path.basename(a))
        print("publicado:", publicados[-1])
    publicados_previos = sorted(
        os.path.basename(f) for f in glob.glob(
            os.path.join(DESTINO, "visualizador_*.html")))
    items = "\n".join(
        f'  <li><a href="{n}">{n.replace("visualizador_", "").replace(".html", "")}</a></li>'
        for n in publicados_previos)
    with open(os.path.join(DESTINO, "index.html"), "w", encoding="utf-8") as f:
        f.write(INDICE.format(bl=items or "  <li>sin visualizadores</li>"))
    print(f"\n\u00cdndice: docs/web/index.html ({len(publicados_previos)} mapas)")
    print("Sube el commit y activa Settings > Pages > main > /docs si es")
    print("la primera vez. URL final: "
          "https://<usuario>.github.io/ElctoGeoIA/web/")
    return publicados


if __name__ == "__main__":
    publicar(sys.argv[1:] or None)
