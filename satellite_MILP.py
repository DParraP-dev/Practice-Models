import os
import csv
import json
import math
import time
import platform
import gurobipy as gp
from gurobipy import GRB

"""
================================================================================
Localización de puntos satélite y programación semanal de atención en salud
================================================================================

PROBLEM DESCRIPTION:
- 50 nodos de demanda (I) se asignan, cada uno, a un único punto satélite
  elegido entre 10 candidatos (IP).
- 4 disciplinas (S) y una semana de 6 días (T).
- En cada punto abierto se decide qué disciplinas atienden cada día.
- Reglas R1-R5 del enunciado (demanda completa, capacidad semanal suficiente,
  número MÍNIMO de días por disciplina, al menos una disciplina cada día,
  solo se atiende en puntos abiertos).
- Objetivos: (i) puntos abiertos, (ii) distancia total (sin ponderar),
  (iii) equipos totales (máximo, por disciplina, de puntos que atienden
  esa disciplina el mismo día; sumado sobre disciplinas).

MATHEMATICAL FORMULATION:
- y[j]      : binaria, 1 si el candidato j se abre como punto satélite.
- x[i,j]    : binaria, 1 si el nodo de demanda i se asigna al punto j.
- z[j,s,t]  : binaria, 1 si la disciplina s atiende en j el día t.
- n[j,s]    : entera [0,6], número de días que s atiende en j.
- E[s]      : entera >= 0, número de equipos de la disciplina s.
- D[j,s]    : expresión, demanda semanal de s asignada a j = sum_i w[i,s] x[i,j].

  (R1)  sum_j x[i,j] = 1                              para todo i
  (R5a) x[i,j] <= y[j]                                para todo i, j
  (R5b) z[j,s,t] <= y[j]                              para todo j, s, t
  (DIAS) n[j,s] = sum_t z[j,s,t]                      para todo j, s
  (R2)  Q[j,s] n[j,s] >= D[j,s]                       para todo j, s
  (R3)  Q[j,s] (n[j,s] - 1) <= D[j,s] - 1             para todo j, s
        -> con w y Q enteros, R2 + R3 obligan n[j,s] = ceil(D[j,s] / Q[j,s]).
           Si D = 0 la restricción obliga n = 0 (no se programan días).
  (R4)  sum_s z[j,s,t] >= y[j]                        para todo j, t
  (EQ)  E[s] >= sum_j z[j,s,t]                        para todo s, t
        -> linealiza E[s] = max_t sum_j z[j,s,t] (al minimizar equipos, o con
           la restricción épsilon, E[s] toma el valor del máximo).
  (P)   sum_j y[j] = p   (variante "exacto")   ó   <= p   (variante "a lo sumo")
  (EPS) sum_s E[s] <= eps                     (método épsilon-restricción)

  Objetivo "dist" : min sum_{i,j} d[i,j] x[i,j]
  Objetivo "teams": min sum_s E[s]

  Refuerzos válidos (no cambian el conjunto de soluciones de interés):
  - x[i,j] = 0 si algún w[i,s] > 6 Q[j,s] (el nodo no cabe en j ni con 6 días).
  - Ruptura de simetría de días: los días son intercambiables, así que se
    ordenan por carga total: sum_{j,s} z[j,s,t] >= sum_{j,s} z[j,s,t+1].

SOLUTION APPROACH:
- MIP resuelto con Gurobi (TimeLimit >= 30 min, MIPGap = 0).
- Cribado rápido de p = 1..10 (factibilidad y distancia aproximada) y selección
  de 3 valores de p por instancia para la experimentación completa.
- Cada solución se verifica con una función independiente del solver.
- Resultados en resultados/resultados.csv y soluciones en resultados/soluciones.json.
"""

# ============================================================================
# CONFIGURACIÓN (editar aquí antes de ejecutar desde el IDE)
# ============================================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Instancias a resolver (rutas relativas a la carpeta de este script)
INSTANCES = ["instance_A.json", "instance_B.json"]

# Valores de p para la experimentación completa, por nombre de instancia.
# None -> selección automática a partir del cribado: menor p factible,
#         mayor p factible y un p intermedio.
# Ejemplo manual: P_VALUES = {"A": [2, 5, 8], "B": [3, 5, 7]}
P_VALUES = {"A": None, "B": None}
N_P_VALUES = 3

# Cribado: minimiza distancia con exactamente p puntos para p = 1..10 con un
# tiempo corto. Sirve para saber qué p son infactibles (pregunta 6a) y para
# elegir los 3 valores de p.
RUN_SCREENING = True
SCREEN_TIME_LIMIT = 60          # segundos por corrida de cribado

# Experimentos completos (actividad 4.3)
RUN_MIN_DISTANCE = True         # 4.3.1 (a)  exactamente p, min distancia
RUN_MIN_TEAMS = True            # 4.3.1 (b)  exactamente p, min equipos
RUN_EPSILON = True              # 4.3.1 (c)  épsilon-restricción
RUN_AT_MOST = True              # 4.3.4      a lo sumo p, min distancia

# Parámetros del solver
TIME_LIMIT = 1800               # segundos (30 min, mínimo exigido)
MIP_GAP = 0.0
THREADS = 0                     # 0 = Gurobi decide
OUTPUT_FLAG = 1                 # 1 = mostrar log de Gurobi en consola
SAVE_LOGS = True                # guarda el log de cada corrida en resultados/logs
SYMMETRY_BREAKING = True

# Reanudar: si una corrida ya está en el CSV (terminada con al menos el mismo
# TimeLimit, o resuelta a optimalidad / infactible), no se vuelve a correr.
RESUME = True

OUTPUT_DIR = os.path.join(BASE_DIR, "resultados")
RESULTS_CSV = os.path.join(OUTPUT_DIR, "resultados.csv")
SOLUTIONS_JSON = os.path.join(OUTPUT_DIR, "soluciones.json")
ENV_JSON = os.path.join(OUTPUT_DIR, "entorno.json")
LOG_DIR = os.path.join(OUTPUT_DIR, "logs")

TOL = 1e-6

# ============================================================================
# DATA LOADING
# ============================================================================


def load_instance(path):
    """Lee una instancia JSON y valida dimensiones e integralidad de w y Q."""
    if not os.path.isabs(path):
        path = os.path.join(BASE_DIR, path)
    with open(path, encoding="utf-8") as f:
        inst = json.load(f)

    nI, nJ = inst["n_demand"], inst["n_candidates"]
    nS, nT = len(inst["services"]), inst["n_days"]
    w, Q, d = inst["w"], inst["Q"], inst["d"]
    assert len(w) == nI and all(len(r) == nS for r in w), "w mal dimensionada"
    assert len(Q) == nJ and all(len(r) == nS for r in Q), "Q mal dimensionada"
    assert len(d) == nI and all(len(r) == nJ for r in d), "d mal dimensionada"

    # La linealización de R3 usa que w y Q son enteros
    for M, name in ((w, "w"), (Q, "Q")):
        for r in M:
            for v in r:
                if abs(v - round(v)) > TOL or v < 0:
                    raise ValueError(f"{name} debe ser entera y no negativa (valor {v})")
    inst["w"] = [[int(round(v)) for v in r] for r in w]
    inst["Q"] = [[int(round(v)) for v in r] for r in Q]
    inst["_path"] = path
    return inst


# ============================================================================
# MATHEMATICAL MODEL
# ============================================================================


def build_model(inst, p, objective="dist", mode="exact", eps=None):
    """
    Construye el MILP.
      p         : número de puntos satélite (exacto o máximo según mode)
      objective : "dist" (distancia total) o "teams" (equipos totales)
      mode      : "exact" (sum y = p) o "atmost" (sum y <= p)
      eps       : si no es None, agrega sum_s E[s] <= eps
    """
    w, Q, d = inst["w"], inst["Q"], inst["d"]
    I = range(inst["n_demand"])
    J = range(inst["n_candidates"])
    S = range(len(inst["services"]))
    T = range(inst["n_days"])
    nT = inst["n_days"]

    md = gp.Model(f"Satelite_{inst['name']}_{objective}_{mode}_p{p}")

    # ---------------- Variables ----------------
    # y[j] = 1 si el candidato j se abre
    y = md.addVars(J, vtype=GRB.BINARY, name="y")
    # x[i,j] = 1 si el nodo i se asigna al punto j
    x = md.addVars(I, J, vtype=GRB.BINARY, name="x")
    # z[j,s,t] = 1 si la disciplina s atiende en j el día t
    z = md.addVars(J, S, T, vtype=GRB.BINARY, name="z")
    # n[j,s] = número de días de la disciplina s en j
    n = md.addVars(J, S, vtype=GRB.INTEGER, lb=0, ub=nT, name="n")
    # E[s] = número de equipos de la disciplina s
    E = md.addVars(S, vtype=GRB.INTEGER, lb=0, ub=len(J), name="E")

    # Preprocesamiento: un nodo no puede ir a un candidato donde no cabe ni con 6 días
    for i in I:
        for j in J:
            if any(w[i][s] > nT * Q[j][s] for s in S):
                x[i, j].UB = 0

    # Demanda semanal asignada D[j,s] (expresión lineal)
    D = {(j, s): gp.quicksum(w[i][s] * x[i, j] for i in I) for j in J for s in S}

    # ---------------- Restricciones ----------------
    # (R1) Cada nodo se asigna a exactamente un punto (toda su demanda va allí)
    md.addConstrs((x.sum(i, "*") == 1 for i in I), name="R1_asignacion")

    # (R5a) Solo se asigna a puntos abiertos
    md.addConstrs((x[i, j] <= y[j] for i in I for j in J), name="R5_asig_abierto")

    # (R5b) Solo se programan disciplinas en puntos abiertos
    md.addConstrs((z[j, s, t] <= y[j] for j in J for s in S for t in T), name="R5_prog_abierto")

    # (DIAS) Número de días de cada disciplina en cada punto
    md.addConstrs((n[j, s] == z.sum(j, s, "*") for j in J for s in S), name="DIAS")

    for j in J:
        for s in S:
            if Q[j][s] == 0:
                # Sin capacidad: no se puede asignar demanda de s ni programar s
                md.addConstr(D[j, s] == 0, name=f"R2_sinQ[{j},{s}]")
                md.addConstr(n[j, s] == 0, name=f"R3_sinQ[{j},{s}]")
            else:
                # (R2) Capacidad semanal suficiente
                md.addConstr(Q[j][s] * n[j, s] >= D[j, s], name=f"R2_capacidad[{j},{s}]")
                # (R3) Días mínimos: Q (n-1) <= D - 1  <=>  n <= ceil(D/Q)
                md.addConstr(Q[j][s] * (n[j, s] - 1) <= D[j, s] - 1, name=f"R3_dias_min[{j},{s}]")

    # (R4) Un punto abierto atiende al menos una disciplina cada día
    md.addConstrs((z.sum(j, "*", t) >= y[j] for j in J for t in T), name="R4_dia_activo")

    # (EQ) Equipos de cada disciplina >= puntos donde atiende ese día
    md.addConstrs((E[s] >= z.sum("*", s, t) for s in S for t in T), name="EQ_equipos")

    # (P) Número de puntos satélite abiertos
    if mode == "exact":
        md.addConstr(y.sum() == p, name="P_exacto")
    elif mode == "atmost":
        md.addConstr(y.sum() <= p, name="P_alosumo")
    else:
        raise ValueError("mode debe ser 'exact' o 'atmost'")

    # (EPS) Restricción épsilon sobre equipos
    if eps is not None:
        md.addConstr(E.sum() <= eps, name="EPS_equipos")

    # Ruptura de simetría: días ordenados por carga total (los días son intercambiables)
    if SYMMETRY_BREAKING:
        md.addConstrs((z.sum("*", "*", t) >= z.sum("*", "*", t + 1) for t in range(nT - 1)),
                      name="SIM_dias")

    # ---------------- Objetivos ----------------
    obj_dist = gp.quicksum(d[i][j] * x[i, j] for i in I for j in J)
    obj_teams = E.sum()
    obj_open = y.sum()

    if objective == "dist":
        md.setObjective(obj_dist, GRB.MINIMIZE)
    elif objective == "teams":
        md.setObjective(obj_teams, GRB.MINIMIZE)
    else:
        raise ValueError("objective debe ser 'dist' o 'teams'")

    md.update()
    var = dict(y=y, x=x, z=z, n=n, E=E)
    exprs = dict(dist=obj_dist, teams=obj_teams, open=obj_open)
    return md, var, exprs


def set_start(inst, var, sol):
    """Carga una solución (formato de extract_solution) como MIP start."""
    I = range(inst["n_demand"])
    J = range(inst["n_candidates"])
    S = range(len(inst["services"]))
    T = range(inst["n_days"])
    open_set = set(sol["open"])
    for j in J:
        var["y"][j].Start = 1 if j in open_set else 0
        for s in S:
            days = set(sol["schedule"][j][s])
            var["n"][j, s].Start = len(days)
            for t in T:
                var["z"][j, s, t].Start = 1 if t in days else 0
    for i in I:
        for j in J:
            var["x"][i, j].Start = 1 if sol["assign"][i] == j else 0
    for s in S:
        var["E"][s].Start = max(sum(1 for j in J if t in sol["schedule"][j][s]) for t in T)


def extract_solution(inst, var):
    """Lee la solución incumbente del modelo a un diccionario plano (índices 0-based)."""
    I = range(inst["n_demand"])
    J = range(inst["n_candidates"])
    S = range(len(inst["services"]))
    T = range(inst["n_days"])
    y, x, z = var["y"], var["x"], var["z"]
    sol = {
        "open": [j for j in J if y[j].X > 0.5],
        "assign": [max(J, key=lambda j: x[i, j].X) for i in I],
        "schedule": [[[t for t in T if z[j, s, t].X > 0.5] for s in S] for j in J],
    }
    return sol


# ============================================================================
# INDEPENDENT VERIFICATION (no usa el solver)
# ============================================================================


def verify_solution(inst, sol, p=None, mode=None, eps=None):
    """
    Comprueba R1-R5 (y las restricciones de p y épsilon) y recalcula los tres
    objetivos a partir de los datos. Devuelve (ok, mensajes, métricas).
    """
    w, Q, d = inst["w"], inst["Q"], inst["d"]
    nI, nJ = inst["n_demand"], inst["n_candidates"]
    nS, nT = len(inst["services"]), inst["n_days"]
    sv = inst["services"]
    cid = [c["id"] for c in inst["candidates"]]
    msgs = []

    open_set = set(sol["open"])
    assign = sol["assign"]
    sched = sol["schedule"]

    # R1: cada nodo asignado a exactamente un candidato válido
    if len(assign) != nI:
        msgs.append(f"R1: hay {len(assign)} asignaciones para {nI} nodos")
    for i, j in enumerate(assign):
        if not (isinstance(j, int) and 0 <= j < nJ):
            msgs.append(f"R1: nodo {i} con asignación inválida {j}")

    # R5: asignaciones y programación solo en puntos abiertos
    for i, j in enumerate(assign):
        if j not in open_set:
            msgs.append(f"R5: nodo {inst['demand_nodes'][i]['id']} asignado a {cid[j]} cerrado")
    for j in range(nJ):
        if j not in open_set and any(sched[j][s] for s in range(nS)):
            msgs.append(f"R5: {cid[j]} está cerrado pero tiene días programados")

    # Demanda asignada D[j][s] (R1: toda la demanda del nodo va a su punto)
    Dm = [[0] * nS for _ in range(nJ)]
    for i, j in enumerate(assign):
        for s in range(nS):
            Dm[j][s] += w[i][s]

    days = [[0] * nS for _ in range(nJ)]
    for j in range(nJ):
        for s in range(nS):
            ds = sched[j][s]
            if len(set(ds)) != len(ds) or any(t < 0 or t >= nT for t in ds):
                msgs.append(f"Días inválidos en {cid[j]}-{sv[s]}: {ds}")
            days[j][s] = len(set(ds))
            # R2: capacidad semanal suficiente
            if Q[j][s] * days[j][s] < Dm[j][s]:
                msgs.append(f"R2: {cid[j]}-{sv[s]} capacidad {Q[j][s]}x{days[j][s]} < demanda {Dm[j][s]}")
            # R3: número mínimo de días
            if Q[j][s] > 0:
                need = math.ceil(Dm[j][s] / Q[j][s])
                if days[j][s] != need:
                    msgs.append(f"R3: {cid[j]}-{sv[s]} tiene {days[j][s]} días, mínimo {need}")
            elif days[j][s] != 0 or Dm[j][s] > 0:
                msgs.append(f"R2/R3: {cid[j]}-{sv[s]} sin capacidad con días o demanda")

    # R4: cada punto abierto atiende al menos una disciplina cada día
    for j in open_set:
        for t in range(nT):
            if not any(t in sched[j][s] for s in range(nS)):
                msgs.append(f"R4: {cid[j]} no atiende ninguna disciplina el día {t + 1}")

    # Objetivos recalculados
    n_open = len(open_set)
    dist = sum(d[i][j] for i, j in enumerate(assign))
    teams_by_s = [max(sum(1 for j in range(nJ) if t in sched[j][s]) for t in range(nT))
                  for s in range(nS)]
    teams = sum(teams_by_s)

    if p is not None:
        if mode == "exact" and n_open != p:
            msgs.append(f"P: {n_open} puntos abiertos, se exigían exactamente {p}")
        if mode == "atmost" and n_open > p:
            msgs.append(f"P: {n_open} puntos abiertos, se permitían a lo sumo {p}")
    if eps is not None and teams > eps:
        msgs.append(f"EPS: {teams} equipos > eps = {eps}")

    # Utilización de la capacidad semanal programada (demanda / (Q * días))
    util_by_s = []
    for s in range(nS):
        cap = sum(Q[j][s] * days[j][s] for j in open_set)
        dem = sum(Dm[j][s] for j in open_set)
        util_by_s.append(dem / cap if cap > 0 else None)

    metrics = dict(n_open=n_open, dist=dist, teams=teams, teams_by_s=teams_by_s,
                   days=days, D=Dm, util_by_s=util_by_s)
    return len(msgs) == 0, msgs, metrics


# ============================================================================
# RUN A SINGLE EXPERIMENT AND RECORD RESULTS
# ============================================================================

STATUS_NAMES = {
    GRB.OPTIMAL: "OPTIMAL", GRB.INFEASIBLE: "INFEASIBLE", GRB.INF_OR_UNBD: "INFEASIBLE",
    GRB.UNBOUNDED: "UNBOUNDED", GRB.TIME_LIMIT: "TIME_LIMIT", GRB.INTERRUPTED: "INTERRUPTED",
    GRB.SUBOPTIMAL: "SUBOPTIMAL", GRB.NODE_LIMIT: "NODE_LIMIT", GRB.SOLUTION_LIMIT: "SOLUTION_LIMIT",
    GRB.NUMERIC: "NUMERIC", GRB.MEM_LIMIT: "MEM_LIMIT",
}


def make_run_id(name, experiment, p, eps=None):
    rid = f"{name}_{experiment}_p{p}"
    return rid if eps is None else f"{rid}_eps{eps}"


def solve_and_record(inst, experiment, p, objective, mode, eps=None,
                     time_limit=TIME_LIMIT, start=None):
    """Construye, resuelve, verifica y devuelve (fila_csv, solución)."""
    name = inst["name"]
    sv = inst["services"]
    cid = [c["id"] for c in inst["candidates"]]
    run_id = make_run_id(name, experiment, p, eps)

    print("\n" + "=" * 70)
    print(f"CORRIDA {run_id}: objetivo={objective}, modo={mode}, p={p}, eps={eps}, "
          f"TimeLimit={time_limit}s")
    print("=" * 70)

    md, var, exprs = build_model(inst, p, objective, mode, eps)
    md.setParam(GRB.Param.OutputFlag, OUTPUT_FLAG)
    md.setParam(GRB.Param.TimeLimit, time_limit)
    md.setParam(GRB.Param.MIPGap, MIP_GAP)
    md.setParam(GRB.Param.Threads, THREADS)
    if SAVE_LOGS:
        os.makedirs(LOG_DIR, exist_ok=True)
        md.setParam(GRB.Param.LogFile, os.path.join(LOG_DIR, f"{run_id}.log"))
    if start is not None:
        set_start(inst, var, start)

    t0 = time.time()
    md.optimize()
    wall = time.time() - t0

    status = STATUS_NAMES.get(md.Status, f"STATUS_{md.Status}")
    has_sol = md.SolCount > 0

    def safe(attr):
        try:
            return getattr(md, attr)
        except (gp.GurobiError, AttributeError):
            return None

    row = {
        "run_id": run_id, "instance": name, "experiment": experiment,
        "objective": objective, "mode": mode, "p": p, "eps": eps,
        "status": status, "has_solution": has_sol,
        "obj_val": safe("ObjVal") if has_sol else None,
        "best_bound": safe("ObjBound"),
        "gap": safe("MIPGap") if has_sol else None,
        "runtime_s": round(md.Runtime, 3), "wall_s": round(wall, 3),
        "nodes": safe("NodeCount"), "time_limit": time_limit,
        "n_vars": md.NumVars, "n_constrs": md.NumConstrs,
    }

    sol = None
    if has_sol:
        sol = extract_solution(inst, var)
        ok, msgs, m = verify_solution(inst, sol, p=p, mode=mode, eps=eps)
        # Consistencia entre el objetivo del solver y el recalculado
        recomputed = m["dist"] if objective == "dist" else m["teams"]
        if abs(recomputed - md.ObjVal) > 1e-4 * max(1.0, abs(md.ObjVal)):
            ok = False
            msgs.append(f"Objetivo del solver {md.ObjVal:.4f} != recalculado {recomputed:.4f}")

        days_by_site = {cid[j]: {sv[s]: m["days"][j][s] for s in range(len(sv))}
                        for j in sol["open"]}
        util_by_site = {cid[j]: {sv[s]: (round(m["D"][j][s] / (inst["Q"][j][s] * m["days"][j][s]), 4)
                                         if m["days"][j][s] > 0 else None)
                                 for s in range(len(sv))}
                        for j in sol["open"]}
        row.update({
            "n_open": m["n_open"], "total_distance": round(m["dist"], 4),
            "total_teams": m["teams"],
            "open_sites": " ".join(cid[j] for j in sol["open"]),
        })
        for s, sname in enumerate(sv):
            row[f"teams_{sname}"] = m["teams_by_s"][s]
        for s, sname in enumerate(sv):
            u = m["util_by_s"][s]
            row[f"util_{sname}"] = round(u, 4) if u is not None else None
        row["days_by_site"] = json.dumps(days_by_site)
        row["util_by_site"] = json.dumps(util_by_site)
        row["verified"] = ok
        row["verify_msgs"] = " | ".join(msgs)

        print(f"\n>> {status} | abiertos={m['n_open']} ({row['open_sites']}) | "
              f"distancia={m['dist']:.2f} | equipos={m['teams']} {m['teams_by_s']} | "
              f"gap={row['gap']} | t={md.Runtime:.1f}s | verificación={'OK' if ok else 'FALLA'}")
        if not ok:
            for msg in msgs:
                print("   !!", msg)
    else:
        row["verified"] = None
        print(f"\n>> {status} | sin solución | t={md.Runtime:.1f}s")

    md.dispose()
    return row, sol


# ============================================================================
# PERSISTENCE (CSV + JSON, se guardan después de cada corrida)
# ============================================================================

BASE_COLUMNS = ["run_id", "instance", "experiment", "objective", "mode", "p", "eps",
                "status", "has_solution", "obj_val", "best_bound", "gap", "runtime_s",
                "wall_s", "nodes", "time_limit", "n_vars", "n_constrs", "n_open",
                "total_distance", "total_teams", "open_sites"]
TAIL_COLUMNS = ["days_by_site", "util_by_site", "verified", "verify_msgs"]


def columns_for(services):
    return (BASE_COLUMNS + [f"teams_{s}" for s in services]
            + [f"util_{s}" for s in services] + TAIL_COLUMNS)


def load_previous():
    rows, sols = {}, {}
    if RESUME and os.path.exists(RESULTS_CSV):
        with open(RESULTS_CSV, newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                rows[r["run_id"]] = r
    if RESUME and os.path.exists(SOLUTIONS_JSON):
        with open(SOLUTIONS_JSON, encoding="utf-8") as f:
            sols = json.load(f)
    return rows, sols


def save_all(rows, sols, services):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    cols = columns_for(services)
    with open(RESULTS_CSV, "w", newline="", encoding="utf-8") as f:
        wr = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        wr.writeheader()
        for r in rows.values():
            wr.writerow({c: ("" if r.get(c) is None else r.get(c)) for c in cols})
    with open(SOLUTIONS_JSON, "w", encoding="utf-8") as f:
        json.dump(sols, f)


def can_skip(prev_row, time_limit):
    """Una corrida previa se reutiliza si es concluyente o tuvo al menos el mismo TimeLimit."""
    if prev_row is None:
        return False
    if prev_row["status"] in ("OPTIMAL", "INFEASIBLE"):
        return True
    try:
        return float(prev_row["time_limit"]) >= time_limit - TOL
    except (TypeError, ValueError):
        return False


def row_int(row, key):
    v = row.get(key)
    return None if v in (None, "") else int(float(v))


# ============================================================================
# ENVIRONMENT REPORT (versión de Gurobi y características del computador)
# ============================================================================


def environment_info():
    info = {
        "gurobi_version": ".".join(map(str, gp.gurobi.version())),
        "python_version": platform.python_version(),
        "os": platform.platform(),
        "machine": platform.machine(),
        "processor": platform.processor() or "N/D",
        "logical_cpus": os.cpu_count(),
        "time_limit_s": TIME_LIMIT, "mip_gap": MIP_GAP, "threads_param": THREADS,
        "screen_time_limit_s": SCREEN_TIME_LIMIT,
        "date": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    try:
        import psutil
        info["physical_cpus"] = psutil.cpu_count(logical=False)
        info["ram_gb"] = round(psutil.virtual_memory().total / 1024 ** 3, 2)
        freq = psutil.cpu_freq()
        if freq:
            info["cpu_max_mhz"] = freq.max
    except ImportError:
        info["physical_cpus"] = "N/D (instale psutil)"
        info["ram_gb"] = "N/D (instale psutil)"
    return info


# ============================================================================
# EXPERIMENT DRIVER
# ============================================================================


def select_p_values(rows, name, n_cand):
    """Elige N_P_VALUES valores de p factibles: el menor, el mayor y los intermedios."""
    feas = sorted(p for p in range(1, n_cand + 1)
                  if (r := rows.get(make_run_id(name, "screen", p))) is not None
                  and str(r["has_solution"]) == "True")
    if len(feas) <= N_P_VALUES:
        return feas
    k = N_P_VALUES
    idx = sorted({round(q * (len(feas) - 1) / (k - 1)) for q in range(k)})
    return [feas[q] for q in idx]


def run_instance(inst, rows, sols):
    name = inst["name"]
    services = inst["services"]
    n_cand = inst["n_candidates"]

    def run(experiment, p, objective, mode, eps=None, time_limit=TIME_LIMIT, start=None):
        rid = make_run_id(name, experiment, p, eps)
        if can_skip(rows.get(rid), time_limit):
            print(f"[reanudar] {rid} ya existe ({rows[rid]['status']}), se omite.")
            return rows[rid], sols.get(rid)
        row, sol = solve_and_record(inst, experiment, p, objective, mode, eps, time_limit, start)
        rows[rid] = row
        if sol is not None:
            sols[rid] = sol
        else:
            sols.pop(rid, None)
        save_all(rows, sols, services)
        return row, sol

    # ---- Cribado p = 1..|IP| ----
    if RUN_SCREENING:
        for p in range(1, n_cand + 1):
            run("screen", p, "dist", "exact", time_limit=SCREEN_TIME_LIMIT)

    # ---- Selección de p ----
    p_list = P_VALUES.get(name)
    if p_list is None:
        if not RUN_SCREENING:
            raise ValueError(f"Defina P_VALUES['{name}'] o active RUN_SCREENING")
        p_list = select_p_values(rows, name, n_cand)
    print(f"\n### Instancia {name}: valores de p para la experimentación completa: {p_list}")

    for p in p_list:
        row_a, sol_a = (None, None)
        row_b, sol_b = (None, None)
        # 4.3.1 (a) min distancia, exactamente p
        if RUN_MIN_DISTANCE or RUN_EPSILON:
            row_a, sol_a = run("a_dist", p, "dist", "exact")
        # 4.3.1 (b) min equipos, exactamente p
        if RUN_MIN_TEAMS or RUN_EPSILON:
            row_b, sol_b = run("b_teams", p, "teams", "exact", start=sol_a)

        # 4.3.1 (c) épsilon-restricción: min distancia s.a. equipos <= eps,
        # eps entero desde E(b) hasta E(a) - 1 (eps = E(a) reproduce la corrida (a)).
        if RUN_EPSILON and sol_a is not None and sol_b is not None:
            e_a = row_int(row_a, "total_teams")
            e_b = row_int(row_b, "total_teams")
            d_a = float(row_a["total_distance"])
            a_opt = row_a["status"] == "OPTIMAL"
            start = sol_b  # factible para todo eps >= E(b)
            for eps in range(e_b, e_a):
                row_e, sol_e = run("c_eps", p, "dist", "exact", eps=eps, start=start)
                if sol_e is not None:
                    start = sol_e  # factible para eps + 1
                    # La distancia óptima es no creciente en eps y acotada por la de (a):
                    # si ya se alcanzó el óptimo de (a), los eps mayores dan la misma
                    # distancia y no aportan puntos nuevos a la curva.
                    if (a_opt and row_e["status"] == "OPTIMAL"
                            and float(row_e["total_distance"]) <= d_a + 1e-6):
                        print(f"[épsilon] p={p}: eps={eps} alcanza la distancia óptima de (a); "
                              f"se detiene la curva.")
                        break
        elif RUN_EPSILON:
            print(f"[épsilon] p={p}: se omite (falta solución de (a) o (b)).")

        # 4.3.4 a lo sumo p, min distancia
        if RUN_AT_MOST:
            run("atmost_dist", p, "dist", "atmost")


def print_summary(rows):
    print("\n" + "=" * 100)
    print("RESUMEN DE CORRIDAS")
    print("=" * 100)
    print(f"{'run_id':<28}{'estado':<12}{'abiertos':>9}{'distancia':>12}{'equipos':>9}"
          f"{'gap':>10}{'tiempo(s)':>11}{'nodos':>10}  verif.")
    for r in rows.values():
        gap = r.get("gap")
        gap_s = f"{float(gap):.4f}" if gap not in (None, "") else "-"
        print(f"{r['run_id']:<28}{r['status']:<12}{str(r.get('n_open') or '-'):>9}"
              f"{str(r.get('total_distance') or '-'):>12}{str(r.get('total_teams') or '-'):>9}"
              f"{gap_s:>10}{float(r['runtime_s']):>11.1f}{str(r.get('nodes') or '-'):>10}"
              f"  {r.get('verified')}")


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    env = environment_info()
    with open(ENV_JSON, "w", encoding="utf-8") as f:
        json.dump(env, f, indent=2)
    print("ENTORNO DE CÓMPUTO")
    for k, v in env.items():
        print(f"  {k}: {v}")

    rows, sols = load_previous()
    services = None
    for path in INSTANCES:
        inst = load_instance(path)
        services = inst["services"]
        print("\n" + "#" * 70)
        print(f"# INSTANCIA {inst['name']}: {inst.get('description', '')}")
        print("#" * 70)
        run_instance(inst, rows, sols)

    if services is not None:
        save_all(rows, sols, services)
    print_summary(rows)
    print(f"\nResultados: {RESULTS_CSV}\nSoluciones: {SOLUTIONS_JSON}\nEntorno: {ENV_JSON}")
