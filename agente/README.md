# Agente experto ElctoGeoIA (local)

Agente conversacional que corre **100% en tu PC** (sin internet, sin servicios pagos)
y responde preguntas sobre el panel electoral de secciones en lenguaje natural,
ejecutando el análisis real del proyecto.

> Diseñado y probado para: Intel Core i7-8700 · 16 GB RAM · GTX 1060 3 GB · Windows 10.

## Arquitectura

```
Tú (pregunta en español)
  └─ Ollama + modelo local (qwen2.5:7b)     ← el "cerebro" que interpreta y redacta
       └─ orquestador.py (agente/orquestador.py)
            ├─ radiografia_municipio()      ← herramientas: código validado del proyecto
            ├─ radiografia_distrito()
            ├─ pronostico_2027()
            ├─ secciones_prioritarias()
            ├─ generar_mapa()               ← PNG del territorio en salidas_agente/
            │    (fondo=True → mapa base de OpenStreetMap, vía contextily)
            └─ generar_visualizador()      ← HTML interactivo (folium) del territorio
                 └─ panel_secciones (71,541 secciones × 150 variables, en RAM)
```

El modelo **no inventa cifras**: solo decide qué herramienta llamar con qué
argumentos y redacta la respuesta a partir de los resultados reales del panel.

## Instalación (Windows 10)

### 1. Ollama (el motor del modelo)

1. Descarga el instalador desde <https://ollama.com/download/windows> y ejecútalo.
2. Abre **PowerShell** y descarga el modelo (≈4.7 GB, una sola vez):

   ```powershell
   ollama pull qwen2.5:7b
   ```

   Ollama queda corriendo en segundo plano (icono de llama en la bandeja).

### 2. Python y dependencias

```powershell
cd ruta\donde\clonaste\ElctoGeoIA
pip install -r agente/requisitos.txt
```

> La primera vez que uses `generar_mapa`, si no encuentra la cartografía de
> secciones (`data/upload/mgsan_ext/SECCION.shp`), la descarga automáticamente
> desde un espejo público del MGS del INE (~86 MB, una sola vez). Requiere
> `pip install geopandas matplotlib py7zr` además de los requisitos base.
>
> **Mapa base de OpenStreetMap (opcional):** con `pip install contextily` y
> conexión a internet, `generar_mapa` puede agregar el fondo callejero de OSM
> (parámetro `fondo=True`; p. ej. "dame el mapa de participación de León sobre
> OpenStreetMap"). Sin internet o sin contextily, el mapa se genera sin fondo
> y el resultado incluye una nota explicándolo.

### 3. Datos

El agente lee `data/processed/panel_secciones.csv` o el comprimido
`data/processed/comprimidos/panel_secciones.csv.gz` (incluido en el repo, 60 MB).
No necesita nada de `data/upload/`.

### 4. Prueba sin modelo (verificación de instalación)

```powershell
python -m agente.orquestador --demo
```

Ejecuta las 4 herramientas con ejemplos (León, Guanajuato) y muestra las cifras.
Si ves los resultados, todo está instalado correctamente.

### 5. Arranca el agente

```powershell
python -m agente.orquestador
```

Y conversa:

```
Tú > Dame la radiografía de León, Guanajuato
Tú > ¿Qué escenarios 2027 pintan para Tuxtla Gutiérrez?
Tú > Cuáles son las 10 secciones prioritarias en Querétaro?
Tú > Radiografía del distrito 4 de Guanajuato
```

## Elección de modelo para tu hardware

| Modelo | RAM/VRAM | Velocidad en tu PC | Comentario |
|---|---|---|---|
| **qwen2.5:7b** (recomendado) | ~5 GB | Buena (GPU parcial) | Excelente en español y con herramientas |
| llama3.1:8b | ~5 GB | Buena | Alternativa sólida |
| qwen2.5:3b | ~2 GB | Muy rápida | Si quieres respuestas instantáneas, algo menos precisa |

Con 3 GB de VRAM, Ollama pone parte del modelo en GPU y el resto en RAM —
funciona bien con 7B (respuestas en segundos). Cambia de modelo con:

```powershell
python -m agente.orquestador --modelo llama3.1:8b
```

## Qué NO hace (honestidad metodológica)

- No "predice" con certeza: los escenarios 2027 son composición 2024 + deltas
  históricos calibrados; el backtest mostró que el swing uniforme es la mejor
  referencia (λ=0).
- No inventa datos: si el municipio no existe o es ambiguo, te lo dice.
- No ejecuta el pipeline completo (`src/panel_maestro.py` etc.): consulta el
  panel ya construido y validado.

## Archivos

| Archivo | Función |
|---|---|
| `agente/panel.py` | Carga del panel y catálogo de municipios (búsqueda tolerante a acentos) |
| `agente/herramientas.py` | Las 5 herramientas de análisis + especificaciones para el LLM |
| `agente/mapas.py` | Quinta herramienta: mapas PNG del territorio (tipología, ganador, pronóstico, participación, margen) ; `fondo=True` agrega mapa base de OpenStreetMap) |
| `agente/cartografia.py` | Carga (o descarga automática) del shapefile de secciones del INE |
| `agente/visualizador.py` | Sexta herramienta: `generar_visualizador`, HTML interactivo con fichas por sección |
| `agente/orquestador.py` | Bucle de chat con Ollama (tool calling) y modo `--demo` |
| `agente/datos/catalogo_municipios.csv` | Catálogo INEGI de 2,457 municipios (ent, mun, nombres) |
| `agente/requisitos.txt` | Dependencias (solo pandas + requests-free: urllib de la stdlib) |
