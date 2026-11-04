# Clase 13 — Declarative Automation Bundles y ambientes

El job de la clase 12 se convierte en un producto desplegable: `databricks.yml` + `resources/*.yml` + tareas parametrizadas por ambiente. El mismo código se despliega a `dev` y a `qa` desde el workspace, sin instalar nada; `prod` queda para el pipeline de la clase 14.

**Sesión 1 de 2 h 30 (clases 13 y 14, un receso).** Esta clase ocupa la primera mitad:

| Bloque | Duración | Material |
|---|---|---|
| Apertura: lo que dejó la clase 12 | 5 min | `slides/` 1–3 |
| Bundles y ambientes | 20 min | `slides/` 4–12 |
| Notebook guiado + práctica | 40 min | `slides/` 13, `notebooks/lab13_bundles_ambientes.py`, `databricks.yml`, `resources/`, `notebooks/tareas/`, `src/xm_demanda/utils/ambiente.py` |
| **Receso** (el job de qa sigue corriendo) | 10 min | — |
| → Clase 14 | 75 min | `../c14-cicd/` |

**Free Edition:** los ambientes son esquemas del catálogo `workspace` (`c01_<usuario>`, `_qa`, `_prod`). Se despliega desde el panel **Deployments** del workspace; la CLI es opcional.

El detalle de teoría, práctica, contexto del sector y entregable está en el [README del curso](../../README.md#detalle-por-clase).
