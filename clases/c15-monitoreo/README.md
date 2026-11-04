# Clase 15 — Monitoreo, drift, reentrenamiento y cierre del curso

El job aprende a cuidar el modelo: mide el error observado y el drift de las entradas, decide si reentrenar con una política escrita como código, entrena un candidato con los datos del ambiente y lo promueve **solo si gana** en días que ninguno de los dos modelos vio. Alerta SQL, SLOs y runbook. Cierra el hito 6 y el curso.

**Sesión 2 de 2 h 30 (un receso).** Abre con el último paso del lab 14.

| Bloque | Duración | Material |
|---|---|---|
| Apertura + tag `v1.0.0` (lab 14, paso e) | 10 min | `slides/` 1–3, `../c14-cicd/notebooks/lab14_cicd_promocion.py` |
| Qué se monitorea y con qué (mientras corre `deploy-qa`) | 20 min | `slides/` 4–9 |
| Aprobar prod, auditar, promover código o modelo | 15 min | `../c14-cicd/slides/` 7, lab 14 (sección 5, `verificar()`) |
| Notebook: error observado, segmentos y drift (con un Niño simulado) | 25 min | `notebooks/lab15_monitoreo_reentrenamiento.py`, secciones 1–3 |
| **Receso** | 10 min | — |
| Políticas de reentrenamiento y promoción; el sector | 15 min | `slides/` 10–12 |
| TODO + el monitor dentro del job + reentrenamiento por evento | 30 min | `slides/` 15, secciones 4–5, `src/xm_demanda/monitoreo/`, `notebooks/tareas/t7…t9`, `resources/job_reentrenamiento.yml` |
| Alerta SQL, SLOs y runbook (mientras entrena el candidato) | 10 min | `slides/` 13–14, sección 6, `docs/runbook.md` |
| Cierre del curso: recorrido, backlog, retro | 15 min | sección 7, `slides/` 16–19 (en el PDF del repo, 16–18), `docs/backlog.md` |

**Free Edition:** *Data quality monitoring* puede no estar disponible; el monitor del lab es propio y funciona igual en Azure. Las tablas de sistema de facturación no están disponibles.

El detalle de teoría, práctica, contexto del sector y entregable está en el [README del curso](../../README.md#detalle-por-clase).
