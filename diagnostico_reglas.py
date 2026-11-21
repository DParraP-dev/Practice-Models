import os
import csv
import gurobipy as gp
from gurobipy import GRB
import satellite_MILP as base

"""
================================================================================
Diagnóstico de reglas: qué causa la infactibilidad y la no monotonía
================================================================================
Pruebas cortas (menos de 1 s cada una) que apoyan las preguntas 6(a) y 6(b).

PRUEBA 1 (pregunta 6a, p pequeño infactible):
  - modelo completo;
  - modelo sin R3 ni R4 (solo asignación única + capacidad semanal con n <= 6);
  - demanda divisible pero agrupada por nodo: x[i,j] continua, el MISMO x para
    las 4 disciplinas, capacidad sum_i w[i,s] x[i,j] <= 6 Q[j,s] y[j].
  Si la versión divisible sigue siendo infactible, la causa no es la
  indivisibilidad del nodo sino que su demanda viaja "en paquete" (las 4
  disciplinas al mismo punto) y la capacidad está repartida de forma desigual
  entre disciplinas.

PRUEBA 2 (pregunta 6b, distancia creciente con p):
  - modelo completo, sin R3 y sin R4, minimizando distancia con exactamente p.
"""

TIME_LIMIT = 60
OUT_CSV = os.path.join(base.BASE_DIR, "resultados", "diagnostico_reglas.csv")

STATUS = {GRB.OPTIMAL: "OPTIMAL", GRB.INFEASIBLE: "INFEASIBLE", GRB.INF_OR_UNBD: "INFEASIBLE",
          GRB.TIME_LIMIT: "TIME_LIMIT"}


def solve(md):
    md.setParam(GRB.Param.OutputFlag, 0)
    md.setParam(GRB.Param.TimeLimit, TIME_LIMIT)
    md.optimize()
    st = STATUS.get(md.Status, f"STATUS_{md.Status}")
    val = round(md.ObjVal, 2) if md.SolCount > 0 else None
    md.dispose()
    return st, val


def full_model_without(inst, p, drop_prefixes=()):
    """Modelo de satellite_MILP.py (min distancia, exactamente p) quitando restricciones por prefijo."""
    md, _, _ = base.build_model(inst, p, "dist", "exact")
    for c in md.getConstrs():
        if any(c.ConstrName.startswith(pre) for pre in drop_prefixes):
            md.remove(c)
    md.update()
    return solve(md)


def divisible_bundled(inst, p):
    """Relajación: demanda del nodo divisible entre puntos, pero con el mismo reparto en las 4 disciplinas."""
    w, Q, d, nT = inst["w"], inst["Q"], inst["d"], inst["n_days"]
    I, J, S = range(inst["n_demand"]), range(inst["n_candidates"]), range(len(inst["services"]))
    md = gp.Model("divisible_agrupada")
    y = md.addVars(J, vtype=GRB.BINARY, name="y")
    x = md.addVars(I, J, lb=0, ub=1, name="x")
    md.addConstrs(x.sum(i, "*") == 1 for i in I)
    md.addConstrs(gp.quicksum(w[i][s] * x[i, j] for i in I) <= nT * Q[j][s] * y[j] for j in J for s in S)
    md.addConstr(y.sum() == p)
    md.setObjective(gp.quicksum(d[i][j] * x[i, j] for i in I for j in J), GRB.MINIMIZE)
    return solve(md)


if __name__ == "__main__":
    rows = []

    def record(test, name, p, variant, res):
        rows.append({"prueba": test, "instancia": name, "p": p, "variante": variant,
                     "estado": res[0], "distancia": res[1]})
        print(f"{test:<10}{name:<4}p={p:<4}{variant:<45}{res[0]:<12}{res[1] if res[1] is not None else '-'}")

    instA = base.load_instance("instance_A.json")
    instB = base.load_instance("instance_B.json")

    print("PRUEBA 1: causas de infactibilidad con p pequeño")
    for inst, p in [(instA, 3), (instA, 4), (instB, 5), (instB, 6), (instB, 7)]:
        record("6a", inst["name"], p, "completo", full_model_without(inst, p))
        record("6a", inst["name"], p, "sin R3 ni R4", full_model_without(inst, p, ("R3_", "R4_")))
        record("6a", inst["name"], p, "demanda divisible agrupada por nodo", divisible_bundled(inst, p))

    print("\nPRUEBA 2: distancia mínima con p grande en la instancia A")
    for p in (8, 9, 10):
        record("6b", "A", p, "completo", full_model_without(instA, p))
        record("6b", "A", p, "sin R3", full_model_without(instA, p, ("R3_",)))
        record("6b", "A", p, "sin R4", full_model_without(instA, p, ("R4_",)))

    os.makedirs(os.path.dirname(OUT_CSV), exist_ok=True)
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        wr = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        wr.writeheader()
        wr.writerows(rows)
    print(f"\nResultados: {OUT_CSV}")
