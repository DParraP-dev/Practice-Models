# Análisis e interpretación de resultados

Este documento interpreta `resultados.csv` y `soluciones.json` (67 corridas) y responde lo que pide el documento guía en 4.3.3, 4.3.4 y 4.4 (secciones 3 a 7 del informe). Las tablas y figuras citadas están en `resultados/informe/` y se regeneran con `report_analysis.py`. Las pruebas de diagnóstico de las preguntas 6(a) y 6(b) se reproducen con `diagnostico_reglas.py` (menos de 1 s por prueba; salida en `resultados/diagnostico_reglas.csv`).

Las 58 corridas con solución (27 de A y 31 de B; las otras 9 son infactibles) pasaron la verificación independiente de R1–R5, y el objetivo recalculado coincide con el del solver en todas.

---

## 1. Diseño experimental realizado (sección 4 del informe)

**Hardware y software** (de `entorno.json`): Windows 11, procesador Intel de 4 núcleos físicos y 8 lógicos (Family 6 Model 142, identificador de un Intel de 8.ª–10.ª generación serie U; conviene copiar el nombre exacto del modelo desde *Configuración > Sistema > Información*), 7.8 GB de RAM, Python 3.14.2, Gurobi 13.0.3 con licencia académica.

**Parámetros del solver**: `TimeLimit = 1800 s`, `MIPGap = 0`, `Threads = 0` (Gurobi decide). El cribado usó 60 s por corrida.

**Corridas** (todas con "exactamente p" salvo la última fila):

| Experimento | Instancia A | Instancia B |
|---|---|---|
| Cribado, min distancia, p = 1..10 | 10 | 10 |
| p estudiados a fondo | 4, 7, 10 | 7, 9, 10 |
| (a) min distancia | 3 | 3 |
| (b) min equipos | 3 | 3 |
| (c) ε-restricción | 11 | 18 |
| min distancia, a lo sumo p | 3 | 3 |
| **Total / tiempo de cómputo** | **30 corridas / 0.62 h** | **37 corridas / 7.32 h** |

Los 3 valores de p de cada instancia se eligieron con el cribado: el menor p factible, el mayor y uno intermedio. En ε-restricción se usaron los ε enteros desde el resultado de (b) hasta el de (a) − 1, y la curva se detuvo cuando alcanzó la distancia óptima de (a).

**Anomalía que hay que mencionar en el informe.** La corrida `B_c_eps_p9_eps24` registra 11 132 s (3.1 h) aunque el límite era 1800 s. Gurobi mide tiempo de reloj, así que la causa más probable es que el computador entró en suspensión durante la corrida. La solución y la cota siguen siendo válidas, pero su tiempo no es comparable con el de las demás. Si se cuenta como 1800 s, el tiempo total de B baja a 4.73 h. Para repetirla, borre su fila del CSV y vuelva a ejecutar `satellite_MILP.py` con `RESUME = True`.

---

## 2. Descripción de las instancias (sección 3 del informe)

Fuente: `estadisticas_instancias.csv`, `espacial_instancias.csv`, `cotas_capacidad.csv`, `mapa_instancia_A.png`, `mapa_instancia_B.png`.

| | Instancia A | Instancia B |
|---|---|---|
| Demanda semanal total S1 / S2 / S3 / S4 | 468 / 520 / 519 / 480 | 699 / 446 / 243 / 119 |
| Coef. de variación de la demanda por nodo | 0.30 – 0.33 | 0.68 – 0.88 |
| Nodos con demanda 0 (S1 / S2 / S3 / S4) | ninguno | 12 / 8 / 4 / 7 |
| Rango de Q diaria por disciplina | entre 19 y 31 en todas | S1 4–28, S2 3–23, S3 2–19, S4 2–7 |
| Coef. de variación de Q | 0.10 – 0.14 | 0.36 – 0.72 |
| Holgura (capacidad semanal de los 10 candidatos / demanda) | 2.90 – 3.22 | 1.47 – 2.12 |
| Pares nodo–candidato imposibles (w > 6Q) | 0 | 19 (en j4, j5, j7, j8) |
| Índice de Clark–Evans de los nodos | 1.08 (distribución uniforme) | 0.74 (agrupada) |
| Distancia media al vecino más cercano | 7.39 | 4.16 |
| Cota inferior de distancia (cada nodo a su candidato más cercano) | 893.82 | 773.15 |
| p mínimo por capacidad total, disciplina por disciplina | 4 (lo fija S2) | 5 (lo fijan S1 y S2) |
| p mínimo por capacidad total, las 4 disciplinas a la vez | 4 | 6 |

La holgura de la tabla usa los 10 candidatos. El campo `target_capacity_ratio` del JSON (1.5 en A y 1.25 en B) se refiere a los 5 y 8 candidatos originales, antes de la extensión.

Lectura: A es homogénea en todo (demanda, capacidad y ubicación) y tiene capacidad de sobra. B tiene menos holgura, demanda muy dispareja con nodos grandes (i15 pide 52 atenciones semanales de S1) y una capacidad mal repartida entre disciplinas: j5 tiene Q = 28 en S1 pero Q = 2 en S3, y j7 tiene Q = 4 en S1 pero Q = 20 en S2.

---

## 3. Resultados (sección 5 del informe)

Figuras: `p_vs_distancia_A.png`, `p_vs_distancia_B.png`, `distancia_vs_equipos_A.png`, `distancia_vs_equipos_B.png`, `tiempo_vs_p.png`, mapas `mapa_solucion_*.png` y calendarios `calendario_*.png`. Las tablas completas por corrida están en `tabla_resultados_A.csv` y `tabla_resultados_B.csv`.

### 3.1 Min distancia con exactamente p, para p = 1..10 (cribado)

Todas las corridas factibles terminaron en el óptimo. Los equipos de esta tabla no se optimizaron (ver 6e).

| p | A distancia | A equipos | B distancia | B equipos |
|---|---|---|---|---|
| 1–3 | infactible | – | infactible | – |
| 4 | 1096.56 | 16 | infactible | – |
| 5 | 999.76 | 19 | infactible | – |
| 6 | 945.30 | 23 | infactible | – |
| 7 | 913.05 | 23 | 1206.01 | 26 |
| 8 | **893.82** | 24 | 1076.31 | 29 |
| 9 | 908.08 | 25 | 1042.58 | 33 |
| 10 | 951.39 | 25 | **1035.88** | 33 |

### 3.2 Experimentos completos por p

"TL" significa que la corrida llegó al límite de tiempo. En ese caso la distancia es la mejor encontrada y el gap indica cuánto podría mejorar. En la columna (c), un número entre paréntesis indica los equipos reales cuando son menos que ε.

**Instancia A**

| p | (a) min distancia | (b) min equipos | (c) ε → distancia (equipos reales) | a lo sumo p |
|---|---|---|---|---|
| 4 | 1096.56 / 16 eq | 14 eq / 2622.44 | 14 → 2088.75; 15 → 1138.00 | 1096.56 / 16 eq, abre 4 |
| 7 | 913.05 / 23 eq | 15 eq / 2666.33 | 15 → 1014.75; 16 → 913.13; 17 → 913.13 (16); 18 → 913.05 | 913.05 / 20 eq, abre 7 |
| 10 | 951.39 / 25 eq | 15 eq / 2373.40 | 15 → 1233.12 (TL, gap 4.9 %); 16 → 969.28; 17 → 959.80; 18 → 955.67; 19 → 951.39 | 893.82 / 23 eq, **abre 8** |

**Instancia B**

| p | (a) min distancia | (b) min equipos | (c) ε → distancia | a lo sumo p |
|---|---|---|---|---|
| 7 | 1206.01 / 26 eq | 23 eq / 2168.90 | 23 → 1616.41; 24 → 1525.88 (TL, 3.7 %); 25 → 1285.40 | 1206.01 / 27 eq |
| 9 | 1042.58 / 33 eq | 24 eq / 2205.66 (TL, cota 23) | 24 → 1453.46 (TL, 10.5 %); 25 → 1291.84 (TL, 10.6 %); 26 → 1114.55; 27 → 1065.42; 28 → 1056.57; 29 → 1046.04; 30 → 1042.58 | 1042.58 / 33 eq |
| 10 | 1035.88 / 33 eq | 24 eq / 2445.01 (TL, cota 23) | 24 → 1813.85 (TL, 26.0 %); 25 → 1381.17 (TL, 14.2 %); 26 → 1137.51 (TL, 1.3 %); 27 → 1073.76; 28 → 1058.80; 29 → 1051.01; 30 → 1042.29; 31 → 1035.88 | 1035.88 / 34 eq |

Las soluciones de (b) tienen distancias muy altas porque, al minimizar solo equipos, la distancia queda libre. Con el mismo número de equipos, ε-restricción encuentra distancias mucho menores: en A con p = 7 y 15 equipos, (b) da 2666.33 y ε = 15 da 1014.75.

---

## 4. Soluciones no dominadas con los tres objetivos (actividad 4.3.3)

Fuente: `no_dominadas_A.csv`, `no_dominadas_B.csv`. Se comparan todas las corridas con solución de cada instancia en (puntos abiertos, distancia, equipos), los tres minimizados.

**Instancia A: 9 puntos no dominados distintos; 15 corridas dominadas.**

| Puntos | Distancia | Equipos | Corrida |
|---|---|---|---|
| 4 | 2088.75 | 14 | A_c_eps_p4_eps14 |
| 4 | 1138.00 | 15 | A_c_eps_p4_eps15 |
| 4 | 1096.56 | 16 | A_a_dist_p4 |
| 5 | 999.76 | 19 | A_screen_p5 |
| 6 | 945.30 | 23 | A_screen_p6 |
| 7 | 1014.75 | 15 | A_c_eps_p7_eps15 |
| 7 | 913.13 | 16 | A_c_eps_p7_eps16 |
| 7 | 913.05 | 18 | A_c_eps_p7_eps18 |
| 8 | 893.82 | 23 | A_atmost_dist_p10 |

Corridas dominadas en A:

- **Todas las soluciones con p = 9 y p = 10.** Por ejemplo, (10, 951.39, 19) está dominada por (7, 913.13, 16).
- La solución de (a) con p = 7, (7, 913.05, 23), está dominada por (7, 913.05, 18): la misma distancia con 5 equipos menos.
- Las tres corridas de (b).

**Instancia B: 13 puntos no dominados distintos; 17 corridas dominadas.**

| Puntos | Distancia | Equipos | Corrida |
|---|---|---|---|
| 7 | 1616.41 | 23 | B_c_eps_p7_eps23 |
| 7 | 1525.88 | 24 | B_c_eps_p7_eps24 (TL) |
| 7 | 1285.40 | 25 | B_c_eps_p7_eps25 |
| 7 | 1206.01 | 26 | B_a_dist_p7 |
| 8 | 1076.31 | 29 | B_screen_p8 |
| 9 | 1453.46 | 24 | B_c_eps_p9_eps24 (TL) |
| 9 | 1114.55 | 26 | B_c_eps_p9_eps26 |
| 9 | 1065.42 | 27 | B_c_eps_p9_eps27 |
| 9 | 1056.57 | 28 | B_c_eps_p9_eps28 |
| 9 | 1046.04 | 29 | B_c_eps_p9_eps29 |
| 9 | 1042.58 | 30 | B_c_eps_p9_eps30 |
| 10 | 1042.29 | 30 | B_c_eps_p10_eps30 |
| 10 | 1035.88 | 31 | B_c_eps_p10_eps31 |

En B casi todas las soluciones con p = 10 están dominadas por soluciones con p = 7 o p = 9. Solo sobreviven dos puntos de p = 10, y mejoran la distancia en menos de 7 unidades.

**Alcance de este conjunto.** Es una aproximación del frente real, por dos razones:

- Para p = 5, 6 y 8 en A y p = 8 en B solo hay corridas de min distancia, sin curva ε. Esos puntos probablemente admiten menos equipos con la misma distancia, como pasó con p = 7 en A.
- Las corridas con TL dan solo una cota superior de la distancia.

---

## 5. Análisis de resultados (sección 6 del informe)

### (a) ¿Para qué p es infactible? ¿Basta la cota de capacidad total?

- **A: infactible para p = 1, 2, 3.** La cota de capacidad total lo explica por completo. S2 pide 520 atenciones semanales, y los 3 candidatos con más capacidad de S2 (Q = 29, 29, 27) ofrecen 6 × 85 = 510 < 520. Con p = 4 el modelo ya es factible.
- **B: infactible para p = 1 a 6.** La cota de capacidad total solo explica hasta p = 5:
  - Disciplina por disciplina, S1 y S2 necesitan 5 puntos. Los 4 mejores candidatos de S1 ofrecen 6 × 100 = 600 < 699.
  - Ningún subconjunto de 5 candidatos cubre las 4 disciplinas a la vez.
  - Para p = 6 sí hay 4 subconjuntos que cubren la capacidad total de las 4 disciplinas, por ejemplo {j1, j2, j3, j4, j5, j6}. Aun así, el problema es infactible.

  **Respuesta: en B no basta la cota de capacidad total.** `diagnostico_reglas.py` aísla la causa de p = 6:
  1. Quitar R3 y R4: sigue infactible. Los días mínimos y la cobertura de los 6 días no son la causa.
  2. Permitir que la demanda de un nodo se reparta entre varios puntos, pero con el mismo reparto en sus 4 disciplinas: sigue infactible con p = 6 y es factible con p = 7.

  La causa es que **cada nodo lleva sus 4 disciplinas juntas a un único punto** (decisión b y R1), mientras que en B la capacidad de cada sede está repartida de forma muy desigual entre disciplinas. Un punto con mucha capacidad en S1 y muy poca en S3 (j5) no puede recibir nodos suficientes para aprovechar su S1 sin saturar su S3. Por eso la capacidad que suma la cota no se puede usar entera. La indivisibilidad de los nodos no es necesaria para explicar la infactibilidad: el modelo sigue infactible incluso con demanda divisible.
- En ninguna instancia aparece infactibilidad con p grande: p = 10 es factible en las dos.

### (b) ¿Cómo varía la distancia con p? ¿Es no creciente?

- **B: no creciente con rendimientos decrecientes**: 1206.01 → 1076.31 → 1042.58 → 1035.88. Las mejoras son −129.7, −33.7 y −6.7. Con capacidad ajustada, cada punto nuevo alivia la capacidad. El valor de p = 10 sigue lejos de la cota de 773.15 (todos al candidato más cercano) porque la capacidad no permite esa asignación.
- **A: no es monótona.** Baja hasta p = 8 (−96.8, −54.5, −32.3, −19.2) y luego sube: 908.08 con p = 9 y 951.39 con p = 10.
  - Con p = 8 la distancia es 893.82, que coincide con la cota "cada nodo a su candidato más cercano". Esa asignación usa exactamente 8 candidatos; j3 y j9 no son los más cercanos de ningún nodo.
  - Con p = 9 y p = 10, "exactamente p" obliga a abrir j3 y j9, y cada punto abierto necesita al menos 6 días-disciplina (R4). R3 prohíbe programar días de más, así que la única forma de llenar esos días es asignarle demanda: Σₛ ⌈Dⱼₛ/Qⱼₛ⌉ ≥ 6.
  - En A la demanda de un nodo por disciplina es como máximo 15 y toda Q es al menos 19, así que un solo nodo genera 1 día por disciplina, es decir 4 días. Por eso cada punto nuevo necesita al menos 2 nodos (en la práctica 2 o 3), que se quitan a puntos más cercanos.
  - En `A_a_dist_p10` hay 4 puntos con exactamente 6 días, el mínimo de R4, con 2 o 3 nodos cada uno.

  `diagnostico_reglas.py` confirma la causa: sin R3, o sin R4, la distancia con p = 9 y p = 10 vuelve a 893.82. **La no monotonía la produce la combinación de R3 (días mínimos) con R4 (atención los 6 días), bajo "exactamente p".**

### (c) Exactamente p frente a a lo sumo p

Fuente: `exacto_vs_alosumo.csv`.

- "A lo sumo p" es una relajación de "exactamente p", así que su distancia nunca es mayor. La curva de "a lo sumo p" es la envolvente inferior de la otra y siempre es no creciente.
- **En B coinciden** las distancias para p = 7, 9 y 10, porque la distancia de "exactamente p" ya es decreciente.
- **En A difieren para p = 10.** "A lo sumo 10" abre solo 8 puntos y logra 893.82, contra 951.39 de "exactamente 10" (−6.1 %). Para p = 4 y p = 7 coinciden.
- El número de equipos cambia sin patrón entre las dos variantes (A p = 7: 20 contra 23; B p = 7: 27 contra 26), porque ninguna de las dos lo optimiza.
- El tiempo es parecido. "A lo sumo 10" en A fue más rápido (0.04 s contra 2.5 s) porque no tiene que forzar la apertura de j3 y j9. "A lo sumo 7" en B fue más lento (26.9 s contra 8.8 s).
- Interpretación para la entidad: en A abrir más de 8 puntos empeora la distancia y los equipos. Con "a lo sumo p" el modelo lo descubre solo, mientras que "exactamente p" obliga a operar puntos que no aportan.

### (d) ¿Qué instancia es más difícil y por qué?

**B es claramente más difícil.**

| | A | B |
|---|---|---|
| Corridas que llegaron al límite de tiempo | 1 de 30 (gap 4.9 %) | 8 de 37 (gaps de 1.3 % a 26.0 %) |
| Tiempo total | 0.62 h | 7.32 h (4.73 h sin la anomalía) |
| Nodos máximos del árbol | 2.9 millones | 5.2 millones |
| Mínimo de equipos demostrado | sí, en los 3 p | solo con p = 7; con p = 9 y 10 queda 24 con cota 23 |

La dificultad está en el objetivo de equipos, no en la distancia. Minimizar distancia tarda menos de 3.5 s en A (casi siempre en el nodo raíz) y menos de 27 s en B. Las corridas difíciles son las de (b) y las de ε con el ε más bajo. En A las únicas lentas también son las de ε mínimo: 174 s con p = 4, 159 s con p = 7 y TL con p = 10.

Por qué cuesta el objetivo de equipos: el número de equipos de una disciplina es, en una buena programación, ⌈(Σⱼ ⌈Dⱼₛ/Qⱼₛ⌉) / 6⌉. Es un doble redondeo hacia arriba. Esa igualdad se cumple exactamente en las 6 soluciones de (b). La relajación lineal de ese doble redondeo es muy débil: bajar un equipo exige quitar días justo en la disciplina y en los puntos donde un cambio de asignación cruza un múltiplo de Q, y hay muchas asignaciones casi equivalentes.

Características de B que agravan esto:

- **Poca holgura** (1.47–2.12 contra 2.90–3.22) y **19 pares imposibles**: muchas asignaciones están al límite y casi todos los cambios de un nodo rompen R2 en algún punto.
- **Capacidades pequeñas y dispares** (Q de 2 a 7 en S3 y S4): un nodo mueve varios días de golpe y el redondeo pesa más.
- **Demanda heterogénea con ceros** (CV 0.68–0.88): nodos grandes como i15 (52 en S1) solo caben en pocos puntos y fijan buena parte de la solución.
- **Distribución agrupada** (Clark–Evans 0.74): dentro de cada cluster muchos candidatos están a distancias parecidas, lo que crea muchas soluciones de distancia similar y un árbol de búsqueda grande.
- **Más equipos** (23–36 contra 14–25): más combinaciones de días que balancear.

La dificultad también crece con p en B. (b) con p = 7 se resolvió al óptimo en 12 s, y con p = 9 y p = 10 llegó al límite.

### (e) Equipos frente a p, costo de reducir un equipo y disciplinas que concentran equipos

**Cómo cambian los equipos con p.**

- Al minimizar la distancia, los equipos suben con p: en A de 16 (p = 4) a 25 (p = 10), y en B de 26 (p = 7) a 33 (p = 9 y 10).
- Parte de ese aumento es artificial, porque (a) no optimiza equipos. Con p = 7 en A, (a) reporta 23 equipos, pero ε encuentra la misma distancia (913.05) con 18 equipos y 913.13 con 16.
- El mínimo de equipos sube poco con p: en A 14 (p = 4) y 15 (p = 7 y 10); en B 23 (p = 7) y 24 encontrados con cota 23 (p = 9 y 10).
- La razón es que cada punto adicional redondea hacia arriba los días de cada disciplina, y en A además R4 obliga a cada punto a tener al menos 6 días-disciplina. Repartir la misma demanda en más puntos suma más días, y por lo tanto más equipos.

**Distancia adicional por equipo reducido** (fuente: `costo_por_equipo_A.csv`, `costo_por_equipo_B.csv`; cada fila es un paso de la curva ε):

| Instancia, p | Paso | Distancia adicional |
|---|---|---|
| A, 7 | 23 → 16 equipos | **+0.08 en total** (prácticamente gratis) |
| A, 7 | 16 → 15 | +101.6 |
| A, 4 | 16 → 15 | +41.4 |
| A, 4 | 15 → 14 | +950.8 |
| A, 10 | 25 → 16 | +17.9 en total (4 a 9 por equipo) |
| A, 10 | 16 → 15 | entre +202.9 y +263.8 (TL) |
| B, 7 | 26 → 25 | +79.4 |
| B, 7 | 25 → 23 | +331.0 en total (el paso 24 tiene TL) |
| B, 9 | 33 → 27 | +22.8 en total (unos 4 por equipo) |
| B, 9 | 27 → 26 | +49.1 |
| B, 9 | 26 → 25 | entre +40 y +177 (TL) |
| B, 10 | 33 → 27 | +37.9 en total |
| B, 10 | 27 → 26 | entre +49 y +64 (TL) |

Patrón: las curvas tienen un codo. Los primeros equipos se eliminan casi sin costo, solo balanceando mejor los días entre la semana. Pasado el codo, cada equipo cuesta entre 40 y 950 unidades de distancia, porque ya hay que reasignar nodos para reducir días. El codo está en 16 equipos en A (p = 7 y 10) y en 26–27 equipos en B (p = 9 y 10).

**Disciplinas que concentran los equipos.**

- En A los equipos se reparten casi por igual: 4/4/4/4 en la solución de compromiso con p = 7. Al minimizar distancia, S2 y S3 reciben uno o dos más, porque tienen la mayor demanda (520 y 519).
- En B, S1, S2 y S3 tienen de 6 a 10 equipos cada una y S4 de 5 a 7, aunque la demanda es muy distinta: 699, 446, 243 y 119.
- Los equipos siguen la relación demanda/capacidad, no la demanda. Con p = 7, S3 atiende 243 pacientes pero necesita 36 a 41 días porque la mayoría de sedes tiene Q de 2 a 9. Eso le da tantos equipos como a S1, que atiende 699 pacientes. S4, con solo 119 pacientes, necesita 28 a 30 días (Q de 2 a 7) y 5 equipos.

### (f) ¿Cómo se reparten los días de atención y reflejan la demanda atendida?

Fuente: `dias_por_punto_A.csv`, `dias_por_punto_B.csv` y los calendarios.

- Por R3, en todas las soluciones los días de cada disciplina en cada punto son exactamente ⌈D/Q⌉. Por eso los días siguen la demanda dividida por la capacidad, no la demanda sola.
- **En A los días sí reflejan la demanda.** Como Q es casi igual en todas las sedes, la correlación entre demanda asignada y días está entre 0.88 y 0.96 por disciplina (con p = 7 y p = 10). Los puntos que atienden más nodos tienen más días.
- **En B los días no reflejan la demanda.** Con p = 7 (solución de min distancia), las correlaciones son 0.18 (S1), −0.57 (S2), −0.86 (S3) y 0.37 (S4). Por ejemplo, j3 atiende 79 pacientes de S3 en 5 días (Q = 19), mientras j5 atiende 12 pacientes de S3 en 6 días (Q = 2). Además, la mayoría de pares punto–disciplina de S1, S2 y S3 están en 6 días, el máximo posible: la capacidad está saturada.
- La utilización de la capacidad programada baja al abrir más puntos, porque cada punto redondea hacia arriba. En A pasa de 0.91–0.97 (p = 4) a 0.82–0.87 (p = 7) y a 0.75–0.82 (p = 10). Algunos puntos pequeños de p = 10 usan apenas el 52 % de lo programado. En B se mantiene entre 0.87 y 0.99 porque la capacidad es escasa.

Conclusión para el informe: la regla de "días mínimos" consigue que la oferta sea proporcional a la demanda *medida en días de capacidad*. Solo cuando las capacidades son parecidas entre sedes (instancia A), eso equivale a ser proporcional al número de pacientes.

### (g) Solución recomendada

La elección depende de cuánto vale abrir un punto frente a un equipo o a una unidad de distancia, y el enunciado no da esos costos. Estas son propuestas justificadas con los datos, para que las ajustes a tu criterio.

**Instancia A: `A_c_eps_p7_eps16`, con 7 puntos (j1, j2, j4, j5, j7, j8, j10), distancia 913.13 y 16 equipos (4 por disciplina).**

- Su distancia está solo 2.2 % por encima del mínimo absoluto (893.82, que exige 8 puntos).
- Usa 2 equipos más que el mínimo absoluto (14). Llegar a 14 equipos cuesta más del doble de distancia (2088.75).
- Bajar a 15 equipos con p = 7 cuesta +101.6.
- Si abrir puntos es lo más costoso, la alternativa es `A_a_dist_p4` (4 puntos, 1096.56, 16 equipos). Abrir 3 puntos más reduce la distancia en 183.4 (16.7 %) con los mismos equipos.
- En cualquier caso no conviene abrir 9 o 10 puntos: esas soluciones están dominadas.
- Mapa y calendario: `mapa_solucion_A_c_eps_p7_eps16.png`, `calendario_A_c_eps_p7_eps16.png`.

**Instancia B: `B_a_dist_p7`, con 7 puntos (j1, j2, j3, j5, j6, j9, j10), distancia 1206.01 y 26 equipos (7/7/7/5).**

- 7 es el mínimo de puntos factible.
- Con 7 puntos, reducir equipos sale caro: +79 por el primero y +410 (+34 %) para llegar al mínimo de 23.
- Si la entidad prioriza la distancia de los pacientes, la alternativa es `B_c_eps_p9_eps27` (9 puntos, 1065.42, 27 equipos): 11.7 % menos distancia a cambio de 2 puntos y 1 equipo más.
- Pasar a 10 puntos casi no aporta: 0.6 % menos distancia que con 9.
- Mapa y calendario: `mapa_solucion_B_a_dist_p7.png`, `calendario_B_a_dist_p7.png` y los de la alternativa.

---

## 6. Conclusiones (sección 7 del informe)

**Hallazgos principales**

1. La formulación es correcta en las 58 soluciones: el verificador independiente confirmó R1–R5 y los tres objetivos. La linealización de R3, Q(n − 1) ≤ D − 1 junto con Qn ≥ D, fija n = ⌈D/Q⌉ sin big-M.
2. La factibilidad depende de cómo está repartida la capacidad, no solo de cuánta hay. En A la cota de capacidad total predice el p mínimo (4). En B no: el p mínimo real es 7, mientras la cota da 6, porque cada nodo lleva sus 4 disciplinas al mismo punto.
3. La distancia no siempre mejora al abrir más puntos. En A empeora para p > 8 por la interacción de R3 con R4. "A lo sumo p" evita ese efecto.
4. Los equipos dependen de los días totales de cada disciplina: ⌈días/6⌉ con una buena programación. Minimizar solo distancia sobreestima los equipos necesarios: en A con p = 7 reporta 23 equipos, y con 16 la distancia sube apenas 0.08. Minimizar solo equipos da distancias de hasta 2.9 veces la mínima (A, p = 7). La curva ε es necesaria para ver el compromiso real.
5. La instancia B es más difícil por la poca holgura, la capacidad dispareja, la demanda heterogénea y el mayor número de equipos. La parte difícil es el objetivo de equipos.

**Limitaciones**

- Solo 3 valores de p por instancia tienen el estudio completo; el frente no dominado es una aproximación.
- 9 corridas terminaron por límite de tiempo, y el mínimo de equipos de B con p = 9 y 10 no quedó demostrado.
- La distancia no se pondera por la demanda (así lo pide el enunciado), por lo que un nodo pequeño pesa igual que uno grande.
- El modelo no considera el desplazamiento de los equipos entre puntos ni límites de distancia por paciente.
- La demanda es determinista y la semana es fija. La capacidad diaria de cada disciplina es independiente de qué otras disciplinas atienden ese día en la misma sede.
- No hay costos explícitos para comparar puntos, equipos y distancia.

**Extensiones posibles**

- Optimización lexicográfica (por ejemplo, minimizar equipos con la distancia fija en su óptimo) para que (a) y (b) no produzcan soluciones dominadas.
- Mejorar la resolución del objetivo de equipos para cerrar los gaps de B. En las 6 soluciones de (b), los equipos coincidieron con Σₛ ⌈Nₛ/6⌉, donde Nₛ son los días totales de la disciplina. Eso sugiere una descomposición: decidir la asignación con un objetivo que cuente días y programar los días después. También se puede probar más ruptura de simetría entre días y prioridades de ramificación sobre Eₛ.
- Ponderar la distancia por la demanda o imponer una distancia máxima por nodo.
- Modelar las rutas de los equipos entre puntos y días.
- Considerar demanda incierta y escenarios.
- Estudiar todos los p con ε-restricción, con más tiempo o en un computador con más núcleos y memoria.
