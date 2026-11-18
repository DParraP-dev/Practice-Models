import os
import csv
import numpy as np
import matplotlib.pyplot as plt
import gurobipy as gp
from gurobipy import GRB

"""
================================================================================
Clustering MILP (p-mediana / k-medoids y variantes)  -  plantilla estilo clase
================================================================================
Misma estructura que VRP_MILP_base.py:
    datos -> parametros -> variables -> conjuntos -> restricciones -> objetivo
    -> optimizar -> extraer y mostrar la solucion

DESCRIPCION DEL PROBLEMA:
- Se tienen n puntos (con coordenadas, o directamente una matriz de distancias).
- Se deben formar K clusters (K es como la flota de vehiculos en el VRP).
- Cada punto puede tener un peso/demanda q[i] y cada cluster una capacidad Q
  (opcional, igual que en el VRP).
- Objetivo: que los puntos de un mismo cluster queden "cerca".

DOS FORMULACIONES (se elige con MODELO):

  MODELO = 'CENTROS'  (p-mediana / k-medoids)  <- la mas usada
      Y[j]   binaria: 1 si el punto j es elegido como CENTRO de un cluster
      X[i,j] binaria: 1 si el punto i se asigna al centro j
      Objetivo 'SUMA': min sum d[i][j] X[i,j]            (p-mediana)
      Objetivo 'MAX' : min Rmax,  Rmax >= sum_j d[i][j] X[i,j]   (p-centro)

  MODELO = 'PARES'  (sin centros: importa que los puntos del grupo esten juntos)
      X[i,k] binaria: 1 si el punto i va al cluster k
      Z[i,j] continua: 1 si i y j quedaron en el mismo cluster (i < j)
      Objetivo 'SUMA': min sum d[i][j] Z[i,j]   (suma de distancias entre pares)
      Objetivo 'MAX' : min Rmax (diametro maximo: mayor distancia dentro de un cluster)

ARCHIVOS DE DATOS (lo que probablemente entregue el profesor):
- Coordenadas: texto/csv con una fila por punto (x y)  o  (indice x y)  o mas
  columnas. Las lineas que no son numericas (encabezados, NAME:, EOF) se saltan.
- Matriz de distancias: archivo cuadrado n x n  (TIPO_DATOS = 'DISTANCIAS').
- Si el archivo no existe, el script genera puntos de ejemplo para poder probar.
"""

# ============================================================================
# CONFIGURACION  (lo unico que normalmente hay que tocar)
# ============================================================================

ARCHIVO = 'datos_clustering.txt'   # archivo entregado por el profesor
TIPO_DATOS = 'COORDENADAS'         # 'COORDENADAS' o 'DISTANCIAS' (matriz n x n)
METRICA = 'euclidiana'             # 'euclidiana', 'manhattan' o 'cuadrada'
COLUMNAS_COORD = None              # None = automatico. Ej: [1, 2] usa esas columnas
COL_PESO = None                    # None = peso 1 por punto. Ej: 3 usa la columna 3 como q[i]
NORMALIZAR = False                 # True: estandariza columnas (util si hay unidades distintas)
N_MAX = None                       # limitar puntos para pruebas (como n = 10 en el VRP)

MODELO = 'CENTROS'                 # 'CENTROS' o 'PARES'
OBJETIVO = 'SUMA'                  # 'SUMA' o 'MAX'
K = 3                              # numero de clusters
Q = None                           # capacidad maxima por cluster (suma de q[i]); None = sin limite
Q_MIN = None                       # carga minima por cluster; None = sin limite
R_MAX = None                       # (CENTROS) distancia maxima permitida punto-centro; None = sin limite
D_MAX = None                       # (PARES)   distancia maxima permitida dentro de un cluster; None = sin limite

TIME_LIMIT = 600                   # segundos
MIP_GAP = 0.0                      # 0.01 = aceptar 1 % de gap
MOSTRAR_GRAFICO = True
ARCHIVO_RESULTADO = 'resultado_clustering.csv'

# ============================================================================
# DATA LOADING AND PREPROCESSING
# ============================================================================


def leer_numeros(nombre):
    """Lee un archivo de texto/csv y devuelve un array con solo las filas numericas."""
    filas = []
    with open(nombre) as f:
        for linea in f:
            if ';' in linea:       # csv de Excel en espanol: separador ; y coma decimal
                partes = [p.strip().replace(',', '.') for p in linea.split(';')]
            else:
                partes = linea.replace(',', ' ').split()
            try:
                fila = [float(p) for p in partes]
            except ValueError:
                continue           # encabezado, NAME:, NODE_COORD_SECTION, EOF, ...
            if fila:
                filas.append(fila)
    largos = [len(fila) for fila in filas]
    largo = max(set(largos), key=largos.count)        # largo de fila mas comun
    return np.array([fila for fila in filas if len(fila) == largo])


def calcular_distancias(P, metrica):
    """Matriz de distancias n x n (lista de listas) a partir de las filas de P."""
    diff = P[:, None, :] - P[None, :, :]
    if metrica == 'euclidiana':
        D = np.sqrt((diff ** 2).sum(axis=2))
    elif metrica == 'manhattan':
        D = np.abs(diff).sum(axis=2)
    elif metrica == 'cuadrada':
        D = (diff ** 2).sum(axis=2)
    else:
        raise ValueError(f'METRICA desconocida: {metrica}')
    return D.tolist()


if os.path.exists(ARCHIVO):
    datos = leer_numeros(ARCHIVO)
else:
    print(f'AVISO: no existe {ARCHIVO}. Se generan datos de ejemplo.')
    rnd = np.random.RandomState(7)
    centros_demo = [(20, 20), (80, 30), (50, 90)]
    datos = np.vstack([rnd.normal(c, 8, size=(10, 2)) for c in centros_demo])
    TIPO_DATOS = 'COORDENADAS'

coord = None    # matriz de coordenadas (None si solo hay matriz de distancias)
q = None        # peso/demanda de cada punto

if TIPO_DATOS == 'COORDENADAS':
    # --- Seleccion de columnas -------------------------------------------------
    if COLUMNAS_COORD is not None:
        cols = list(COLUMNAS_COORD)
    else:
        cols = list(range(datos.shape[1]))
        primera = datos[:, 0]
        # Si la primera columna es un indice 1..n o 0..n-1 y hay 3+ columnas, se descarta
        if datos.shape[1] >= 3 and (np.array_equal(primera, np.arange(1, len(datos) + 1)) or
                                    np.array_equal(primera, np.arange(0, len(datos)))):
            cols = cols[1:]
        if COL_PESO is not None and COL_PESO in cols:
            cols.remove(COL_PESO)
    coord = datos[:, cols]
    if COL_PESO is not None:
        q = [float(v) for v in datos[:, COL_PESO]]
    if NORMALIZAR:
        coord = (coord - coord.mean(axis=0)) / coord.std(axis=0)
    n = len(coord)
    if N_MAX is not None:
        n = min(n, N_MAX)
        coord = coord[:n]
        if q is not None:
            q = q[:n]
    dist = calcular_distancias(coord, METRICA)
elif TIPO_DATOS == 'DISTANCIAS':
    M_dist = datos            # si el archivo trae indice en la 1a fila/columna, recortarlo aqui
    assert M_dist.shape[0] == M_dist.shape[1], 'La matriz de distancias debe ser cuadrada'
    n = len(M_dist)
    if N_MAX is not None:
        n = min(n, N_MAX)
    dist = M_dist[:n, :n].tolist()
else:
    raise ValueError(f'TIPO_DATOS desconocido: {TIPO_DATOS}')

# ============================================================================
# INSTANCE PARAMETERS
# ============================================================================

# Peso/demanda de cada punto (como q en el VRP). Por defecto cada punto pesa 1,
# asi que Q funciona como "numero maximo de puntos por cluster".
if q is None:
    q = [1] * n

print(f'n = {n} puntos, K = {K} clusters, modelo = {MODELO}, objetivo = {OBJETIVO}')

# ============================================================================
# SET DEFINITIONS
# ============================================================================

# Conjunto de todos los puntos (0..n-1)
V = range(n)

# Conjunto de clusters (solo MODELO = 'PARES')
Kset = range(K)

# ============================================================================
# MATHEMATICAL MODEL: DECISION VARIABLES AND CONSTRAINTS
# ============================================================================

md = gp.Model("Clustering base")

if MODELO == 'CENTROS':
    # ------------------------------------------------------------------------
    # VARIABLES
    # ------------------------------------------------------------------------
    # X[i,j] = 1 si el punto i se asigna al centro j
    X = md.addVars(n, n, vtype=GRB.BINARY, name='X')
    # Y[j] = 1 si el punto j es un centro
    Y = md.addVars(n, vtype=GRB.BINARY, name='Y')
    # Rmax: distancia maxima punto-centro (solo se usa con OBJETIVO = 'MAX')
    Rmax = md.addVar(vtype=GRB.CONTINUOUS, name='Rmax', lb=0)

    # ------------------------------------------------------------------------
    # CONSTRAINTS
    # ------------------------------------------------------------------------
    # CONSTRAINT 1: cada punto se asigna a exactamente un centro
    md.addConstrs((gp.quicksum(X[i, j] for j in V) == 1 for i in V), name='un_centro')

    # CONSTRAINT 2: solo se puede asignar a un punto que sea centro
    md.addConstrs((X[i, j] <= Y[j] for i in V for j in V), name='solo_a_centros')

    # CONSTRAINT 3: se eligen exactamente K centros
    md.addConstr(gp.quicksum(Y[j] for j in V) == K, name='k_centros')

    # CONSTRAINT 4: el centro pertenece a su propio cluster
    # (si j no es centro, X[j,j] = 0 por la restriccion 2)
    md.addConstrs((X[j, j] == Y[j] for j in V), name='centro_en_su_cluster')

    # CONSTRAINT 5 (opcional): capacidad maxima por cluster
    if Q is not None:
        md.addConstrs((gp.quicksum(q[i] * X[i, j] for i in V) <= Q * Y[j] for j in V), name='cap_max')

    # CONSTRAINT 6 (opcional): carga minima por cluster
    if Q_MIN is not None:
        md.addConstrs((gp.quicksum(q[i] * X[i, j] for i in V) >= Q_MIN * Y[j] for j in V), name='cap_min')

    # CONSTRAINT 7 (opcional): distancia maxima permitida de un punto a su centro
    if R_MAX is not None:
        md.addConstrs((dist[i][j] * X[i, j] <= R_MAX for i in V for j in V), name='radio_max')

    # CONSTRAINT 8: definicion de Rmax (solo OBJETIVO = 'MAX', tecnica minimax)
    if OBJETIVO == 'MAX':
        md.addConstrs((Rmax >= gp.quicksum(dist[i][j] * X[i, j] for j in V) for i in V), name='def_Rmax')

    # ------------------------------------------------------------------------
    # OBJECTIVE FUNCTION
    # ------------------------------------------------------------------------
    if OBJETIVO == 'SUMA':
        # Objective 1: minimizar la suma de distancias punto-centro (p-mediana)
        md.setObjective(gp.quicksum(dist[i][j] * X[i, j] for i in V for j in V), GRB.MINIMIZE)
    else:
        # Objective 2: minimizar la distancia maxima punto-centro (p-centro)
        md.setObjective(Rmax, GRB.MINIMIZE)

elif MODELO == 'PARES':
    # ------------------------------------------------------------------------
    # VARIABLES
    # ------------------------------------------------------------------------
    # X[i,k] = 1 si el punto i va al cluster k
    X = md.addVars(n, K, vtype=GRB.BINARY, name='X')
    # Z[i,j] = 1 si i y j estan en el mismo cluster (solo pares i < j).
    # Puede ser continua: al minimizar distancias positivas, toma 0 o 1 sola.
    Z = md.addVars([(i, j) for i in V for j in V if i < j], vtype=GRB.CONTINUOUS, lb=0, name='Z')
    # Rmax: diametro maximo (mayor distancia entre dos puntos del mismo cluster)
    Rmax = md.addVar(vtype=GRB.CONTINUOUS, name='Rmax', lb=0)

    # ------------------------------------------------------------------------
    # CONSTRAINTS
    # ------------------------------------------------------------------------
    # CONSTRAINT 1: cada punto va a exactamente un cluster
    md.addConstrs((gp.quicksum(X[i, k] for k in Kset) == 1 for i in V), name='un_cluster')

    # CONSTRAINT 2: todos los clusters tienen al menos un punto (usa los K clusters)
    md.addConstrs((gp.quicksum(X[i, k] for i in V) >= 1 for k in Kset), name='cluster_no_vacio')

    # CONSTRAINT 3: ruptura de simetria (los clusters son intercambiables entre si).
    # El punto i solo puede ir a clusters con indice <= i
    md.addConstrs((X[i, k] == 0 for i in V for k in Kset if k > i), name='simetria')

    # CONSTRAINT 4 (opcional): capacidad maxima por cluster
    if Q is not None:
        md.addConstrs((gp.quicksum(q[i] * X[i, k] for i in V) <= Q for k in Kset), name='cap_max')

    # CONSTRAINT 5 (opcional): carga minima por cluster
    if Q_MIN is not None:
        md.addConstrs((gp.quicksum(q[i] * X[i, k] for i in V) >= Q_MIN for k in Kset), name='cap_min')

    # CONSTRAINT 6 (opcional): dos puntos muy lejanos no pueden compartir cluster
    if D_MAX is not None:
        md.addConstrs((X[i, k] + X[j, k] <= 1
                       for i in V for j in V if i < j and dist[i][j] > D_MAX for k in Kset), name='diametro_max')

    if OBJETIVO == 'SUMA':
        # CONSTRAINT 7: si i y j estan en el mismo cluster k, entonces Z[i,j] = 1
        md.addConstrs((Z[i, j] >= X[i, k] + X[j, k] - 1 for i in V for j in V if i < j for k in Kset), name='mismo_cluster')
    else:
        # CONSTRAINT 8: definicion del diametro maximo (minimax)
        md.addConstrs((Rmax >= dist[i][j] * (X[i, k] + X[j, k] - 1)
                       for i in V for j in V if i < j for k in Kset), name='def_Rmax')

    # ------------------------------------------------------------------------
    # OBJECTIVE FUNCTION
    # ------------------------------------------------------------------------
    if OBJETIVO == 'SUMA':
        # Objective 1: minimizar la suma de distancias entre pares del mismo cluster
        md.setObjective(gp.quicksum(dist[i][j] * Z[i, j] for i in V for j in V if i < j), GRB.MINIMIZE)
    else:
        # Objective 2: minimizar el diametro maximo
        md.setObjective(Rmax, GRB.MINIMIZE)

else:
    raise ValueError(f'MODELO desconocido: {MODELO}')

# ============================================================================
# MODEL UPDATE AND OPTIMIZATION
# ============================================================================

md.update()

# md.write('modelo_clustering.lp')   # descomentar para revisar el modelo escrito

md.setParam(GRB.Param.OutputFlag, 1)
md.setParam(GRB.Param.TimeLimit, TIME_LIMIT)
md.setParam(GRB.Param.MIPGap, MIP_GAP)

md.optimize()

# ============================================================================
# SOLUTION EXTRACTION AND DISPLAY
# ============================================================================

if md.SolCount == 0:
    print('\nNo se encontro solucion. status =', md.status,
          '(3 = infactible, 9 = limite de tiempo sin solucion)')
    if md.status == GRB.INFEASIBLE:
        md.computeIIS()
        for c in md.getConstrs():
            if c.IISConstr:
                print('  restriccion en conflicto:', c.ConstrName)
    raise SystemExit

# etiqueta[i] = identificador del cluster al que pertenece el punto i
# (CENTROS: indice del punto-centro | PARES: numero de cluster k)
if MODELO == 'CENTROS':
    centros = [j for j in V if Y[j].X > 0.5]
    etiqueta = [next(j for j in V if X[i, j].X > 0.5) for i in V]
else:
    centros = []
    etiqueta = [next(k for k in Kset if X[i, k].X > 0.5) for i in V]

grupos = {}
for i in V:
    grupos.setdefault(etiqueta[i], []).append(i)

print("\n" + "=" * 60)
print("CLUSTERING SOLUTION")
print("=" * 60)
print(f'Objetivo = {md.ObjVal:.4f} | cota = {md.ObjBound:.4f} | gap = {md.MIPGap * 100:.2f} %')

for et, miembros in grupos.items():
    carga = sum(q[i] for i in miembros)
    diametro = max((dist[i][j] for i in miembros for j in miembros), default=0)
    if MODELO == 'CENTROS':
        suma = sum(dist[i][et] for i in miembros)
        radio = max(dist[i][et] for i in miembros)
        print(f'Cluster con centro {et}: {len(miembros)} puntos | carga = {carga:.1f} | '
              f'suma dist = {suma:.2f} | radio = {radio:.2f} | diametro = {diametro:.2f}')
    else:
        pares = sum(dist[i][j] for i in miembros for j in miembros if i < j)
        print(f'Cluster {et}: {len(miembros)} puntos | carga = {carga:.1f} | '
              f'suma pares = {pares:.2f} | diametro = {diametro:.2f}')
    print(f'    puntos: {miembros}')

# ---- Guardar resultado en csv ----------------------------------------------
with open(ARCHIVO_RESULTADO, 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['punto', 'cluster'] + ([f'c{d}' for d in range(coord.shape[1])] if coord is not None else []))
    for i in V:
        w.writerow([i, etiqueta[i]] + (list(coord[i]) if coord is not None else []))
print(f'\nResultado guardado en {ARCHIVO_RESULTADO}')

# ---- Grafico (solo si hay coordenadas) --------------------------------------
if coord is not None and coord.shape[1] >= 2:
    plt.figure(figsize=(7, 6))
    colores = plt.cm.tab10.colors
    for idx, (et, miembros) in enumerate(grupos.items()):
        c = colores[idx % len(colores)]
        plt.scatter([coord[i][0] for i in miembros], [coord[i][1] for i in miembros],
                    color=c, label=f'cluster {et}')
        if MODELO == 'CENTROS':
            for i in miembros:   # linea de cada punto a su centro
                plt.plot([coord[i][0], coord[et][0]], [coord[i][1], coord[et][1]],
                         color=c, alpha=0.3, linewidth=0.8)
            plt.scatter(coord[et][0], coord[et][1], marker='*', s=300, color=c, edgecolor='k')
    plt.title(f'{MODELO} / {OBJETIVO} | K = {K} | obj = {md.ObjVal:.2f}')
    plt.legend()
    plt.savefig('clustering.png', dpi=120)
    if MOSTRAR_GRAFICO:
        plt.show()
