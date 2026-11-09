# Backlog post-curso

Ideas y extensiones que exceden el alcance del curso, por clase de origen. Ordenadas por lo que más le aporta a un equipo que empieza a operar modelos en Azure Databricks.

| Ítem | Origen (clase) | Prioridad |
|---|---|---|
| Federación OIDC (GitHub) o *service connection* con Entra ID (Azure DevOps) en lugar de tokens | 14 | Alta |
| Un service principal por ambiente como `run_as` de qa y prod; grupos como dueños de los jobs | 3, 13 | Alta |
| Workspaces y catálogos por ambiente con *workspace-catalog binding*, creados con Terraform | 3, 13 | Alta |
| Reentrenar en cada ambiente con sus datos (deploy code) y retirar `copy_model_version` salvo para arrancar un ambiente | 14, 15 | Alta |
| *Data quality monitoring*: anomaly detection en los esquemas de producción y data profiling InferenceLog sobre `pronostico_demanda` | 5, 15 | Media |
| Disparador por llegada de archivo y `fecha_proceso = {{job.start_time.iso_date}}` | 12 | Media |
| Features exógenas: temperatura, hidrología, indicador ONI de El Niño; ADR sobre si entran al modelo | 7, 9, 15 | Media |
| Walk-forward automático en `evaluar_promover` (varios cortes, no uno) | 9, 15 | Media |
| Ajustes del usuario en la app escritos en su propia tabla (o Lakebase), nunca sobre la salida del pipeline | 11, 12 | Media |
| Tablero AI/BI de operación: SLOs, error por segmento, drift y decisiones del modelo | 11, 15 | Media |
| Costos: presupuesto de DBUs por job con `system.billing.usage` y política de cómputo | 15 | Baja |
| Recursos del bundle en Python (`databricks-bundles`) generados desde `job.py` | 13 | Baja |
