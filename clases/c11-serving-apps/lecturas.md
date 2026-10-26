# Lecturas — Clase 11

## Escoger el canal

| Tema | Referencia |
|---|---|
| Databricks, *The Big Book of MLOps*: batch, streaming y tiempo real; "deploy code, not models" | https://www.databricks.com/resources/ebook/the-big-book-of-mlops |
| Limitaciones de Free Edition (apps, endpoints, warehouse) | https://docs.databricks.com/aws/en/getting-started/free-edition-limitations |

## Inferencia batch

| Tema | Referencia |
|---|---|
| `MERGE INTO` en Delta Lake: upsert idempotente | https://docs.databricks.com/aws/en/delta/merge |
| `ai_query`: inferencia batch desde SQL contra un endpoint | https://docs.databricks.com/aws/en/sql/language-manual/functions/ai_query |

## Model Serving

| Tema | Referencia |
|---|---|
| Endpoints para modelos personalizados (pyfunc desde Unity Catalog) | https://docs.databricks.com/aws/en/machine-learning/model-serving/custom-models |
| Consultar un endpoint: `dataframe_split`, `dataframe_records`, respuesta | https://docs.databricks.com/aws/en/machine-learning/model-serving/score-custom-model-endpoints |
| Varios modelos en un endpoint y división de tráfico (A/B champion/challenger) | https://docs.databricks.com/aws/en/machine-learning/model-serving/serve-multiple-models-to-serving-endpoint |
| Límites y regiones de Model Serving | https://docs.databricks.com/aws/en/machine-learning/model-serving/model-serving-limits |
| AI Gateway: tablas de inferencia para monitorear lo que se sirve | https://docs.databricks.com/aws/en/ai-gateway/inference-tables |
| Online Feature Store: features en milisegundos para tiempo real | https://docs.databricks.com/aws/en/machine-learning/feature-store/online-feature-store |

## Databricks Apps

| Tema | Referencia |
|---|---|
| Tutorial: app con Streamlit que lee tablas de Unity Catalog | https://docs.databricks.com/aws/en/dev-tools/databricks-apps/tutorial-streamlit |
| Recursos de una app (SQL warehouse, endpoints) y permisos | https://docs.databricks.com/aws/en/dev-tools/databricks-apps/resources |
| Variables de entorno y `valueFrom` en `app.yaml` | https://docs.databricks.com/aws/en/dev-tools/databricks-apps/environment-variables |

## AI/BI

| Tema | Referencia |
|---|---|
| Dashboards AI/BI | https://docs.databricks.com/aws/en/dashboards/ |
| Genie: conceptos, instrucciones y activos confiables | https://docs.databricks.com/aws/en/genie/ · https://docs.databricks.com/aws/en/genie/trusted-assets |

## Sector

| Tema | Referencia |
|---|---|
| Databricks Data Intelligence Platform for Energy (AEMO, Octopus Energy, Shell, TotalEnergies) | https://www.databricks.com/company/newsroom/press-releases/databricks-launches-data-intelligence-platform-energy-bringing |
| XM — pronóstico de demanda publicado | https://www.xm.com.co/consumo/pronostico-de-demanda |
