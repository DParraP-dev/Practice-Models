# Practice-Models

Material de estudio para *Modelos y Métodos de Optimización* (programación lineal y entera con Gurobi en Python).

## Archivos

| Archivo | Para qué sirve |
|---|---|
| `VRP_MILP_base.py` | Script de clase (VRP). Es la referencia de estilo. |
| `Clustering_MILP_base.py` | El mismo estilo aplicado a **clustering**. Lee los archivos del profesor, resuelve, imprime los clusters, grafica y guarda un csv. |
| `guia_gurobi.py` | Guía de estudio: metodología, cheatsheet de la API, problemas clásicos, linealizaciones, diagnóstico y teoría de clustering con cada modelo como función. |

## Instalación

```bash
pip install -r requirements.txt
```

## Clustering_MILP_base.py

Todo lo que se configura está en la sección `CONFIGURACION`, al inicio del archivo.

```python
ARCHIVO = 'datos_clustering.txt'   # archivo del profesor
TIPO_DATOS = 'COORDENADAS'         # o 'DISTANCIAS' (matriz n x n)
METRICA = 'euclidiana'             # 'manhattan', 'cuadrada'
COLUMNAS_COORD = None              # None = automático; o una lista como [1, 2]
COL_PESO = None                    # columna con demanda/peso por punto (q[i])
MODELO = 'CENTROS'                 # 'CENTROS' (p-mediana) o 'PARES'
OBJETIVO = 'SUMA'                  # 'SUMA' o 'MAX' (minimax)
K = 3                              # número de clusters
Q, Q_MIN = None, None              # capacidad máxima / mínima por cluster
R_MAX, D_MAX = None, None          # radio máximo (CENTROS) / diámetro máximo (PARES)
```

Formatos de archivo que acepta:

- Texto o csv con `x y`, o `índice x y`, o más columnas. Descarta solas las líneas no numéricas (encabezados, `NODE_COORD_SECTION`, `EOF`).
- csv de Excel en español (separador `;` y coma decimal).
- Matriz de distancias cuadrada (`TIPO_DATOS = 'DISTANCIAS'`).
- Si el archivo no existe, genera puntos de ejemplo para poder probar.

| MODELO | OBJETIVO | Qué resuelve |
|---|---|---|
| `CENTROS` | `SUMA` | p-mediana (k-medoids): mínima suma de distancias punto-centro |
| `CENTROS` | `MAX` | p-centro: mínimo radio máximo |
| `PARES` | `SUMA` | mínima suma de distancias entre puntos del mismo cluster |
| `PARES` | `MAX` | mínimo diámetro máximo |

Si el modelo es infactible, el script imprime el conjunto de restricciones en conflicto (IIS).

## guia_gurobi.py

```bash
python guia_gurobi.py                 # lista los ejemplos
python guia_gurobi.py todo            # ejecuta todos
python guia_gurobi.py p_mediana       # ejecuta uno
```

| Nombre | Tema |
|---|---|
| `plantilla`, `cheatsheet` | Pasos de modelado y referencia de la API |
| `produccion` | LP de maximización y análisis de sensibilidad |
| `dieta` | LP de minimización |
| `transporte` | Oferta y demanda |
| `asignacion`, `mochila`, `cobertura` | Binarias |
| `localizacion` | Costo fijo y big-M |
| `multiperiodo` | Balance de inventarios |
| `ruta_corta` | Flujo en redes |
| `linealizaciones` | abs, minimax, if-then, producto binaria×continua, restricciones generales, multiobjetivo |
| `infactible` | IIS y status del solver |
| `p_mediana`, `p_mediana_cap`, `p_centro` | Clustering con centros, con capacidades y minimax |
| `pares` | Clustering por pares, sin centros |
| `min_clusters` | Mínimo de clusters con diámetro máximo |
| `asignar_centroides` | Clustering con centros dados |
| `barrido_k` | Elegir K con el método del codo |
| `kmeans` | Por qué k-means no es un MIP y qué alternativas hay |
| `checklist` | Errores comunes y consejos para el examen |
