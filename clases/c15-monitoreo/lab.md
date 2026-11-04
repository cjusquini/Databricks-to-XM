# Lab 15 — El modelo se monitorea, se reentrena y se promueve solo si gana

**Duración:** 25 + 30 + 10 min (después de cerrar el lab 14) · **Modalidad:** individual, en tu propio fork · **Rama:** `feature/c15-monitoreo`

## Objetivo

Medir el error observado (WAPE y sesgo, por día y segmento) y el drift de las entradas (PSI); implementar la política de reentrenamiento; desplegar el job diario con monitoreo y el job de reentrenamiento; lanzar un reentrenamiento por evento y leer la decisión de promoción; crear una alerta SQL y completar el runbook. Cierra el hito 6.

## Antes de empezar

| Requisito | Si no lo tienes |
|---|---|
| Lab 14, parte 1 (PR fusionado y `deploy-dev` en verde) | La parte 2 (el tag a qa y prod) se hace al abrir esta sesión; no bloquea este lab: todo se hace en dev |
| `demanda_7d@champion` en dev con su run (clase 9) | El monitor lee de ahí el WAPE de validación y la fecha de corte |
| Git folder en `main` actualizado | GitHub: **Sync fork** → Databricks: Git → **Pull** |
| Rama nueva | Git → Create branch → `feature/c15-monitoreo` |

## Pasos

Abre `clases/c15-monitoreo/notebooks/lab15_monitoreo_reentrenamiento`. Widget `usuario`.

| Sección | Qué haces | Qué debes ver |
|---|---|---|
| 1 | Leer qué se monitorea y con qué | — |
| 2 | Error observado | WAPE de 7 y 28 días del champion y el challenger; la tabla de WAPE y sesgo de los últimos 14 días; WAPE por `tipo_mercado` |
| 3 | Drift | PSI por feature (semana actual vs. 8 semanas); con el Niño simulado, PSI alto en las features de demanda |
| 4 TODO | `decidir_reentrenamiento()` en `src/xm_demanda/monitoreo/politica.py` | `test_monitoreo.py` sin skip; la decisión de hoy y la del escenario simulado |
| 5 | **Deploy** del bundle a dev; job diario y reentrenamiento por evento | Tareas `monitoreo` y `hay_que_reentrenar` en el diario; `entrenar` y `evaluar_promover` en verde; una fila nueva en `decisiones_modelo` (10–20 min) |
| 6 | Alerta SQL y runbook | Alerta `wape_7d > 0.058` creada; en `docs/runbook.md`, cada `<dueño>` reemplazado por un rol |
| Preguntas | reentrenar con PSI alto y WAPE bueno; el disparador más importante en su proyecto | — |
| 7 | Cierre del curso | — |
| `verificar()` | 9 comprobaciones en OK | Commit `feat(c15): monitoreo de error y drift, política de reentrenamiento y runbook` → push → PR → CI → merge |

## Criterios de aceptación

- [ ] `decidir_reentrenamiento()` implementada; `tests/unit/test_monitoreo.py` sin skip
- [ ] Job diario de dev con `monitoreo` → `hay_que_reentrenar` → `reentrenar`; job `reentrenamiento` desplegado
- [ ] `monitoreo_error`, `monitoreo_drift`, `monitoreo_decisiones` y `decisiones_modelo` con filas
- [ ] Un `@candidato` registrado con `datos_hasta` y `motivo`
- [ ] Alerta SQL creada; runbook sin `<dueño>`
- [ ] Las dos preguntas respondidas
- [ ] `verificar()` en OK; PR en verde

**Hito 6 cerrado.**

## Llevarlo a qa y prod

Con el PR fusionado: `git tag v1.1.0 && git push origin v1.1.0`. El pipeline de la clase 14 despliega el monitor a qa y, con tu aprobación, a prod. En esos ambientes el modelo es una copia promovida: el monitor lee su linaje de los tags que dejó `preparar_ambiente`.

## Comparar con la solución de referencia

```bash
git fetch upstream --tags
git diff s15 -- src/xm_demanda/monitoreo notebooks/tareas resources conf/base.yml docs/runbook.md
```

## Extensión opcional

1. **Data profiling.** En la sección 6, cambia `PROBAR_PERFILADO = True`. Si tu workspace lo permite, Databricks crea `observado_vs_estimado_log_profile_metrics` y `_drift_metrics` y un tablero. Compara su PSI con el tuyo.
2. **Anomaly detection.** Catalog Explorer → tu esquema → **Details** → *Data Quality Monitoring* → **Enable**. ¿Qué tablas marca como frescas y cuáles no?
3. **Walk-forward en la promoción.** Cambia `t9_evaluar_promover` para que compare en tres ventanas y promueva solo si gana en al menos dos.
4. **Un tablero de operación.** Un tablero AI/BI con `monitoreo_error`, `monitoreo_drift` y `decisiones_modelo`, y un espacio de Genie encima.

## Así sería en Azure Databricks

| En Free Edition (hoy) | En Azure Databricks (XM) |
|---|---|
| Monitor propio en `src/xm_demanda/monitoreo` | El mismo, más *Data quality monitoring* (anomaly detection y data profiling InferenceLog) |
| Alerta SQL a tu correo | Alertas a un canal de guardia (Teams, PagerDuty) con el runbook enlazado |
| Reentrenamiento en dev por evento | Reentrenamiento en prod con los datos de prod; la promoción queda en `decisiones_modelo` y en el historial de alias |
| Sin costos visibles | `system.billing.usage` por job y etiqueta `iniciativa`; presupuesto por producto |
