# Clase 15 — Monitoreo, drift, reentrenamiento y cierre del curso

El job aprende a cuidar el modelo: mide el error observado y el drift de las entradas, decide si reentrenar con una política escrita como código, entrena un candidato con los datos del ambiente y lo promueve **solo si gana** en días que ninguno de los dos modelos vio. Alerta SQL, SLOs y runbook. Cierra el hito 6 y el curso.

**Sesión 2 de 3 h 30.**

| Bloque | Duración | Material |
|---|---|---|
| Apertura: qa y prod en el mismo commit | 10 min | `slides/` 1–3 |
| Qué se monitorea y con qué | 30 min | `slides/` 4–9 |
| Notebook: error observado, segmentos y drift (con un Niño simulado) | 35 min | `notebooks/lab15_monitoreo_reentrenamiento.py`, secciones 1–3 |
| **Receso** | 10 min | — |
| Políticas de reentrenamiento y promoción; el sector | 20 min | `slides/` 10–14 |
| TODO + el monitor dentro del job + reentrenamiento por evento | 40 min | secciones 4–5, `src/xm_demanda/monitoreo/`, `notebooks/tareas/t7…t9`, `resources/job_reentrenamiento.yml` |
| **Receso** (mientras entrena el candidato) | 10 min | — |
| Alerta SQL, SLOs y runbook | 25 min | sección 6, `docs/runbook.md` |
| Cierre del curso: recorrido, backlog, retro | 30 min | sección 7, `slides/` 16–19 (en el PDF del repo, 16–18), `docs/backlog.md` |

**Free Edition:** *Data quality monitoring* puede no estar disponible; el monitor del lab es propio y funciona igual en Azure. Las tablas de sistema de facturación no están disponibles.

El detalle de teoría, práctica, contexto del sector y entregable está en el [README del curso](../../README.md#detalle-por-clase).
