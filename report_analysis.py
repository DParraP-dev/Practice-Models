import os
import csv
import json
import math
import itertools
import statistics
import matplotlib
matplotlib.use("Agg")  # solo guarda archivos, no abre ventanas
import matplotlib.pyplot as plt

"""
================================================================================
Generación de insumos para el informe (actividad 4.4)
================================================================================
Lee las instancias y los resultados producidos por satellite_MILP.py y genera,
en resultados/informe/:

  Sección 3 (instancias)
    - estadisticas_instancias.csv   demanda, capacidad, holgura, heterogeneidad
    - espacial_instancias.csv       dispersión espacial y distancias
    - cotas_capacidad.csv           p mínimo según capacidad total (pregunta 6a)
    - mapa_instancia_<X>.png
  Sección 5 (resultados)
    - tabla_resultados_<X>.csv      todas las corridas de la instancia
    - p_vs_distancia_<X>.png        puntos satélite vs distancia (cribado, exacto, a lo sumo)
    - distancia_vs_equipos_<X>.png  curva épsilon por p, con dominadas marcadas
    - tiempo_vs_p.png               tiempo de cómputo frente a p
    - mapa_solucion_<run>.png       asignaciones de la solución
    - calendario_<run>.png          programación semanal por punto y por equipo
  Sección 6 (análisis)
    - no_dominadas_<X>.csv          conjunto no dominado (3 objetivos) y dominadas
    - exacto_vs_alosumo.csv         comparación de variantes (pregunta 6c)
    - costo_por_equipo_<X>.csv      distancia adicional por equipo reducido (6e)
    - dias_por_punto_<X>.csv        días, demanda y utilización por punto (6f)
    - resumen.md                    tablas en Markdown listas para copiar
"""

# ============================================================================
# CONFIGURACIÓN
# ============================================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INSTANCES = ["instance_A.json", "instance_B.json"]
RESULTS_DIR = os.path.join(BASE_DIR, "resultados")
OUT_DIR = os.path.join(RESULTS_DIR, "informe")


def _find(fname):
    """Busca el archivo en resultados/ y, si no está, en la carpeta del script."""
    p = os.path.join(RESULTS_DIR, fname)
    return p if os.path.exists(p) else os.path.join(BASE_DIR, fname)


RESULTS_CSV = _find("resultados.csv")
SOLUTIONS_JSON = _find("soluciones.json")
ENV_JSON = _find("entorno.json")

# Corridas para mapa de solución y calendario. None -> todas las corridas
# "a_dist" con solución (una por cada p estudiado). Ejemplo: ["A_a_dist_p7"]
SOLUTION_RUNS_TO_PLOT = None
# Corridas adicionales que se grafican siempre (soluciones recomendadas)
EXTRA_SOLUTION_RUNS = ["A_c_eps_p7_eps16", "B_c_eps_p9_eps27"]

DPI = 150
TOL = 1e-6
EXPERIMENT_LABELS = {
    "screen": "Cribado (min distancia, t corto)",
    "a_dist": "(a) min distancia, exactamente p",
    "b_teams": "(b) min equipos, exactamente p",
    "c_eps": "(c) épsilon-restricción",
    "atmost_dist": "min distancia, a lo sumo p",
}
COLORS = ["tab:blue", "tab:orange", "tab:green", "tab:red", "tab:purple",
          "tab:brown", "tab:pink", "tab:gray", "tab:olive", "tab:cyan"]

# ============================================================================
# LOADING
# ============================================================================


def load_instance(path):
    if not os.path.isabs(path):
        path = os.path.join(BASE_DIR, path)
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def to_num(v):
    if v in (None, "", "None"):
        return None
    try:
        f = float(v)
        return int(f) if f.is_integer() else f
    except ValueError:
        return v


def load_results():
    rows = []
    with open(RESULTS_CSV, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            for k in r:
                if k not in ("run_id", "instance", "experiment", "objective", "mode", "status",
                             "open_sites", "days_by_site", "util_by_site", "verify_msgs",
                             "has_solution", "verified"):
                    r[k] = to_num(r[k])
            r["has_solution"] = r["has_solution"] == "True"
            rows.append(r)
    sols = {}
    if os.path.exists(SOLUTIONS_JSON):
        with open(SOLUTIONS_JSON, encoding="utf-8") as f:
            sols = json.load(f)
    return rows, sols


def write_csv(path, rows, cols=None):
    if not rows:
        return
    cols = cols or list(rows[0].keys())
    with open(path, "w", newline="", encoding="utf-8") as f:
        wr = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        wr.writeheader()
        for r in rows:
            wr.writerow({c: ("" if r.get(c) is None else r.get(c)) for c in cols})


def md_table(rows, cols, headers=None):
    headers = headers or cols
    out = ["| " + " | ".join(headers) + " |", "|" + "---|" * len(cols)]
    for r in rows:
        vals = []
        for c in cols:
            v = r.get(c)
            if isinstance(v, float):
                v = f"{v:.4g}" if abs(v) < 1 else f"{v:.2f}"
            vals.append("-" if v in (None, "") else str(v))
        out.append("| " + " | ".join(vals) + " |")
    return "\n".join(out)


# ============================================================================
# SECTION 3: INSTANCE DESCRIPTION
# ============================================================================


def instance_stats(inst):
    w, Q = inst["w"], inst["Q"]
    nT = inst["n_days"]
    rows = []
    for s, sname in enumerate(inst["services"]):
        col = [r[s] for r in w]
        qcol = [r[s] for r in Q]
        W = sum(col)
        cap = nT * sum(qcol)
        mean = statistics.mean(col)
        rows.append({
            "instancia": inst["name"], "disciplina": sname,
            "demanda_total": W,
            "demanda_media": round(mean, 2), "demanda_min": min(col), "demanda_max": max(col),
            "cv_demanda": round(statistics.pstdev(col) / mean, 3) if mean > 0 else None,
            "nodos_con_demanda_0": sum(1 for v in col if v == 0),
            "Q_min": min(qcol), "Q_max": max(qcol),
            "cv_Q": round(statistics.pstdev(qcol) / statistics.mean(qcol), 3),
            "capacidad_semanal_total": cap,
            "holgura_ratio": round(cap / W, 3) if W > 0 else None,
            "holgura_abs": cap - W,
        })
    return rows


def spatial_stats(inst):
    dn, cd = inst["demand_nodes"], inst["candidates"]
    d = inst["d"]
    xs = [p["x"] for p in dn]
    ys = [p["y"] for p in dn]

    def nn(points):
        out = []
        for a in points:
            out.append(min(math.hypot(a["x"] - b["x"], a["y"] - b["y"]) for b in points if b is not a))
        return out

    nn_d = nn(dn)
    # Índice de Clark-Evans: R = NN_obs / (0.5 sqrt(A/n)); R<1 agrupado, R~1 aleatorio
    area = (max(xs) - min(xs)) * (max(ys) - min(ys))
    expected = 0.5 * math.sqrt(area / len(dn))
    nearest_cand = [min(r) for r in d]
    return {
        "instancia": inst["name"],
        "x_rango": f"[{min(xs):.1f}, {max(xs):.1f}]", "y_rango": f"[{min(ys):.1f}, {max(ys):.1f}]",
        "desv_x": round(statistics.pstdev(xs), 2), "desv_y": round(statistics.pstdev(ys), 2),
        "dist_media_vecino_mas_cercano": round(statistics.mean(nn_d), 2),
        "indice_clark_evans": round(statistics.mean(nn_d) / expected, 3),
        "dist_media_a_candidato_mas_cercano": round(statistics.mean(nearest_cand), 2),
        "cota_inf_distancia_p10": round(sum(nearest_cand), 2),
        "dist_media_nodo_candidato": round(statistics.mean(v for r in d for v in r), 2),
    }


def capacity_bounds(inst):
    """
    Cotas de p basadas solo en capacidad (para la pregunta 6a):
    - p_min_por_disciplina: menor k tal que los k candidatos con más capacidad
      de cada disciplina, por separado, cubren su demanda total.
    - p_min_conjunto: menor k tal que existe UN subconjunto de k candidatos que
      cubre la demanda total de todas las disciplinas a la vez (enumeración).
    """
    w, Q, nT = inst["w"], inst["Q"], inst["n_days"]
    nJ, nS = inst["n_candidates"], len(inst["services"])
    W = [sum(r[s] for r in w) for s in range(nS)]
    per_s = []
    for s in range(nS):
        caps = sorted((nT * Q[j][s] for j in range(nJ)), reverse=True)
        acc, k = 0, 0
        while acc < W[s] and k < nJ:
            acc += caps[k]
            k += 1
        per_s.append(k if acc >= W[s] else None)
    joint = None
    for k in range(1, nJ + 1):
        if any(all(nT * sum(Q[j][s] for j in c) >= W[s] for s in range(nS))
               for c in itertools.combinations(range(nJ), k)):
            joint = k
            break
    row = {"instancia": inst["name"],
           "p_min_capacidad_por_disciplina": max(v for v in per_s if v is not None),
           "p_min_capacidad_conjunta": joint}
    for s, sname in enumerate(inst["services"]):
        row[f"k_min_{sname}"] = per_s[s]
    return row


def plot_instance_map(inst, path):
    dn, cd = inst["demand_nodes"], inst["candidates"]
    tot = [sum(r) for r in inst["w"]]
    fig, ax = plt.subplots(figsize=(7, 6.5))
    ax.scatter([p["x"] for p in dn], [p["y"] for p in dn], s=[8 + 3 * t for t in tot],
               c="tab:blue", alpha=0.6, edgecolors="k", linewidths=0.4,
               label="Nodo de demanda (tamaño ∝ demanda total)")
    ax.scatter([c["x"] for c in cd], [c["y"] for c in cd], marker="s", s=90, c="tab:red",
               edgecolors="k", label="Candidato")
    for c, q in zip(cd, inst["Q"]):
        ax.annotate(f"{c['id']}\nQ={q}", (c["x"], c["y"]), fontsize=6.5,
                    xytext=(4, 4), textcoords="offset points")
    ax.set_title(f"Instancia {inst['name']}: nodos de demanda y candidatos")
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.1), ncol=2, fontsize=8)
    ax.set_aspect("equal", adjustable="datalim")
    fig.tight_layout()
    fig.savefig(path, dpi=DPI)
    plt.close(fig)


# ============================================================================
# SECTION 5: RESULTS PLOTS
# ============================================================================


def rows_of(rows, name, experiment=None, p=None):
    out = [r for r in rows if r["instance"] == name]
    if experiment is not None:
        out = [r for r in out if r["experiment"] == experiment]
    if p is not None:
        out = [r for r in out if r["p"] == p]
    return out


def plot_p_vs_distance(rows, inst, path):
    name, nJ = inst["name"], inst["n_candidates"]
    fig, ax = plt.subplots(figsize=(7, 4.5))
    styles = {"screen": ("o", ":", "tab:gray"), "a_dist": ("s", "-", "tab:blue"),
              "atmost_dist": ("^", "--", "tab:green")}
    for exp, (mk, ls, col) in styles.items():
        rs = sorted(rows_of(rows, name, exp), key=lambda r: r["p"])
        pts = [(r["p"], r["total_distance"]) for r in rs if r["has_solution"]]
        if pts:
            ax.plot(*zip(*pts), marker=mk, ls=ls, color=col, label=EXPERIMENT_LABELS[exp])
        # Marcar los p sin solución óptima garantizada
        for r in rs:
            if r["has_solution"] and r["status"] != "OPTIMAL":
                ax.annotate("TL", (r["p"], r["total_distance"]), fontsize=7, color=col,
                            xytext=(3, 3), textcoords="offset points")
    infeas = sorted({r["p"] for r in rows_of(rows, name)
                     if r["experiment"] in ("screen", "a_dist") and r["status"] == "INFEASIBLE"})
    if infeas:
        ymin = ax.get_ylim()[0] if ax.has_data() else 0
        ax.scatter(infeas, [ymin] * len(infeas), marker="x", color="tab:red", s=60, zorder=5,
                   label="Infactible (exactamente p)")
    ax.set_xticks(range(1, nJ + 1))
    ax.set_xlabel("p (puntos satélite)")
    ax.set_ylabel("Distancia total")
    ax.set_title(f"Instancia {name}: puntos satélite vs distancia total")
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=DPI)
    plt.close(fig)


def plot_distance_vs_teams(rows, inst, nd_ids, path):
    name = inst["name"]
    ps = sorted({r["p"] for r in rows_of(rows, name) if r["experiment"] in ("a_dist", "b_teams", "c_eps")})
    if not ps:
        return
    fig, ax = plt.subplots(figsize=(7, 4.5))
    for k, p in enumerate(ps):
        col = COLORS[k % len(COLORS)]
        rs = [r for r in rows_of(rows, name, p=p)
              if r["experiment"] in ("a_dist", "b_teams", "c_eps") and r["has_solution"]]
        # Curva épsilon: mejor distancia por número de equipos
        best = {}
        for r in rs:
            e = r["total_teams"]
            if e not in best or r["total_distance"] < best[e]["total_distance"]:
                best[e] = r
        curve = sorted(best.items())
        ax.plot([e for e, _ in curve], [r["total_distance"] for _, r in curve], "-", color=col,
                alpha=0.6, label=f"p = {p}")
        for r in rs:
            filled = r["run_id"] in nd_ids
            mk = {"a_dist": "s", "b_teams": "D", "c_eps": "o"}[r["experiment"]]
            ax.scatter(r["total_teams"], r["total_distance"], marker=mk, s=40,
                       facecolors=col if filled else "none", edgecolors=col, zorder=3)
    ax.scatter([], [], marker="s", facecolors="none", edgecolors="k", label="(a) min distancia")
    ax.scatter([], [], marker="D", facecolors="none", edgecolors="k", label="(b) min equipos")
    ax.scatter([], [], marker="o", facecolors="none", edgecolors="k", label="(c) épsilon")
    ax.scatter([], [], marker="o", facecolors="k", edgecolors="k", label="relleno = no dominada")
    ax.set_xlabel("Equipos totales")
    ax.set_ylabel("Distancia total")
    ax.set_title(f"Instancia {name}: compromiso distancia vs equipos")
    ax.grid(alpha=0.3)
    ax.legend(fontsize=7, ncol=2)
    fig.tight_layout()
    fig.savefig(path, dpi=DPI)
    plt.close(fig)


def plot_time_vs_p(rows, insts, path):
    exps = ["screen", "a_dist", "b_teams", "c_eps", "atmost_dist"]
    fig, axes = plt.subplots(1, len(insts), figsize=(6 * len(insts), 4.5), squeeze=False)
    for ax, inst in zip(axes[0], insts):
        name = inst["name"]
        for k, exp in enumerate(exps):
            rs = rows_of(rows, name, exp)
            if not rs:
                continue
            if exp == "c_eps":
                # Tiempo total de la curva épsilon por p
                agg = {}
                for r in rs:
                    agg[r["p"]] = agg.get(r["p"], 0) + r["runtime_s"]
                pts = sorted(agg.items())
                lab = "(c) épsilon (suma por p)"
            else:
                pts = sorted((r["p"], r["runtime_s"]) for r in rs)
                lab = EXPERIMENT_LABELS[exp]
            ax.plot([q for q, _ in pts], [max(t, 1e-2) for _, t in pts], marker="o",
                    color=COLORS[k], label=lab)
        ax.set_yscale("log")
        ax.set_xticks(range(1, inst["n_candidates"] + 1))
        ax.set_xlabel("p")
        ax.set_ylabel("Tiempo de cómputo (s, escala log)")
        ax.set_title(f"Instancia {name}")
        ax.grid(alpha=0.3, which="both")
        ax.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(path, dpi=DPI)
    plt.close(fig)


def plot_solution_map(inst, sol, run_row, path):
    dn, cd = inst["demand_nodes"], inst["candidates"]
    fig, ax = plt.subplots(figsize=(7, 6.5))
    open_set = sol["open"]
    color_of = {j: COLORS[k % len(COLORS)] for k, j in enumerate(open_set)}
    for i, j in enumerate(sol["assign"]):
        ax.plot([dn[i]["x"], cd[j]["x"]], [dn[i]["y"], cd[j]["y"]], color=color_of.get(j, "k"),
                lw=0.8, alpha=0.7)
    ax.scatter([p["x"] for p in dn], [p["y"] for p in dn], s=18,
               c=[color_of.get(j, "k") for j in sol["assign"]], edgecolors="k", linewidths=0.3)
    closed = [j for j in range(len(cd)) if j not in open_set]
    ax.scatter([cd[j]["x"] for j in closed], [cd[j]["y"] for j in closed], marker="s", s=60,
               facecolors="none", edgecolors="gray", label="Candidato cerrado")
    ax.scatter([cd[j]["x"] for j in open_set], [cd[j]["y"] for j in open_set], marker="s", s=110,
               c=[color_of[j] for j in open_set], edgecolors="k", label="Punto satélite abierto")
    for j in range(len(cd)):
        ax.annotate(cd[j]["id"], (cd[j]["x"], cd[j]["y"]), fontsize=8, xytext=(4, 4),
                    textcoords="offset points")
    ax.set_title(f"{run_row['run_id']}: p={run_row['n_open']}, distancia={run_row['total_distance']:.1f}, "
                 f"equipos={run_row['total_teams']}", fontsize=10)
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.1), ncol=2, fontsize=8)
    ax.set_aspect("equal", adjustable="datalim")
    fig.tight_layout()
    fig.savefig(path, dpi=DPI)
    plt.close(fig)


def team_calendar(inst, sol):
    """Asigna equipos a puntos por día: el k-ésimo punto (en orden) donde atiende s el día t
    lo cubre el equipo k de s. Devuelve {s: [[sitio o None por día] por equipo]}."""
    nJ, nS, nT = inst["n_candidates"], len(inst["services"]), inst["n_days"]
    cid = [c["id"] for c in inst["candidates"]]
    cal = {}
    for s in range(nS):
        per_day = [[cid[j] for j in range(nJ) if t in sol["schedule"][j][s]] for t in range(nT)]
        n_teams = max(len(x) for x in per_day)
        cal[s] = [[per_day[t][k] if k < len(per_day[t]) else None for t in range(nT)]
                  for k in range(n_teams)]
    return cal


def plot_calendar(inst, sol, run_row, path):
    sv, nT = inst["services"], inst["n_days"]
    cid = [c["id"] for c in inst["candidates"]]
    days = [f"Día {t + 1}" for t in range(nT)]
    open_set = sol["open"]
    cal = team_calendar(inst, sol)
    team_rows = [(f"{sv[s]}-E{k + 1}", cal[s][k]) for s in range(len(sv)) for k in range(len(cal[s]))]

    h1 = 0.45 * len(open_set) + 1.2
    h2 = 0.32 * len(team_rows) + 1.2
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, h1 + h2),
                                   gridspec_kw={"height_ratios": [h1, h2]})
    # Panel 1: disciplinas por punto y día
    cell1 = [[" ".join(sv[s] for s in range(len(sv)) if t in sol["schedule"][j][s]) or "-"
              for t in range(nT)] for j in open_set]
    ax1.axis("off")
    t1 = ax1.table(cellText=cell1, rowLabels=[cid[j] for j in open_set], colLabels=days,
                   loc="center", cellLoc="center")
    t1.auto_set_font_size(False)
    t1.set_fontsize(7.5)
    t1.scale(1, 1.3)
    ax1.set_title(f"{run_row['run_id']}: disciplinas que atienden en cada punto por día", fontsize=10)
    # Panel 2: ruta semanal de cada equipo
    s_color = {sv[s]: COLORS[s] for s in range(len(sv))}
    cell2 = [[x or "libre" for x in r] for _, r in team_rows]
    ax2.axis("off")
    t2 = ax2.table(cellText=cell2, rowLabels=[lab for lab, _ in team_rows], colLabels=days,
                   loc="center", cellLoc="center")
    t2.auto_set_font_size(False)
    t2.set_fontsize(7.5)
    t2.scale(1, 1.2)
    for (r, c), cell in t2.get_celld().items():
        if r >= 1:
            sname = team_rows[r - 1][0].split("-")[0]
            if c >= 0 and team_rows[r - 1][1][c] is not None:
                cell.set_facecolor(matplotlib.colors.to_rgba(s_color[sname], 0.25))
    ax2.set_title(f"Calendario semanal de equipos (total {run_row['total_teams']} equipos)", fontsize=10)
    fig.tight_layout()
    fig.savefig(path, dpi=DPI)
    plt.close(fig)


# ============================================================================
# SECTION 6: ANALYSIS TABLES
# ============================================================================


def non_dominated(rows, name):
    """Filtro de Pareto sobre (puntos abiertos, distancia, equipos), todas minimizadas,
    usando todas las corridas con solución verificada de la instancia."""
    cand = [r for r in rows_of(rows, name) if r["has_solution"] and r["verified"] == "True"]
    out = []
    for r in cand:
        a = (r["n_open"], r["total_distance"], r["total_teams"])
        dom_by = None
        for q in cand:
            b = (q["n_open"], q["total_distance"], q["total_teams"])
            if all(bb <= aa + TOL for aa, bb in zip(a, b)) and any(bb < aa - TOL for aa, bb in zip(a, b)):
                dom_by = q["run_id"]
                break
        out.append({"run_id": r["run_id"], "experiment": r["experiment"], "status": r["status"],
                    "p": r["p"], "n_open": a[0], "total_distance": a[1], "total_teams": a[2],
                    "dominada": dom_by is not None, "dominada_por": dom_by})
    out.sort(key=lambda r: (r["dominada"], r["n_open"], r["total_teams"], r["total_distance"]))
    # Puntos únicos no dominados (varias corridas pueden dar el mismo vector)
    seen, uniq = set(), []
    for r in out:
        key = (r["n_open"], round(r["total_distance"], 4), r["total_teams"])
        if not r["dominada"] and key not in seen:
            seen.add(key)
            uniq.append(r)
    return out, uniq


def exact_vs_atmost(rows, insts):
    out = []
    for inst in insts:
        name = inst["name"]
        ps = sorted({r["p"] for r in rows_of(rows, name, "atmost_dist")})
        for p in ps:
            ex = rows_of(rows, name, "a_dist", p) or rows_of(rows, name, "screen", p)
            am = rows_of(rows, name, "atmost_dist", p)
            ex, am = (ex[0] if ex else {}), (am[0] if am else {})
            out.append({
                "instancia": name, "p": p,
                "exacto_estado": ex.get("status"), "exacto_abiertos": ex.get("n_open"),
                "exacto_distancia": ex.get("total_distance"), "exacto_equipos": ex.get("total_teams"),
                "alosumo_estado": am.get("status"), "alosumo_abiertos": am.get("n_open"),
                "alosumo_distancia": am.get("total_distance"), "alosumo_equipos": am.get("total_teams"),
                "alosumo_tiempo_s": am.get("runtime_s"), "exacto_tiempo_s": ex.get("runtime_s"),
            })
    return out


def cost_per_team(rows, name):
    """Para cada p: puntos de la curva épsilon (mejor distancia por número de equipos) y
    distancia adicional por cada equipo reducido entre puntos consecutivos."""
    out = []
    for p in sorted({r["p"] for r in rows_of(rows, name, "c_eps")} |
                    {r["p"] for r in rows_of(rows, name, "a_dist")}):
        rs = [r for r in rows_of(rows, name, p=p)
              if r["experiment"] in ("a_dist", "b_teams", "c_eps") and r["has_solution"]]
        best = {}
        for r in rs:
            e = r["total_teams"]
            if e not in best or r["total_distance"] < best[e]["total_distance"]:
                best[e] = r
        # Quitar dominados dentro de la curva (más equipos y no menos distancia)
        curve, best_d = [], math.inf
        for e in sorted(best):
            r = best[e]
            if r["total_distance"] < best_d - TOL:
                curve.append(r)
                best_d = r["total_distance"]
        for k, r in enumerate(curve):
            row = {"instancia": name, "p": p, "equipos": r["total_teams"],
                   "distancia": r["total_distance"], "run_id": r["run_id"], "estado": r["status"]}
            for s in inst_services(name):
                row[f"equipos_{s}"] = r.get(f"teams_{s}")
            if k + 1 < len(curve):
                nxt = curve[k + 1]
                de = nxt["total_teams"] - r["total_teams"]
                row["dist_extra_por_equipo_reducido"] = round(
                    (r["total_distance"] - nxt["total_distance"]) / de, 3)
            out.append(row)
    return out


_SERVICES = {}


def inst_services(name):
    return _SERVICES[name]


def days_table(inst, rows, sols):
    """Días, demanda asignada, capacidad y utilización por punto y disciplina (pregunta 6f)."""
    name = inst["name"]
    Q, w, nT = inst["Q"], inst["w"], inst["n_days"]
    cid = [c["id"] for c in inst["candidates"]]
    out = []
    for r in rows_of(rows, name):
        if r["experiment"] not in ("a_dist", "b_teams", "atmost_dist") or r["run_id"] not in sols:
            continue
        sol = sols[r["run_id"]]
        for j in sol["open"]:
            nodes = [i for i, jj in enumerate(sol["assign"]) if jj == j]
            for s, sname in enumerate(inst["services"]):
                D = sum(w[i][s] for i in nodes)
                n = len(sol["schedule"][j][s])
                out.append({
                    "run_id": r["run_id"], "p": r["p"], "punto": cid[j], "nodos_asignados": len(nodes),
                    "disciplina": sname, "demanda_asignada": D, "Q_diaria": Q[j][s], "dias": n,
                    "ceil_D_Q": math.ceil(D / Q[j][s]) if Q[j][s] else None,
                    "capacidad_semanal": Q[j][s] * n,
                    "utilizacion": round(D / (Q[j][s] * n), 3) if n else None,
                    "dias_por_100_pacientes": round(100 * n / D, 2) if D else None,
                })
    return out


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    os.makedirs(OUT_DIR, exist_ok=True)
    insts = [load_instance(p) for p in INSTANCES]
    for inst in insts:
        _SERVICES[inst["name"]] = inst["services"]
    md = ["# Insumos para el informe\n"]

    if os.path.exists(ENV_JSON):
        with open(ENV_JSON, encoding="utf-8") as f:
            env = json.load(f)
        md.append("## Entorno de cómputo\n")
        md.append("\n".join(f"- **{k}**: {v}" for k, v in env.items()) + "\n")

    # ---- Sección 3 ----
    stats = [r for inst in insts for r in instance_stats(inst)]
    spatial = [spatial_stats(inst) for inst in insts]
    bounds = [capacity_bounds(inst) for inst in insts]
    write_csv(os.path.join(OUT_DIR, "estadisticas_instancias.csv"), stats)
    write_csv(os.path.join(OUT_DIR, "espacial_instancias.csv"), spatial)
    write_csv(os.path.join(OUT_DIR, "cotas_capacidad.csv"), bounds)
    for inst in insts:
        plot_instance_map(inst, os.path.join(OUT_DIR, f"mapa_instancia_{inst['name']}.png"))
    md.append("## Descripción de las instancias\n")
    md.append(md_table(stats, ["instancia", "disciplina", "demanda_total", "cv_demanda",
                               "nodos_con_demanda_0", "Q_min", "Q_max", "capacidad_semanal_total",
                               "holgura_ratio"]) + "\n")
    md.append(md_table(spatial, list(spatial[0].keys())) + "\n")
    md.append("Cotas de p basadas solo en capacidad total:\n")
    md.append(md_table(bounds, list(bounds[0].keys())) + "\n")
    print("Sección 3 (instancias) generada.")

    if not os.path.exists(RESULTS_CSV):
        print(f"No existe {RESULTS_CSV}. Ejecute primero satellite_MILP.py.")
    else:
        rows, sols = load_results()

        # ---- Sección 5 ----
        cols = ["run_id", "experiment", "p", "eps", "status", "n_open", "total_distance",
                "total_teams", "best_bound", "gap", "runtime_s", "nodes", "verified"]
        md.append("## Resultados por instancia\n")
        nd_all = {}
        for inst in insts:
            name = inst["name"]
            rs = sorted(rows_of(rows, name), key=lambda r: (r["p"], r["experiment"], r["eps"] or 0))
            write_csv(os.path.join(OUT_DIR, f"tabla_resultados_{name}.csv"), rs)
            md.append(f"### Instancia {name}\n")
            md.append(md_table(rs, cols) + "\n")

            all_nd, uniq_nd = non_dominated(rows, name)
            nd_all[name] = (all_nd, uniq_nd)
            nd_ids = {r["run_id"] for r in all_nd if not r["dominada"]}
            plot_p_vs_distance(rows, inst, os.path.join(OUT_DIR, f"p_vs_distancia_{name}.png"))
            plot_distance_vs_teams(rows, inst, nd_ids, os.path.join(OUT_DIR, f"distancia_vs_equipos_{name}.png"))

            to_plot = SOLUTION_RUNS_TO_PLOT or [r["run_id"] for r in rs
                                                if r["experiment"] == "a_dist" and r["has_solution"]]
            to_plot = list(to_plot) + [rid for rid in EXTRA_SOLUTION_RUNS if rid not in to_plot]
            by_id = {r["run_id"]: r for r in rs}
            for rid in to_plot:
                if rid in sols and rid in by_id:
                    plot_solution_map(inst, sols[rid], by_id[rid], os.path.join(OUT_DIR, f"mapa_solucion_{rid}.png"))
                    plot_calendar(inst, sols[rid], by_id[rid], os.path.join(OUT_DIR, f"calendario_{rid}.png"))
        plot_time_vs_p(rows, insts, os.path.join(OUT_DIR, "tiempo_vs_p.png"))
        print("Sección 5 (resultados y gráficas) generada.")

        # ---- Sección 6 ----
        md.append("## Soluciones no dominadas (puntos abiertos, distancia, equipos)\n")
        for inst in insts:
            name = inst["name"]
            all_nd, uniq_nd = nd_all[name]
            write_csv(os.path.join(OUT_DIR, f"no_dominadas_{name}.csv"), all_nd)
            md.append(f"### Instancia {name}: {len(uniq_nd)} puntos no dominados distintos, "
                      f"{sum(r['dominada'] for r in all_nd)} corridas dominadas\n")
            md.append(md_table(uniq_nd, ["run_id", "n_open", "total_distance", "total_teams", "status"]) + "\n")
            dom = [r for r in all_nd if r["dominada"]]
            if dom:
                md.append("Corridas dominadas:\n")
                md.append(md_table(dom, ["run_id", "n_open", "total_distance", "total_teams", "dominada_por"]) + "\n")

        eva = exact_vs_atmost(rows, insts)
        write_csv(os.path.join(OUT_DIR, "exacto_vs_alosumo.csv"), eva)
        md.append("## Exactamente p vs a lo sumo p (min distancia)\n")
        if eva:
            md.append(md_table(eva, list(eva[0].keys())) + "\n")

        md.append("## Curva épsilon y distancia adicional por equipo reducido\n")
        for inst in insts:
            cpt = cost_per_team(rows, inst["name"])
            write_csv(os.path.join(OUT_DIR, f"costo_por_equipo_{inst['name']}.csv"), cpt)
            if cpt:
                md.append(f"### Instancia {inst['name']}\n")
                md.append(md_table(cpt, list(cpt[0].keys())) + "\n")

            dt = days_table(inst, rows, sols)
            write_csv(os.path.join(OUT_DIR, f"dias_por_punto_{inst['name']}.csv"), dt)
        print("Sección 6 (tablas de análisis) generada.")

    with open(os.path.join(OUT_DIR, "resumen.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(md))
    print(f"Archivos generados en: {OUT_DIR}")
