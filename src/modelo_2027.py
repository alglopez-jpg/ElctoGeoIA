"""Modelo predictivo 2027: swing relativo territorial a nivel sección.

Arquitectura:
1. Composición sobre LISTA NOMINAL por sección-año: partidos + nulos +
   abstención (suma 1). Captura la caída de participación en intermedias.
2. Objetivo: cambio en log-ratio aditivo (ALR, ref = abstención) entre
   t0 y t1, menos la media nacional -> SOLO el swing territorial relativo.
3. Features en t0: ALR de la composición, rezago espacial (reina),
   participación, covariables censales 2020.
4. Modelo: HistGradientBoosting por componente (statsmodels no; sklearn).
5. Calibración: raking del pronóstico a un escenario nacional definido
   por el usuario (el nivel nacional NO se predice con datos territoriales).
6. Incertidumbre: semianchos conformales a partir de errores del backtest.

Limitaciones documentadas: la oferta de 2027 incluye partidos nuevos
(PAZ, Somos México) sin historial; se trata como escenario, no como
predicción. Falacia ecológica vigente: modelamos áreas, no votantes.
"""
import os

import numpy as np
import pandas as pd
from libpysal.weights import Queen, KNN
from sklearn.ensemble import HistGradientBoostingRegressor

BASE = os.path.join(os.path.dirname(__file__), "..")
PROCESSED = os.path.join(BASE, "data", "processed")

PARTIDOS = ["pan", "pri", "prd", "pvem", "pt", "mc", "morena", "otros"]
COMPONENTES = PARTIDOS + ["nulos", "abstencion"]
REF = "abstencion"

COVARS = ["pob_total", "pct_rural", "pct_sin_basica", "pct_analfabeta",
          "pct_piso_tierra", "pct_sin_drenaje", "pct_sin_bienes",
          "pct_auto", "pct_internet", "pct_sin_salud", "pct_60ymas",
          "pct_18a24"]


def cargar_composicion(anio):
    """Composición sobre lista nominal por sección para un año."""
    v = pd.read_csv(os.path.join(PROCESSED, f"votos_seccion_{anio}_m2024.csv"),
                    index_col=0)
    v.index = v.index.astype(str).str.zfill(6)
    comp = v[PARTIDOS].copy()
    comp["nulos"] = v["nulos"]
    emitidos = comp.sum(axis=1)
    comp["abstencion"] = (v["lista_nominal"] - emitidos).clip(lower=0)
    return comp.div(comp.sum(axis=1).replace(0, np.nan), axis=0).dropna()


def alr(comp, ref=REF):
    s = comp.clip(lower=1e-4)
    return np.log(s.drop(columns=[ref]).div(s[ref], axis=0))


def inv_alr(z, cols, ref=REF):
    e = np.exp(z)
    e[ref] = 1.0
    e = e[[c for c in cols if c != ref] + [ref]]
    return e.div(e.sum(axis=1), axis=0)


def construir_pesos(gdf, k=8):
    """Reina; cae a k-vecinos si hay islas."""
    w = Queen.from_dataframe(gdf, use_index=False)
    if w.islands:
        w = KNN.from_dataframe(gdf, k=k)
    w.transform = "r"
    return w


def rezago_espacial(w, df):
    return pd.DataFrame(w.sparse @ df.values, index=df.index,
                        columns=["W_" + c for c in df.columns])


def matriz_features(comp_t0, w, covars):
    """Features en t0: ALR + rezago espacial + participación + censo."""
    z = alr(comp_t0)
    lag = rezago_espacial(w, z)
    emitidos = comp_t0[PARTIDOS + ["nulos"]].sum(axis=1)
    part = 100 * emitidos / comp_t0.sum(axis=1).replace(0, np.nan)
    X = pd.concat([z.add_suffix("_t0"), lag, part.rename("participacion_t0"),
                   covars], axis=1)
    return X


def objetivo_relativo(comp_t0, comp_t1):
    """Cambio en ALR t0->t1 menos la media nacional (swing territorial)."""
    y = alr(comp_t1) - alr(comp_t0)
    return y - y.mean()


def ajustar(X, y):
    return {c: HistGradientBoostingRegressor(
        max_depth=4, learning_rate=0.05, max_iter=400, random_state=42
    ).fit(X, y[c]) for c in y.columns}


def predecir_swing(modelos, X):
    return pd.DataFrame({c: m.predict(X) for c, m in modelos.items()},
                        index=X.index)


def componer(comp_t0, swing, w_nacional=None):
    """Aplica el swing relativo a la composición t0 y renormaliza."""
    z0 = alr(comp_t0)
    z1 = z0 + swing.reindex(columns=z0.columns, fill_value=0)
    return inv_alr(z1, list(comp_t0.columns), REF)


def rake_nacional(comp, pesos, objetivo, n_iter=300):
    """Calibra composiciones por sección para que el promedio ponderado
    coincida con el escenario nacional `objetivo` {componente: proporción}."""
    s = comp.copy()
    t = pd.Series(objetivo).reindex(s.columns).fillna(0)
    t = t / t.sum()
    pesos = pesos / pesos.sum()
    for _ in range(n_iter):
        actual = s.mul(pesos, axis=0).sum()
        s = s * (t / actual).replace([np.inf, -np.inf], 1.0)
        s = s.div(s.sum(axis=1), axis=0)
    return s


def semiancho_conformal(abs_err, alfa=0.1):
    return pd.Series(np.quantile(abs_err.values, 1 - alfa, axis=0),
                     index=abs_err.columns)


def evaluar(comp_real, comp_pred, comp_base, pesos):
    """MAE por componente contra realidad y contra línea base persistencia."""
    def mae(a, b):
        d = (a - b).abs().mul(pesos, axis=0).sum().sum() / pesos.sum()
        return 100 * d
    return {"MAE_modelo_%": mae(comp_real, comp_pred),
            "MAE_persistencia_%": mae(comp_real, comp_base)}
