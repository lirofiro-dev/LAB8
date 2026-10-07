# Lab 8 - DuckDB

Repositorio base del laboratorio 8 del curso **CC3084 - Data Science**
(Universidad del Valle de Guatemala, Ciclo 2, 2026).

Este es el repositorio **proporcionado por el docente**. Contiene la estructura
del proyecto, el ambiente de ejecucion basado en Docker y un script de descarga
de datos. Todo lo demas debe ser construido por cada equipo.

## Trabajo con fork

El laboratorio se desarrolla y se entrega sobre un **fork** de este repositorio.
No se trabaja directamente sobre el repositorio del docente.

1. Realice un fork de este repositorio:
   <https://github.com/menene/duckdb>

2. Clone **su propio fork** (no el del docente):

   ```bash
   git clone https://github.com/<su-usuario>/duckdb.git
   cd duckdb
   ```

3. Opcional, para recibir correcciones publicadas por el docente:

   ```bash
   git remote add upstream https://github.com/menene/duckdb.git
   git fetch upstream
   ```

Realice commits frecuentes y descriptivos: el historial del repositorio es parte
de la evaluacion. **La entrega del laboratorio es la URL de su fork.**

## Estructura

```text
duckdb/
|
+-- data/
|   +-- raw/
|   +-- processed/
|
+-- notebooks/
|
+-- scripts/
|
+-- sql/
|
+-- docs/
|
+-- Dockerfile
+-- metabase.Dockerfile
+-- docker-compose.yml
+-- README.md
```

Proposito de cada directorio y archivo principal:

- `data/raw/`: almacena los archivos Parquet originales descargados desde la TLC. No se versiona en Git.
- `data/processed/`: almacena datos derivados o bases generadas durante el analisis. No se versiona en Git.
- `notebooks/`: contiene notebooks para exploracion, analisis y visualizaciones.
- `scripts/`: contiene scripts reproducibles, como la descarga de datos.
- `sql/`: contiene consultas SQL documentadas para DuckDB.
- `docs/`: contiene documentacion adicional del laboratorio, resultados y evidencias.
- `Dockerfile`: define el ambiente Python/Jupyter para el analisis.
- `metabase.Dockerfile`: define el ambiente de Metabase con el driver de DuckDB.
- `docker-compose.yml`: levanta los servicios del laboratorio y monta las carpetas del proyecto.
- `README.md`: documenta como reproducir el flujo de trabajo.

## Requisitos

- Docker, con Docker Compose
- Git

La primera construccion del ambiente descarga varios cientos de MB y puede
tardar algunos minutos.

Considere el espacio en disco: las imagenes de Docker ocupan unos 3 GB y los
datos de los tres anios del laboratorio superan 1.5 GB, a los que se suma la
base materializada del Ejercicio 6. Se recomienda tener al menos 10 GB libres.

## Datos

El repositorio incluye `scripts/download_data.py`, que descarga los archivos
publicados por la TLC (`--help` muestra las opciones disponibles). Los archivos
se guardan en `data/raw/<tipo>/<anio>/`.

La TLC publica cada mes con varias semanas de atraso, por lo que los ultimos
meses de 2026 todavia no existen. El script consulta al servidor que meses estan
publicados, de modo que vuelve a ejecutarse sin problema conforme aparezcan
nuevos archivos.

Los datos descargados **no deben incluirse en el repositorio Git**. El archivo
`.gitignore` ya esta configurado para evitarlo.

Fuente de datos: NYC TLC Trip Record Data
<https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page>

Dentro de los contenedores, la carpeta `data/` del proyecto esta montada en
`/workspace/data`. Esa es la ruta que deben usar las herramientas que corren
dentro del ambiente, no la ruta de su computadora.

> **Nota sobre DuckDB:** un archivo `.duckdb` admite un solo proceso con permiso
> de escritura a la vez. Si conecta una herramienta externa a su base de datos,
> use el modo de solo lectura (`read_only`) en esa conexion; de lo contrario los
> demas procesos no podran abrir el archivo.

## Material a entregar

Al finalizar, su fork debe contener:

- el codigo fuente modificado y los scripts de descarga;
- las consultas SQL desarrolladas;
- el notebook o notebooks utilizados;
- la documentacion de las consultas;
- los scripts utilizados para los benchmarks;
- el codigo de los indicadores y visualizaciones;
- el tablero o la evidencia del tablero desarrollado;
- este `README.md`, completado segun la siguiente seccion.

Los archivos de datos descargados **no** deben incluirse.

---

# Documentacion del equipo

Las siguientes secciones deben ser completadas por cada equipo. El README final
debe permitir que una persona que no participo en el desarrollo pueda levantar el
ambiente, descargar los datos, ejecutar el analisis, reproducir los benchmarks y
generar los resultados principales.

## Como levantar el ambiente

Requisitos locales:

- Docker Desktop o Docker Engine con Docker Compose.
- Git.

Procedimiento usado para preparar el repositorio:

1. Se realizo un fork del repositorio base del docente.
2. Se clono el fork localmente.
3. Como el fork local estaba vacio, se agrego el remoto `upstream` y se trajo la plantilla base:

   ```bash
   git remote add upstream https://github.com/menene/duckdb.git
   git fetch upstream
   git merge upstream/main --allow-unrelated-histories
   ```

Para levantar el ambiente:

```bash
docker compose up -d --build
```

Servicios disponibles:

- JupyterLab: <http://127.0.0.1:8889>
- Metabase: <http://127.0.0.1:3000>

Para verificar que los contenedores estan corriendo:

```bash
docker compose ps
```

Para detener el ambiente:

```bash
docker compose down
```

Herramientas disponibles dentro del ambiente:

- Python 3.11.
- DuckDB 1.5.5.
- JupyterLab 4.6.4.
- Pandas 3.0.6.
- PyArrow 25.0.1.
- Matplotlib 3.11.2.
- Requests 2.34.2.
- Metabase con driver de DuckDB.

El uso de un ambiente reproducible es importante porque asegura que todas las personas del equipo, el docente y cualquier evaluador ejecuten el proyecto con las mismas versiones de Python, DuckDB y librerias. Esto reduce errores por diferencias entre computadoras, facilita repetir el analisis cuando ingresan nuevos archivos y permite validar los resultados de forma consistente.

## Como descargar los datos

Fase 1: descarga inicial de datos 2026 para taxis amarillos (`yellow`) y verdes (`green`).

El script usado es:

```bash
python scripts/download_data.py --years 2026
```

Tambien puede descargarse un solo tipo de taxi:

```bash
python scripts/download_data.py --taxi yellow --years 2026
python scripts/download_data.py --taxi green --years 2026
```

Los archivos se guardan en la estructura definida por el proyecto:

```text
data/raw/<tipo>/<anio>/<archivo>.parquet
```

Ejemplos:

```text
data/raw/yellow/2026/yellow_tripdata_2026-01.parquet
data/raw/green/2026/green_tripdata_2026-01.parquet
```

El script verifica cada archivo mensual publicado por la TLC antes de descargarlo. Si el archivo ya existe localmente y tiene tamano mayor a cero, lo omite para evitar descargas repetidas. Las descargas se escriben primero como archivo temporal `.part` y solo se renombran a `.parquet` cuando terminan correctamente.

Verificacion realizada para Fase 1:

```bash
python scripts/download_data.py --years 2026
```

Resultado obtenido:

- 16 archivos descargados.
- 0 archivos fallidos.
- 8 archivos no publicados por la TLC al momento de la ejecucion.
- Meses descargados: enero a agosto de 2026 para `yellow` y `green`.
- Meses no publicados: septiembre a diciembre de 2026 para `yellow` y `green`.

Luego se ejecuto nuevamente el mismo comando para comprobar que no vuelve a descargar archivos existentes. Resultado de la segunda ejecucion:

- 0 archivos descargados.
- 16 archivos omitidos porque ya existian.
- 8 archivos no publicados.
- 0 archivos fallidos.

Comando usado para listar los archivos locales descargados:

```bash
python -c "from pathlib import Path; files=sorted(Path('data/raw').glob('**/*.parquet')); print(len(files)); [print(f) for f in files]"
```

El conjunto descargado se considero completo para Fase 1 porque el script consulta los 12 meses de 2026 para ambos tipos de taxi y distingue entre archivos publicados, existentes, no publicados y fallidos. Al momento de la verificacion, la TLC solo tenia publicados enero-agosto de 2026 para ambos tipos, por lo que esos 16 archivos representan todos los archivos disponibles en la fuente original.

Ejercicio 5: incorporacion incremental de 2024 y ampliacion posterior a 2025.

El script ahora acepta multiples anios mediante `--years`. Para descargar 2024 y conservar 2026:

```bash
python scripts/download_data.py --years 2024 2026
```

El valor por defecto actual equivale a descargar 2024, 2025 y 2026:

```bash
python scripts/download_data.py
```

Ejercicio 8: incorporacion de 2025.

Para trabajar con los tres anios requeridos en la entrega final:

```bash
python scripts/download_data.py --years 2024 2025 2026
```

Resultado de la descarga incremental del Ejercicio 5:

- 24 archivos nuevos descargados para 2024.
- 16 archivos de 2026 omitidos porque ya existian.
- 8 archivos de 2026 no publicados por la TLC.
- 0 archivos fallidos.
- Total local despues de la incorporacion: 40 archivos Parquet.

Una segunda ejecucion del mismo script confirmo que no se redescargan archivos existentes: 0 descargados, 40 omitidos, 8 no publicados y 0 fallidos.

## Como ejecutar el analisis

Ejercicio 3: exploracion directa de archivos Parquet con DuckDB.

Notebook de analisis:

```text
notebooks/01_direct_parquet_exploration.ipynb
```

Este notebook se actualiza con el avance del laboratorio. Actualmente verifica los archivos descargados, ejecuta consultas directas sobre Parquet, revisa calidad inicial e incluye la validacion de incorporacion de 2024.

Archivo SQL:

```text
sql/exercise3_direct_parquet_exploration.sql
```

Documentacion de consultas y resultados:

```text
docs/exercise3_direct_parquet_exploration.md
```

Para validar que las consultas SQL se ejecutan correctamente dentro del ambiente Docker:

```bash
docker compose exec lab python -c "import duckdb; from pathlib import Path; con=duckdb.connect(); con.execute(Path('/workspace/sql/exercise3_direct_parquet_exploration.sql').read_text()); print('SQL ejecutado correctamente')"
```

Para trabajar interactivamente con los resultados, abra JupyterLab en <http://127.0.0.1:8889> y ejecute las consultas del archivo SQL una por una desde Python/DuckDB.

Ejercicio 4: analisis exploratorio con DuckDB.

Archivo SQL:

```text
sql/exercise4_exploratory_analysis.sql
```

Documentacion de preguntas, resultados y hallazgos:

```text
docs/exercise4_exploratory_analysis.md
```

Para validar que las consultas del Ejercicio 4 se ejecutan correctamente:

```bash
docker compose exec lab python -c "import duckdb; from pathlib import Path; con=duckdb.connect(); con.execute(Path('/workspace/sql/exercise4_exploratory_analysis.sql').read_text()); print('SQL ejercicio 4 ejecutado correctamente')"
```

Ejercicio 5: incorporacion incremental de 2024.

Archivo SQL:

```text
sql/exercise5_incremental_2024_validation.sql
```

Documentacion de validacion:

```text
docs/exercise5_incremental_2024.md
```

Para validar que DuckDB puede consultar 2024 y 2026 conjuntamente:

```bash
docker compose exec lab python -c "import duckdb; from pathlib import Path; con=duckdb.connect(); con.execute(Path('/workspace/sql/exercise5_incremental_2024_validation.sql').read_text()); print('SQL ejercicio 5 ejecutado correctamente')"
```

Ejercicio 8: incorporacion de 2025 y analisis completo 2024-2026.

Archivo SQL:

```text
sql/exercise8_full_2024_2025_2026_analysis.sql
```

Documentacion:

```text
docs/exercise8_full_analysis.md
docs/exercise8_results.md
```

Para validar el analisis conjunto de 2024, 2025 y 2026:

```bash
docker compose exec lab python -c "import duckdb; from pathlib import Path; con=duckdb.connect(); con.execute(Path('/workspace/sql/exercise8_full_2024_2025_2026_analysis.sql').read_text()); print('SQL ejercicio 8 ejecutado correctamente')"
```

## Como reproducir los benchmarks

Ejercicio 6: comparacion entre consultas directas sobre Parquet y una tabla
materializada en DuckDB.

Script reproducible:

```text
scripts/benchmark_parquet_vs_duckdb.py
```

Archivo SQL documentado:

```text
sql/exercise6_benchmark.sql
```

Documentacion del benchmark:

```text
docs/exercise6_benchmark.md
```

Para ejecutar el benchmark dentro del ambiente Docker:

```bash
docker compose exec lab python scripts/benchmark_parquet_vs_duckdb.py --force-materialize
```

Con los tres anios el benchmark tarda ~10 minutos y usa `--memory-limit 4GB` por defecto para no agotar la
RAM del contenedor.

El script crea la base materializada:

```text
data/processed/lab8.duckdb
```

Tambien genera los resultados en:

```text
docs/exercise6_benchmark_results.md
data/processed/exercise6_benchmark_results.csv
```

La comparacion usa las mismas consultas sobre dos estrategias:

- lectura directa con `read_parquet`;
- consulta sobre la tabla materializada `trips`.

El benchmark se ejecuta con diferentes cantidades de datos: primer mes disponible,
primeros cuatro meses disponibles y todos los meses disponibles por anio.

## Como generar los resultados principales

Ejercicio 7: indicadores y visualizaciones.

Consultas SQL:

```text
sql/exercise7_indicators.sql
```

Script generador:

```text
scripts/generate_indicators.py
```

Para generar los indicadores, tablas derivadas y figuras:

```bash
docker compose exec lab python scripts/generate_indicators.py
```

Despues de incorporar 2025, vuelva a ejecutar ese comando para actualizar las
visualizaciones a los tres anios disponibles.

El script genera:

```text
docs/exercise7_dashboard_results.md
docs/figures/exercise7_*.png
data/processed/indicators/*.csv
```

La documentacion del tablero esta en:

```text
docs/exercise7_dashboard.md
```

Tablero en Metabase (requiere haber ejecutado el benchmark, que crea `data/processed/lab8.duckdb`):

```bash
docker compose exec lab python scripts/setup_metabase.py
```

Crea el tablero `Lab 8 - Indicadores TLC` en <http://127.0.0.1:3000> (usuario local
`lab8@example.com` / `Lab8-DuckDB-2026`). Capturas en `docs/figures/metabase_dashboard_*.png`;
detalle en `docs/exercise7_dashboard.md`.

## Flujo completo de reproduccion

```bash
docker compose up -d --build
docker compose exec lab python scripts/download_data.py --years 2024 2025 2026
docker compose exec lab python scripts/benchmark_parquet_vs_duckdb.py --force-materialize
docker compose exec lab python scripts/generate_indicators.py
docker compose exec lab python scripts/setup_metabase.py
```

Las consultas de `sql/` pueden ejecutarse despues con los comandos de validacion de cada ejercicio.

## Resumen de hallazgos

- Yellow concentra mas del 98% de los viajes; yellow y green deben analizarse por separado.
- Yellow crece de 41.2 M (2024) a 48.7 M (2025) viajes validos; green baja de 660 mil a 591 mil.
  2026 solo tiene enero-agosto publicados y no es comparable como anio completo.
- El monto promedio por viaje sube en ambos servicios entre 2024 y 2026 (yellow 27.83 a 30.07, green 24.26 a 25.49).
- La actividad maxima se mantiene entre 16:00 y 19:00 en los tres anios.
- Distancias cero y montos negativos aparecen en todos los anios, por lo que los indicadores incluyen metricas de calidad.
- En el benchmark, la lectura directa de Parquet gano con poco volumen (1 mes por anio); con los 121 M de filas
  la tabla materializada gano las cuatro consultas, hasta 3.4 veces en la de medianas. Ver `docs/exercise6_benchmark.md`.

Detalle: `docs/exercise4_exploratory_analysis.md`, `docs/exercise7_dashboard_results.md` y `docs/exercise8_results.md`.

## Discusion (Ejercicio 9)

Las respuestas a las preguntas de reflexion 9.1-9.8 estan en `docs/exercise9_discussion.md`.
