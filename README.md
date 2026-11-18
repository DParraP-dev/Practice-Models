# Practice-Models

Material de estudio para *Modelos y Métodos de Optimización* (programación lineal y entera con Gurobi en Python).

## Contenido

- `guia_gurobi.py`: guía ejecutable con la metodología de modelado, un cheatsheet de la API de `gurobipy`, problemas clásicos, linealizaciones, diagnóstico de modelos infactibles y una sección completa de **clustering**.

## Uso

```bash
pip install -r requirements.txt

python guia_gurobi.py                 # lista los ejemplos
python guia_gurobi.py todo            # ejecuta todos
python guia_gurobi.py p_mediana       # ejecuta uno
```

## Ejemplos incluidos

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
| `p_mediana` | Clustering: k-medoids |
| `p_mediana_cap` | Clustering con tamaño mínimo y máximo |
| `p_centro` | Clustering: minimizar el radio máximo |
| `min_clusters` | Clustering: mínimo de clusters con diámetro máximo |
| `asignar_centroides` | Clustering con centros dados |
| `kmeans` | Por qué k-means no es un MIP y qué alternativas hay |
| `checklist` | Errores comunes y consejos para el examen |

La licencia gratuita de `gurobipy` instalada con pip limita el modelo a 2000 variables y 2000 restricciones lineales.
