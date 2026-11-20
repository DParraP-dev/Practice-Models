# Localización de puntos satélite y programación semanal de atención en salud

Proyecto de Modelos y Métodos de Optimización (Universidad EAFIT). MILP resuelto con Gurobi.

## Archivos

| Archivo | Contenido |
|---|---|
| `satellite_MILP.py` | Modelo, verificación independiente (R1–R5) y experimentación. Genera `resultados/`. |
| `report_analysis.py` | Estadísticas de instancias, tablas, gráficas, mapas, calendarios y soluciones no dominadas. Genera `resultados/informe/`. |
| `instance_A.json`, `instance_B.json` | Instancias del enunciado. |
| `VRP_MILP_base.py` | Ejemplo de referencia de clase. |

## Requisitos

- Python 3.9 o superior.
- Gurobi con licencia académica activa (`gurobipy`).
- `pip install -r requirements.txt` (`psutil` solo se usa para reportar RAM y núcleos).

## Ejecución

1. Abrir `satellite_MILP.py`, revisar el bloque **CONFIGURACIÓN** y ejecutar el script desde el IDE (o `python satellite_MILP.py`).
2. Cuando termine, ejecutar `report_analysis.py` de la misma forma.

Los resultados se guardan después de cada corrida. Si la ejecución se interrumpe, al volver a ejecutar el script (con `RESUME = True`) se omiten las corridas ya terminadas.

## Diseño experimental implementado

Para cada instancia:

1. **Cribado** (`screen`): minimiza la distancia con exactamente p puntos para p = 1..10, con un tiempo límite corto (`SCREEN_TIME_LIMIT`, 60 s). Sirve para identificar los p infactibles y la forma de la curva p vs distancia.
2. **Selección de 3 valores de p** entre los factibles: el menor, el mayor y uno intermedio. Se pueden fijar a mano en `P_VALUES`.
3. Para cada p seleccionado, con `TIME_LIMIT = 1800` s y `MIPGap = 0`:
   - `a_dist`: min distancia, exactamente p (4.3.1 a).
   - `b_teams`: min equipos, exactamente p (4.3.1 b).
   - `c_eps`: min distancia s.a. equipos ≤ ε, para ε entero desde E(b) hasta E(a) − 1 (4.3.1 c). La curva se detiene cuando se alcanza la distancia óptima de (a), porque los ε mayores repiten esa distancia.
   - `atmost_dist`: min distancia, a lo sumo p (4.3.4).

## Salidas

- `resultados/resultados.csv`: una fila por corrida con estado, objetivo, mejor cota, gap, tiempo, nodos, puntos abiertos, distancia, equipos (total y por disciplina), utilización por disciplina, días y utilización por punto (JSON) y resultado de la verificación.
- `resultados/soluciones.json`: puntos abiertos, asignaciones y calendario de cada solución.
- `resultados/entorno.json`: versión de Gurobi, sistema operativo, CPU y RAM.
- `resultados/logs/`: log de Gurobi de cada corrida.
- `resultados/informe/`: insumos del informe (ver encabezado de `report_analysis.py`) y `resumen.md` con las tablas en Markdown.
