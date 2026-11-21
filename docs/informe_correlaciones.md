# Correlación entre comportamiento electoral y sociedad
## Estudio a dos escalas: sección electoral y municipio

**Elección de referencia:** diputados federales 2024 (nivel sección) y presidencial 2024 (nivel municipio).
**Datos:** panel maestro de 71,541 secciones × 152 variables (INE + Censo 2020 INEGI) y base municipal INEGI/CONAPO + cómputos INE (2,462 municipios con voto).
**Nota de corrección:** este estudio detectó y corrigió un error del pipeline: la variable censal `VPH_PISODT` ("% de viviendas con piso **distinto** de tierra") se usaba como si fuera "piso **de** tierra", invirtiendo el indicador a nivel sección (media 96.6% → corregida a 3.4%, consistente con la base municipal). Todos los números de este informe usan el panel corregido.

---

## 1. Hallazgos principales

### 1.1 El voto tiene firma socioeconómica clara y consistente en ambas escalas

| Voto (2024) | Correlaciona POSITIVAMENTE con | Correlaciona NEGATIVAMENTE con |
|---|---|---|
| **Morena / Sheinbaum** | % sin educación básica (+0.31 sección, +0.26 municipio), % piso de tierra (+0.49 municipio), % ingresos bajos (+0.44 municipio) | % con automóvil (−0.41 sección), % con internet (−0.36 sección) |
| **PAN / Gálvez** | % con internet (+0.53 sección), % con auto (+0.46 sección), % adultos mayores (+0.37 sección) | % sin educación básica (−0.42 sección), % piso de tierra (−0.38 municipio) |
| **Participación** | % adultos mayores (+0.43 sección, beta +0.39), % con internet (+0.34 sección) | % sin educación básica (−0.32 sección, beta −0.36), % jóvenes 18-24 (−0.25 sección) |

La dimensiones **educativa y de conectividad** son las que más separan al voto oficialista del voto de oposición: las secciones con internet y automóvil votan sistemáticamente más PAN y participan más; las secciones con rezago educativo votan sistemáticamente más Morena.

### 1.2 La dimensión geoespacial: densidad y ruralidad pesan menos de lo esperado

Se incorporó una variable nueva al análisis: **densidad de población por sección** (hab/km², del polígono de la cartografía INE). Resultado notable:

- Controlando por todo lo demás (betas estandarizadas), la **densidad apenas explica el voto** (beta +0.07 para Morena, −0.04 para PAN).
- La **ruralidad por sí sola tampoco** (beta −0.05 Morena, +0.02 PAN a nivel sección).
- Lo que comúnmente se atribuye a "lo rural" en realidad es **capturado por el nivel socioeconómico** (educación, bienes, conectividad): una vez controlado el rezago social, la densidad casi no agrega poder explicativo.

Excepción municipal: la ruralidad sí sube la participación municipal (perfil mediano: municipios ganados por Sheinbaum son 100% rurales en la mediana, vs 76% en los ganados por Gálvez), en gran parte por el efecto del voto duro en zonas de marginación.

### 1.3 El envejecimiento predice participación (y electorado de oposición)

- **% de adultos mayores es el predictor multivariado más fuerte de participación** (beta +0.39 sección; +0.43 Spearman): donde hay más mayores, se vota más.
- Además, % 60ymás predice voto PAN (beta +0.25 sección) y baja el voto a Morena (beta −0.23). El electorado de la oposición es **sistemáticamente mayor**.

### 1.4 La marginación estructural (CONAPO) ordena el voto municipal

A escala municipal, **% de ingresos bajos** es el predictor dominante del voto presidencial 2024 (beta +0.48 Sheinbaum, −0.42 Gálvez). El índice `im_2020` de la base (mayor valor = mejores condiciones: correlaciona −0.85 con analfabetismo y −0.70 con ingresos bajos) se asocia con MENOS voto por Sheinbaum (ρ −0.39) y MÁS voto por Máynez (ρ +0.46): el voto por las opciones emergentes se concentra en municipios con mejores condiciones socioeconómicas, mientras el oficialismo domina donde hay más carencias.

### 1.5 Perfiles por tipología política de sección (dimensión política)

| Tipología | Internet | Auto | Sin básica | Piso tierra | Participación | Secciones | Población |
|---|---|---|---|---|---|---|---|
| Bastión oposicionista | 87.9% | 76.5% | 1.2% | 0.8% | 71.3% | 4,576 | 6.3 M |
| Competitiva (<5 pts) | 67.0% | 53.2% | 5.6% | 1.2% | 62.6% | 9,160 | 12.6 M |
| Dominante moderada | 64.7% | 50.0% | 6.2% | 1.4% | 62.7% | 22,446 | 32.4 M |
| Bastión oficialista | 57.1% | 39.0% | 8.5% | 1.8% | 59.1% | 35,359 | 53.8 M |

Lectura: el camino de la competitividad pasa por clases medias urbanas conectadas — en las 9,160 secciones que definieron la elección viven 12.6 millones de personas, con internet 10 puntos por encima de los bastiones oficialistas y participación 3.5 puntos mayor.

---

## 2. Qué explica el voto: ranking multivariado (betas estandarizadas, OLS)

### 2.1 Sección (R² Morena 0.26, PAN 0.36, participación 0.25)

- **Morena:** −auto (−0.35), −60ymás (−0.23), −internet (−0.15), −analfabetismo (−0.15), +sin básica (+0.11).
- **PAN:** +auto (+0.30), +internet (+0.28), +60ymás (+0.25), +analfabetismo (+0.14).
- **Participación:** +60ymás (+0.39), +analfabetismo (+0.19)ᵃ, −sin básica (−0.36), −auto (−0.10).

ᵃNota metodológica: el analfabetismo sube la participación controlando el resto —residual de voto duro en zonas rurales adultas—, mientras que la falta de básica la baja. Ambos efectos simultáneos solo se ven con análisis multivariado.

### 2.2 Municipio (R² Sheinbaum 0.27, Gálvez 0.17, participación 0.18)

- **Sheinbaum:** +ingresos bajos (+0.48), +piso de tierra (+0.31), −sin básica (−0.23), −im_2020 (−0.21; mayor índice = mejores condiciones).
- **Gálvez:** −ingresos bajos (−0.42), −piso de tierra (−0.30), +im_2020 (+0.30; mejores condiciones).
- **Participación:** −sin básica (−0.36), −piso de tierra (−0.33), +hacinamiento (+0.29), +sin drenaje (+0.20).

La contradicción aparente (participación baja donde hay piso de tierra, pero alta participación en municipios oficialistas) se resuelve distinguiendo escala: la carencia educativa-estructural detitulo la participación; el voto duro organizado en zonas pobres la sostiene. A escala fina, la sección es la unidad correcta para separar ambos efectos.

---

## 3. Implicaciones operativas

1. **Para campañas:** el targeting socioeconómico más eficiente es conectividad/bienes (internet, auto) y estructura educativa, no ruralidad per se. La variable nueva **densidad de sección** permite priorizar territorio urbano denso con bajo costo operativo.
2. **Para el análisis 2027:** el modelo de swing territorial y su backtest fueron re-entrenados con el panel corregido en esta misma entrega (`backtest.py` → `pronostico_2027.py` → panel reconstruido). El pronóstico por sección no cambia (depende solo de votos: MAE backtest 35.43% vs swing uniforme 26.60%, mismo ordenamiento); los semianchos conformales se recalibraron marginalmente (p. ej. morena 19.1→19.3 pts). El modelo SAR del notebook 07 también fue re-entrenado con el panel corregido (iguales especificación y datos de entrada): ρ 0.270→0.249, pseudo-R² 0.589→0.568; las categorías de residuo son prácticamente idénticas (en_lo_esperado 45,801→45,797; sobre 3,983→3,988; sub 3,192→3,191 de 52,976 secciones), lo que confirma que la radiografía de secciones sobre/sub-performantes es robusta a la corrección del indicador.
3. **Voto joven:** consistente con la literatura, % 18-24 se asocia con menor participación (ρ −0.25); memiliki oportunidad de movilización en secciones jóvenes urbanas con alta conectividad.

---

## 4. Archivos reproducibles

| Archivo | Contenido |
|---|---|
| `src/correlaciones.py` | Script que regenera todas las tablas y figuras |
| `data/processed/correlaciones/corr_seccion.csv` | Spearman voto × sociedad, 8 variables de voto × 12 sociales (sección) |
| `data/processed/correlaciones/corr_municipio.csv` | Spearman candidaturas × 11 sociales (municipio) |
| `data/processed/correlaciones/betas_*.csv` | 6 rankings de betas estandarizadas (3 sección + 3 municipio) |
| `data/processed/correlaciones/perfiles_*.csv` | Perfiles medianos por tipología de sección y por ganador municipal |
| `figuras/heatmap_correlaciones_seccion.png` | Heatmap sección |
| `figuras/heatmap_correlaciones_municipio.png` | Heatmap municipio |
| `figuras/betas_*.png` | 6 figuras de betas |

Reproducir: `python src/correlaciones.py`

**Sources:** INE — cómputos distritales 2012-2024 y MGS cartografía; INEGI — Censo de Población y Vivienda 2020 (manzanas + ITER + gaia) y Marco Geoestadístico; CONAPO — Índice de Marginación 2020.
