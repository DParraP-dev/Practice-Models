"""
=============================================================================
 GUIA DE ESTUDIO: MODELOS Y METODOS DE OPTIMIZACION CON GUROBI (PYTHON)
=============================================================================

Como usar este archivo
----------------------
    python guia_gurobi.py                 -> muestra el menu de ejemplos
    python guia_gurobi.py todo            -> ejecuta todos los ejemplos
    python guia_gurobi.py p_mediana       -> ejecuta un ejemplo concreto

Cada ejemplo es una funcion independiente (copiar y pegar la que sirva).
Instalacion:  pip install gurobipy      (con licencia de estudiante no hay limite de tamano;
                                          la version de pip sin licencia limita a 2000 variables)

ARCHIVOS RELACIONADOS
  VRP_MILP_base.py         script de clase (VRP): la estructura de referencia.
  Clustering_MILP_base.py  ese mismo estilo aplicado a clustering, listo para
                           cargar los archivos de datos que entregue el profesor.
Esta guia usa la nomenclatura de clase: md (modelo), X, Y (binarias), dist, V, K, q, Q.

INDICE
------
  PARTE 0. Metodologia en 6 pasos y plantilla base
  PARTE 1. Cheatsheet de la API de gurobipy
  PARTE 2. Problemas clasicos (LP / MIP)
           2.1 produccion (max, <=)          + analisis de sensibilidad
           2.2 dieta (min, >=)
           2.3 transporte (oferta/demanda)
           2.4 asignacion (binarias)
           2.5 mochila (binarias)
           2.6 localizacion de instalaciones (costo fijo, big-M)
           2.7 planificacion multiperiodo (inventarios)
           2.8 ruta mas corta (flujo en redes)
           2.9 cobertura de conjuntos
  PARTE 3. Linealizaciones y restricciones logicas (abs, max, if-then...)
  PARTE 4. Modelo infactible / no acotado: como diagnosticar
  PARTE 5. CLUSTERING con optimizacion
           5.1 leer archivos de datos y calcular distancias
           5.2 p-mediana (k-medoids)           <- el mas importante
           5.3 p-mediana con capacidades / clusters balanceados
           5.4 p-centro (minimizar el radio maximo)
           5.5 formulacion por pares (sin centros)
           5.6 minimo numero de clusters con diametro maximo
           5.7 asignar puntos a centroides dados
           5.8 elegir K: barrido y metodo del codo
           5.9 que NO es un MIP: k-means
  PARTE 6. Checklist de errores comunes y consejos para el examen
"""

import math
import random
import sys

import gurobipy as gp
from gurobipy import GRB


# =============================================================================
# PARTE 0. METODOLOGIA Y PLANTILLA
# =============================================================================
"""
Los 6 pasos para modelar CUALQUIER problema (escribirlos en el examen ayuda):

  1. CONJUNTOS / INDICES  : ¿sobre que se indexa? (productos i, plantas j, ...)
  2. PARAMETROS (datos)   : costos, capacidades, demandas, distancias.
  3. VARIABLES DE DECISION: ¿que decide el modelo? Definir TIPO y COTAS:
        - continua   (GRB.CONTINUOUS): cantidades divisibles
        - entera     (GRB.INTEGER)   : unidades indivisibles
        - binaria    (GRB.BINARY)    : decisiones si/no, asignaciones
  4. FUNCION OBJETIVO     : minimizar costo / maximizar utilidad.
  5. RESTRICCIONES        : capacidad (<=), demanda (>=), balance (==), enlace.
  6. RESOLVER E INTERPRETAR: estado, valor objetivo, valores de variables.

Plantilla minima (copiar y adaptar):
"""


def plantilla():
    """Max 3x + 2y  s.a.  x + y <= 4 ;  x + 3y <= 6 ;  x, y >= 0"""
    # --- 1-2. Datos ----------------------------------------------------------
    utilidad = {"x": 3, "y": 2}
    # --- Modelo --------------------------------------------------------------
    md = gp.Model("plantilla")
    # --- 3. Variables --------------------------------------------------------
    # OJO: por defecto lb=0 y ub=infinito. Para variables libres usar lb=-GRB.INFINITY
    x = md.addVar(vtype=GRB.CONTINUOUS, lb=0, name="x")
    y = md.addVar(vtype=GRB.CONTINUOUS, lb=0, name="y")
    # --- 4. Objetivo ---------------------------------------------------------
    md.setObjective(utilidad["x"] * x + utilidad["y"] * y, GRB.MAXIMIZE)
    # --- 5. Restricciones ----------------------------------------------------
    md.addConstr(x + y <= 4, name="r1")
    md.addConstr(x + 3 * y <= 6, name="r2")
    # --- 6. Resolver ---------------------------------------------------------
    md.optimize()
    if md.status == GRB.OPTIMAL:
        print(f"Objetivo = {md.ObjVal:.2f}")
        for v in md.getVars():
            print(f"  {v.VarName} = {v.X:.2f}")
    return md


# =============================================================================
# PARTE 1. CHEATSHEET DE LA API
# =============================================================================
def cheatsheet_api():
    """Recorrido por todo lo que se usa con frecuencia. Ejecutarlo y leerlo."""
    md = gp.Model("cheatsheet")

    # ---------------- Parametros utiles del solver ---------------------------
    md.setParam(GRB.Param.OutputFlag, 0)      # 0 = silencia el log (1 = lo muestra)
    # md.setParam(GRB.Param.TimeLimit, 60)   # segundos maximos
    # md.setParam(GRB.Param.MIPGap, 0.01)    # detener con gap relativo del 1 %
    # md.setParam(GRB.Param.Threads, 1)

    # ---------------- Variables ---------------------------------------------
    a = md.addVar(lb=0, ub=10, obj=0, vtype=GRB.CONTINUOUS, name="a")
    b = md.addVar(vtype=GRB.INTEGER, name="b")          # entera >= 0
    c = md.addVar(vtype=GRB.BINARY, name="c")           # 0 / 1
    libre = md.addVar(lb=-GRB.INFINITY, name="libre")   # puede ser negativa

    # Varias a la vez: devuelve un tupledict indexado
    I = ["p1", "p2", "p3"]
    J = ["t1", "t2"]
    x = md.addVars(I, vtype=GRB.CONTINUOUS, name="x")          # x["p1"]
    z = md.addVars(I, J, vtype=GRB.BINARY, name="z")           # z["p1","t2"]
    # indices numericos: md.addVars(5, 3) -> z[i, j] con i en 0..4, j en 0..2
    # Indices irregulares (solo pares validos):
    arcos = gp.tuplelist([("A", "B"), ("B", "C"), ("A", "C")])
    f = md.addVars(arcos, name="f")

    # ---------------- Sumas --------------------------------------------------
    costo = {"p1": 4, "p2": 5, "p3": 6}
    expr1 = gp.quicksum(costo[i] * x[i] for i in I)    # suma generica (la mas usada)
    expr2 = x.sum()                                    # suma de todas
    expr3 = x.prod(costo)                              # sum costo[i]*x[i]
    expr4 = z.sum("p1", "*")                           # suma sobre j fijando i = p1
    expr5 = z.sum("*", "t2")                           # suma sobre i fijando j = t2
    # f.sum("A", "*") = flujo que sale de A ; f.sum("*", "C") = flujo que entra a C

    # ---------------- Restricciones -----------------------------------------
    md.addConstr(a + b <= 10, name="una_restriccion")
    md.addConstr(expr1 >= 5, name="demanda")
    md.addConstr(x["p1"] == 2 * x["p2"])                # igualdad: usar ==
    md.addConstrs((z.sum(i, "*") <= 1 for i in I), name="max_uno_por_i")   # familia
    md.addConstrs((x[i] <= 8 * c for i in I), name="enlace")               # big-M
    md.addConstr(libre >= -3)
    # Cotas rapidas despues de crear: x[i].UB = 5 ; x[i].LB = 1
    # Fijar variable: x["p1"].LB = x["p1"].UB = 3

    # ---------------- Objetivo ----------------------------------------------
    md.setObjective(expr1 + a + 2 * b, GRB.MINIMIZE)    # o GRB.MAXIMIZE
    # md.ModelSense = GRB.MAXIMIZE  (alternativa)

    # ---------------- Resolver y leer resultados ----------------------------
    md.optimize()
    print("status:", md.status, "(2=OPTIMAL, 3=INFEASIBLE, 4=INF_OR_UNBD, "
          "5=UNBOUNDED, 9=TIME_LIMIT)")
    if md.status == GRB.OPTIMAL:
        print("ObjVal  :", md.ObjVal)
        print("a.X     :", a.X)
        print("x       :", md.getAttr("X", x))              # dict {indice: valor}
        print("NumVars :", md.NumVars, " NumConstrs:", md.NumConstrs)
        print("Binarias:", md.NumBinVars, " Enteras (incluye binarias):", md.NumIntVars)
        # Para MIP: md.MIPGap, md.ObjBound, md.SolCount, md.Runtime
        # Recorrer solo lo que vale algo:
        activos = [k for k, v in z.items() if v.X > 0.5]    # binarias: comparar con 0.5
        print("z activas:", activos)

    # ---------------- Guardar / depurar el modelo ---------------------------
    # md.write("modelo.lp")   # formato legible: revisar que lo escrito = lo pensado
    # md.write("modelo.sol")  # solucion
    # md.update()             # (opcional) refresca el modelo antes de leer atributos
    return md


# =============================================================================
# PARTE 2. PROBLEMAS CLASICOS
# =============================================================================
def ej_produccion():
    """
    2.1 PRODUCCION (LP de maximizacion) + ANALISIS DE SENSIBILIDAD.
    Una fabrica produce sillas, mesas y camas. Cada una consume horas de
    carpinteria y de acabado, y madera. Maximizar utilidad.

      max  sum_i util[i] * x[i]
      s.a. sum_i uso[r,i] * x[i] <= disp[r]     para cada recurso r
           x[i] >= 0
    """
    productos = ["silla", "mesa", "cama"]
    recursos = ["carpinteria", "acabado", "madera"]
    util = {"silla": 30, "mesa": 50, "cama": 80}
    disp = {"carpinteria": 400, "acabado": 300, "madera": 500}
    uso = {
        ("carpinteria", "silla"): 2, ("carpinteria", "mesa"): 4, ("carpinteria", "cama"): 6,
        ("acabado", "silla"): 1,     ("acabado", "mesa"): 2,     ("acabado", "cama"): 4,
        ("madera", "silla"): 3,      ("madera", "mesa"): 5,      ("madera", "cama"): 8,
    }

    md = gp.Model("produccion")
    md.setParam(GRB.Param.OutputFlag, 0)
    x = md.addVars(productos, lb=0, name="x")
    md.setObjective(gp.quicksum(util[i] * x[i] for i in productos), GRB.MAXIMIZE)
    rest = md.addConstrs(
        (gp.quicksum(uso[r, i] * x[i] for i in productos) <= disp[r] for r in recursos),
        name="recurso",
    )
    md.optimize()

    print(f"Utilidad maxima = {md.ObjVal:.2f}")
    for i in productos:
        print(f"  produce {x[i].X:8.2f} de {i}")

    # ---- Sensibilidad (SOLO para LP, no para modelos con enteras) -----------
    print("\nSensibilidad de restricciones:")
    print(f"{'recurso':<12}{'holgura':>9}{'precio sombra':>15}{'RHS desde':>11}{'RHS hasta':>11}")
    for r in recursos:
        c = rest[r]
        # Pi = precio sombra: cuanto sube el objetivo por 1 unidad extra de RHS
        # Slack = holgura (0 => restriccion activa/limitante)
        print(f"{r:<12}{c.Slack:9.2f}{c.Pi:15.2f}{c.SARHSLow:11.2f}{c.SARHSUp:11.2f}")
    print("\nSensibilidad de variables:")
    print(f"{'var':<8}{'valor':>9}{'costo reducido':>16}{'c desde':>10}{'c hasta':>10}")
    for i in productos:
        v = x[i]
        # RC = costo reducido: cuanto debe mejorar el coef. para que entre a la base
        print(f"{i:<8}{v.X:9.2f}{v.RC:16.2f}{v.SAObjLow:10.2f}{v.SAObjUp:10.2f}")
    return md


def ej_dieta():
    """
    2.2 DIETA (LP de minimizacion con restricciones >=).

      min  sum_a precio[a] * x[a]
      s.a. sum_a aporte[n,a] * x[a] >= minimo[n]    para cada nutriente n
           x[a] <= maximo[a]  (cota superior de porciones)
    """
    alimentos = ["pan", "leche", "huevo", "carne"]
    nutrientes = ["calorias", "proteina", "calcio"]
    precio = {"pan": 2.0, "leche": 3.5, "huevo": 2.5, "carne": 8.0}
    minimo = {"calorias": 2000, "proteina": 55, "calcio": 800}
    aporte = {
        ("calorias", "pan"): 250, ("calorias", "leche"): 150, ("calorias", "huevo"): 80, ("calorias", "carne"): 300,
        ("proteina", "pan"): 8,   ("proteina", "leche"): 8,   ("proteina", "huevo"): 6,  ("proteina", "carne"): 25,
        ("calcio", "pan"): 50,    ("calcio", "leche"): 300,   ("calcio", "huevo"): 30,   ("calcio", "carne"): 20,
    }
    md = gp.Model("dieta")
    md.setParam(GRB.Param.OutputFlag, 0)
    x = md.addVars(alimentos, lb=0, ub=10, name="porciones")   # ub = cota por variable
    md.setObjective(x.prod(precio), GRB.MINIMIZE)
    md.addConstrs(
        (gp.quicksum(aporte[n, a] * x[a] for a in alimentos) >= minimo[n] for n in nutrientes),
        name="nutriente",
    )
    md.optimize()
    print(f"Costo minimo = {md.ObjVal:.2f}")
    for a in alimentos:
        print(f"  {a:<6}: {x[a].X:.2f} porciones")
    return md


def ej_transporte():
    """
    2.3 TRANSPORTE. Enviar desde plantas (oferta) a clientes (demanda).

      min  sum_{i,j} c[i,j] * x[i,j]
      s.a. sum_j x[i,j] <= oferta[i]      (cada planta)
           sum_i x[i,j] >= demanda[j]     (cada cliente)
           x >= 0
    Si oferta total == demanda total, usar == en ambas.
    Para que x sea entero no hace falta declararlo: la matriz es totalmente
    unimodular, el LP ya da soluciones enteras si los datos son enteros.
    """
    plantas = ["P1", "P2", "P3"]
    clientes = ["C1", "C2", "C3", "C4"]
    oferta = {"P1": 120, "P2": 100, "P3": 80}
    demanda = {"C1": 70, "C2": 90, "C3": 60, "C4": 80}
    costo = {
        ("P1", "C1"): 4, ("P1", "C2"): 6, ("P1", "C3"): 9, ("P1", "C4"): 5,
        ("P2", "C1"): 7, ("P2", "C2"): 3, ("P2", "C3"): 4, ("P2", "C4"): 8,
        ("P3", "C1"): 6, ("P3", "C2"): 5, ("P3", "C3"): 2, ("P3", "C4"): 7,
    }
    # Atajo: gp.multidict permite declarar claves y varios diccionarios juntos
    # arcos, costo = gp.multidict({("P1","C1"): 4, ...})

    md = gp.Model("transporte")
    md.setParam(GRB.Param.OutputFlag, 0)
    x = md.addVars(plantas, clientes, lb=0, name="x")
    md.setObjective(gp.quicksum(costo[i, j] * x[i, j] for i in plantas for j in clientes),
                   GRB.MINIMIZE)
    md.addConstrs((x.sum(i, "*") <= oferta[i] for i in plantas), name="oferta")
    md.addConstrs((x.sum("*", j) >= demanda[j] for j in clientes), name="demanda")
    md.optimize()
    print(f"Costo minimo = {md.ObjVal:.2f}")
    for (i, j), v in x.items():
        if v.X > 1e-6:
            print(f"  {i} -> {j}: {v.X:.0f}")
    return md


def ej_asignacion():
    """
    2.4 ASIGNACION (variables BINARIAS). n trabajadores a n tareas.

      min  sum_{i,j} c[i,j] * x[i,j]
      s.a. sum_j x[i,j] == 1   (cada trabajador hace 1 tarea)
           sum_i x[i,j] == 1   (cada tarea la hace 1 trabajador)
           x[i,j] in {0,1}
    """
    trabajadores = ["Ana", "Beto", "Carla", "Diego"]
    tareas = ["T1", "T2", "T3", "T4"]
    c = {
        "Ana":   {"T1": 9, "T2": 2, "T3": 7, "T4": 8},
        "Beto":  {"T1": 6, "T2": 4, "T3": 3, "T4": 7},
        "Carla": {"T1": 5, "T2": 8, "T3": 1, "T4": 8},
        "Diego": {"T1": 7, "T2": 6, "T3": 9, "T4": 4},
    }
    md = gp.Model("asignacion")
    md.setParam(GRB.Param.OutputFlag, 0)
    x = md.addVars(trabajadores, tareas, vtype=GRB.BINARY, name="x")
    md.setObjective(gp.quicksum(c[i][j] * x[i, j] for i in trabajadores for j in tareas),
                   GRB.MINIMIZE)
    md.addConstrs((x.sum(i, "*") == 1 for i in trabajadores), name="trab")
    md.addConstrs((x.sum("*", j) == 1 for j in tareas), name="tarea")
    md.optimize()
    print(f"Costo minimo = {md.ObjVal:.2f}")
    for (i, j), v in x.items():
        if v.X > 0.5:
            print(f"  {i} -> {j} (costo {c[i][j]})")
    return md


def ej_mochila():
    """
    2.5 MOCHILA (binarias, una sola restriccion de capacidad).

      max  sum_i valor[i] * x[i]
      s.a. sum_i peso[i] * x[i] <= W
           x[i] in {0,1}
    Variantes: x entera (mochila no acotada) -> vtype=GRB.INTEGER, ub=cantidad.
    """
    items = range(6)
    valor = [10, 13, 18, 31, 7, 15]
    peso = [11, 15, 20, 35, 10, 33]
    W = 47
    md = gp.Model("mochila")
    md.setParam(GRB.Param.OutputFlag, 0)
    x = md.addVars(items, vtype=GRB.BINARY, name="x")
    md.setObjective(gp.quicksum(valor[i] * x[i] for i in items), GRB.MAXIMIZE)
    md.addConstr(gp.quicksum(peso[i] * x[i] for i in items) <= W, name="capacidad")
    md.optimize()
    elegidos = [i for i in items if x[i].X > 0.5]
    print(f"Valor = {md.ObjVal:.0f}; items {elegidos}; peso = {sum(peso[i] for i in elegidos)}/{W}")
    return md


def ej_localizacion():
    """
    2.6 LOCALIZACION DE INSTALACIONES (con capacidad y costo fijo).
    Patron MUY comun: variable binaria y[j] "se abre j" enlazada con la
    cantidad x[i,j] mediante  x[i,j] <= cap[j] * y[j]   (big-M).

      min  sum_j fijo[j]*y[j] + sum_{i,j} c[i,j]*x[i,j]
      s.a. sum_j x[i,j] == demanda[i]          (se cubre cada cliente)
           sum_i x[i,j] <= cap[j] * y[j]       (solo despacha si esta abierta)
           y[j] in {0,1},  x[i,j] >= 0
    """
    clientes = ["C1", "C2", "C3", "C4", "C5"]
    sitios = ["S1", "S2", "S3"]
    demanda = {"C1": 30, "C2": 40, "C3": 25, "C4": 35, "C5": 20}
    cap = {"S1": 90, "S2": 80, "S3": 70}
    fijo = {"S1": 500, "S2": 400, "S3": 350}
    c = {("C1", "S1"): 2, ("C1", "S2"): 5, ("C1", "S3"): 6,
         ("C2", "S1"): 3, ("C2", "S2"): 2, ("C2", "S3"): 7,
         ("C3", "S1"): 6, ("C3", "S2"): 3, ("C3", "S3"): 2,
         ("C4", "S1"): 5, ("C4", "S2"): 4, ("C4", "S3"): 3,
         ("C5", "S1"): 7, ("C5", "S2"): 6, ("C5", "S3"): 2}

    md = gp.Model("localizacion")
    md.setParam(GRB.Param.OutputFlag, 0)
    y = md.addVars(sitios, vtype=GRB.BINARY, name="y")
    x = md.addVars(clientes, sitios, lb=0, name="x")
    md.setObjective(
        gp.quicksum(fijo[j] * y[j] for j in sitios)
        + gp.quicksum(c[i, j] * x[i, j] for i in clientes for j in sitios),
        GRB.MINIMIZE,
    )
    md.addConstrs((x.sum(i, "*") == demanda[i] for i in clientes), name="demanda")
    md.addConstrs((x.sum("*", j) <= cap[j] * y[j] for j in sitios), name="capacidad")
    md.optimize()
    print(f"Costo total = {md.ObjVal:.2f}")
    print("  Abiertos:", [j for j in sitios if y[j].X > 0.5])
    for (i, j), v in x.items():
        if v.X > 1e-6:
            print(f"  {i} <- {j}: {v.X:.0f}")
    return md


def ej_multiperiodo():
    """
    2.7 PLANIFICACION MULTIPERIODO con inventario.
    Variable de estado: inventario al final del periodo t.

      Balance:  inv[t-1] + prod[t] - ventas[t] == inv[t]     (inv[-1] = inv inicial)
      min  sum_t costo_prod*prod[t] + costo_inv*inv[t]
      s.a. prod[t] <= cap_prod ;  inv[t] >= 0 ; ventas[t] == demanda[t]
    """
    T = range(6)
    demanda = [80, 120, 150, 90, 60, 110]
    cap_prod = 120
    c_prod = [10, 10, 12, 12, 11, 11]
    c_inv = 1.5
    inv0 = 20

    md = gp.Model("multiperiodo")
    md.setParam(GRB.Param.OutputFlag, 0)
    prod = md.addVars(T, ub=cap_prod, name="prod")
    inv = md.addVars(T, lb=0, name="inv")
    md.setObjective(gp.quicksum(c_prod[t] * prod[t] + c_inv * inv[t] for t in T), GRB.MINIMIZE)
    for t in T:
        anterior = inv0 if t == 0 else inv[t - 1]       # <- patron para t = 0
        md.addConstr(anterior + prod[t] - demanda[t] == inv[t], name=f"balance_{t}")
    md.optimize()
    print(f"Costo = {md.ObjVal:.2f}")
    print("  t  demanda  prod  inv")
    for t in T:
        print(f"  {t}  {demanda[t]:7d}  {prod[t].X:4.0f}  {inv[t].X:4.0f}")
    return md


def ej_ruta_corta():
    """
    2.8 RUTA MAS CORTA / FLUJO EN REDES.
    Variable binaria por arco. Conservacion de flujo en cada nodo:
        salida - entrada = +1 en origen, -1 en destino, 0 en el resto.
    (Flujo de costo minimo general: salida - entrada = oferta neta[n],
     con x <= capacidad del arco.)
    """
    arcos, costo = gp.multidict({
        ("A", "B"): 7, ("A", "C"): 9, ("A", "F"): 14,
        ("B", "C"): 10, ("B", "D"): 15,
        ("C", "D"): 11, ("C", "F"): 2,
        ("D", "E"): 6, ("F", "E"): 9,
    })
    nodos = ["A", "B", "C", "D", "E", "F"]
    origen, destino = "A", "E"

    md = gp.Model("ruta_corta")
    md.setParam(GRB.Param.OutputFlag, 0)
    x = md.addVars(arcos, vtype=GRB.BINARY, name="x")
    md.setObjective(x.prod(costo), GRB.MINIMIZE)
    for n in nodos:
        b = 1 if n == origen else (-1 if n == destino else 0)
        md.addConstr(x.sum(n, "*") - x.sum("*", n) == b, name=f"flujo_{n}")
    md.optimize()
    print(f"Distancia = {md.ObjVal:.0f}; arcos:", [a for a in arcos if x[a].X > 0.5])
    return md


def ej_cobertura():
    """
    2.9 COBERTURA DE CONJUNTOS. Abrir el minimo de estaciones tal que cada
    zona quede cubierta por al menos una.

      min  sum_j y[j]
      s.a. sum_{j que cubre i} y[j] >= 1      para cada zona i
    """
    zonas = range(1, 8)
    cubre = {          # estacion -> zonas que cubre
        "E1": {1, 2, 3}, "E2": {3, 4, 5}, "E3": {5, 6, 7},
        "E4": {1, 4, 7}, "E5": {2, 6},
    }
    md = gp.Model("cobertura")
    md.setParam(GRB.Param.OutputFlag, 0)
    y = md.addVars(cubre.keys(), vtype=GRB.BINARY, name="y")
    md.setObjective(y.sum(), GRB.MINIMIZE)
    md.addConstrs((gp.quicksum(y[j] for j in cubre if i in cubre[j]) >= 1 for i in zonas),
                 name="cubrir")
    md.optimize()
    print(f"Estaciones = {md.ObjVal:.0f}:", [j for j in cubre if y[j].X > 0.5])
    return md


# =============================================================================
# PARTE 3. LINEALIZACIONES Y RESTRICCIONES LOGICAS
# =============================================================================
def ej_linealizaciones():
    """
    Tecnicas para convertir condiciones no lineales o logicas en MIP.
    M = constante "grande" pero LO MAS PEQUENA POSIBLE (M enorme -> modelo debil).

    (a) VALOR ABSOLUTO en el objetivo (minimizar |g(x)|):
            variable t >= 0 ;  t >= g(x) ;  t >= -g(x) ;  min t
    (b) MINIMAX (minimizar el maximo de varias expresiones):
            variable z ;  z >= e_k  para todo k ;  min z
        MAXIMIN (maximizar el minimo):  z <= e_k ;  max z
    (c) COSTO FIJO:  x <= M*y ;  costo = fijo*y + c*x
    (d) SI y == 1 ENTONCES expr <= b:   expr <= b + M*(1 - y)
    (e) O ESTO O LO OTRO (al menos una se cumple):
            expr1 <= b1 + M*(1 - w) ;  expr2 <= b2 + M*w ;  w binaria
    (f) AL MENOS k de n condiciones:  sum_i w[i] >= k  con cada w[i] activando una.
    (g) PRODUCTO binaria*continua (p = y*x, 0<=x<=U):
            p <= U*y ;  p <= x ;  p >= x - U*(1-y) ;  p >= 0
    (h) Gurobi trae restricciones GENERALES que lo hacen por ti:
            addGenConstrAbs, addGenConstrMax, addGenConstrMin,
            addGenConstrAnd, addGenConstrOr, addGenConstrIndicator
    """
    # ---- (a) valor absoluto: min |x - 5| + |y + 2| con x + y == 10 ----------
    md = gp.Model("abs")
    md.setParam(GRB.Param.OutputFlag, 0)
    x = md.addVar(lb=-GRB.INFINITY, name="x")
    y = md.addVar(lb=-GRB.INFINITY, name="y")
    t1 = md.addVar(name="t1")
    t2 = md.addVar(name="t2")
    md.addConstr(x + y == 10)
    md.addConstr(t1 >= x - 5)
    md.addConstr(t1 >= -(x - 5))
    md.addConstr(t2 >= y + 2)
    md.addConstr(t2 >= -(y + 2))
    md.setObjective(t1 + t2, GRB.MINIMIZE)
    md.optimize()
    print(f"(a) abs      : obj={md.ObjVal:.2f}, x={x.X:.2f}, y={y.X:.2f}")

    # ---- (b) minimax: repartir 100 unidades en 3 destinos minimizando la mayor carga ponderada
    md = gp.Model("minimax")
    md.setParam(GRB.Param.OutputFlag, 0)
    w = {0: 1.0, 1: 2.0, 2: 4.0}
    q = md.addVars(w.keys(), lb=0, name="q")
    z = md.addVar(name="z")
    md.addConstr(q.sum() == 100)
    md.addConstrs((z >= w[k] * q[k] for k in w), name="max")
    md.setObjective(z, GRB.MINIMIZE)
    md.optimize()
    print(f"(b) minimax  : z={z.X:.2f}, q={[round(q[k].X, 2) for k in w]}")

    # ---- (c) costo fijo: x <= M*y ------------------------------------------
    md = gp.Model("fijo")
    md.setParam(GRB.Param.OutputFlag, 0)
    x = md.addVar(ub=50, name="x")
    y = md.addVar(vtype=GRB.BINARY, name="y")
    md.addConstr(x <= 50 * y)
    md.addConstr(x >= 10)
    md.setObjective(100 * y + 2 * x, GRB.MINIMIZE)
    md.optimize()
    print(f"(c) fijo     : obj={md.ObjVal:.2f}, y={y.X:.0f}, x={x.X:.0f}")

    # ---- (d)/(e) implicaciones con big-M vs. restriccion INDICADORA ----------
    md = gp.Model("logica")
    md.setParam(GRB.Param.OutputFlag, 0)
    x = md.addVar(ub=100, name="x")
    w = md.addVar(vtype=GRB.BINARY, name="w")
    M = 100
    # "Si w == 1 entonces x <= 20"  (big-M)
    md.addConstr(x <= 20 + M * (1 - w))
    # Equivalente con indicadora (sin necesidad de M):
    #   md.addGenConstrIndicator(w, True, x, GRB.LESS_EQUAL, 20)
    #   md.addConstr((w == 1) >> (x <= 20))            # sintaxis corta
    # "Si w == 0 entonces x >= 60"
    md.addConstr(x >= 60 - 60 * w)
    md.setObjective(x - 30 * w, GRB.MAXIMIZE)
    md.optimize()
    print(f"(d) logica   : obj={md.ObjVal:.2f}, w={round(w.X)}, x={x.X:.0f}")

    # ---- (g) producto binaria*continua -------------------------------------
    md = gp.Model("producto")
    md.setParam(GRB.Param.OutputFlag, 0)
    U = 10
    x = md.addVar(ub=U, name="x")
    y = md.addVar(vtype=GRB.BINARY, name="y")
    p = md.addVar(name="p")                       # p = x*y
    md.addConstr(p <= U * y)
    md.addConstr(p <= x)
    md.addConstr(p >= x - U * (1 - y))
    md.addConstr(x == 7)
    md.addConstr(y == 1)
    md.setObjective(p, GRB.MAXIMIZE)
    md.optimize()
    print(f"(g) producto : p={p.X:.1f} (esperado 7)")

    # ---- (h) restricciones generales ---------------------------------------
    md = gp.Model("general")
    md.setParam(GRB.Param.OutputFlag, 0)
    x = md.addVar(lb=-10, ub=10, name="x")
    absx = md.addVar(name="absx")
    md.addGenConstrAbs(absx, x, name="abs")       # absx = |x|
    md.addConstr(x <= -3)
    md.setObjective(absx, GRB.MINIMIZE)
    md.optimize()
    print(f"(h) GenConstr: |x|={absx.X:.1f}, x={x.X:.1f}")

    # ---- Multiobjetivo (jerarquico): primero el de mayor prioridad ----------
    md = gp.Model("multiobj")
    md.setParam(GRB.Param.OutputFlag, 0)
    x = md.addVar(ub=10, name="x")
    y = md.addVar(ub=10, name="y")
    md.addConstr(x + y <= 12)
    md.ModelSense = GRB.MAXIMIZE
    md.setObjectiveN(x, index=0, priority=2, name="primero_x")
    md.setObjectiveN(y, index=1, priority=1, name="luego_y")
    md.optimize()
    print(f"(i) multiobj : x={x.X:.1f}, y={y.X:.1f}")
    return md


# =============================================================================
# PARTE 4. DIAGNOSTICO: INFACTIBLE / NO ACOTADO
# =============================================================================
def ej_infactible():
    """
    status 3 (INFEASIBLE): restricciones contradictorias.
    status 5 (UNBOUNDED) : el objetivo mejora sin limite (falta una restriccion/cota).
    status 4 (INF_OR_UNBD): Gurobi no sabe cual; poner md.setParam(GRB.Param.DualReductions, 0)
                            y reoptimizar para distinguir.
    Herramienta clave: IIS = subconjunto minimo de restricciones en conflicto.
    """
    md = gp.Model("infactible")
    md.setParam(GRB.Param.OutputFlag, 0)
    md.setParam(GRB.Param.DualReductions, 0)     # evita el status ambiguo 4 (INF_OR_UNBD)
    x = md.addVar(name="x")
    y = md.addVar(name="y")
    md.addConstr(x + y <= 4, name="a")
    md.addConstr(x + y >= 6, name="b")       # contradice a
    md.addConstr(x <= 10, name="c")          # irrelevante
    md.setObjective(x + y, GRB.MAXIMIZE)
    md.optimize()

    if md.status == GRB.INFEASIBLE:
        print("Modelo INFACTIBLE. Calculando IIS...")
        md.computeIIS()
        for c in md.getConstrs():
            if c.IISConstr:
                print("  en conflicto:", c.ConstrName)
        # md.write("conflicto.ilp")
        # Alternativa: md.feasRelax(...) para ver cuanto habria que relajar.
    elif md.status in (GRB.UNBOUNDED, GRB.INF_OR_UNBD):
        print("No acotado: revisar signos del objetivo y cotas faltantes")
    return md


# =============================================================================
# PARTE 5. CLUSTERING CON OPTIMIZACION
# =============================================================================
"""
La plantilla completa, lista para usar con los archivos del profesor, esta en
    Clustering_MILP_base.py     (misma estructura que VRP_MILP_base.py)
Esta parte explica la teoria y deja cada modelo como funcion para estudiarlo.

NOMENCLATURA (la misma de la clase / VRP_MILP_base.py)
    n      numero de puntos            V = range(n)   conjunto de puntos
    K      numero de clusters          Kset = range(K)
    dist   matriz de distancias (lista de listas): dist[i][j]
    q, Q   peso de cada punto y capacidad maxima de un cluster
    md     el modelo de Gurobi         X, Y   variables binarias

IDEA GENERAL
------------
Clustering = repartir n puntos en K grupos para que los puntos de un mismo
grupo esten "cerca". Hay dos formas de modelarlo:

(A) CON CENTROS (p-mediana / k-medoids / p-centro).  Cada cluster tiene un
    punto REAL como representante.
        Y[j]   binaria = 1 si el punto j es elegido como CENTRO
        X[i,j] binaria = 1 si el punto i se asigna al centro j
        (1) sum_j X[i,j] == 1        cada punto va a exactamente un centro
        (2) X[i,j] <= Y[j]           solo se asigna a puntos que son centros
        (3) sum_j Y[j] == K          exactamente K centros
    Objetivos: suma de distancias (p-mediana) o distancia maxima (p-centro).

(B) POR PARES (sin centros).  Importa que los puntos del grupo esten juntos.
        X[i,k] binaria = 1 si el punto i va al cluster k
        Z[i,j] = 1 si i y j quedan en el mismo cluster
        (1) sum_k X[i,k] == 1
        (2) Z[i,j] >= X[i,k] + X[j,k] - 1     para todo k
    Objetivos: suma de distancias entre pares o diametro maximo.

Variantes segun lo que pida el enunciado:
    - Tamano/carga limitada por cluster       -> restriccion con q y Q (5.3)
    - Minimizar la distancia MAXIMA           -> tecnica minimax (5.4)
    - No fijar K, fijar distancia maxima      -> min #clusters   (5.6)
    - Centros ya conocidos                    -> asignacion      (5.7)
    - Elegir K                                -> barrido de K    (5.8)
"""


# ---------------------------- 5.1 DATOS Y DISTANCIAS -------------------------
def leer_numeros(nombre):
    """
    Lee un txt/csv y devuelve la lista de filas numericas. Salta encabezados,
    'NAME:', 'NODE_COORD_SECTION', 'EOF', etc. Acepta separador espacio, coma
    o ';' (csv de Excel con coma decimal).
    Alternativas: np.loadtxt(nombre) o pandas.read_csv(nombre).
    """
    filas = []
    with open(nombre) as f:
        for linea in f:
            if ";" in linea:
                partes = [p.strip().replace(",", ".") for p in linea.split(";")]
            else:
                partes = linea.replace(",", " ").split()
            try:
                fila = [float(p) for p in partes]
            except ValueError:
                continue
            if fila:
                filas.append(fila)
    largos = [len(fila) for fila in filas]
    largo = max(set(largos), key=largos.count)
    return [fila for fila in filas if len(fila) == largo]


def cargar_coordenadas(nombre, columnas=None):
    """
    Devuelve la lista de puntos (tuplas). Si hay 3+ columnas y la primera es un
    indice 1..n (o 0..n-1) la descarta. `columnas` fuerza cuales usar.
    """
    filas = leer_numeros(nombre)
    if columnas is None:
        primera = [fila[0] for fila in filas]
        es_indice = primera in (list(range(1, len(filas) + 1)), list(range(len(filas))))
        columnas = list(range(1 if (len(filas[0]) >= 3 and es_indice) else 0, len(filas[0])))
    return [tuple(fila[c] for c in columnas) for fila in filas]


def generar_puntos(n_por_grupo=(8, 8, 8), centros=((2, 2), (8, 3), (5, 9)),
                   dispersion=1.0, seed=7):
    """Genera puntos 2D alrededor de `centros` (para practicar sin archivo)."""
    rnd = random.Random(seed)
    pts = []
    for (cx, cy), n in zip(centros, n_por_grupo):
        for _ in range(n):
            pts.append((rnd.gauss(cx, dispersion), rnd.gauss(cy, dispersion)))
    return pts


def distancia(p, q, tipo="euclidiana"):
    """Distancia entre dos puntos (tuplas de cualquier dimension)."""
    if tipo == "euclidiana":
        return math.sqrt(sum((a - b) ** 2 for a, b in zip(p, q)))
    if tipo == "manhattan":
        return sum(abs(a - b) for a, b in zip(p, q))
    if tipo == "cuadrada":      # euclidiana al cuadrado (la usa k-means)
        return sum((a - b) ** 2 for a, b in zip(p, q))
    raise ValueError(tipo)


def matriz_distancias(pts, tipo="euclidiana"):
    """dist[i][j] igual que en VRP_MILP_base.py."""
    n = len(pts)
    return [[distancia(pts[i], pts[j], tipo) for j in range(n)] for i in range(n)]
    # Si el profesor entrega directamente la matriz: dist = leer_numeros("matriz.txt")


def imprimir_clusters(dist, centros, asign):
    """asign: dict {i: j}. Muestra los clusters y su costo."""
    total = 0.0
    for j in centros:
        miembros = [i for i, c in asign.items() if c == j]
        costo = sum(dist[i][j] for i in miembros)
        total += costo
        print(f"  Cluster con centro {j}: {len(miembros)} puntos "
              f"{sorted(miembros)} | suma dist = {costo:.2f}")
    print(f"  Suma total de distancias = {total:.2f}")


def _extraer(X, Y, n):
    centros = [j for j in range(n) if Y[j].X > 0.5]
    asign = {i: j for i in range(n) for j in range(n) if X[i, j].X > 0.5}
    return centros, asign


# ---------------------------- 5.2 p-MEDIANA ----------------------------------
def modelo_p_mediana(dist, K, q=None, Q=None, Q_min=None, nombre="p_mediana"):
    """
    p-MEDIANA / k-MEDOIDS (con capacidades opcionales).

      min  sum_{i,j} dist[i][j] * X[i,j]
      s.a. sum_j X[i,j] == 1               para todo i     (cada punto, un centro)
           X[i,j] <= Y[j]                  para todo i,j   (asignar solo a centros)
           sum_j Y[j] == K                                 (exactamente K centros)
           X[j,j] == Y[j]                  para todo j     (el centro esta en su cluster)
           sum_i q[i] X[i,j] <= Q * Y[j]   para todo j     (opcional: carga maxima)
           sum_i q[i] X[i,j] >= Q_min * Y[j]               (opcional: carga minima)
           X[i,j], Y[j] in {0,1}

    Sin capacidades, X puede ser continua (lb=0, ub=1) y la solucion sale
    entera igual (mas rapido). Con capacidades, dejar X BINARIA.
    """
    n = len(dist)
    V = range(n)
    q = q if q is not None else [1] * n
    md = gp.Model(nombre)
    md.setParam(GRB.Param.OutputFlag, 0)
    X = md.addVars(n, n, vtype=GRB.BINARY, name="X")
    Y = md.addVars(n, vtype=GRB.BINARY, name="Y")

    md.setObjective(gp.quicksum(dist[i][j] * X[i, j] for i in V for j in V), GRB.MINIMIZE)
    md.addConstrs((gp.quicksum(X[i, j] for j in V) == 1 for i in V), name="un_centro")
    md.addConstrs((X[i, j] <= Y[j] for i in V for j in V), name="solo_a_centros")
    md.addConstr(gp.quicksum(Y[j] for j in V) == K, name="k_centros")
    md.addConstrs((X[j, j] == Y[j] for j in V), name="centro_en_su_cluster")
    if Q is not None:
        md.addConstrs((gp.quicksum(q[i] * X[i, j] for i in V) <= Q * Y[j] for j in V), name="cap_max")
    if Q_min is not None:
        md.addConstrs((gp.quicksum(q[i] * X[i, j] for i in V) >= Q_min * Y[j] for j in V), name="cap_min")
    return md, X, Y


def ej_p_mediana(K=3, archivo=None):
    """5.2 CLUSTERING p-mediana (k-medoids): minimiza la suma de distancias."""
    pts = cargar_coordenadas(archivo) if archivo else generar_puntos()
    dist = matriz_distancias(pts)
    md, X, Y = modelo_p_mediana(dist, K)
    md.optimize()
    print(f"[p-mediana] n={len(pts)}, K={K}, status={md.status}, obj={md.ObjVal:.2f}")
    centros, asign = _extraer(X, Y, len(pts))
    imprimir_clusters(dist, centros, asign)
    return md


# ---------------------------- 5.3 CAPACIDADES / BALANCEO ---------------------
def ej_p_mediana_capacitada(K=3, Q=9, Q_min=7):
    """5.3 CLUSTERING con carga minima y maxima por cluster (q = 1: numero de puntos)."""
    pts = generar_puntos(n_por_grupo=(12, 6, 6))      # grupos naturales desbalanceados
    dist = matriz_distancias(pts)
    md, X, Y = modelo_p_mediana(dist, K, Q=Q, Q_min=Q_min, nombre="p_mediana_cap")
    md.optimize()
    if md.status != GRB.OPTIMAL:
        print("Sin solucion optima. status =", md.status, "(si es 3: K*Q < n o K*Q_min > n)")
        return md
    print(f"[p-mediana capacitada] n={len(pts)}, K={K}, Q={Q}, Q_min={Q_min}, obj={md.ObjVal:.2f}")
    centros, asign = _extraer(X, Y, len(pts))
    imprimir_clusters(dist, centros, asign)
    return md


# ---------------------------- 5.4 p-CENTRO (MINIMAX) -------------------------
def modelo_p_centro(dist, K):
    """
    p-CENTRO: minimizar la distancia MAXIMA de un punto a su centro (radio).
    Se agrega la variable continua Rmax con la tecnica MINIMAX:

      min  Rmax
      s.a. (las mismas restricciones 1-3 de la p-mediana)
           sum_j dist[i][j]*X[i,j] <= Rmax        para todo i
    """
    n = len(dist)
    V = range(n)
    md = gp.Model("p_centro")
    md.setParam(GRB.Param.OutputFlag, 0)
    X = md.addVars(n, n, vtype=GRB.BINARY, name="X")
    Y = md.addVars(n, vtype=GRB.BINARY, name="Y")
    Rmax = md.addVar(lb=0, name="Rmax")
    md.setObjective(Rmax, GRB.MINIMIZE)
    md.addConstrs((gp.quicksum(X[i, j] for j in V) == 1 for i in V), name="un_centro")
    md.addConstrs((X[i, j] <= Y[j] for i in V for j in V), name="solo_a_centros")
    md.addConstr(gp.quicksum(Y[j] for j in V) == K, name="k_centros")
    md.addConstrs((gp.quicksum(dist[i][j] * X[i, j] for j in V) <= Rmax for i in V), name="def_Rmax")
    return md, X, Y, Rmax


def ej_p_centro(K=3):
    """5.4 CLUSTERING p-centro: minimiza la distancia maxima punto-centro."""
    pts = generar_puntos()
    dist = matriz_distancias(pts)
    md, X, Y, Rmax = modelo_p_centro(dist, K)
    md.optimize()
    print(f"[p-centro] n={len(pts)}, K={K}, radio minimo = {Rmax.X:.3f}")
    centros, asign = _extraer(X, Y, len(pts))
    imprimir_clusters(dist, centros, asign)
    return md


# ---------------------------- 5.5 FORMULACION POR PARES ----------------------
def modelo_pares(dist, K, objetivo="SUMA", q=None, Q=None):
    """
    Clustering SIN centros: X[i,k] = 1 si el punto i va al cluster k.

      Objetivo 'SUMA': min sum_{i<j} dist[i][j] * Z[i,j]      (distancias dentro de grupos)
      Objetivo 'MAX' : min Rmax                               (diametro maximo)
      s.a. sum_k X[i,k] == 1                     para todo i
           sum_i X[i,k] >= 1                     para todo k  (clusters no vacios)
           Z[i,j] >= X[i,k] + X[j,k] - 1         para i<j, todo k     ('SUMA')
           Rmax >= dist[i][j]*(X[i,k] + X[j,k] - 1)  para i<j, todo k ('MAX')
           sum_i q[i] X[i,k] <= Q                para todo k  (opcional)
           X[i,k] == 0 si k > i                  (ruptura de simetria)

    Z puede ser continua: al minimizar, toma 0 o 1 por si sola.
    """
    n = len(dist)
    V = range(n)
    Kset = range(K)
    q = q if q is not None else [1] * n
    md = gp.Model("pares")
    md.setParam(GRB.Param.OutputFlag, 0)
    X = md.addVars(n, K, vtype=GRB.BINARY, name="X")
    Z = md.addVars([(i, j) for i in V for j in V if i < j], lb=0, name="Z")
    Rmax = md.addVar(lb=0, name="Rmax")

    md.addConstrs((gp.quicksum(X[i, k] for k in Kset) == 1 for i in V), name="un_cluster")
    md.addConstrs((gp.quicksum(X[i, k] for i in V) >= 1 for k in Kset), name="cluster_no_vacio")
    md.addConstrs((X[i, k] == 0 for i in V for k in Kset if k > i), name="simetria")
    if Q is not None:
        md.addConstrs((gp.quicksum(q[i] * X[i, k] for i in V) <= Q for k in Kset), name="cap_max")
    if objetivo == "SUMA":
        md.addConstrs((Z[i, j] >= X[i, k] + X[j, k] - 1
                       for i in V for j in V if i < j for k in Kset), name="mismo_cluster")
        md.setObjective(gp.quicksum(dist[i][j] * Z[i, j] for i in V for j in V if i < j), GRB.MINIMIZE)
    else:
        md.addConstrs((Rmax >= dist[i][j] * (X[i, k] + X[j, k] - 1)
                       for i in V for j in V if i < j for k in Kset), name="def_Rmax")
        md.setObjective(Rmax, GRB.MINIMIZE)
    return md, X


def ej_pares(K=3, objetivo="SUMA"):
    """5.5 CLUSTERING por pares (sin centros): suma de distancias o diametro maximo."""
    pts = generar_puntos(n_por_grupo=(6, 6, 6))
    dist = matriz_distancias(pts)
    md, X = modelo_pares(dist, K, objetivo)
    md.optimize()
    print(f"[pares/{objetivo}] n={len(pts)}, K={K}, obj={md.ObjVal:.2f}")
    for k in range(K):
        print(f"  cluster {k}: {[i for i in range(len(pts)) if X[i, k].X > 0.5]}")
    return md


# ---------------------------- 5.6 MIN #CLUSTERS CON DIAMETRO MAXIMO ----------
def modelo_min_clusters_diametro(dist, D, K_max):
    """
    No se conoce K. Se exige que DOS puntos del mismo cluster esten a distancia
    <= D, y se minimiza el numero de clusters usados.  (Es un coloreo de grafos.)

      X[i,k] = 1 si el punto i va al cluster k ;  U[k] = 1 si el cluster k se usa
      min  sum_k U[k]
      s.a. sum_k X[i,k] == 1                  para todo i
           X[i,k] <= U[k]                     para todo i,k
           X[i,k] + X[j,k] <= 1               para todo k y pares i<j con dist[i][j] > D
           X[i,k] == 0  si k > i              (ruptura de simetria, opcional)

    K_max = cota superior de clusters posibles.
    """
    n = len(dist)
    V = range(n)
    Kset = range(K_max)
    md = gp.Model("min_clusters")
    md.setParam(GRB.Param.OutputFlag, 0)
    X = md.addVars(n, K_max, vtype=GRB.BINARY, name="X")
    U = md.addVars(K_max, vtype=GRB.BINARY, name="U")
    md.setObjective(gp.quicksum(U[k] for k in Kset), GRB.MINIMIZE)
    md.addConstrs((gp.quicksum(X[i, k] for k in Kset) == 1 for i in V), name="un_cluster")
    md.addConstrs((X[i, k] <= U[k] for i in V for k in Kset), name="uso")
    md.addConstrs((X[i, k] + X[j, k] <= 1
                   for i in V for j in V if i < j and dist[i][j] > D for k in Kset),
                  name="incompatibles")
    md.addConstrs((X[i, k] == 0 for i in V for k in Kset if k > i), name="simetria")
    return md, X, U


def ej_min_clusters_diametro(D=3.5, K_max=6):
    """5.6 CLUSTERING: minimo de clusters con diametro maximo D."""
    pts = generar_puntos(n_por_grupo=(5, 5, 5))
    dist = matriz_distancias(pts)
    md, X, U = modelo_min_clusters_diametro(dist, D, K_max)
    md.optimize()
    if md.status != GRB.OPTIMAL:
        print("status =", md.status, "-> subir K_max o D")
        return md
    print(f"[min clusters] D={D}: se necesitan {md.ObjVal:.0f} clusters")
    for k in range(K_max):
        miembros = [i for i in range(len(pts)) if X[i, k].X > 0.5]
        if miembros:
            diam = max((dist[i][j] for i in miembros for j in miembros), default=0)
            print(f"  cluster {k}: {miembros} | diametro real = {diam:.2f}")
    return md


# ---------------------------- 5.7 ASIGNAR A CENTROIDES DADOS -----------------
def ej_asignar_a_centroides():
    """5.7 CLUSTERING con centros dados: asignacion con capacidad (LP puro)."""
    # Si los centros YA estan dados (por ejemplo, centroides de un k-means),
    # ya no hay variable Y: es un problema de asignacion/transporte.
    #   min  sum_{i,k} dist(p_i, c_k) * X[i,k]
    #   s.a. sum_k X[i,k] == 1 ;  sum_i q[i] X[i,k] <= Q ;  X >= 0
    pts = generar_puntos()
    centroides = [(2, 2), (8, 3), (5, 9)]
    n, K = len(pts), len(centroides)
    V, Kset = range(n), range(K)
    q = [1] * n
    Q = 9
    dist = [[distancia(p, c) for c in centroides] for p in pts]   # dist[i][k]

    md = gp.Model("asignar_centroides")
    md.setParam(GRB.Param.OutputFlag, 0)
    X = md.addVars(n, K, lb=0, ub=1, name="X")             # continua: sale entera
    md.setObjective(gp.quicksum(dist[i][k] * X[i, k] for i in V for k in Kset), GRB.MINIMIZE)
    md.addConstrs((gp.quicksum(X[i, k] for k in Kset) == 1 for i in V), name="un_cluster")
    md.addConstrs((gp.quicksum(q[i] * X[i, k] for i in V) <= Q for k in Kset), name="cap")
    md.optimize()
    print(f"[asignacion a centroides] obj={md.ObjVal:.2f}")
    for k in Kset:
        print(f"  centroide {centroides[k]}: {sum(1 for i in V if X[i, k].X > 0.5)} puntos")
    return md


# ---------------------------- 5.8 BARRIDO DE K (METODO DEL CODO) -------------
def ej_barrido_k(K_max=7):
    """5.8 Como elegir K: resolver la p-mediana para K = 1..K_max y mirar el codo."""
    pts = generar_puntos()
    dist = matriz_distancias(pts)
    print("  K   objetivo   mejora")
    anterior = None
    for K in range(1, K_max + 1):
        md, X, Y = modelo_p_mediana(dist, K)
        md.optimize()
        mejora = "" if anterior is None else f"{anterior - md.ObjVal:8.2f}"
        print(f"  {K}  {md.ObjVal:9.2f}  {mejora}")
        anterior = md.ObjVal
    print("  (el 'codo' es donde la mejora deja de ser grande; aqui deberia ser K = 3)")


# ---------------------------- 5.9 K-MEANS NO ES UN MIP -----------------------
def nota_kmeans():
    """
    k-means usa CENTROIDES = promedios (continuos, no son puntos del conjunto):
        min  sum_i sum_k X[i,k] * ||p_i - c_k||^2     con c_k variable.
    El producto X[i,k]*c_k (binaria * continua) al cuadrado es NO CONVEXO:
    no es un LP ni un MIP. Opciones aceptables en un examen:

      1) Usar p-mediana/k-medoids (5.2): el centro es uno de los puntos.
      2) Fijar los centroides y asignar (5.7), iterar a mano (algoritmo de Lloyd):
             repetir: asignar (LP) -> recalcular centroides (promedio) -> hasta converger.
      3) Si hay que dejar los centroides como variable, Gurobi acepta modelos
         no convexos con  md.setParam(GRB.Param.NonConvex, 2)  (lento, solo instancias chicas).
      4) Con distancia Manhattan, el centroide optimo es la MEDIANA por
         coordenada, y la distancia |p - c| se linealiza con la tecnica (a)
         de la PARTE 3.
    """
    print(nota_kmeans.__doc__)


# =============================================================================
# PARTE 6. CHECKLIST DE ERRORES COMUNES Y CONSEJOS
# =============================================================================
CHECKLIST = """
ERRORES FRECUENTES
  [ ] lb por defecto = 0: si la variable puede ser negativa, lb=-GRB.INFINITY.
  [ ] Comparar binarias con == 1 -> usar  v.X > 0.5  (hay tolerancia numerica).
  [ ] Leer .X antes de optimizar o con status != OPTIMAL -> AttributeError.
  [ ] Usar `=` en vez de `==` / `<=` / `>=` dentro de addConstr.
  [ ] Usar sum() de Python con muchos terminos: preferir gp.quicksum().
  [ ] No dar nombre (name=...) a variables/restricciones: dificulta leer el .lp.
  [ ] Big-M muy grande o con valor equivocado: modelo debil o respuestas falsas.
  [ ] Sensibilidad (Pi, RC, SARHSLow...) en un modelo con enteras: no existe.
  [ ] Olvidar la restriccion de enlace x <= M*y o x[i,j] <= y[j].
  [ ] Maximizar vs minimizar al reves. Revisar GRB.MAXIMIZE / GRB.MINIMIZE.
  [ ] Restricciones con desigualdad estricta (< o >): no existen; usar +-epsilon.
  [ ] Indices que empiezan en 0 en Python vs. en 1 en el enunciado.

CONSEJOS PARA EL EXAMEN
  * Escribir primero conjuntos, parametros, variables, objetivo, restricciones
    (como comentarios) y luego codificar.
  * Hacer md.write("modelo.lp") y leerlo: ahi se ve el modelo tal cual lo entiende Gurobi.
  * Probar primero con datos chicos; verificar la solucion a mano.
  * Si pide interpretar: precio sombra (Pi), holgura (Slack), costo reducido (RC).
  * Si el modelo tarda: md.setParam(GRB.Param.TimeLimit, 60) y GRB.Param.MIPGap.
  * md.setParam(GRB.Param.OutputFlag, 0) para ocultar el log; 1 para ver nodos, gap, cotas.
  * Status utiles: 2 OPTIMAL, 3 INFEASIBLE, 5 UNBOUNDED, 9 TIME_LIMIT.
"""


def checklist():
    """Errores comunes y consejos para el examen."""
    print(CHECKLIST)


# =============================================================================
# MENU / EJECUCION
# =============================================================================
EJEMPLOS = {
    "plantilla": plantilla,
    "cheatsheet": cheatsheet_api,
    "produccion": ej_produccion,
    "dieta": ej_dieta,
    "transporte": ej_transporte,
    "asignacion": ej_asignacion,
    "mochila": ej_mochila,
    "localizacion": ej_localizacion,
    "multiperiodo": ej_multiperiodo,
    "ruta_corta": ej_ruta_corta,
    "cobertura": ej_cobertura,
    "linealizaciones": ej_linealizaciones,
    "infactible": ej_infactible,
    "p_mediana": ej_p_mediana,
    "p_mediana_cap": ej_p_mediana_capacitada,
    "p_centro": ej_p_centro,
    "pares": ej_pares,
    "min_clusters": ej_min_clusters_diametro,
    "asignar_centroides": ej_asignar_a_centroides,
    "barrido_k": ej_barrido_k,
    "kmeans": nota_kmeans,
    "checklist": checklist,
}


def main(argv):
    if len(argv) < 2:
        print(__doc__.split("INDICE")[0])
        print("Ejemplos disponibles:")
        for nombre, f in EJEMPLOS.items():
            resumen = (f.__doc__ or "").strip().splitlines()[0] if f.__doc__ else ""
            print(f"  {nombre:<20} {resumen}")
        return
    pedidos = list(EJEMPLOS) if argv[1] == "todo" else argv[1:]
    for nombre in pedidos:
        if nombre not in EJEMPLOS:
            print(f"Ejemplo desconocido: {nombre}")
            continue
        print("\n" + "=" * 70 + f"\n {nombre}\n" + "=" * 70)
        EJEMPLOS[nombre]()


if __name__ == "__main__":
    main(sys.argv)
