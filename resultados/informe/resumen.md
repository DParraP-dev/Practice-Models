# Insumos para el informe

## Entorno de cómputo

- **gurobi_version**: 13.0.3
- **python_version**: 3.14.2
- **os**: Windows-11-10.0.26300-SP0
- **machine**: AMD64
- **processor**: Intel64 Family 6 Model 142 Stepping 12, GenuineIntel
- **logical_cpus**: 8
- **time_limit_s**: 1800
- **mip_gap**: 0.0
- **threads_param**: 0
- **screen_time_limit_s**: 60
- **date**: 2026-11-20 03:18:55
- **physical_cpus**: 4
- **ram_gb**: 7.8
- **cpu_max_mhz**: 2112.0

## Descripción de las instancias

| instancia | disciplina | demanda_total | cv_demanda | nodos_con_demanda_0 | Q_min | Q_max | capacidad_semanal_total | holgura_ratio |
|---|---|---|---|---|---|---|---|---|
| A | S1 | 468 | 0.327 | 0 | 21 | 30 | 1506 | 3.22 |
| A | S2 | 520 | 0.299 | 0 | 21 | 29 | 1506 | 2.90 |
| A | S3 | 519 | 0.31 | 0 | 20 | 31 | 1554 | 2.99 |
| A | S4 | 480 | 0.316 | 0 | 19 | 30 | 1398 | 2.91 |
| B | S1 | 699 | 0.883 | 12 | 4 | 28 | 1128 | 1.61 |
| B | S2 | 446 | 0.676 | 8 | 3 | 23 | 654 | 1.47 |
| B | S3 | 243 | 0.692 | 4 | 2 | 19 | 384 | 1.58 |
| B | S4 | 119 | 0.708 | 7 | 2 | 7 | 252 | 2.12 |

| instancia | x_rango | y_rango | desv_x | desv_y | dist_media_vecino_mas_cercano | indice_clark_evans | dist_media_a_candidato_mas_cercano | cota_inf_distancia_p10 | dist_media_nodo_candidato |
|---|---|---|---|---|---|---|---|---|---|
| A | [0.2, 96.7] | [1.3, 99.0] | 25.81 | 26.07 | 7.39 | 1.08 | 17.88 | 893.82 | 49.10 |
| B | [1.4, 80.2] | [14.8, 94.1] | 21.95 | 22.91 | 4.16 | 0.744 | 15.46 | 773.15 | 46.64 |

Cotas de p basadas solo en capacidad total:

| instancia | p_min_capacidad_por_disciplina | p_min_capacidad_conjunta | k_min_S1 | k_min_S2 | k_min_S3 | k_min_S4 |
|---|---|---|---|---|---|---|
| A | 4 | 4 | 3 | 4 | 3 | 3 |
| B | 5 | 6 | 5 | 5 | 4 | 4 |

## Resultados por instancia

### Instancia A

| run_id | experiment | p | eps | status | n_open | total_distance | total_teams | best_bound | gap | runtime_s | nodes | verified |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A_screen_p1 | screen | 1 | - | INFEASIBLE | - | - | - | inf | - | 0.061 | 0 | - |
| A_screen_p2 | screen | 2 | - | INFEASIBLE | - | - | - | inf | - | 0.167 | 1 | - |
| A_screen_p3 | screen | 3 | - | INFEASIBLE | - | - | - | inf | - | 0.161 | 1 | - |
| A_a_dist_p4 | a_dist | 4 | - | OPTIMAL | 4 | 1096.56 | 16 | 1096.56 | 0 | 0.53 | 1 | True |
| A_atmost_dist_p4 | atmost_dist | 4 | - | OPTIMAL | 4 | 1096.56 | 16 | 1096.56 | 0 | 0.472 | 1 | True |
| A_b_teams_p4 | b_teams | 4 | - | OPTIMAL | 4 | 2622.44 | 14 | 14 | 0 | 1.30 | 1118 | True |
| A_c_eps_p4_eps14 | c_eps | 4 | 14 | OPTIMAL | 4 | 2088.75 | 14 | 2088.75 | 0 | 173.59 | 701581 | True |
| A_c_eps_p4_eps15 | c_eps | 4 | 15 | OPTIMAL | 4 | 1138 | 15 | 1138 | 0 | 14.86 | 29327 | True |
| A_screen_p4 | screen | 4 | - | OPTIMAL | 4 | 1096.56 | 16 | 1096.56 | 0 | 0.569 | 1 | True |
| A_screen_p5 | screen | 5 | - | OPTIMAL | 5 | 999.76 | 19 | 999.76 | 0 | 0.227 | 1 | True |
| A_screen_p6 | screen | 6 | - | OPTIMAL | 6 | 945.30 | 23 | 945.30 | 0 | 0.042 | 1 | True |
| A_a_dist_p7 | a_dist | 7 | - | OPTIMAL | 7 | 913.05 | 23 | 913.05 | 0 | 0.045 | 1 | True |
| A_atmost_dist_p7 | atmost_dist | 7 | - | OPTIMAL | 7 | 913.05 | 20 | 913.05 | 0 | 0.043 | 1 | True |
| A_b_teams_p7 | b_teams | 7 | - | OPTIMAL | 7 | 2666.33 | 15 | 15 | 0 | 1.93 | 578 | True |
| A_c_eps_p7_eps15 | c_eps | 7 | 15 | OPTIMAL | 7 | 1014.75 | 15 | 1014.75 | 0 | 158.46 | 416747 | True |
| A_c_eps_p7_eps16 | c_eps | 7 | 16 | OPTIMAL | 7 | 913.13 | 16 | 913.13 | 0 | 0.191 | 1 | True |
| A_c_eps_p7_eps17 | c_eps | 7 | 17 | OPTIMAL | 7 | 913.13 | 16 | 913.13 | 0 | 0.318 | 643 | True |
| A_c_eps_p7_eps18 | c_eps | 7 | 18 | OPTIMAL | 7 | 913.05 | 18 | 913.05 | 0 | 0.07 | 1 | True |
| A_screen_p7 | screen | 7 | - | OPTIMAL | 7 | 913.05 | 23 | 913.05 | 0 | 0.041 | 1 | True |
| A_screen_p8 | screen | 8 | - | OPTIMAL | 8 | 893.82 | 24 | 893.82 | 0 | 0.035 | 1 | True |
| A_screen_p9 | screen | 9 | - | OPTIMAL | 9 | 908.08 | 25 | 908.08 | 0 | 0.772 | 71 | True |
| A_a_dist_p10 | a_dist | 10 | - | OPTIMAL | 10 | 951.39 | 25 | 951.39 | 0 | 2.52 | 4022 | True |
| A_atmost_dist_p10 | atmost_dist | 10 | - | OPTIMAL | 8 | 893.82 | 23 | 893.82 | 0 | 0.037 | 1 | True |
| A_b_teams_p10 | b_teams | 10 | - | OPTIMAL | 10 | 2373.40 | 15 | 15 | 0 | 6.62 | 8860 | True |
| A_c_eps_p10_eps15 | c_eps | 10 | 15 | TIME_LIMIT | 10 | 1233.12 | 15 | 1172.20 | 0.0494 | 1800.03 | 2862289 | True |
| A_c_eps_p10_eps16 | c_eps | 10 | 16 | OPTIMAL | 10 | 969.28 | 16 | 969.28 | 0 | 29.35 | 29173 | True |
| A_c_eps_p10_eps17 | c_eps | 10 | 17 | OPTIMAL | 10 | 959.80 | 17 | 959.80 | 0 | 9.76 | 7273 | True |
| A_c_eps_p10_eps18 | c_eps | 10 | 18 | OPTIMAL | 10 | 955.67 | 18 | 955.67 | 0 | 11.76 | 27209 | True |
| A_c_eps_p10_eps19 | c_eps | 10 | 19 | OPTIMAL | 10 | 951.39 | 19 | 951.39 | 0 | 1.53 | 2832 | True |
| A_screen_p10 | screen | 10 | - | OPTIMAL | 10 | 951.39 | 25 | 951.39 | 0 | 3.35 | 4022 | True |

### Instancia B

| run_id | experiment | p | eps | status | n_open | total_distance | total_teams | best_bound | gap | runtime_s | nodes | verified |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| B_screen_p1 | screen | 1 | - | INFEASIBLE | - | - | - | inf | - | 0.09 | 0 | - |
| B_screen_p2 | screen | 2 | - | INFEASIBLE | - | - | - | inf | - | 0.058 | 1 | - |
| B_screen_p3 | screen | 3 | - | INFEASIBLE | - | - | - | inf | - | 0.058 | 1 | - |
| B_screen_p4 | screen | 4 | - | INFEASIBLE | - | - | - | inf | - | 0.086 | 1 | - |
| B_screen_p5 | screen | 5 | - | INFEASIBLE | - | - | - | inf | - | 0.078 | 1 | - |
| B_screen_p6 | screen | 6 | - | INFEASIBLE | - | - | - | inf | - | 0.09 | 1 | - |
| B_a_dist_p7 | a_dist | 7 | - | OPTIMAL | 7 | 1206.01 | 26 | 1206.01 | 0 | 8.78 | 11866 | True |
| B_atmost_dist_p7 | atmost_dist | 7 | - | OPTIMAL | 7 | 1206.01 | 27 | 1206.01 | 0 | 26.90 | 23739 | True |
| B_b_teams_p7 | b_teams | 7 | - | OPTIMAL | 7 | 2168.90 | 23 | 23 | 0 | 12.16 | 3128 | True |
| B_c_eps_p7_eps23 | c_eps | 7 | 23 | OPTIMAL | 7 | 1616.41 | 23 | 1616.41 | 0 | 477.09 | 418230 | True |
| B_c_eps_p7_eps24 | c_eps | 7 | 24 | TIME_LIMIT | 7 | 1525.88 | 24 | 1470.13 | 0.03654 | 1800.03 | 5184789 | True |
| B_c_eps_p7_eps25 | c_eps | 7 | 25 | OPTIMAL | 7 | 1285.40 | 25 | 1285.40 | 0 | 957.00 | 981601 | True |
| B_screen_p7 | screen | 7 | - | OPTIMAL | 7 | 1206.01 | 26 | 1206.01 | 0 | 8.75 | 11866 | True |
| B_screen_p8 | screen | 8 | - | OPTIMAL | 8 | 1076.31 | 29 | 1076.31 | 0 | 1.94 | 1969 | True |
| B_a_dist_p9 | a_dist | 9 | - | OPTIMAL | 9 | 1042.58 | 33 | 1042.58 | 0 | 1.55 | 1033 | True |
| B_atmost_dist_p9 | atmost_dist | 9 | - | OPTIMAL | 9 | 1042.58 | 33 | 1042.58 | 0 | 2.21 | 1192 | True |
| B_b_teams_p9 | b_teams | 9 | - | TIME_LIMIT | 9 | 2205.66 | 24 | 23 | 0.04167 | 1800.06 | 997749 | True |
| B_c_eps_p9_eps24 | c_eps | 9 | 24 | TIME_LIMIT | 9 | 1453.46 | 24 | 1301.55 | 0.1045 | 11132.22 | 693865 | True |
| B_c_eps_p9_eps25 | c_eps | 9 | 25 | TIME_LIMIT | 9 | 1291.84 | 25 | 1154.55 | 0.1063 | 1800.04 | 1361524 | True |
| B_c_eps_p9_eps26 | c_eps | 9 | 26 | OPTIMAL | 9 | 1114.55 | 26 | 1114.55 | 0 | 898.37 | 539392 | True |
| B_c_eps_p9_eps27 | c_eps | 9 | 27 | OPTIMAL | 9 | 1065.42 | 27 | 1065.42 | 0 | 68.71 | 41057 | True |
| B_c_eps_p9_eps28 | c_eps | 9 | 28 | OPTIMAL | 9 | 1056.57 | 28 | 1056.57 | 0 | 16.41 | 14355 | True |
| B_c_eps_p9_eps29 | c_eps | 9 | 29 | OPTIMAL | 9 | 1046.04 | 29 | 1046.04 | 0 | 2.53 | 2108 | True |
| B_c_eps_p9_eps30 | c_eps | 9 | 30 | OPTIMAL | 9 | 1042.58 | 30 | 1042.58 | 0 | 2.31 | 522 | True |
| B_screen_p9 | screen | 9 | - | OPTIMAL | 9 | 1042.58 | 33 | 1042.58 | 0 | 1.45 | 1033 | True |
| B_a_dist_p10 | a_dist | 10 | - | OPTIMAL | 10 | 1035.88 | 33 | 1035.88 | 0 | 1.48 | 1037 | True |
| B_atmost_dist_p10 | atmost_dist | 10 | - | OPTIMAL | 10 | 1035.88 | 34 | 1035.88 | 0 | 1.57 | 1292 | True |
| B_b_teams_p10 | b_teams | 10 | - | TIME_LIMIT | 10 | 2445.01 | 24 | 23 | 0.04167 | 1800.04 | 426989 | True |
| B_c_eps_p10_eps24 | c_eps | 10 | 24 | TIME_LIMIT | 10 | 1813.85 | 24 | 1343.09 | 0.2595 | 1800.05 | 1711986 | True |
| B_c_eps_p10_eps25 | c_eps | 10 | 25 | TIME_LIMIT | 10 | 1381.17 | 25 | 1185.68 | 0.1415 | 1800.10 | 1712283 | True |
| B_c_eps_p10_eps26 | c_eps | 10 | 26 | TIME_LIMIT | 10 | 1137.51 | 26 | 1122.83 | 0.01291 | 1800.06 | 1434477 | True |
| B_c_eps_p10_eps27 | c_eps | 10 | 27 | OPTIMAL | 10 | 1073.76 | 27 | 1073.76 | 0 | 88.45 | 84827 | True |
| B_c_eps_p10_eps28 | c_eps | 10 | 28 | OPTIMAL | 10 | 1058.80 | 28 | 1058.80 | 0 | 32.30 | 26554 | True |
| B_c_eps_p10_eps29 | c_eps | 10 | 29 | OPTIMAL | 10 | 1051.01 | 29 | 1051.01 | 0 | 21.19 | 27195 | True |
| B_c_eps_p10_eps30 | c_eps | 10 | 30 | OPTIMAL | 10 | 1042.29 | 30 | 1042.29 | 0 | 3.15 | 5087 | True |
| B_c_eps_p10_eps31 | c_eps | 10 | 31 | OPTIMAL | 10 | 1035.88 | 31 | 1035.88 | 0 | 1.21 | 681 | True |
| B_screen_p10 | screen | 10 | - | OPTIMAL | 10 | 1035.88 | 33 | 1035.88 | 0 | 1.24 | 1037 | True |

## Soluciones no dominadas (puntos abiertos, distancia, equipos)

### Instancia A: 9 puntos no dominados distintos, 15 corridas dominadas

| run_id | n_open | total_distance | total_teams | status |
|---|---|---|---|---|
| A_c_eps_p4_eps14 | 4 | 2088.75 | 14 | OPTIMAL |
| A_c_eps_p4_eps15 | 4 | 1138 | 15 | OPTIMAL |
| A_screen_p4 | 4 | 1096.56 | 16 | OPTIMAL |
| A_screen_p5 | 5 | 999.76 | 19 | OPTIMAL |
| A_screen_p6 | 6 | 945.30 | 23 | OPTIMAL |
| A_c_eps_p7_eps15 | 7 | 1014.75 | 15 | OPTIMAL |
| A_c_eps_p7_eps16 | 7 | 913.13 | 16 | OPTIMAL |
| A_c_eps_p7_eps18 | 7 | 913.05 | 18 | OPTIMAL |
| A_atmost_dist_p10 | 8 | 893.82 | 23 | OPTIMAL |

Corridas dominadas:

| run_id | n_open | total_distance | total_teams | dominada_por |
|---|---|---|---|---|
| A_b_teams_p4 | 4 | 2622.44 | 14 | A_c_eps_p4_eps14 |
| A_b_teams_p7 | 7 | 2666.33 | 15 | A_b_teams_p4 |
| A_atmost_dist_p7 | 7 | 913.05 | 20 | A_c_eps_p7_eps18 |
| A_screen_p7 | 7 | 913.05 | 23 | A_c_eps_p7_eps18 |
| A_a_dist_p7 | 7 | 913.05 | 23 | A_c_eps_p7_eps18 |
| A_screen_p8 | 8 | 893.82 | 24 | A_atmost_dist_p10 |
| A_screen_p9 | 9 | 908.08 | 25 | A_screen_p8 |
| A_c_eps_p10_eps15 | 10 | 1233.12 | 15 | A_c_eps_p4_eps15 |
| A_b_teams_p10 | 10 | 2373.40 | 15 | A_c_eps_p4_eps14 |
| A_c_eps_p10_eps16 | 10 | 969.28 | 16 | A_c_eps_p7_eps16 |
| A_c_eps_p10_eps17 | 10 | 959.80 | 17 | A_c_eps_p7_eps16 |
| A_c_eps_p10_eps18 | 10 | 955.67 | 18 | A_c_eps_p7_eps16 |
| A_c_eps_p10_eps19 | 10 | 951.39 | 19 | A_c_eps_p7_eps16 |
| A_screen_p10 | 10 | 951.39 | 25 | A_screen_p6 |
| A_a_dist_p10 | 10 | 951.39 | 25 | A_screen_p6 |

### Instancia B: 13 puntos no dominados distintos, 17 corridas dominadas

| run_id | n_open | total_distance | total_teams | status |
|---|---|---|---|---|
| B_c_eps_p7_eps23 | 7 | 1616.41 | 23 | OPTIMAL |
| B_c_eps_p7_eps24 | 7 | 1525.88 | 24 | TIME_LIMIT |
| B_c_eps_p7_eps25 | 7 | 1285.40 | 25 | OPTIMAL |
| B_screen_p7 | 7 | 1206.01 | 26 | OPTIMAL |
| B_screen_p8 | 8 | 1076.31 | 29 | OPTIMAL |
| B_c_eps_p9_eps24 | 9 | 1453.46 | 24 | TIME_LIMIT |
| B_c_eps_p9_eps26 | 9 | 1114.55 | 26 | OPTIMAL |
| B_c_eps_p9_eps27 | 9 | 1065.42 | 27 | OPTIMAL |
| B_c_eps_p9_eps28 | 9 | 1056.57 | 28 | OPTIMAL |
| B_c_eps_p9_eps29 | 9 | 1046.04 | 29 | OPTIMAL |
| B_c_eps_p9_eps30 | 9 | 1042.58 | 30 | OPTIMAL |
| B_c_eps_p10_eps30 | 10 | 1042.29 | 30 | OPTIMAL |
| B_c_eps_p10_eps31 | 10 | 1035.88 | 31 | OPTIMAL |

Corridas dominadas:

| run_id | n_open | total_distance | total_teams | dominada_por |
|---|---|---|---|---|
| B_b_teams_p7 | 7 | 2168.90 | 23 | B_c_eps_p7_eps23 |
| B_atmost_dist_p7 | 7 | 1206.01 | 27 | B_screen_p7 |
| B_b_teams_p9 | 9 | 2205.66 | 24 | B_b_teams_p7 |
| B_c_eps_p9_eps25 | 9 | 1291.84 | 25 | B_c_eps_p7_eps25 |
| B_screen_p9 | 9 | 1042.58 | 33 | B_c_eps_p9_eps30 |
| B_a_dist_p9 | 9 | 1042.58 | 33 | B_c_eps_p9_eps30 |
| B_atmost_dist_p9 | 9 | 1042.58 | 33 | B_c_eps_p9_eps30 |
| B_c_eps_p10_eps24 | 10 | 1813.85 | 24 | B_c_eps_p7_eps23 |
| B_b_teams_p10 | 10 | 2445.01 | 24 | B_b_teams_p7 |
| B_c_eps_p10_eps25 | 10 | 1381.17 | 25 | B_c_eps_p7_eps25 |
| B_c_eps_p10_eps26 | 10 | 1137.51 | 26 | B_c_eps_p9_eps26 |
| B_c_eps_p10_eps27 | 10 | 1073.76 | 27 | B_c_eps_p9_eps27 |
| B_c_eps_p10_eps28 | 10 | 1058.80 | 28 | B_c_eps_p9_eps28 |
| B_c_eps_p10_eps29 | 10 | 1051.01 | 29 | B_c_eps_p9_eps29 |
| B_screen_p10 | 10 | 1035.88 | 33 | B_c_eps_p10_eps31 |
| B_a_dist_p10 | 10 | 1035.88 | 33 | B_c_eps_p10_eps31 |
| B_atmost_dist_p10 | 10 | 1035.88 | 34 | B_screen_p10 |

## Exactamente p vs a lo sumo p (min distancia)

| instancia | p | exacto_estado | exacto_abiertos | exacto_distancia | exacto_equipos | alosumo_estado | alosumo_abiertos | alosumo_distancia | alosumo_equipos | alosumo_tiempo_s | exacto_tiempo_s |
|---|---|---|---|---|---|---|---|---|---|---|---|
| A | 4 | OPTIMAL | 4 | 1096.56 | 16 | OPTIMAL | 4 | 1096.56 | 16 | 0.472 | 0.53 |
| A | 7 | OPTIMAL | 7 | 913.05 | 23 | OPTIMAL | 7 | 913.05 | 20 | 0.043 | 0.045 |
| A | 10 | OPTIMAL | 10 | 951.39 | 25 | OPTIMAL | 8 | 893.82 | 23 | 0.037 | 2.52 |
| B | 7 | OPTIMAL | 7 | 1206.01 | 26 | OPTIMAL | 7 | 1206.01 | 27 | 26.90 | 8.78 |
| B | 9 | OPTIMAL | 9 | 1042.58 | 33 | OPTIMAL | 9 | 1042.58 | 33 | 2.21 | 1.55 |
| B | 10 | OPTIMAL | 10 | 1035.88 | 33 | OPTIMAL | 10 | 1035.88 | 34 | 1.57 | 1.48 |

## Curva épsilon y distancia adicional por equipo reducido

### Instancia A

| instancia | p | equipos | distancia | run_id | estado | equipos_S1 | equipos_S2 | equipos_S3 | equipos_S4 | dist_extra_por_equipo_reducido |
|---|---|---|---|---|---|---|---|---|---|---|
| A | 4 | 14 | 2088.75 | A_c_eps_p4_eps14 | OPTIMAL | 4 | 4 | 3 | 3 | 950.75 |
| A | 4 | 15 | 1138 | A_c_eps_p4_eps15 | OPTIMAL | 3 | 4 | 4 | 4 | 41.44 |
| A | 4 | 16 | 1096.56 | A_a_dist_p4 | OPTIMAL | 4 | 4 | 4 | 4 | - |
| A | 7 | 15 | 1014.75 | A_c_eps_p7_eps15 | OPTIMAL | 3 | 4 | 4 | 4 | 101.62 |
| A | 7 | 16 | 913.13 | A_c_eps_p7_eps16 | OPTIMAL | 4 | 4 | 4 | 4 | 0.04 |
| A | 7 | 18 | 913.05 | A_c_eps_p7_eps18 | OPTIMAL | 4 | 5 | 5 | 4 | - |
| A | 10 | 15 | 1233.12 | A_c_eps_p10_eps15 | TIME_LIMIT | 3 | 4 | 4 | 4 | 263.84 |
| A | 10 | 16 | 969.28 | A_c_eps_p10_eps16 | OPTIMAL | 4 | 4 | 4 | 4 | 9.48 |
| A | 10 | 17 | 959.80 | A_c_eps_p10_eps17 | OPTIMAL | 4 | 4 | 5 | 4 | 4.13 |
| A | 10 | 18 | 955.67 | A_c_eps_p10_eps18 | OPTIMAL | 4 | 5 | 5 | 4 | 4.28 |
| A | 10 | 19 | 951.39 | A_c_eps_p10_eps19 | OPTIMAL | 4 | 5 | 5 | 5 | - |

### Instancia B

| instancia | p | equipos | distancia | run_id | estado | equipos_S1 | equipos_S2 | equipos_S3 | equipos_S4 | dist_extra_por_equipo_reducido |
|---|---|---|---|---|---|---|---|---|---|---|
| B | 7 | 23 | 1616.41 | B_c_eps_p7_eps23 | OPTIMAL | 6 | 6 | 6 | 5 | 90.53 |
| B | 7 | 24 | 1525.88 | B_c_eps_p7_eps24 | TIME_LIMIT | 7 | 6 | 6 | 5 | 240.48 |
| B | 7 | 25 | 1285.40 | B_c_eps_p7_eps25 | OPTIMAL | 6 | 7 | 7 | 5 | 79.39 |
| B | 7 | 26 | 1206.01 | B_a_dist_p7 | OPTIMAL | 7 | 7 | 7 | 5 | - |
| B | 9 | 24 | 1453.46 | B_c_eps_p9_eps24 | TIME_LIMIT | 6 | 6 | 7 | 5 | 161.62 |
| B | 9 | 25 | 1291.84 | B_c_eps_p9_eps25 | TIME_LIMIT | 7 | 6 | 7 | 5 | 177.29 |
| B | 9 | 26 | 1114.55 | B_c_eps_p9_eps26 | OPTIMAL | 7 | 7 | 7 | 5 | 49.13 |
| B | 9 | 27 | 1065.42 | B_c_eps_p9_eps27 | OPTIMAL | 7 | 8 | 7 | 5 | 8.85 |
| B | 9 | 28 | 1056.57 | B_c_eps_p9_eps28 | OPTIMAL | 7 | 8 | 8 | 5 | 10.53 |
| B | 9 | 29 | 1046.04 | B_c_eps_p9_eps29 | OPTIMAL | 7 | 9 | 8 | 5 | 3.46 |
| B | 9 | 30 | 1042.58 | B_c_eps_p9_eps30 | OPTIMAL | 7 | 9 | 8 | 6 | - |
| B | 10 | 24 | 1813.85 | B_c_eps_p10_eps24 | TIME_LIMIT | 7 | 6 | 6 | 5 | 432.68 |
| B | 10 | 25 | 1381.17 | B_c_eps_p10_eps25 | TIME_LIMIT | 7 | 6 | 7 | 5 | 243.66 |
| B | 10 | 26 | 1137.51 | B_c_eps_p10_eps26 | TIME_LIMIT | 7 | 7 | 7 | 5 | 63.75 |
| B | 10 | 27 | 1073.76 | B_c_eps_p10_eps27 | OPTIMAL | 7 | 8 | 7 | 5 | 14.96 |
| B | 10 | 28 | 1058.80 | B_c_eps_p10_eps28 | OPTIMAL | 8 | 8 | 7 | 5 | 7.79 |
| B | 10 | 29 | 1051.01 | B_c_eps_p10_eps29 | OPTIMAL | 8 | 8 | 8 | 5 | 8.72 |
| B | 10 | 30 | 1042.29 | B_c_eps_p10_eps30 | OPTIMAL | 7 | 9 | 8 | 6 | 6.41 |
| B | 10 | 31 | 1035.88 | B_c_eps_p10_eps31 | OPTIMAL | 8 | 9 | 8 | 6 | - |
