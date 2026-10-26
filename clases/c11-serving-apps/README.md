# Clase 11 — Del modelo registrado a quien lo usa: inferencia batch, Serving y Apps

Cierra el hito 5: el `@champion` de la clase 9 deja de vivir solo en el registro y llega a sus consumidores por cuatro canales (tabla batch, endpoint REST, app y AI/BI), escogidos según quién consume, cada cuánto y quién trae las features.

| Bloque | Duración | Material |
|---|---|---|
| Encuadre y teoría, parte 1 | 20 min | `slides/` 1–7: cuatro canales y cómo escoger, inferencia batch, idempotencia |
| **Receso** | 10 min | slide 8 |
| Teoría, parte 2 | 20 min | `slides/` 9–14: Model Serving, Databricks Apps y gobierno, AI/BI y Genie, sector |
| Notebook guiado (con la docente) | 40 min | `notebooks/lab11_inferencia_serving_apps.py`, `src/xm_demanda/inference/`, `app/` |
| Práctica | 25 min | `lab.md`: el mismo notebook, solo |
| Cierre | 5 min | tag `s11`, "así sería en Azure", próxima clase |

**Compartidos en el workspace** (Free Edition: 3 apps por cuenta, pocos endpoints, solo CPU): el endpoint `xm-demanda-7d` y la app `xm-observado-vs-estimado` los despliega la docente con `notebooks/docente_endpoint_app.py`. Cada estudiante escribe su propia tabla de pronósticos, consulta el endpoint y le da permiso a la app para leer su vista.

El detalle de teoría, práctica, contexto del sector y entregable está en el [README del curso](../../README.md#detalle-por-clase).
