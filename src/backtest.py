"""Backtest del modelo de swing territorial.

Transiciones presidencial->intermedia (análogas a 2024->2027):
- Entrenamiento: 2012 -> 2015
- Prueba:        2018 -> 2021 (y dirección inversa como robustez)

Líneas base de comparación:
- Persistencia: la composición de t0 no cambia.
- Swing uniforme: composición t0 calibrada (raking) al resultado nacional t1.
"""
import os
import sys

import geopandas as gpd
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
import modelo_2027 as m

BASE = os.path.join(os.path.dirname(__file__), "..")
UPLOAD = os.path.join(BASE, "data", "upload")
PROCESSED = os.path.join(BASE, "data", "processed")


def cargar_todo():
    compos = {a: m.cargar_composicion(a) for a in (2012, 2015, 2018, 2021, 2024)}
    g = gpd.read_file(os.path.join(UPLOAD, "mgsan_ext", "SECCION.shp"))
    g["id"] = g["ENTIDAD"].astype(int).astype(str).str.zfill(2) + \
        g["SECCION"].astype(int).astype(str).str.zfill(4)
    g = g.set_index("id")
    cov = pd.read_csv(
        os.path.join(PROCESSED, "censo2020_seccion_indicadores_total.csv"),
        index_col=0)
    cov.index = cov.index.astype(str).str.zfill(6)
    return compos, g[["geometry"]], cov


def alinear(comp, cov):
    idx = comp.index.intersection(cov.index)
    return comp.loc[idx], cov.loc[idx]


_cache_w = {}


def pesos_para(gdf, idx):
    key = (len(idx), idx[0] if len(idx) else "")
    if key not in _cache_w:
        _cache_w[key] = m.construir_pesos(gdf.loc[idx])
    return _cache_w[key]


def transicion(compos, cov, gdf, t0, t1):
    c0, cv = alinear(compos[t0], cov)
    idx = c0.index.intersection(compos[t1].index)
    c0 = c0.loc[idx]
    c1 = compos[t1].loc[idx]
    cv = cv.loc[idx]
    w = pesos_para(gdf, idx)
    X = m.matriz_features(c0, w, cv)
    y = m.objetivo_relativo(c0, c1)
    ok = X.notna().all(axis=1) & y.notna().all(axis=1)
    return X[ok], y[ok], c0[ok], c1[ok]


def main():
    print("[1/4] Cargando datos...")
    compos, gdf, cov = cargar_todo()
    idx_comun = gdf.index
    for a in compos:
        compos[a] = compos[a].reindex(idx_comun).dropna()
        print(f"    {a}: {len(compos[a]):,} secciones")
    print("[3/4] Backtest 2012->2015 (entrenar) / 2018->2021 (probar)...")
    X_tr, y_tr, c0_tr, c1_tr = transicion(compos, cov, gdf, 2012, 2015)
    X_te, y_te, c0_te, c1_te = transicion(compos, cov, gdf, 2018, 2021)
    print(f"    train: {len(X_tr):,} | test: {len(X_te):,}")
    modelos = m.ajustar(X_tr, y_tr)
    swing_pred = m.predecir_swing(modelos, X_te)
    comp_pred = m.componer(c0_te, swing_pred)

    pesos = c1_te.sum(axis=1)
    nac_t1 = (c1_te.mul(pesos, axis=0).sum() / pesos.sum()).to_dict()
    comp_uniforme = m.rake_nacional(c0_te, pesos, nac_t1)
    comp_pred_cal = m.rake_nacional(comp_pred, pesos, nac_t1)
    res = m.evaluar(c1_te, comp_pred_cal, c0_te, pesos)
    res_uniforme = m.evaluar(c1_te, comp_uniforme, c0_te, pesos)
    err = (comp_pred_cal - c1_te).abs()
    err_uniforme = (comp_uniforme - c1_te).abs()
    err_uniforme.to_csv(os.path.join(
        PROCESSED, "backtest_errores_swing_uniforme.csv"))
    semiancho = m.semiancho_conformal(err_uniforme)

    print("\n    Resultados (MAE % ponderado por lista nominal):")
    print(f"      persistencia (nada cambia): {res['MAE_persistencia_%']:.2f}%")
    print(f"      swing uniforme (calibrado):  {res_uniforme['MAE_modelo_%']:.2f}%")
    print(f"      MODELO (swing territorial calibrado): {res['MAE_modelo_%']:.2f}%")
    print("\n    MAE por componente (modelo, puntos pct):")
    for c in err.columns:
        print(f"      {c:10s}: {err[c].mean():.2f}  (semiancho 90%: {semiancho[c]:.2f})")

    print("\n[4/4] Robustez: dirección inversa (2018->2021 entrena, 2012->2015 prueba)")
    modelos2 = m.ajustar(X_te, y_te)
    swing2 = m.predecir_swing(modelos2, X_tr)
    comp2 = m.componer(c0_tr, swing2)
    pesos_tr = c1_tr.sum(axis=1)
    nac_15 = (c1_tr.mul(pesos_tr, axis=0).sum() / pesos_tr.sum()).to_dict()
    comp2_cal = m.rake_nacional(comp2, pesos_tr, nac_15)
    res2 = m.evaluar(c1_tr, comp2_cal, c0_tr, pesos_tr)
    print(f"      persistencia: {res2['MAE_persistencia_%']:.2f}% | "
          f"modelo: {res2['MAE_modelo_%']:.2f}%")

    pd.DataFrame({
        "MAE_modelo_%": [res["MAE_modelo_%"], res2["MAE_modelo_%"]],
        "MAE_persistencia_%": [res["MAE_persistencia_%"],
                               res2["MAE_persistencia_%"]],
    }, index=["2012->2015 entrenó / 2018->2021 probó",
              "2018->2021 entrenó / 2012->2015 probó"]
    ).to_csv(os.path.join(PROCESSED, "backtest_resumen.csv"))
    err.to_csv(os.path.join(PROCESSED, "backtest_errores_absolutos.csv"))
    print("\nBacktest listo.")


if __name__ == "__main__":
    main()
