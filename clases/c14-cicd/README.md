# Clase 14 — CI/CD y promoción entre ambientes

Nadie despliega a mano: cada PR pasa por pruebas (incluidas las del bundle y del propio pipeline), cada merge despliega `dev`, y cada tag `v*` se promueve a `qa`, se prueba corriendo el job completo y, con una aprobación, llega a `prod`. La auditoría (qué versión, quién, cuándo) queda en GitHub y en los tags de cada job.

**Sesión 1 de 2 h 30 (clases 13 y 14).** Esta clase ocupa la segunda mitad, y su último paso abre la sesión 2:

| Bloque | Duración | Material |
|---|---|---|
| ← Clase 13 y receso | 1 h 15 | `../c13-bundles/` |
| CI/CD | 20 min | `slides/` 1–6 y 8 |
| Lab 14, parte 1: configurar el fork + TODO + PR rojo, PR verde, push directo rechazado, merge → dev | 45 min | `slides/` 9, `notebooks/lab14_cicd_promocion.py` (secciones 1–4, pasos a–d), `.github/workflows/ci.yml` |
| Cierre | 10 min | `slides/` 10, tags `s13` y `s14`, "así sería en Azure" |
| **Sesión 2, al abrir** · lab 14, parte 2: tag `v1.0.0` → qa → aprobación → prod, auditoría, promover código o modelo | 15 min | `slides/` 7, notebook (paso e, sección 5, `verificar()`) |

**Requisitos:** fork **público** en GitHub (las aprobaciones de *environments* en planes gratuitos solo existen en repositorios públicos), Actions habilitado y un token personal de Databricks.

El detalle de teoría, práctica, contexto del sector y entregable está en el [README del curso](../../README.md#detalle-por-clase).
