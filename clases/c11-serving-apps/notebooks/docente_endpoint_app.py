# Databricks notebook source
# MAGIC %md
# MAGIC # Clase 11 — Preparación de la docente: endpoint, app y Genie compartidos
# MAGIC
# MAGIC Free Edition permite **3 apps por cuenta** (se apagan 24 h después de iniciarse) y **pocos endpoints de Serving
# MAGIC activos**, solo CPU. El workspace del curso es una sola cuenta, así que el endpoint y la app se despliegan **una vez**,
# MAGIC desde el esquema de la docente, y los usa todo el grupo:
# MAGIC
# MAGIC | Qué | Cuándo | Cuánto tarda |
# MAGIC |---|---|---|
# MAGIC | 1. Correr el lab 11 con `usuario = docente` hasta la sección 5 (tabla y vista) | el día anterior | 5 min |
# MAGIC | 2. Crear el endpoint `xm-demanda-7d` (esta notebook, sección 1) | el día anterior | 15–25 min de construcción |
# MAGIC | 3. Crear y desplegar la app (sección 2) y conceder `USE CATALOG` a su service principal | el día anterior o 1 h antes | 5 min + 3 de despliegue |
# MAGIC | 4. Calentar el endpoint y reiniciar la app si pasaron 24 h (sección 3) | 15 min antes de clase | 3 min |
# MAGIC | 5. Espacio de Genie (sección 4) | 1 h antes | 10 min |
# MAGIC
# MAGIC Requiere el lab 9 corrido con `usuario = docente`: `workspace.c01_docente.demanda_7d@champion`.

# COMMAND ----------

dbutils.widgets.text("endpoint", "xm-demanda-7d")
dbutils.widgets.text("app", "xm-observado-vs-estimado")
ENDPOINT = dbutils.widgets.get("endpoint")
APP = dbutils.widgets.get("app")
NOMBRE_MODELO = "workspace.c01_docente.demanda_7d"

import mlflow
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.serving import (
    EndpointCoreConfigInput,
    ServedEntityInput,
    ServingEndpointAccessControlRequest,
    ServingEndpointPermissionLevel,
)

w = WorkspaceClient()
mlflow.set_registry_uri("databricks-uc")
version = mlflow.MlflowClient().get_model_version_by_alias(NOMBRE_MODELO, "champion").version
print(f"{NOMBRE_MODELO}@champion → versión {version}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1 · Endpoint de Model Serving
# MAGIC
# MAGIC Una *served entity*: el modelo de Unity Catalog en su versión `@champion`, tamaño `Small` (hasta 4 solicitudes
# MAGIC concurrentes) y *scale to zero*: sin tráfico, no consume. El endpoint se construye a partir del run: lee el `MLmodel`, el
# MAGIC `requirements.txt` que MLflow infirió (aquí aparece `lightgbm`) y el `code_paths` con `xm_demanda`. Si el despliegue falla,
# MAGIC la pestaña **Logs → Build logs** del endpoint dice qué dependencia faltó.
# MAGIC
# MAGIC Al final se le da `CAN QUERY` al grupo `users`: todos pueden consultarlo, nadie más puede cambiarlo.

# COMMAND ----------

entidad = ServedEntityInput(
    entity_name=NOMBRE_MODELO,
    entity_version=str(version),
    workload_size="Small",
    scale_to_zero_enabled=True,
)
existentes = {e.name for e in w.serving_endpoints.list()}
if ENDPOINT in existentes:
    w.serving_endpoints.update_config(name=ENDPOINT, served_entities=[entidad])
    print(f"Actualizando {ENDPOINT} a la versión {version}…")
else:
    config = EndpointCoreConfigInput.from_dict({"name": ENDPOINT, "served_entities": [entidad.as_dict()]})
    w.serving_endpoints.create(name=ENDPOINT, config=config)
    print(f"Creando {ENDPOINT} con la versión {version}…")
print("Sigue el estado en Serving (menú lateral) o en la celda siguiente. Construir el contenedor tarda 15–25 min.")

# COMMAND ----------

ep = w.serving_endpoints.get(ENDPOINT)
print("Estado:", ep.state.ready, "| actualización:", ep.state.config_update)
if str(ep.state.ready).endswith("READY"):
    w.serving_endpoints.update_permissions(
        serving_endpoint_id=ep.id,
        access_control_list=[
            ServingEndpointAccessControlRequest(
                group_name="users", permission_level=ServingEndpointPermissionLevel.CAN_QUERY
            )
        ],
    )
    print("CAN QUERY concedido al grupo users")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2 · La app "observado vs. estimado"
# MAGIC
# MAGIC Desde la interfaz, porque es la forma en que la van a crear en su trabajo y porque se ve cada pieza:
# MAGIC
# MAGIC 1. **Compute → Apps → Create app → Create a custom app.** Nombre: `xm-observado-vs-estimado`.
# MAGIC 2. **Configure → App resources → Add resource → SQL warehouse**: el warehouse del workspace, permiso **Can use**,
# MAGIC    clave **`sql-warehouse`** (la misma que usa `app/app.yaml` en `valueFrom`).
# MAGIC 3. **Create app.** Databricks crea el contenedor y, con él, un **service principal** con el nombre de la app.
# MAGIC 4. **Deploy → desde la carpeta** `/Workspace/Users/<docente>/Databricks-to-XM/app` del Git folder (rama `main`).
# MAGIC 5. Ejecutar la celda de abajo: concede `USE CATALOG` sobre `workspace` al service principal e imprime su ID, que se comparte
# MAGIC    con el grupo para el widget `app_sp` del lab. Cada estudiante concede `USE SCHEMA` y `SELECT` sobre su vista (TODO 2).
# MAGIC
# MAGIC La app corre con **autorización de app**: lee con su propia identidad. La alternativa, **autorización de usuario**
# MAGIC (*on-behalf-of*), hace que cada persona vea con sus propios permisos; se activa en *Configure → User authorization* y
# MAGIC es lo que se usaría en XM para una app con datos sensibles por agente.

# COMMAND ----------

app = w.apps.get(APP)
sp = app.service_principal_client_id
spark.sql(f"GRANT USE CATALOG ON CATALOG workspace TO `{sp}`")
spark.sql(f"GRANT USE SCHEMA ON SCHEMA workspace.c01_docente TO `{sp}`")
spark.sql(f"GRANT SELECT ON TABLE workspace.c01_docente.v_observado_vs_estimado TO `{sp}`")
print(f"App: {app.url}")
print(f"Service principal (para el widget app_sp del lab): {sp}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3 · Antes de clase: calentar el endpoint y revisar la app
# MAGIC
# MAGIC Con *scale to zero*, la primera solicitud despierta el endpoint y puede tardar unos minutos. Una solicitud 15 minutos antes
# MAGIC evita que el grupo entero espere en vivo. Si la app lleva más de 24 h iniciada, Free Edition la detuvo: **Start** en su
# MAGIC página.

# COMMAND ----------

import os
import sys
import time

import pandas as pd
from mlflow.deployments import get_deploy_client

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.getcwd()))), "src"))
from xm_demanda.inference import batch

oro = spark.table("workspace.c01_docente.features_demanda_diaria").toPandas()
oro["fecha"] = pd.to_datetime(oro["fecha"])
filas = batch.filas_a_pronosticar(oro, "y_h7", 7).head(1)
t0 = time.perf_counter()
r = get_deploy_client("databricks").predict(endpoint=ENDPOINT, inputs=batch.payload_endpoint(filas))
print(batch.leer_predicciones(r), f"en {time.perf_counter() - t0:.1f} s")
print("App:", w.apps.get(APP).compute_status)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4 · Espacio de Genie (demo en vivo)
# MAGIC
# MAGIC **Genie → New** (o *New → Genie space*). Nombre: `XM · pronóstico de demanda`. Datos: `workspace.c01_docente.v_observado_vs_estimado` y
# MAGIC `workspace.c01_docente.features_demanda_diaria`. Warehouse: el del workspace.
# MAGIC
# MAGIC **Instrucciones generales** (pestaña *Instructions*), para que hable el idioma del negocio:
# MAGIC
# MAGIC ```
# MAGIC - Responde en español. La demanda está en kWh; muéstrala en GWh (dividir por 1e6) salvo que pidan kWh.
# MAGIC - WAPE = sum(error_abs_kwh) / sum(abs(demanda_observada_kwh)), solo filas con demanda_observada_kwh no nula.
# MAGIC   Reporta el WAPE como porcentaje con un decimal.
# MAGIC - "El modelo" o "el pronóstico oficial" es alias = 'champion'. "El retador" es alias = 'challenger'.
# MAGIC - "Futuro" son las filas con demanda_observada_kwh nula.
# MAGIC - Una serie es la combinación codigo_sic_agente + mercado_comercializacion + tipo_mercado + clasificacion_industrial.
# MAGIC ```
# MAGIC
# MAGIC **Consulta de ejemplo** (*SQL queries*, marcada como confiable): el WAPE por tipo de mercado del champion.
# MAGIC
# MAGIC **Preguntas para la demo**, de menos a más:
# MAGIC 1. ¿Cuál fue el WAPE del champion y del challenger en julio?
# MAGIC 2. ¿En qué mercados de comercialización el champion tiene más error? Muéstralo en una gráfica de barras.
# MAGIC 3. ¿Qué días el challenger le ganó al champion? (Genie tiene que inferir comparar por día; revisar el SQL que generó.)
# MAGIC 4. ¿Cuánta energía se pronostica para la semana del 26 de julio en el mercado regulado de Bogotá?
# MAGIC
# MAGIC Lo que se enseña con Genie no es la respuesta, es **leer el SQL que generó** (botón *Show code*) y ver que usa la misma
# MAGIC definición de WAPE que la vista. Sin instrucciones, en la pregunta 1 suele promediar porcentajes por fila: se muestra
# MAGIC primero sin instrucciones y luego con ellas.

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5 · Después de la clase
# MAGIC
# MAGIC El endpoint en cero no consume; se puede dejar para la clase 12. La app se detiene sola a las 24 h. Si hace falta el cupo de
# MAGIC apps o endpoints para otra cosa: `w.serving_endpoints.delete(ENDPOINT)` y **Delete** en la página de la app.
