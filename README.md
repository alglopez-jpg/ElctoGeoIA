# ElctoGeoIA — Análisis geoespacial electoral de México

Proyecto de análisis geoespacial del comportamiento electoral mexicano y su
relación con aspectos sociodemográficos y socioeconómicos, con un pipeline
completo desde la descarga de datos públicos hasta un modelo predictivo
para la elección federal intermedia de 2027.

## Contenido del repositorio

| Directorio | Contenido |
|---|---|
| `notebooks/` | 6 notebooks ejecutados: análisis municipal (01-04), modelo 2027 (05) y exploración del panel de secciones (06) |
| `src/` | Pipeline reproducible: descarga, carga, armonización, censo, panel, backtest y pronóstico |
| `data/processed/` | Tablas procesadas (el panel completo viaja comprimido en `comprimidos/`) |
| `figuras/` | Mapas y diagnósticos de todos los análisis |

## Fase 1 — Análisis municipal (elección presidencial 2024)

Pipeline de fuentes públicas (INE cómputos 2024, CONAPO marginación 2020,
INEGI gaia) y 4 notebooks ejecutados:

1. `01_comportamiento_electoral.ipynb` — mapas del voto y participación
2. `02_correlaciones_voto_sociedad.ipynb` — Pearson/Spearman voto vs sociedad
3. `03_autocorrelacion_espacial.ipynb` — Moran global y LISA (Anselin 1995)
4. `04_regresion_espacial.ipynb` — MCO vs SAR/SEM (`spreg`)

Hallazgos: el voto está espacialmente agrupado (Moran I=0.54 municipal);
mayor marginación → más voto a la coalición gobernante (ρ hasta 0.49);
el modelo SAR supera a MCO (AIC 18,870 vs 19,524).

## Fase 2 — Panel de secciones electorales (2012-2024)

**Archivo central**: `data/processed/comprimidos/panel_secciones.csv.gz`
— **71,541 secciones (marco INE 2024) × 150 columnas**. El GeoPackage para
QGIS se regenera con `python src/panel_maestro.py` (~260 MB, no se versiona).

### Pipeline

| Paso | Script | Resultado |
|---|---|---|
| Supuestos de coaliciones por año | `src/config_coaliciones.py` | Documentación de cada redistribución |
| Carga de 5 elecciones (dip. MR) | `src/cargar_elecciones.py` | `votos_seccion_{año}.csv` |
| Armonización espacial | `src/armonizar_secciones.py` | `votos_seccion_{año}_m2024.csv` + `crosswalk_2018_2024.csv` |
| Censo 2020 urbano → sección | `src/censo_seccion.py` | `censo2020_seccion_indicadores.csv` |
| Censo 2020 rural → sección | `src/censo_rural.py` | indicadores totales (105.1M hab) |
| Panel final | `src/panel_maestro.py` | `panel_secciones.csv` / `.gpkg` |

### Fuentes

- **2012, 2015**: Magar (ITAM), `elecRetrns` — cómputos por casilla
- **2018, 2021, 2024**: INE, cómputos distritales (diputaciones federales)
- **Cartografía maestra**: MGSAN 2024 del INE (71,541 secciones)
- **Cartografía 2018**: INE por estado (para el crosswalk areal)
- **Censo 2020**: INEGI, resultados por AGEB/manzana urbana + ITER
  (localidades) + manzanas y localidades del servicio gaia

### Decisiones metodológicas

1. **Cargo comparable**: diputados federales de mayoría relativa en los 5
   años (el cargo que se elige en 2027).
2. **Coaliciones**: reparto equitativo 1/N, documentado por año; el mapa
   distrito×coalición valida las coaliciones parciales por distrito.
3. **Armonización**: match directo + crosswalk areal para 1,712 secciones
   desaparecidas. Cobertura de votos >99% (98.9% en 2012).
4. **Censo**: urbano (manzana) + rural (localidad), 105.1M habitantes.
5. **Casillas especiales** (sin sección) excluidas.

### Validación

- Participación nacional: 62.8% (2012), 47.5% (2015), 62.7% (2018),
  52.2% (2021), 59.9% (2024) — coincide con cifras oficiales.
- Voto 2024 (dip. MR): Morena 42.5%, PVEM 8.8%, PT 5.7%, PAN 17.6%,
  PRI 11.6%, MC 11.4% — coherente con oficiales.
- Persistencia territorial del voto (ρ 2018 vs 2024):
  PAN 0.71, Morena 0.53, PRI 0.45, MC 0.38.

El panel incluye: voto por partido-año, participación, indicadores
censales 2020, `tipologia_2024` (bastión oficialista / bastión oposición /
dominante moderada / competitiva), `ganador_2024`, `margen_2024`,
`volatilidad_18_24` y el pronóstico 2027 por escenario
(`inercia_intermedia_*`, `oficialismo_resistente_*`,
`oposicion_recupera_*`).

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
   sección por centroide (`src/censo_rural.py`). El panel cubre 105.1 M
   de habitantes (99.2 M urbanos + 22.4 M de población rural repartidos
   en 22,131 secciones) e incluye `pct_rural` por sección.

## Fase 3 (opción B) — Modelo predictivo 2027

### Arquitectura validada: dos componentes

1. **Nivel nacional = escenario** (no se predice con datos territoriales)
2. **Distribución territorial = composición 2024 por sección**, rakeada al
   escenario (`src/pronostico_2027.py`)

### Backtest fuera de época (transiciones pres→intermedia)

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

### Escenarios 2027 (editables en `src/pronostico_2027.py`)

Cambio histórico 2018→2021 aplicado al punto de partida 2024, en tres
intensidades (% del voto emitido, escenario `inercia_intermedia`):
participación 51.6%, oficialismo 55.0% (Morena 40.1 + PVEM 9.8 + PT 5.2),
oposición 27.8% (PAN 16.1 + PRI 11.2 + PRD 0.5), MC 14.0%.

### Entregables

- `notebooks/05_modelo_2027.ipynb` — backtest, escenarios, pronóstico e
  incertidumbre, con salidas ejecutadas
- `data/processed/pronostico_2027_seccion.csv` — pronóstico por sección
  (3 escenarios × 10 componentes)
- `data/processed/pronostico_2027_semiancho.csv` — intervalos conformales 90%
  (semiancho Morena: ±19 puntos de LN; abstención: ±16)
- `figuras/pronostico_2027_*.png` — mapas de oficialismo, ganador e
  incertidumbre

## Fase 4 (opción A) — Exploración del panel de secciones

`notebooks/06_exploracion_panel_secciones.ipynb`:

- **Moran's I del voto a Morena a nivel sección: 0.747** — el voto está
  fuertemente agrupado espacialmente; LISA identifica 14,886 secciones en
  clusters Alto-Alto (bastiones) y 16,013 en Bajo-Bajo (oposición).
- **Tipología de secciones (2024)**: 35,359 bastiones oficialistas,
  22,446 dominantes moderadas, 9,160 competitivas (<5 pts de margen) y
  4,576 bastiones de oposición; cruzada con volatilidad 2018→2024.
- **Correlaciones voto-censo fino** (escala sección, la más fina posible):
  Morena vs sin educación básica ρ≈+0.31; PAN vs automóvil ρ≈+0.4;
  MC vs internet ρ≈+0.35.
- Swing territorial 2018→2024 y panoramas de voto/participación por sección.
- **Nota metodológica**: participación >100% en algunas secciones refleja
  votos emitidos fuera de la sección de la lista nominal (traslados);
  documentado como límite de los cómputos por casilla.

## Reproducción

```bash
pip install -r requirements.txt
python src/descarga_datos.py     # fuentes públicas municipales (fase 1)
python src/cargar_elecciones.py  # requiere datos brutos en data/upload/
python src/armonizar_secciones.py
python src/censo_seccion.py && python src/censo_rural.py
python src/panel_maestro.py      # regenera panel + GeoPackage (QGIS)
python src/backtest.py && python src/pronostico_2027.py
jupyter lab notebooks/
```

## Referencias

- Anselin, L. (1995). *Local Indicators of Spatial Association—LISA*.
  Geographical Analysis, 27(2), 93–115.
- INE (2018-2024). Cómputos Distritales de las elecciones federales.
- INEGI (2020). Censo de Población y Vivienda 2020 y Marco Geoestadístico.
- CONAPO (2020). Índice de marginación por municipio.
- Magar, E. (ITAM). `elecRetrns` — resultados electorales por casilla.

## Licencias

Los datos del INE, INEGI y CONAPO son de uso libre bajo los términos de los
Sistemas Nacionales de Información Estadística y Geográfica y de datos
abiertos del Gobierno de México. El código de este repositorio se libera
bajo licencia MIT.
