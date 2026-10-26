# Databricks notebook source
# MAGIC %md
# MAGIC # Inferencia batch a gold_energia.pronostico_demanda
# MAGIC Clase 11. Notebook delgado: recibe parámetros del job y llama a `xm_demanda.inference`.
# MAGIC En producción lo ejecuta la tarea `batch_inference` del job diario (clase 12), después de `gold_features`.
# MAGIC
# MAGIC 1. Resuelve el alias una sola vez (la corrida entera usa la misma versión aunque alguien mueva el alias).
# MAGIC 2. Lee oro con su versión Delta y verifica el contrato.
# MAGIC 3. Pronostica los últimos `horizon_days` días (o desde una fecha, para backfill) y valida antes de escribir.
# MAGIC 4. `MERGE` idempotente sobre `(fecha_pronostico, serie, modelo_version)` y refresca la vista observado vs. estimado.

# COMMAND ----------

# MAGIC %pip install -q lightgbm

# COMMAND ----------

dbutils.widgets.text("catalog", "dev")
dbutils.widgets.text("alias", "champion")
dbutils.widgets.text("desde", "")
catalog = dbutils.widgets.get("catalog")
alias = dbutils.widgets.get("alias")
desde = dbutils.widgets.get("desde") or None

# COMMAND ----------

import os
import sys

import mlflow
import pandas as pd

raiz = os.path.dirname(os.getcwd())
sys.path.insert(0, os.path.join(raiz, "src"))
sys.dont_write_bytecode = True

from xm_demanda.features.build import columnas_contrato
from xm_demanda.inference import batch
from xm_demanda.utils.config import fqn, load_config, validar_config

cfg = load_config(catalog)
validar_config(cfg)
H = cfg["modelo"]["horizon_days"]
OBJETIVO = f"y_h{H}"
t_oro = fqn(cfg, "gold", "gold_features")
t_pron = fqn(cfg, "gold", "gold_pronostico")
v_obs = f"{cfg['catalog']}.{cfg['schemas']['gold']}.v_observado_vs_estimado"
nombre_modelo = f"{cfg['catalog']}.{cfg['schemas']['models']}.{cfg['modelo']['nombre']}"
mlflow.set_registry_uri("databricks-uc")

mv = mlflow.MlflowClient().get_model_version_by_alias(nombre_modelo, alias)
modelo = mlflow.pyfunc.load_model(f"models:/{nombre_modelo}/{mv.version}")
nombre_estimador = mlflow.get_run(mv.run_id).data.params.get("modelo", "?")
print(f"{nombre_modelo}@{alias} → versión {mv.version} ({nombre_estimador}) · {t_oro} → {t_pron}")

# COMMAND ----------

version_oro = spark.sql(f"DESCRIBE HISTORY {t_oro}").agg({"version": "max"}).first()[0]
oro = spark.read.option("versionAsOf", version_oro).table(t_oro).toPandas()
assert set(oro.columns) == set(columnas_contrato(cfg)), "La tabla de oro no cumple el contrato (clase 8)"
oro["fecha"] = pd.to_datetime(oro["fecha"])

filas = batch.filas_a_pronosticar(oro, OBJETIVO, H, desde=desde)
assert len(filas) > 0, "No hay filas para pronosticar: ¿llegó la carga de hoy a oro?"
pron = batch.preparar_pronosticos(
    filas,
    modelo.predict(filas).to_numpy(),
    H,
    nombre_estimador,
    mv.version,
    alias,
    version_oro,
    pd.Timestamp.now(tz="America/Bogota").tz_localize(None).floor("s"),
)

# COMMAND ----------

spark.sql(batch.ddl_pronostico(t_pron))
spark.createDataFrame(
    pron.assign(
        fecha_emision=pron["fecha_emision"].dt.date,
        fecha_pronostico=pron["fecha_pronostico"].dt.date,
    )
).createOrReplaceTempView("pronosticos_nuevos")
spark.sql(batch.sql_merge_pronosticos(t_pron, "pronosticos_nuevos"))
spark.sql(batch.sql_vista_observado_vs_estimado(v_obs, t_pron, t_oro))

met_op = spark.sql(f"DESCRIBE HISTORY {t_pron} LIMIT 1").first()["operationMetrics"]
print(
    f"{len(pron):,} pronósticos {pron['fecha_pronostico'].min().date()} → "
    f"{pron['fecha_pronostico'].max().date()} · insertadas {met_op.get('numTargetRowsInserted')} · "
    f"actualizadas {met_op.get('numTargetRowsUpdated')} · oro v{version_oro}"
)
