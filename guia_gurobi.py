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
Instalacion:  pip install gurobipy
(La licencia gratuita de pip limita el tamano: 2000 variables y 2000
restricciones lineales. Suficiente para los ejemplos de esta guia.)

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
           5.1 datos y distancias
           5.2 p-mediana (k-medoids)           <- el mas importante
           5.3 p-mediana con capacidades / clusters balanceados
           5.4 p-centro (minimizar el radio maximo)
           5.5 minimo numero de clusters con diametro maximo
           5.6 asignar puntos a centroides dados
           5.7 que NO es un MIP: k-means
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
    m = gp.Model("plantilla")
    # --- 3. Variables --------------------------------------------------------
    # OJO: por defecto lb=0 y ub=infinito. Para variables libres usar lb=-GRB.INFINITY
    x = m.addVar(vtype=GRB.CONTINUOUS, lb=0, name="x")
    y = m.addVar(vtype=GRB.CONTINUOUS, lb=0, name="y")
    # --- 4. Objetivo ---------------------------------------------------------
    m.setObjective(utilidad["x"] * x + utilidad["y"] * y, GRB.MAXIMIZE)
    # --- 5. Restricciones ----------------------------------------------------
    m.addConstr(x + y <= 4, name="r1")
    m.addConstr(x + 3 * y <= 6, name="r2")
    # --- 6. Resolver ---------------------------------------------------------
    m.optimize()
    if m.status == GRB.OPTIMAL:
        print(f"Objetivo = {m.ObjVal:.2f}")
        for v in m.getVars():
            print(f"  {v.VarName} = {v.X:.2f}")
    return m


# =============================================================================
# PARTE 1. CHEATSHEET DE LA API
# =============================================================================
def cheatsheet_api():
    """Recorrido por todo lo que se usa con frecuencia. Ejecutarlo y leerlo."""
    m = gp.Model("cheatsheet")

    # ---------------- Parametros utiles del solver ---------------------------
    m.Params.OutputFlag = 0      # 0 = silencia el log (1 = lo muestra)
    # m.Params.TimeLimit = 60    # segundos maximos
    # m.Params.MIPGap = 0.01     # detener con gap relativo del 1 %
    # m.Params.Threads = 1

    # ---------------- Variables ---------------------------------------------
    a = m.addVar(lb=0, ub=10, obj=0, vtype=GRB.CONTINUOUS, name="a")
    b = m.addVar(vtype=GRB.INTEGER, name="b")          # entera >= 0
    c = m.addVar(vtype=GRB.BINARY, name="c")           # 0 / 1
    libre = m.addVar(lb=-GRB.INFINITY, name="libre")   # puede ser negativa

    # Varias a la vez: devuelve un tupledict indexado
    I = ["p1", "p2", "p3"]
    J = ["t1", "t2"]
    x = m.addVars(I, vtype=GRB.CONTINUOUS, name="x")          # x["p1"]
    z = m.addVars(I, J, vtype=GRB.BINARY, name="z")           # z["p1","t2"]
    # indices numericos: m.addVars(5, 3) -> z[i, j] con i en 0..4, j en 0..2
    # Indices irregulares (solo pares validos):
    arcos = gp.tuplelist([("A", "B"), ("B", "C"), ("A", "C")])
    f = m.addVars(arcos, name="f")

    # ---------------- Sumas --------------------------------------------------
    costo = {"p1": 4, "p2": 5, "p3": 6}
    expr1 = gp.quicksum(costo[i] * x[i] for i in I)    # suma generica (la mas usada)
    expr2 = x.sum()                                    # suma de todas
    expr3 = x.prod(costo)                              # sum costo[i]*x[i]
    expr4 = z.sum("p1", "*")                           # suma sobre j fijando i = p1
    expr5 = z.sum("*", "t2")                           # suma sobre i fijando j = t2
    # f.sum("A", "*") = flujo que sale de A ; f.sum("*", "C") = flujo que entra a C

    # ---------------- Restricciones -----------------------------------------
    m.addConstr(a + b <= 10, name="una_restriccion")
    m.addConstr(expr1 >= 5, name="demanda")
    m.addConstr(x["p1"] == 2 * x["p2"])                # igualdad: usar ==
    m.addConstrs((z.sum(i, "*") <= 1 for i in I), name="max_uno_por_i")   # familia
    m.addConstrs((x[i] <= 8 * c for i in I), name="enlace")               # big-M
    m.addConstr(libre >= -3)
    # Cotas rapidas despues de crear: x[i].UB = 5 ; x[i].LB = 1
    # Fijar variable: x["p1"].LB = x["p1"].UB = 3

    # ---------------- Objetivo ----------------------------------------------
    m.setObjective(expr1 + a + 2 * b, GRB.MINIMIZE)    # o GRB.MAXIMIZE
    # m.ModelSense = GRB.MAXIMIZE  (alternativa)

    # ---------------- Resolver y leer resultados ----------------------------
    m.optimize()
    print("status:", m.status, "(2=OPTIMAL, 3=INFEASIBLE, 4=INF_OR_UNBD, "
          "5=UNBOUNDED, 9=TIME_LIMIT)")
    if m.status == GRB.OPTIMAL:
        print("ObjVal  :", m.ObjVal)
        print("a.X     :", a.X)
        print("x       :", m.getAttr("X", x))              # dict {indice: valor}
        print("NumVars :", m.NumVars, " NumConstrs:", m.NumConstrs)
        print("Binarias:", m.NumBinVars, " Enteras (incluye binarias):", m.NumIntVars)
        # Para MIP: m.MIPGap, m.ObjBound, m.SolCount, m.Runtime
        # Recorrer solo lo que vale algo:
        activos = [k for k, v in z.items() if v.X > 0.5]    # binarias: comparar con 0.5
        print("z activas:", activos)

    # ---------------- Guardar / depurar el modelo ---------------------------
    # m.write("modelo.lp")   # formato legible: revisar que lo escrito = lo pensado
    # m.write("modelo.sol")  # solucion
    # m.update()             # (opcional) refresca el modelo antes de leer atributos
    return m


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

    m = gp.Model("produccion")
    m.Params.OutputFlag = 0
    x = m.addVars(productos, lb=0, name="x")
    m.setObjective(gp.quicksum(util[i] * x[i] for i in productos), GRB.MAXIMIZE)
    rest = m.addConstrs(
        (gp.quicksum(uso[r, i] * x[i] for i in productos) <= disp[r] for r in recursos),
        name="recurso",
    )
    m.optimize()

    print(f"Utilidad maxima = {m.ObjVal:.2f}")
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
    return m


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
    m = gp.Model("dieta")
    m.Params.OutputFlag = 0
    x = m.addVars(alimentos, lb=0, ub=10, name="porciones")   # ub = cota por variable
    m.setObjective(x.prod(precio), GRB.MINIMIZE)
    m.addConstrs(
        (gp.quicksum(aporte[n, a] * x[a] for a in alimentos) >= minimo[n] for n in nutrientes),
        name="nutriente",
    )
    m.optimize()
    print(f"Costo minimo = {m.ObjVal:.2f}")
    for a in alimentos:
        print(f"  {a:<6}: {x[a].X:.2f} porciones")
    return m


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

    m = gp.Model("transporte")
    m.Params.OutputFlag = 0
    x = m.addVars(plantas, clientes, lb=0, name="x")
    m.setObjective(gp.quicksum(costo[i, j] * x[i, j] for i in plantas for j in clientes),
                   GRB.MINIMIZE)
    m.addConstrs((x.sum(i, "*") <= oferta[i] for i in plantas), name="oferta")
    m.addConstrs((x.sum("*", j) >= demanda[j] for j in clientes), name="demanda")
    m.optimize()
    print(f"Costo minimo = {m.ObjVal:.2f}")
    for (i, j), v in x.items():
        if v.X > 1e-6:
            print(f"  {i} -> {j}: {v.X:.0f}")
    return m


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
    m = gp.Model("asignacion")
    m.Params.OutputFlag = 0
    x = m.addVars(trabajadores, tareas, vtype=GRB.BINARY, name="x")
    m.setObjective(gp.quicksum(c[i][j] * x[i, j] for i in trabajadores for j in tareas),
                   GRB.MINIMIZE)
    m.addConstrs((x.sum(i, "*") == 1 for i in trabajadores), name="trab")
    m.addConstrs((x.sum("*", j) == 1 for j in tareas), name="tarea")
    m.optimize()
    print(f"Costo minimo = {m.ObjVal:.2f}")
    for (i, j), v in x.items():
        if v.X > 0.5:
            print(f"  {i} -> {j} (costo {c[i][j]})")
    return m


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
    m = gp.Model("mochila")
    m.Params.OutputFlag = 0
    x = m.addVars(items, vtype=GRB.BINARY, name="x")
    m.setObjective(gp.quicksum(valor[i] * x[i] for i in items), GRB.MAXIMIZE)
    m.addConstr(gp.quicksum(peso[i] * x[i] for i in items) <= W, name="capacidad")
    m.optimize()
    elegidos = [i for i in items if x[i].X > 0.5]
    print(f"Valor = {m.ObjVal:.0f}; items {elegidos}; peso = {sum(peso[i] for i in elegidos)}/{W}")
    return m


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

    m = gp.Model("localizacion")
    m.Params.OutputFlag = 0
    y = m.addVars(sitios, vtype=GRB.BINARY, name="y")
    x = m.addVars(clientes, sitios, lb=0, name="x")
    m.setObjective(
        gp.quicksum(fijo[j] * y[j] for j in sitios)
        + gp.quicksum(c[i, j] * x[i, j] for i in clientes for j in sitios),
        GRB.MINIMIZE,
    )
    m.addConstrs((x.sum(i, "*") == demanda[i] for i in clientes), name="demanda")
    m.addConstrs((x.sum("*", j) <= cap[j] * y[j] for j in sitios), name="capacidad")
    m.optimize()
    print(f"Costo total = {m.ObjVal:.2f}")
    print("  Abiertos:", [j for j in sitios if y[j].X > 0.5])
    for (i, j), v in x.items():
        if v.X > 1e-6:
            print(f"  {i} <- {j}: {v.X:.0f}")
    return m


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

    m = gp.Model("multiperiodo")
    m.Params.OutputFlag = 0
    prod = m.addVars(T, ub=cap_prod, name="prod")
    inv = m.addVars(T, lb=0, name="inv")
    m.setObjective(gp.quicksum(c_prod[t] * prod[t] + c_inv * inv[t] for t in T), GRB.MINIMIZE)
    for t in T:
        anterior = inv0 if t == 0 else inv[t - 1]       # <- patron para t = 0
        m.addConstr(anterior + prod[t] - demanda[t] == inv[t], name=f"balance_{t}")
    m.optimize()
    print(f"Costo = {m.ObjVal:.2f}")
    print("  t  demanda  prod  inv")
    for t in T:
        print(f"  {t}  {demanda[t]:7d}  {prod[t].X:4.0f}  {inv[t].X:4.0f}")
    return m


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

    m = gp.Model("ruta_corta")
    m.Params.OutputFlag = 0
    x = m.addVars(arcos, vtype=GRB.BINARY, name="x")
    m.setObjective(x.prod(costo), GRB.MINIMIZE)
    for n in nodos:
        b = 1 if n == origen else (-1 if n == destino else 0)
        m.addConstr(x.sum(n, "*") - x.sum("*", n) == b, name=f"flujo_{n}")
    m.optimize()
    print(f"Distancia = {m.ObjVal:.0f}; arcos:", [a for a in arcos if x[a].X > 0.5])
    return m


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
    m = gp.Model("cobertura")
    m.Params.OutputFlag = 0
    y = m.addVars(cubre.keys(), vtype=GRB.BINARY, name="y")
    m.setObjective(y.sum(), GRB.MINIMIZE)
    m.addConstrs((gp.quicksum(y[j] for j in cubre if i in cubre[j]) >= 1 for i in zonas),
                 name="cubrir")
    m.optimize()
    print(f"Estaciones = {m.ObjVal:.0f}:", [j for j in cubre if y[j].X > 0.5])
    return m


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
    m = gp.Model("abs")
    m.Params.OutputFlag = 0
    x = m.addVar(lb=-GRB.INFINITY, name="x")
    y = m.addVar(lb=-GRB.INFINITY, name="y")
    t1 = m.addVar(name="t1")
    t2 = m.addVar(name="t2")
    m.addConstr(x + y == 10)
    m.addConstr(t1 >= x - 5)
    m.addConstr(t1 >= -(x - 5))
    m.addConstr(t2 >= y + 2)
    m.addConstr(t2 >= -(y + 2))
    m.setObjective(t1 + t2, GRB.MINIMIZE)
    m.optimize()
    print(f"(a) abs      : obj={m.ObjVal:.2f}, x={x.X:.2f}, y={y.X:.2f}")

    # ---- (b) minimax: repartir 100 unidades en 3 destinos minimizando la mayor carga ponderada
    m = gp.Model("minimax")
    m.Params.OutputFlag = 0
    w = {0: 1.0, 1: 2.0, 2: 4.0}
    q = m.addVars(w.keys(), lb=0, name="q")
    z = m.addVar(name="z")
    m.addConstr(q.sum() == 100)
    m.addConstrs((z >= w[k] * q[k] for k in w), name="max")
    m.setObjective(z, GRB.MINIMIZE)
    m.optimize()
    print(f"(b) minimax  : z={z.X:.2f}, q={[round(q[k].X, 2) for k in w]}")

    # ---- (c) costo fijo: x <= M*y ------------------------------------------
    m = gp.Model("fijo")
    m.Params.OutputFlag = 0
    x = m.addVar(ub=50, name="x")
    y = m.addVar(vtype=GRB.BINARY, name="y")
    m.addConstr(x <= 50 * y)
    m.addConstr(x >= 10)
    m.setObjective(100 * y + 2 * x, GRB.MINIMIZE)
    m.optimize()
    print(f"(c) fijo     : obj={m.ObjVal:.2f}, y={y.X:.0f}, x={x.X:.0f}")

    # ---- (d)/(e) implicaciones con big-M vs. restriccion INDICADORA ----------
    m = gp.Model("logica")
    m.Params.OutputFlag = 0
    x = m.addVar(ub=100, name="x")
    w = m.addVar(vtype=GRB.BINARY, name="w")
    M = 100
    # "Si w == 1 entonces x <= 20"  (big-M)
    m.addConstr(x <= 20 + M * (1 - w))
    # Equivalente con indicadora (sin necesidad de M):
    #   m.addGenConstrIndicator(w, True, x, GRB.LESS_EQUAL, 20)
    #   m.addConstr((w == 1) >> (x <= 20))            # sintaxis corta
    # "Si w == 0 entonces x >= 60"
    m.addConstr(x >= 60 - 60 * w)
    m.setObjective(x - 30 * w, GRB.MAXIMIZE)
    m.optimize()
    print(f"(d) logica   : obj={m.ObjVal:.2f}, w={round(w.X)}, x={x.X:.0f}")

    # ---- (g) producto binaria*continua -------------------------------------
    m = gp.Model("producto")
    m.Params.OutputFlag = 0
    U = 10
    x = m.addVar(ub=U, name="x")
    y = m.addVar(vtype=GRB.BINARY, name="y")
    p = m.addVar(name="p")                       # p = x*y
    m.addConstr(p <= U * y)
    m.addConstr(p <= x)
    m.addConstr(p >= x - U * (1 - y))
    m.addConstr(x == 7)
    m.addConstr(y == 1)
    m.setObjective(p, GRB.MAXIMIZE)
    m.optimize()
    print(f"(g) producto : p={p.X:.1f} (esperado 7)")

    # ---- (h) restricciones generales ---------------------------------------
    m = gp.Model("general")
    m.Params.OutputFlag = 0
    x = m.addVar(lb=-10, ub=10, name="x")
    absx = m.addVar(name="absx")
    m.addGenConstrAbs(absx, x, name="abs")       # absx = |x|
    m.addConstr(x <= -3)
    m.setObjective(absx, GRB.MINIMIZE)
    m.optimize()
    print(f"(h) GenConstr: |x|={absx.X:.1f}, x={x.X:.1f}")

    # ---- Multiobjetivo (jerarquico): primero el de mayor prioridad ----------
    m = gp.Model("multiobj")
    m.Params.OutputFlag = 0
    x = m.addVar(ub=10, name="x")
    y = m.addVar(ub=10, name="y")
    m.addConstr(x + y <= 12)
    m.ModelSense = GRB.MAXIMIZE
    m.setObjectiveN(x, index=0, priority=2, name="primero_x")
    m.setObjectiveN(y, index=1, priority=1, name="luego_y")
    m.optimize()
    print(f"(i) multiobj : x={x.X:.1f}, y={y.X:.1f}")
    return m


# =============================================================================
# PARTE 4. DIAGNOSTICO: INFACTIBLE / NO ACOTADO
# =============================================================================
def ej_infactible():
    """
    status 3 (INFEASIBLE): restricciones contradictorias.
    status 5 (UNBOUNDED) : el objetivo mejora sin limite (falta una restriccion/cota).
    status 4 (INF_OR_UNBD): Gurobi no sabe cual; poner m.Params.DualReductions = 0
                            y reoptimizar para distinguir.
    Herramienta clave: IIS = subconjunto minimo de restricciones en conflicto.
    """
    m = gp.Model("infactible")
    m.Params.OutputFlag = 0
    m.Params.DualReductions = 0     # evita el status ambiguo 4 (INF_OR_UNBD)
    x = m.addVar(name="x")
    y = m.addVar(name="y")
    m.addConstr(x + y <= 4, name="a")
    m.addConstr(x + y >= 6, name="b")       # contradice a
    m.addConstr(x <= 10, name="c")          # irrelevante
    m.setObjective(x + y, GRB.MAXIMIZE)
    m.optimize()

    if m.status == GRB.INFEASIBLE:
        print("Modelo INFACTIBLE. Calculando IIS...")
        m.computeIIS()
        for c in m.getConstrs():
            if c.IISConstr:
                print("  en conflicto:", c.ConstrName)
        # m.write("conflicto.ilp")
        # Alternativa: m.feasRelax(...) para ver cuanto habria que relajar.
    elif m.status in (GRB.UNBOUNDED, GRB.INF_OR_UNBD):
        print("No acotado: revisar signos del objetivo y cotas faltantes")
    return m


# =============================================================================
# PARTE 5. CLUSTERING CON OPTIMIZACION
# =============================================================================
"""
IDEA GENERAL
------------
Clustering = repartir n puntos en k grupos para que los puntos de un mismo
grupo esten "cerca". Con programacion lineal entera se modela de forma EXACTA
cuando cada grupo se representa por un punto REAL del conjunto (la "mediana"
o "medoide"), no por un promedio (centroide). Ese es el modelo p-MEDIANA.

Patron de variables (aprenderlo de memoria):
    y[j]   binaria = 1 si el punto j es elegido como CENTRO de un cluster
    x[i,j] binaria = 1 si el punto i se asigna al centro j

Restricciones del modelo base:
    (1) sum_j x[i,j] == 1        cada punto va a exactamente un centro
    (2) x[i,j] <= y[j]           solo se asigna a puntos que son centros
    (3) sum_j y[j] == k          hay exactamente k clusters

Variantes segun lo que pida el enunciado:
    - Minimizar suma de distancias           -> p-MEDIANA        (5.2)
    - Clusters de tamano limitado/balanceado -> capacidades      (5.3)
    - Minimizar la distancia MAXIMA          -> p-CENTRO (minimax) (5.4)
    - No fijar k, fijar distancia maxima     -> min #clusters    (5.5)
    - Centros ya conocidos                   -> asignacion       (5.6)
"""


# ---------------------------- 5.1 DATOS Y DISTANCIAS -------------------------
def generar_puntos(n_por_grupo=(8, 8, 8), centros=((2, 2), (8, 3), (5, 9)),
                   dispersion=1.0, seed=7):
    """Genera puntos 2D alrededor de `centros` (para practicar)."""
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
    n = len(pts)
    return [[distancia(pts[i], pts[j], tipo) for j in range(n)] for i in range(n)]
    # Con numpy:  from scipy.spatial.distance import cdist ; cdist(P, P)
    # Si el examen da una matriz o un CSV, leerla con pandas / csv y usarla igual.


def imprimir_clusters(pts, d, centros, asign):
    """asign: dict {i: j}. Muestra los clusters y su costo."""
    total = 0.0
    for j in centros:
        miembros = [i for i, c in asign.items() if c == j]
        costo = sum(d[i][j] for i in miembros)
        total += costo
        print(f"  Cluster con centro {j}: {len(miembros)} puntos "
              f"{sorted(miembros)} | suma dist = {costo:.2f}")
    print(f"  Suma total de distancias = {total:.2f}")


def _extraer(x, y, n):
    centros = [j for j in range(n) if y[j].X > 0.5]
    asign = {i: j for i in range(n) for j in range(n) if x[i, j].X > 0.5}
    return centros, asign


# ---------------------------- 5.2 p-MEDIANA ----------------------------------
def modelo_p_mediana(d, k, cap=None, tam_min=None, nombre="p_mediana"):
    """
    p-MEDIANA / k-MEDOIDS (con capacidades opcionales).

      min  sum_{i,j} d[i,j] * x[i,j]
      s.a. sum_j x[i,j] == 1              para todo i      (cada punto, un centro)
           x[i,j] <= y[j]                 para todo i,j    (asignar solo a centros)
           sum_j y[j] == k                                 (exactamente k centros)
           sum_i x[i,j] <= cap * y[j]     para todo j      (opcional: tamano maximo)
           sum_i x[i,j] >= tam_min * y[j] para todo j      (opcional: tamano minimo)
           x[i,j], y[j] in {0,1}

    Nota: x[j,j] = 1 para un centro j (se asigna a si mismo, distancia 0).
    Sin capacidades, x puede declararse continua (lb=0, ub=1) y la solucion
    sale entera igual (mas rapido). Con capacidades, dejar x BINARIA.
    """
    n = len(d)
    m = gp.Model(nombre)
    m.Params.OutputFlag = 0
    x = m.addVars(n, n, vtype=GRB.BINARY, name="x")
    y = m.addVars(n, vtype=GRB.BINARY, name="y")

    m.setObjective(gp.quicksum(d[i][j] * x[i, j] for i in range(n) for j in range(n)),
                   GRB.MINIMIZE)
    m.addConstrs((x.sum(i, "*") == 1 for i in range(n)), name="un_centro")
    m.addConstrs((x[i, j] <= y[j] for i in range(n) for j in range(n)), name="enlace")
    m.addConstr(y.sum() == k, name="k_centros")
    if cap is not None:
        m.addConstrs((x.sum("*", j) <= cap * y[j] for j in range(n)), name="cap_max")
    if tam_min is not None:
        m.addConstrs((x.sum("*", j) >= tam_min * y[j] for j in range(n)), name="cap_min")
    return m, x, y


def ej_p_mediana(k=3):
    """5.2 CLUSTERING p-mediana (k-medoids): minimiza la suma de distancias."""
    pts = generar_puntos()
    d = matriz_distancias(pts)
    m, x, y = modelo_p_mediana(d, k)
    m.optimize()
    print(f"[p-mediana] n={len(pts)}, k={k}, status={m.status}, obj={m.ObjVal:.2f}")
    centros, asign = _extraer(x, y, len(pts))
    imprimir_clusters(pts, d, centros, asign)
    return m


# ---------------------------- 5.3 CAPACIDADES / BALANCEO ---------------------
def ej_p_mediana_capacitada(k=3, cap=9, tam_min=7):
    """Clusters de entre `tam_min` y `cap` puntos (por ejemplo, grupos de trabajo)."""
    pts = generar_puntos(n_por_grupo=(12, 6, 6))      # grupos naturales desbalanceados
    d = matriz_distancias(pts)
    m, x, y = modelo_p_mediana(d, k, cap=cap, tam_min=tam_min, nombre="p_mediana_cap")
    m.optimize()
    if m.status != GRB.OPTIMAL:
        print("Sin solucion optima. status =", m.status, "(si es 3: k*cap < n o k*tam_min > n)")
        return m
    print(f"[p-mediana capacitada] n={len(pts)}, k={k}, cap={cap}, min={tam_min}, obj={m.ObjVal:.2f}")
    centros, asign = _extraer(x, y, len(pts))
    imprimir_clusters(pts, d, centros, asign)
    return m


# ---------------------------- 5.4 p-CENTRO (MINIMAX) -------------------------
def modelo_p_centro(d, k):
    """
    p-CENTRO: minimizar la distancia MAXIMA de un punto a su centro (radio).
    Se agrega la variable continua z y se aplica la tecnica MINIMAX:

      min  z
      s.a. sum_j x[i,j] == 1
           x[i,j] <= y[j]
           sum_j y[j] == k
           sum_j d[i,j]*x[i,j] <= z        para todo i     (z >= distancia de i a su centro)
    """
    n = len(d)
    m = gp.Model("p_centro")
    m.Params.OutputFlag = 0
    x = m.addVars(n, n, vtype=GRB.BINARY, name="x")
    y = m.addVars(n, vtype=GRB.BINARY, name="y")
    z = m.addVar(lb=0, name="radio")
    m.setObjective(z, GRB.MINIMIZE)
    m.addConstrs((x.sum(i, "*") == 1 for i in range(n)), name="un_centro")
    m.addConstrs((x[i, j] <= y[j] for i in range(n) for j in range(n)), name="enlace")
    m.addConstr(y.sum() == k, name="k_centros")
    m.addConstrs((gp.quicksum(d[i][j] * x[i, j] for j in range(n)) <= z for i in range(n)),
                 name="radio")
    return m, x, y, z


def ej_p_centro(k=3):
    """5.4 CLUSTERING p-centro: minimiza la distancia maxima punto-centro."""
    pts = generar_puntos()
    d = matriz_distancias(pts)
    m, x, y, z = modelo_p_centro(d, k)
    m.optimize()
    print(f"[p-centro] n={len(pts)}, k={k}, radio minimo = {z.X:.3f}")
    centros, asign = _extraer(x, y, len(pts))
    imprimir_clusters(pts, d, centros, asign)
    return m


# ---------------------------- 5.5 MIN #CLUSTERS CON DIAMETRO MAXIMO ----------
def modelo_min_clusters_diametro(d, D, K_max):
    """
    No se conoce k. Se exige que DOS puntos del mismo cluster esten a distancia
    <= D, y se minimiza el numero de clusters usados.  (Es un coloreo de grafos.)

      x[i,c] = 1 si el punto i va al cluster c ;  u[c] = 1 si el cluster c se usa
      min  sum_c u[c]
      s.a. sum_c x[i,c] == 1                  para todo i
           x[i,c] <= u[c]                     para todo i,c
           x[i,c] + x[j,c] <= 1               para todo c y pares i<j con d[i,j] > D
           x[i,c] == 0  si c > i              (ruptura de simetria, opcional)

    K_max = cota superior de clusters posibles (basta con un valor razonable).
    """
    n = len(d)
    C = range(K_max)
    m = gp.Model("min_clusters")
    m.Params.OutputFlag = 0
    x = m.addVars(n, K_max, vtype=GRB.BINARY, name="x")
    u = m.addVars(K_max, vtype=GRB.BINARY, name="u")
    m.setObjective(u.sum(), GRB.MINIMIZE)
    m.addConstrs((x.sum(i, "*") == 1 for i in range(n)), name="un_cluster")
    m.addConstrs((x[i, c] <= u[c] for i in range(n) for c in C), name="uso")
    for i in range(n):
        for j in range(i + 1, n):
            if d[i][j] > D:                                 # incompatibles
                for c in C:
                    m.addConstr(x[i, c] + x[j, c] <= 1)
    # Ruptura de simetria: el punto i solo puede estar en clusters con indice <= i
    for i in range(n):
        for c in C:
            if c > i:
                x[i, c].UB = 0
    return m, x, u


def ej_min_clusters_diametro(D=3.5, K_max=6):
    """5.5 CLUSTERING: minimo de clusters con diametro maximo D."""
    pts = generar_puntos(n_por_grupo=(5, 5, 5))
    d = matriz_distancias(pts)
    m, x, u = modelo_min_clusters_diametro(d, D, K_max)
    m.optimize()
    if m.status != GRB.OPTIMAL:
        print("status =", m.status, "-> subir K_max o D")
        return m
    print(f"[min clusters] D={D}: se necesitan {m.ObjVal:.0f} clusters")
    for c in range(K_max):
        miembros = [i for i in range(len(pts)) if x[i, c].X > 0.5]
        if miembros:
            diam = max((d[i][j] for i in miembros for j in miembros), default=0)
            print(f"  cluster {c}: {miembros} | diametro real = {diam:.2f}")
    return m


# ---------------------------- 5.6 ASIGNAR A CENTROIDES DADOS -----------------
def ej_asignar_a_centroides():
    """
    Si los centros YA estan dados (por ejemplo, centroides de un k-means),
    ya no hay variable y: es un problema de asignacion/transporte (LP puro).
    Con capacidad por cluster para balancear:

      min  sum_{i,k} d(p_i, c_k) * x[i,k]
      s.a. sum_k x[i,k] == 1 ;  sum_i x[i,k] <= cap[k] ;  x >= 0
    """
    pts = generar_puntos()
    centroides = [(2, 2), (8, 3), (5, 9)]
    cap = [9, 9, 9]
    K = range(len(centroides))
    d = [[distancia(p, c) for c in centroides] for p in pts]

    m = gp.Model("asignar_centroides")
    m.Params.OutputFlag = 0
    x = m.addVars(len(pts), K, lb=0, ub=1, name="x")       # continua: sale entera
    m.setObjective(gp.quicksum(d[i][k] * x[i, k] for i in range(len(pts)) for k in K),
                   GRB.MINIMIZE)
    m.addConstrs((x.sum(i, "*") == 1 for i in range(len(pts))), name="un_cluster")
    m.addConstrs((x.sum("*", k) <= cap[k] for k in K), name="cap")
    m.optimize()
    print(f"[asignacion a centroides] obj={m.ObjVal:.2f}")
    for k in K:
        print(f"  centroide {centroides[k]}: {sum(1 for i in range(len(pts)) if x[i, k].X > 0.5)} puntos")
    return m


# ---------------------------- 5.7 K-MEANS NO ES UN MIP -----------------------
def nota_kmeans():
    """
    k-means usa CENTROIDES = promedios (continuos, no son puntos del conjunto):
        min  sum_i sum_k x[i,k] * ||p_i - c_k||^2     con c_k variable.
    El producto x[i,k]*c_k (binaria * continua) al cuadrado es NO CONVEXO:
    no es un LP ni un MIP. Opciones aceptables en un examen:

      1) Usar p-mediana/k-medoids (5.2): el centro es uno de los puntos.
      2) Fijar los centroides y asignar (5.6), iterar a mano (algoritmo de Lloyd):
             repetir: asignar (LP) -> recalcular centroides (promedio) -> hasta converger.
      3) Si hay que dejar los centroides como variable, Gurobi acepta modelos
         no convexos con  m.Params.NonConvex = 2  (lento, solo instancias chicas).
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
  * Hacer m.write("modelo.lp") y leerlo: ahi se ve el modelo tal cual lo entiende Gurobi.
  * Probar primero con datos chicos; verificar la solucion a mano.
  * Si pide interpretar: precio sombra (Pi), holgura (Slack), costo reducido (RC).
  * Si el modelo tarda: m.Params.TimeLimit y m.Params.MIPGap.
  * m.Params.OutputFlag = 0 para ocultar el log; 1 para ver nodos, gap, cotas.
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
    "min_clusters": ej_min_clusters_diametro,
    "asignar_centroides": ej_asignar_a_centroides,
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
