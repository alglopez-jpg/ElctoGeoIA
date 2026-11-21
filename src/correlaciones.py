"""Estudio de correlaciones: comportamiento electoral x sociedad, a dos escalas.

Genera tablas (data/processed/correlaciones/) y figuras (figuras/):

1. Sección electoral (panel maestro, ~71k secciones):
   - Spearman: voto por partido 2024, participación, margen, volatilidad
     contra indicadores sociodemográficos/socioeconómicos del Censo 2020
   - Betas estandarizadas (OLS) para pct_morena_2024, pct_pan_2024 y
     participacion_2024: ranking multivariado de qué variables explican el voto
   - Perfil mediano por tipología política de sección (2024)
   - Variable geoespacial nueva: densidad de población por sección
     (pob_total / área del polígono de la cartografía INE)

2. Municipio (municipios_electoral_social.csv, ~2,460 municipios):
   - Spearman: voto por candidatura presidencial 2024 y participación contra
     carencias censales, marginación CONAPO (im_2020), ruralidad y densidad
   - Betas estandarizadas para pct_sheinbaum, pct_galvez, pct_participacion
   - Perfil mediano por partido ganador del municipio

Requiere data/upload/mgsan_ext/SECCION.shp (la descarga el agente si falta).
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats as st
import statsmodels.api as sm

BASE = os.path.join(os.path.dirname(__file__), "..")
UPLOAD = os.path.join(BASE, "data", "upload")
PROCESSED = os.path.join(BASE, "data", "processed")
FIGURAS = os.path.join(BASE, "figuras")
SALIDAS = os.path.join(PROCESSED, "correlaciones")

VOTO_SEC = ["pct_morena_2024", "pct_pan_2024", "pct_pri_2024", "pct_mc_2024",
            "pct_prd_2024", "pct_pvem_2024", "pct_pt_2024", "participacion_2024",
            "pct_nulos_2024", "margen_2024", "volatilidad_18_24",
            "delta_morena_18_24", "delta_pan_18_24"]
SOC_SEC = ["pct_sin_basica", "pct_sin_secundaria", "pct_analfabeta", "pct_pea",
           "pct_piso_tierra", "pct_sin_drenaje", "pct_sin_luz", "pct_sin_agua",
           "pct_sin_bienes", "pct_auto", "pct_refri", "pct_celular",
           "pct_internet", "pct_sin_salud", "pct_60ymas", "pct_18a24",
           "pct_rural", "densidad_sec"]
X_SEC = ["pct_sin_basica", "pct_pea", "pct_piso_tierra",
         "pct_sin_luz", "pct_sin_agua", "pct_auto", "pct_refri", "pct_celular",
         "pct_internet", "pct_60ymas", "pct_18a24", "pct_rural",
         "densidad_sec"]
VOTO_MUN = ["pct_sheinbaum", "pct_galvez", "pct_maynez", "pct_participacion"]
SOC_MUN = ["pct_analfabeta", "pct_sin_basica", "pct_sin_drenaje",
           "pct_sin_electricidad", "pct_sin_agua", "pct_piso_tierra",
           "pct_hacinamiento", "pct_rural", "pct_ingresos_bajos", "im_2020",
           "densidad"]
X_MUN = ["pct_analfabeta", "pct_sin_basica", "pct_sin_drenaje", "pct_piso_tierra",
         "pct_hacinamiento", "pct_rural", "pct_ingresos_bajos", "im_2020",
         "densidad"]


def cargar_secciones():
    import geopandas as gpd
    panel = pd.read_csv(os.path.join(PROCESSED, "comprimidos",
                                     "panel_secciones.csv.gz"),
                        dtype={"id": str})
    sec = gpd.read_file(os.path.join(UPLOAD, "mgsan_ext", "SECCION.shp"))
    sec["id"] = sec["ENTIDAD"].astype(int).astype(str).str.zfill(2) + \
        sec["SECCION"].astype(int).astype(str).str.zfill(4)
    sec["area_km2"] = sec.to_crs(6372).area / 1e6
    p = panel.merge(sec[["id", "area_km2"]].copy(), on="id", how="inner")
    p["densidad_sec"] = p["pob_total"] / p["area_km2"].replace(0, np.nan)
    p["delta_morena_18_24"] = p["pct_morena_2024"] - p["pct_morena_2018"]
    p["delta_pan_18_24"] = p["pct_pan_2024"] - p["pct_pan_2018"]
    p["pct_nulos_2024"] = 100 * p["nulos_2024"] / \
        p["total_votos_2024"].replace(0, np.nan)
    return p


def cargar_municipios():
    import geopandas as gpd
    m = pd.read_csv(os.path.join(PROCESSED, "municipios_electoral_social.csv"),
                    dtype={"cvegeo": str})
    g = gpd.read_file(os.path.join(PROCESSED,
                                   "municipios_cartografia_simplificada.gpkg"))
    g["cvegeo"] = g["cvegeo"].astype(str)
    g["area_km2"] = g.to_crs(6372).area / 1e6
    m = m.merge(g[["cvegeo", "area_km2"]], on="cvegeo", how="inner")
    m["densidad"] = m["pob_total"] / m["area_km2"].replace(0, np.nan)
    return m[m["pct_sheinbaum"].notna()].copy()


def spearman(df, filas, columnas):
    mat = {}
    for v in filas:
        mat[v] = {}
        for s in columnas:
            d = df[[v, s]].replace([np.inf, -np.inf], np.nan).dropna()
            mat[v][s] = st.spearmanr(d[v], d[s]).correlation
    return pd.DataFrame(mat).T.reindex(columns=columnas)


def betas_estandarizadas(df, y, xs):
    d = df[[y] + xs].replace([np.inf, -np.inf], np.nan).dropna()
    z = (d - d.mean()) / d.std()
    r = sm.OLS(z[y], sm.add_constant(z[xs])).fit()
    return (pd.Series({c: r.params[c] for c in xs}),
            round(r.rsquared, 3), len(d))


def guardar_betas(df, ys, xs, etiquetas, prefijo):
    os.makedirs(SALIDAS, exist_ok=True)
    for y, et in zip(ys, etiquetas):
        b, r2, n = betas_estandarizadas(df, y, xs)
        b.sort_values().round(3).to_csv(
            os.path.join(SALIDAS, f"betas_{prefijo}_{et}.csv"))
        print(f"    {et}: R2={r2} (n={n:,})")
        yield et, b.sort_values(), r2


def heatmap(corr, titulo, archivo):
    fig, ax = plt.subplots(figsize=(10, 6))
    im = ax.imshow(corr.values, cmap="RdBu_r", vmin=-0.6, vmax=0.6,
                   aspect="auto")
    ax.set_xticks(range(len(corr.columns)),
                  [c.replace("pct_", "").replace("_sec", "").replace("_2024", "")
                   for c in corr.columns], rotation=45, ha="right", fontsize=8)
    ax.set_yticks(range(len(corr.index)),
                  [i.replace("pct_", "").replace("_2024", "")
                   for i in corr.index], fontsize=8)
    for i in range(corr.shape[0]):
        for j in range(corr.shape[1]):
            ax.text(j, i, f"{corr.values[i, j]:.2f}", ha="center",
                    va="center", fontsize=7,
                    color="black" if abs(corr.values[i, j]) < 0.35 else "white")
    fig.colorbar(im, ax=ax, shrink=0.8, label="Spearman ρ")
    ax.set_title(titulo, fontsize=11)
    fig.tight_layout()
    fig.savefig(os.path.join(FIGURAS, archivo), dpi=110, bbox_inches="tight")
    plt.close(fig)


def barras_betas(b, titulo, archivo, r2):
    fig, ax = plt.subplots(figsize=(7, 6))
    b.plot.barh(ax=ax, color=["#a50f15" if v < 0 else "#08519c" for v in b])
    ax.set_xlabel("beta estandarizada (OLS)")
    ax.set_title(f"{titulo}\n(R\u00b2={r2})", fontsize=10)
    ax.tick_params(axis="y", labelsize=8)
    ax.axvline(0, color="black", linewidth=0.8)
    fig.tight_layout()
    fig.savefig(os.path.join(FIGURAS, archivo), dpi=110, bbox_inches="tight")
    plt.close(fig)


def main():
    os.makedirs(SALIDAS, exist_ok=True)
    print("[1/4] Secciones: panel + densidad...")
    p = cargar_secciones()
    print("    secciones:", f"{len(p):,}")

    print("[2/4] Correlaciones sección...")
    corr_s = spearman(p, VOTO_SEC, SOC_SEC)
    corr_s.round(3).to_csv(os.path.join(SALIDAS, "corr_seccion.csv"))
    heatmap(corr_s, "Correlaci\u00f3n voto x sociedad \u00b7 secciones 2024",
           "heatmap_correlaciones_seccion.png")

    prof = p.groupby("tipologia_2024")[
        ["pct_internet", "pct_auto", "pct_sin_basica", "pct_piso_tierra",
         "participacion_2024", "lista_nominal_2024"]].median().round(1)
    prof["n_secciones"] = p.groupby("tipologia_2024").size()
    prof["pob_millones"] = (p.groupby("tipologia_2024")["pob_total"].sum()
                            / 1e6).round(1)
    prof.to_csv(os.path.join(SALIDAS, "perfiles_tipologia_seccion.csv"))

    print("[3/4] Betas estandarizadas...")
    for et, b, r2 in guardar_betas(
            p, ["pct_morena_2024", "pct_pan_2024", "participacion_2024"],
            X_SEC, ["morena", "pan", "participacion"], "seccion"):
        barras_betas(b, f"Qu\u00e9 explica el voto por secci\u00f3n \u00b7 {et}",
                     f"betas_seccion_{et}.png", r2)

    print("[4/4] Municipios...")
    m = cargar_municipios()
    print("    municipios con voto:", f"{len(m):,}")
    corr_m = spearman(m, VOTO_MUN, SOC_MUN)
    corr_m.round(3).to_csv(os.path.join(SALIDAS, "corr_municipio.csv"))
    heatmap(corr_m, "Correlaci\u00f3n voto x sociedad \u00b7 municipios 2024",
           "heatmap_correlaciones_municipio.png")

    profm = m.groupby("ganador")[
        ["pct_participacion", "im_2020", "pct_rural", "pct_ingresos_bajos",
         "densidad"]].median().round(1)
    profm["n_municipios"] = m.groupby("ganador").size()
    profm.to_csv(os.path.join(SALIDAS, "perfiles_ganador_municipio.csv"))

    for et, b, r2 in guardar_betas(
            m, ["pct_sheinbaum", "pct_galvez", "pct_participacion"], X_MUN,
            ["sheinbaum", "galvez", "participacion"], "municipio"):
        barras_betas(b, f"Qu\u00e9 explica el voto por municipio \u00b7 {et}",
                     f"betas_municipio_{et}.png", r2)
    print("Listo.")


if __name__ == "__main__":
    main()
