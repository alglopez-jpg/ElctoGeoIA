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
