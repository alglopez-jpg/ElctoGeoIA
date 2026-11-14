"""Pronóstico 2027 por sección, calibrado a escenarios nacionales.

Diseño de dos componentes (validado en el backtest):
1. NIVEL NACIONAL: escenario definido por el usuario (NO se predice con
   datos territoriales; el backtest mostró que el swing uniforme calibrado
   es la mejor línea base disponible).
2. DISTRIBUCIÓN TERRITORIAL: la composición 2024 de cada sección, rakeada
   al escenario nacional.

Escenarios (editables): parten del resultado 2024 y aplican el cambio
histórico observado en la transición presidencial->intermedia
2018->2021, en distintas intensidades. La abstención del escenario
reproduce la caída típica de participación en intermedias.
"""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
import modelo_2027 as m

BASE = os.path.join(os.path.dirname(__file__), "..")
PROCESSED = os.path.join(BASE, "data", "processed")


def composicion_nacional(anio):
    comp = m.cargar_composicion(anio)
    pesos = comp.sum(axis=1)
    return (comp.mul(pesos, axis=0).sum() / pesos.sum())


def construir_escenarios():
    """Escenarios 2027 a partir del cambio observado 2018->2021."""
    nac24 = composicion_nacional(2024)
    nac18 = composicion_nacional(2018)
    nac21 = composicion_nacional(2021)
    delta = nac21 - nac18  # cambio observado presidencial->intermedia

    escenarios = {}
    for nombre, factor in [("inercia_intermedia", 1.0),
                           ("oficialismo_resistente", 0.5),
                           ("oposicion_recupera", 1.5)]:
        obj = (nac24 + factor * delta).clip(lower=0.001)
        obj = obj / obj.sum()
        escenarios[nombre] = obj
    return nac24, nac18, nac21, delta, escenarios


def main():
    print("[1/3] Composiciones nacionales...")
    nac24, nac18, nac21, delta, escenarios = construir_escenarios()
    print("    2024:", {k: f"{100*v:.1f}%" for k, v in nac24.items()})
    print("    cambio 2018->2021 (puntos):",
          {k: f"{100*v:+.1f}" for k, v in delta.items()})

    print("[2/3] Composición 2024 por sección...")
    comp24 = m.cargar_composicion(2024)
    pesos = pd.read_csv(os.path.join(PROCESSED,
                                     "votos_seccion_2024_m2024.csv"),
                        index_col=0)["lista_nominal"]
    pesos.index = pesos.index.astype(str).str.zfill(6)
    pesos = pesos.reindex(comp24.index).fillna(1)

    print("[3/3] Raking por escenario...")
    salidas = []
    for nombre, obj in escenarios.items():
        print(f"    escenario '{nombre}':",
              {k: f"{100*v:.1f}%" for k, v in obj.items()
               if k in m.PARTIDOS or k == "abstencion"})
        pron = m.rake_nacional(comp24, pesos, obj.to_dict())
        pron = pron.add_prefix(f"{nombre}_")
        salidas.append(pron)
    out = pd.concat(salidas, axis=1)
    out.index.name = "id"
    out.to_csv(os.path.join(PROCESSED, "pronostico_2027_seccion.csv"))

    err_uniforme = pd.read_csv(
        os.path.join(PROCESSED, "backtest_errores_absolutos.csv"), index_col=0)
    sem = m.semiancho_conformal(err_uniforme)
    sem.to_csv(os.path.join(PROCESSED, "pronostico_2027_semiancho.csv"))
    print("\nSemiancho conformal 90% (puntos pct, del backtest swing uniforme):")
    print((100 * sem).round(1).to_string())
    print("\nPronóstico guardado: pronostico_2027_seccion.csv")


if __name__ == "__main__":
    main()
