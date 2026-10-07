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

El benchmark fue ejecutado con los datos descargados localmente al momento de la prueba:

- `yellow` 2026: 8 archivos.
- `green` 2026: 8 archivos.
- Total evaluado: 16 archivos y 30,040,469 filas.

Los resultados completos estan en `docs/exercise6_benchmark_results.md`.

Resumen de tiempos medianos observados:

| nivel | filas | consulta | Parquet directo | tabla DuckDB |
|---|---:|---|---:|---:|
| 1 mes | 3,765,161 | monthly_volume | 0.1145 s | 0.6598 s |
| 1 mes | 3,765,161 | trip_statistics | 0.2859 s | 0.2802 s |
| 1 mes | 3,765,161 | payment_distribution | 0.0700 s | 1.4035 s |
| 1 mes | 3,765,161 | outlier_counts | 0.1078 s | 0.4123 s |
| 4 meses | 15,074,537 | monthly_volume | 0.2594 s | 0.9038 s |
| 4 meses | 15,074,537 | trip_statistics | 1.1873 s | 1.1449 s |
| 4 meses | 15,074,537 | payment_distribution | 0.1637 s | 0.7391 s |
| 4 meses | 15,074,537 | outlier_counts | 0.2489 s | 0.8011 s |
| 8 meses | 30,040,469 | monthly_volume | 0.5003 s | 0.6576 s |
| 8 meses | 30,040,469 | trip_statistics | 2.4989 s | 2.2031 s |
| 8 meses | 30,040,469 | payment_distribution | 0.2989 s | 0.7596 s |
| 8 meses | 30,040,469 | outlier_counts | 0.4863 s | 0.9125 s |

## Analisis de diferencias observadas

En esta ejecucion, la lectura directa desde Parquet fue mas rapida en la mayoria de consultas.
Esto es razonable porque las consultas usan pocas columnas y Parquet permite lectura columnar:
DuckDB no necesita leer todo el archivo, sino principalmente las columnas involucradas en cada
agregacion. Ademas, los archivos Parquet ya estan particionados por tipo de taxi, anio y mes en
el sistema de archivos.

La tabla materializada tuvo mejor resultado en `trip_statistics` para 1, 4 y 8 meses. Esa consulta
calcula medianas y varias agregaciones sobre columnas normalizadas; al estar los datos ya unidos
en una tabla comun, se evita parte del costo de construir la union normalizada desde Parquet en
cada ejecucion.

Tambien se observa que al aumentar el volumen de datos los tiempos crecen, pero no de forma
identica para todas las consultas. Las consultas de conteos y promedios sobre pocas columnas
escalan muy bien desde Parquet. Las consultas con medianas son mas costosas porque requieren
mas trabajo de agregacion.

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
