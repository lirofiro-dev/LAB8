# Ejercicio 6 - Parquet versus tablas DuckDB

Este ejercicio compara dos estrategias de acceso a los datos:

1. **Consulta directa de archivos Parquet** con `read_parquet`.
2. **Consulta de tabla materializada** dentro de una base DuckDB (`data/processed/lab8.duckdb`).

## Archivos asociados

- Script reproducible: `scripts/benchmark_parquet_vs_duckdb.py`.
- SQL documentado: `sql/exercise6_benchmark.sql`.
- Resultados generados: `docs/exercise6_benchmark_results.md`.
- Resultados en CSV: `data/processed/exercise6_benchmark_results.csv`.

Los archivos en `data/processed/` no se versionan porque son derivados y pueden regenerarse.

## Consultas representativas

Se seleccionaron cuatro consultas basadas en el analisis exploratorio previo:

1. `monthly_volume`: volumen mensual y monto promedio.
2. `trip_statistics`: estadisticas de distancia, duracion y monto.
3. `payment_distribution`: distribucion de formas de pago.
4. `outlier_counts`: conteo de valores atipicos o inconsistencias.

Estas consultas cubren agrupaciones temporales, agregaciones numericas, funciones de ventana,
medianas y validaciones de calidad de datos.

## Diferentes cantidades de datos

El script detecta automaticamente los archivos disponibles y ejecuta el benchmark con niveles
progresivos de datos:

- primer mes disponible por anio;
- primeros cuatro meses disponibles por anio, si existen;
- todos los meses disponibles por anio.

De esta forma puede observarse como cambia el comportamiento al aumentar el volumen.

## Como reproducir

Desde el contenedor del laboratorio:

```bash
docker compose exec lab python scripts/benchmark_parquet_vs_duckdb.py --force-materialize
```

`--force-materialize` recrea la tabla `trips`; si ya existe y no han llegado archivos nuevos puede
omitirse. `--memory-limit` (por defecto `4GB`) ajusta la memoria que DuckDB puede usar.

Para repetir cada consulta mas veces:

```bash
docker compose exec lab python scripts/benchmark_parquet_vs_duckdb.py --repeats 5 --force-materialize
```

## Interpretacion esperada

Consultar Parquet directamente es conveniente cuando se desea explorar datos nuevos sin crear
estructuras adicionales o cuando los archivos siguen llegando de forma incremental. DuckDB puede
leer solo columnas necesarias y aprovechar el formato columnar.

Materializar una tabla DuckDB puede ser conveniente cuando se ejecutan muchas consultas repetidas
sobre el mismo conjunto ya normalizado, porque evita reconstruir la union de archivos y permite
crear indices o almacenar transformaciones comunes. El costo es que requiere espacio adicional y
un paso de preparacion cada vez que cambia el conjunto de archivos.

## Resultado observado con los datos disponibles

El benchmark final se ejecuto con los tres anios descargados (tabla `trips` de 121,184,384 filas,
archivo `lab8.duckdb` de ~5.6 GB, `memory_limit = 4GB`, 3 repeticiones, mediana):

- `yellow` y `green` 2024: 12 archivos cada uno.
- `yellow` y `green` 2025: 12 archivos cada uno.
- `yellow` y `green` 2026: 8 archivos cada uno (enero-agosto).
- Total evaluado: 64 archivos.

Los niveles toman los primeros N meses de cada anio: 1 mes (6 archivos), 4 meses (24 archivos) y
todos los meses disponibles (64 archivos). Los resultados completos estan en
`docs/exercise6_benchmark_results.md`.

| nivel | filas | consulta | Parquet directo | tabla DuckDB | mas rapido |
|---|---:|---|---:|---:|---|
| 1 mes | 10,309,888 | monthly_volume | 0.754 s | 2.557 s | Parquet |
| 1 mes | 10,309,888 | trip_statistics | 1.544 s | 2.018 s | Parquet |
| 1 mes | 10,309,888 | payment_distribution | 0.638 s | 2.085 s | Parquet |
| 1 mes | 10,309,888 | outlier_counts | 0.757 s | 2.758 s | Parquet |
| 4 meses | 43,734,857 | monthly_volume | 3.207 s | 4.300 s | Parquet |
| 4 meses | 43,734,857 | trip_statistics | 9.130 s | 4.230 s | tabla |
| 4 meses | 43,734,857 | payment_distribution | 2.330 s | 2.627 s | Parquet |
| 4 meses | 43,734,857 | outlier_counts | 4.032 s | 3.104 s | tabla |
| todos | 121,184,384 | monthly_volume | 6.672 s | 6.466 s | tabla |
| todos | 121,184,384 | trip_statistics | 34.119 s | 9.976 s | tabla |
| todos | 121,184,384 | payment_distribution | 4.573 s | 3.285 s | tabla |
| todos | 121,184,384 | outlier_counts | 7.470 s | 5.589 s | tabla |

## Analisis de diferencias observadas

**Con poco volumen gana Parquet directo.** Con un mes por anio, la lectura directa fue entre 1.3 y
3.4 veces mas rapida en las cuatro consultas. La tabla se consulta filtrando `source_file IN (...)`
sobre los 121 M de filas almacenadas, por lo que paga un costo de recorrer y filtrar la tabla
completa que no compensa cuando se necesita una fraccion pequena. Parquet, en cambio, solo abre los
6 archivos involucrados y lee unicamente las columnas usadas.

**Al crecer el volumen la ventaja se invierte.** Con 4 meses los resultados son mixtos y con todos
los meses la tabla materializada gana en las cuatro consultas. Ese costo fijo del filtro pierde peso
y domina el costo de leer, descomprimir y normalizar (`tpep_*`/`lpep_*`) los Parquet en cada
ejecucion.

**Las consultas pesadas son las mas sensibles.** `trip_statistics` calcula medianas y varias
agregaciones; sobre todos los datos tardo 34.1 s desde Parquet y 10.0 s desde la tabla (3.4 veces
mas rapido). En consultas de conteo sobre pocas columnas (`monthly_volume`) la diferencia es minima
(6.7 s vs 6.5 s), porque Parquet ya lee solo las columnas necesarias.

**Costo de materializar.** La tabla ocupa ~5.6 GB adicionales y tarda varios minutos en crearse. Con
el limite de memoria por defecto, la lectura directa de 121 M de filas agoto la RAM del contenedor,
por lo que el script fija `--memory-limit 4GB` para que DuckDB use disco temporal.

**Comparacion con la primera ejecucion (solo 2026, 30 M de filas).** En esa corrida Parquet directo
gano en casi todas las consultas en todos los niveles. La conclusion depende del volumen: lo que es
cierto con un anio deja de serlo con tres.

## Escenarios recomendados

Consulta directa sobre Parquet es apropiada cuando:

- los archivos llegan incrementalmente y se desea analizarlos sin un proceso de carga adicional;
- se hacen exploraciones iniciales o validaciones de calidad;
- las consultas leen pocas columnas;
- se quiere evitar duplicar almacenamiento en una base materializada.

Materializar una tabla DuckDB es apropiado cuando:

- se ejecutan muchas consultas repetidas sobre el mismo conjunto;
- se necesita una capa normalizada para simplificar consultas posteriores;
- se desea compartir una base `.duckdb` con herramientas como Metabase;
- se van a crear indices, vistas o tablas derivadas para un tablero o reporte recurrente.

La decision no depende solamente del tiempo de una consulta individual. Tambien debe considerarse
el costo de crear la tabla, el espacio adicional en disco y la frecuencia con la que se incorporan
nuevos archivos.
