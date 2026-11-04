# Clase 14 — CI/CD y promoción entre ambientes

Nadie despliega a mano: cada PR pasa por pruebas (incluidas las del bundle y del propio pipeline), cada merge despliega `dev`, y cada tag `v*` se promueve a `qa`, se prueba corriendo el job completo y, con una aprobación, llega a `prod`. La auditoría (qué versión, quién, cuándo) queda en GitHub y en los tags de cada job.

**Sesión 1 de 3 h 30 (clases 13 y 14).** Esta clase ocupa la segunda mitad:

| Bloque | Duración | Material |
|---|---|---|
| ← Clase 13 y receso | 1 h 40 | `../c13-bundles/` |
| CI/CD y promoción | 25 min | `slides/` 1–10 |
| Configurar el fork + TODO + flujo en vivo (PR rojo, PR verde, push directo rechazado, tag) | 45 min | `notebooks/lab14_cicd_promocion.py`, `.github/workflows/ci.yml`, `ci/azure-pipelines.yml` |
| **Receso** (mientras corre `deploy-qa`) | 10 min | — |
| Aprobación, auditoría y promoción de modelos | 20 min | notebook, secciones 4–5 |
| Cierre | 10 min | tags `s13` y `s14`, "así sería en Azure", próxima sesión |

**Requisitos:** fork **público** en GitHub (las aprobaciones de *environments* en planes gratuitos solo existen en repositorios públicos), Actions habilitado y un token personal de Databricks.

El detalle de teoría, práctica, contexto del sector y entregable está en el [README del curso](../../README.md#detalle-por-clase).
