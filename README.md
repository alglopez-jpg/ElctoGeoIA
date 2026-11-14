# ElctoGeoIA
## Fase 2b — Refinamiento de supuestos (opción C)

1. **Mapa distrito×coalición** (`data/processed/mapa_distrito_coaliciones.csv`):
   construido desde los archivos de candidaturas de los cómputos INE.
   Confirma coaliciones parciales por distrito: en 2021, 144 distritos con
   ambas coaliciones (Va por México y Juntos Hacemos Historia), 72 solo con
   la oposición y 37 solo con el oficialismo. La agregación por columna es
   correcta: cada columna de coalición solo tiene votos donde compitió.
2. **Peso de coaliciones**: se mantiene el reparto equitativo 1/N por
   neutralidad; los porcentajes de los convenios pueden sustituirse en
   `config_coaliciones.py`. Para el modelado se recomienda operar también
   a nivel bloque (inmune al supuesto de reparto).
3. **Cobertura rural del censo**: se integró el ITER 2020 (resultados por
   localidad) con las localidades rurales del servicio gaia, asignadas a
   sección por centroide (`src/censo_rural.py`). El panel ahora cubre
   105.1 M de habitantes (99.2 M urbanos + 5.9 M rurales netos nuevos;
   22.4 M de población rural repartidos en 22,131 secciones) e incluye
   `pct_rural` por sección.

---

# Fase 3 (opción B) — Modelo predictivo 2027

## Arquitectura validada: dos componentes

1. **Nivel nacional = escenario** (no se predice con datos territoriales)
2. **Distribución territorial = composición 2024 por sección**, rakeada al
   escenario (`src/pronostico_2027.py`)

## Backtest fuera de época (transiciones pres→intermedia)

| Línea base | 12→15 entrena / 18→21 prueba | 18→21 entrena / 12→15 prueba |
|---|---|---|
| Persistencia (nada cambia) | 37.2% | 55.1% |
| Modelo territorial calibrado | 35.3% | 34.6% |
| **Swing uniforme calibrado (λ=0)** | **26.6%** | **31.3%** |

**Hallazgo honesto**: el swing uniforme calibrado supera al modelo
territorial en ambas direcciones. Con solo dos transiciones, el patrón
territorial aprendido en una era política no generaliza a otra. La señal
territorial de 2024 es el mejor predictor de la distribución territorial
de 2027; las covariables describen, no predicen el swing.

## Escenarios 2027 (editables en `src/pronostico_2027.py`)

Cambio histórico 2018→2021 aplicado al punto de partida 2024, en tres
intensidades (% del voto emitido, escenario `inercia_intermedia`):
participación 51.6%, oficialismo 55.0% (Morena 40.1 + PVEM 9.8 + PT 5.2),
oposición 27.8% (PAN 16.1 + PRI 11.2 + PRD 0.5), MC 14.0%.

## Entregables

- `notebooks/05_modelo_2027.ipynb` — backtest, escenarios, pronóstico e
  incertidumbre, con salidas ejecutadas
- `data/processed/pronostico_2027_seccion.csv` — pronóstico por sección
  (3 escenarios × 10 componentes)
- `data/processed/pronostico_2027_semiancho.csv` — intervalos conformales 90%
  (semiancho Morena: ±19 puntos de LN; abstención: ±16)
- `figuras/pronostico_2027_*.png` — mapas de oficialismo, ganador e
  incertidumbre

## Qué esperar del pronóstico

- **Sí**: la geografía del voto (bastiones, competitividad, mapa ganador),
  dado un escenario nacional
- **No**: el nivel nacional (es escenario, no predicción), el voto a
  partidos nuevos (PAZ, Somos México) ni efectos de nuevas coaliciones
