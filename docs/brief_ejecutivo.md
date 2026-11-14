# ElctoGeoIA — Inteligencia geoespacial electoral a nivel sección

**Brief ejecutivo** · Análisis del comportamiento electoral mexicano y su relación con la socioeconomía, a la escala más fina que existe: la sección electoral (~1,500 votantes promedio).

---

## 1. La propuesta

Transformamos datos electorales y censales **100% oficiales y públicos** (INE, INEGI, CONAPO) en inteligencia accionable para campañas, partidos, organismos electorales, investigadores, medios y organizaciones de la sociedad civil.

La pregunta que respondemos es simple y poderosa: **¿dónde está el voto, quién lo tiene, y cómo puede moverse en 2027?**

## 2. Qué tenemos (y casi nadie más tiene)

- **Panel geoespacial único en México**: 71,541 secciones electorales (marco INE 2024) × 150 variables
- **Historia electoral completa**: 5 elecciones federales de diputados (2012, 2015, 2018, 2021, 2024), armonizadas espacialmente entre cartografías distintas (cobertura >99% de los votos)
- **Socioeconomía fina**: Censo 2020 desagregado a sección (manzana urbana + localidad rural, 105 millones de habitantes cubiertos)
- **Validación rigurosa**: participación y voto por partido coinciden con cifras oficiales INE; metodología documentada y reproducible de punta a punta

## 3. Hallazgos que ya estamos viendo

**El voto está fuertemente agrupado en el espacio.** El índice de Moran a nivel sección es **0.747**: el voto a Morena forma clusters territorialmente compactos de **14,886 secciones** (bastiones) frente a **16,013 secciones** de oposición contigua. La geografía electoral mexicana está cartografiada con precisión de sección.

**El mapa de batalla 2027 está identificado.** Tipología de secciones (elección 2024):

| Tipo de sección | Cantidad | Qué significa |
|---|---|---|
| Bastión oficialista (≥20 pts de margen) | 35,359 | Voto duro, prioridad de defensa |
| Dominante moderada | 22,446 | Ganadas pero movibles |
| **Competitiva (<5 pts de margen)** | **9,160** | **Donde se define la elección** |
| Bastión de oposición | 4,576 | Objetivo de expansión |

**El voto tiene firma socioeconómica.** A escala de sección: el PAN correlaciona con tenencia de automóvil (ρ≈+0.40) e internet (ρ≈+0.35); Morena con carencia de educación básica (ρ≈+0.31). El perfil socioeconómico de cada sección predice su comportamiento electoral.

**El swing 2018→2024 fue geográficamente estructurado.** MC y PAN avanzaron en zonas urbanas medias del norte y el Bajío; el oficialismo consolidó el sur y las periferias populares. Sabemos qué secciones se movieron, cuánto y en qué dirección.

**Pronóstico 2027 por sección, con escenarios e incertidumbre.** Combinamos la composición 2024 de cada sección con escenarios nacionales calibrados con la evidencia histórica (backtest honesto). Ejemplo del escenario base: participación 51.6%, oficialismo 55.0% del voto emitido, oposición 27.8%, MC 14.0% — **y la distribución territorial sección por sección de cada escenario, con intervalos de confianza**.

## 4. Qué podemos hacer por tu territorio

Para cualquier **municipio, distrito federal o local** que te interese, entregamos:

1. **Radiografía electoral**: tipología de sus secciones, bastiones, márgenes y volatilidad 2012-2024
2. **Perfil socioeconómico × voto**: qué distingue a las secciones que se mueven
3. **Pronóstico 2027 por escenario**: mapas de expectativa e incertidumbre por sección
4. **Priorización de terreno**: ranking de secciones competitivas y volátiles donde cada peso de campaña rinde más
5. **Cartografía lista para usar**: GeoPackage para QGIS + reporte con mapas y cifras

*Todo con la trazabilidad metodológica completa: fuentes oficiales, supuestos documentados y validación contra resultados observados.*

## 5. Cómo solicitar un análisis

Solo necesitamos que nos indiques **el municipio o distrito de interés**. El panel nacional ya está construido y validado, por lo que el análisis específico se entrega en **días, no meses**: reporte ejecutivo + mapas + capas GIS.

---

*ElctoGeoIA — Datos públicos, inteligencia de sección. Metodología completa y reproducible en github.com/alglopez-jpg/ElctoGeoIA*
