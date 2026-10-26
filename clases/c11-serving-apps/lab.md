# Lab 11 — Inferencia batch, Serving y Apps

**Duración:** 25 min (más el notebook guiado) · **Modalidad:** individual, en tu propio fork · **Rama:** `feature/c11-serving`

## Objetivo

Publicar el pronóstico de `@champion` (y de `@challenger`, en sombra) en una tabla Delta con contrato y escritura idempotente; compararlo con lo observado en una vista; consultar el mismo modelo por un endpoint REST; y dejar que la app del curso lea tu vista, concediéndole solo lo necesario. Cierra el hito 5.

## Antes de empezar

| Requisito | Si no lo tienes |
|---|---|
| Lab 9 terminado: `workspace.c01_<usuario>.demanda_7d` con `@champion` y `@challenger` | Corre el lab 9 hasta la sección 10 |
| Git folder en `main` actualizado | GitHub: **Sync fork** → Databricks: Git → **Pull** |
| Rama nueva | Git → Create branch → `feature/c11-serving` |
| ID del service principal de la app | Lo comparte la docente al inicio; va en el widget `app_sp` |

## Pasos

Abre `clases/c11-serving-apps/notebooks/lab11_inferencia_serving_apps`. Widgets `usuario` y `app_sp` (`endpoint` ya viene con `xm-demanda-7d`). La primera celda instala `lightgbm`, que el modelo necesita para cargarse.

| Sección | Qué haces | Qué debes ver |
|---|---|---|
| 1 | Leer los cuatro canales y la regla "batch por defecto" | — |
| 2 | Resolver `@champion` y `@challenger`, leer oro con versión, escoger filas, predecir | Dos versiones con su WAPE de la clase 9; ~8.800 filas (≈ 6.350 de backtest + ≈ 2.470 hacia el futuro) |
| 3 TODO 1 | `preparar_pronosticos` en `src/xm_demanda/inference/batch.py` | ≈ 17.650 filas listas, 12 columnas, sin duplicados |
| 4 | Tabla con DDL y `MERGE` dos veces | MERGE #1: todo insertado · MERGE #2: 0 insertadas, todo actualizado · total igual |
| 5 | Vista `v_observado_vs_estimado` y WAPE por modelo | WAPE de la vista = WAPE del run de la clase 9 (≈ 0,048 champion, ≈ 0,046 challenger) |
| 6 | Consultar el endpoint compartido con 5 filas | Respuesta en milisegundos; compárala con tu batch y explica la diferencia (si la hay) |
| 7 TODO 2 | Dos `GRANT` al service principal de la app | `SHOW GRANTS` con `SELECT`; tu esquema aparece en el selector de la app |
| 8 | Leer los datasets para dashboard y Genie | — |
| Preguntas | Canal por consumidor; features en tiempo real | — |
| `verificar()` | 8 comprobaciones en OK | Commit `feat(c11): inferencia batch idempotente, vista observado vs. estimado y grants para la app` → push → PR → CI → merge |

Los valores son de referencia (con la tabla de oro de la docente); los tuyos pueden diferir en el tercer decimal.

## Criterios de aceptación

- [ ] `preparar_pronosticos` implementada; `tests/unit/test_inference.py` sin skip
- [ ] `workspace.c01_<usuario>.pronostico_demanda` con las 12 columnas del contrato, champion y challenger, sin duplicados por `(fecha_pronostico, serie, modelo_version)`
- [ ] Segunda corrida del `MERGE` con 0 filas insertadas
- [ ] Vista `v_observado_vs_estimado` con el WAPE del champion igual al del run de la clase 9
- [ ] Endpoint `xm-demanda-7d` consultado desde tu notebook
- [ ] La app lee tu vista (y no tu tabla de oro)
- [ ] Las dos preguntas respondidas
- [ ] `verificar()` en OK; PR en verde

**Hito 5 cerrado.**

## Comparar con la solución de referencia

`https://github.com/<docente>/Databricks-to-XM/compare/s11...<tu_usuario>:Databricks-to-XM:main`

```bash
git fetch upstream --tags
git diff s11 -- src/xm_demanda/inference clases/c11-serving-apps/notebooks
```

## Extensión opcional

1. **Dashboard AI/BI.** *New → Dashboard*. Crea dos datasets con el SQL que imprime la sección 8 y arma: un gráfico de líneas (observado vs. estimado por día, color por `alias`), un contador con el WAPE del champion y una barra de WAPE por `mercado_comercializacion`. Agrega un filtro por `tipo_mercado`. Publícalo y compártelo con un compañero: ¿qué ve él si no le diste `SELECT` sobre tu vista?
2. **El eco del festivo.** En la gráfica de la sección 5, mira el challenger el lunes 27 de julio (futuro). ¿Por qué pronostica una caída que el champion no pronostica? Pista: `naive_festivo` copia `y(t)` y `t` fue el festivo del 20.
3. **Batch en SQL.** Con el endpoint compartido, `ai_query('xm-demanda-7d', named_struct(...))` en un SQL warehouse pronostica sin Python. Escribe la consulta para 10 filas de tu oro y compara con tu tabla.
4. **Correr la app en local.** `pip install -r app/requirements.txt`, define `XM_WAREHOUSE_ID` y `DATABRICKS_HOST`/`DATABRICKS_TOKEN` y `streamlit run app/app.py`. ¿Con qué identidad lee ahora?

## Así sería en Azure Databricks

| En Free Edition (hoy) | En Azure Databricks (XM) |
|---|---|
| Un endpoint y una app compartidos por cuenta | Un endpoint por ambiente (`dev`/`qa`/`prod`), desplegado por el bundle (clase 13) con *service principal* |
| `scale to zero` y solo CPU | Mínimo de réplicas según SLA; GPU si el modelo lo pide; *route optimization* para baja latencia |
| Tablas de inferencia no configuradas | AI Gateway con tablas de inferencia hacia `prod.monitoring`, insumo del monitoreo de la clase 15 |
| App con autorización de app | Autorización de usuario (*on-behalf-of*) cuando cada agente solo debe ver sus series; red privada (Private Link) |
| Job de inferencia corrido a mano | Tarea `batch_inference` del job diario (clase 12) después de `gold_features`, con reintentos que el `MERGE` hace seguros |
