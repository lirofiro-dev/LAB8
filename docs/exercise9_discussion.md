# Ejercicio 9 - Discusion

Las respuestas se basan en los resultados obtenidos durante el laboratorio: 64 archivos Parquet
(yellow y green, 2024-2026), ~121 millones de filas, el benchmark del Ejercicio 6
(`docs/exercise6_benchmark.md`) y el analisis completo del Ejercicio 8 (`docs/exercise8_results.md`).

## 9.1 Que caracteristicas de DuckDB resultaron mas utiles?

- **Lectura directa de Parquet con `read_parquet`**: se consultaron los archivos tal como los
  publica la TLC, sin proceso de carga previo.
- **Patrones glob y `filename = true`**: `data/raw/yellow/**/*.parquet` incorpora cualquier anio
  nuevo, y la columna `filename` permite derivar `file_year` desde la ruta del archivo.
- **`union_by_name = true`**: une archivos de distintos meses aunque el orden o la presencia de
  columnas cambie entre publicaciones.
- **SQL analitico completo**: `median`, funciones de ventana (`LAG`, `ROW_NUMBER`), `QUALIFY` y
  `strftime` resolvieron los indicadores sin salir de SQL.
- **Proceso embebido**: DuckDB corre dentro de Python, sin servidor, y la base `.duckdb` es un solo
  archivo que tambien puede abrir Metabase.
- **Ejecucion columnar y paralela**: agregaciones sobre decenas de millones de filas se resolvieron
  en segundos en un contenedor con ~8 GB de RAM.

## 9.2 Ventajas y limitaciones de consultar directamente Parquet

Ventajas:

- cero tiempo de carga y sin duplicar almacenamiento;
- solo se leen las columnas usadas por cada consulta (formato columnar), por lo que conteos y
  distribuciones simples fueron competitivos o mas rapidos que la tabla;
- los archivos nuevos quedan disponibles inmediatamente para todas las consultas.

Limitaciones:

- cada consulta repite la lectura, descompresion y normalizacion de columnas (`tpep_*` vs
  `lpep_*`), lo que penaliza consultas costosas como las medianas;
- las diferencias de esquema entre tipos de taxi obligan a repetir la vista normalizada en cada
  script;
- con el volumen completo, leer Parquet directamente fue el paso que agoto la memoria del
  contenedor y obligo a fijar `memory_limit` (ver 9.8).

## 9.3 Ventajas y limitaciones de las tablas materializadas

Ventajas:

- los datos quedan normalizados una sola vez en la tabla `trips`, lo que simplifica las consultas
  posteriores y el tablero de Metabase;
- las consultas con mas trabajo de agregacion (`trip_statistics`, con medianas) fueron claramente
  mas rapidas sobre la tabla;
- un solo archivo `.duckdb` es facil de compartir con otras herramientas.

Limitaciones:

- materializar 2024-2026 produjo un archivo de ~5.6 GB, espacio adicional a los Parquet;
- la creacion de la tabla toma varios minutos y debe repetirse (o hacerse incremental) cuando llegan
  meses nuevos, por lo que la tabla puede quedar desactualizada;
- el archivo admite un solo proceso con escritura: mientras el benchmark escribia la base, Metabase
  no podia abrirla.

## 9.4 Ventajas frente a cargar todo con Pandas

- Pandas necesita cargar todas las filas en memoria. Con ~121 millones de filas y ~19 columnas eso
  supera por mucho los ~8 GB del contenedor; DuckDB procesa por bloques y puede usar disco temporal.
- DuckDB lee solo las columnas y grupos de filas necesarios; Pandas leeria los archivos completos.
- Las agregaciones de DuckDB son paralelas y vectorizadas; en Pandas muchas operaciones usan un solo
  nucleo.
- Las consultas quedan como SQL documentado y reproducible. Pandas se uso solo al final, sobre
  resultados ya agregados (pocas filas), para generar figuras.

## 9.5 Caracteristicas que permiten incorporar nuevos datos con cambios minimos

- Estructura de directorios fija `data/raw/<tipo>/<anio>/` y nombres de archivo de la TLC.
- Script de descarga parametrizado con `--years`, que consulta que meses estan publicados y omite
  los archivos ya existentes.
- Consultas con patrones `**/*.parquet` y anio derivado de la ruta con `'/(\d{4})/'`. La unica
  consulta que se tuvo que corregir al agregar 2025 fue la del Ejercicio 5, que tenia los anios
  escritos en la expresion regular.
- Scripts de benchmark e indicadores que descubren los archivos disponibles en lugar de usar listas
  fijas.

## 9.6 Que deberia automatizarse en produccion?

- Descarga programada (por ejemplo mensual) que detecte meses nuevos publicados por la TLC.
- Validaciones automaticas de calidad tras cada descarga: conteo de filas, esquema esperado,
  porcentaje de distancias cero, montos negativos y fechas fuera del periodo.
- Actualizacion incremental de la tabla materializada (insertar solo los archivos nuevos en lugar
  de recrearla completa).
- Regeneracion de indicadores y refresco del tablero despues de cada carga.
- Alertas cuando falla una descarga o cuando un indicador de calidad cambia bruscamente.

## 9.7 Decisiones de diseno importantes para la reproducibilidad

- Ambiente Docker con versiones fijas (Python 3.11, DuckDB 1.5.5, Metabase con driver alineado).
- Datos fuera de Git (`.gitignore`), pero obtenibles con un solo comando desde la fuente original.
- Todas las transformaciones en archivos SQL y scripts versionados, sin pasos manuales.
- Rutas dentro del contenedor (`/workspace/data`) iguales para todos los integrantes.
- Resultados documentados en `docs/` y generados por scripts (`benchmark_parquet_vs_duckdb.py`,
  `generate_indicators.py`, `setup_metabase.py`), de modo que pueden regenerarse.

## 9.8 Que se aprendio que no seria evidente con datos pequenos?

- **La memoria es un recurso real**: con solo 2026 todo funcionaba con la configuracion por
  defecto; con 2024-2026 el benchmark y una tabla en memoria agotaron la RAM del contenedor. Fue
  necesario fijar `memory_limit` y trabajar con una base en archivo.
- **La estrategia mas rapida depende del volumen y de la consulta**: con 2026 solamente, Parquet
  directo gano en casi todas las consultas; con los tres anios la tabla materializada gano en las
  consultas pesadas.
- **Los problemas de calidad escalan**: un 2-5% de distancias cero son millones de filas en yellow,
  y las fechas fuera del anio del archivo hacen que el mismo conteo difiera segun el filtro.
- **Los supuestos ocultos se rompen al crecer**: una expresion regular con anios fijos funciono con
  2024 y 2026 y fallo al agregar 2025.
- **Los totales absolutos enganan**: yellow concentra mas del 98% de los viajes, por lo que las
  comparaciones entre servicios deben hacerse con porcentajes o por separado, y 2026
  (enero-agosto) no es comparable como anio completo.
