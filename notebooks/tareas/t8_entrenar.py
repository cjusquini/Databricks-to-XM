# Databricks notebook source
# MAGIC %md
# MAGIC # Tarea 8 · entrenar: un candidato con los datos del ambiente
# MAGIC Parámetros del job: `usuario`, `ambiente`, `motivo`. *Deploy code, not models*: el código de entrenamiento es el mismo
# MAGIC en los tres ambientes; cada uno entrena con **sus** datos. Corte automático: los últimos 14 días con objetivo quedan para
# MAGIC validación. Registra la versión con el alias `candidato` y su linaje en tags (`datos_hasta`, `wape_validacion`, `motivo`).
# MAGIC **No toca `@champion`**: entrenar no es promover.

# COMMAND ----------

# MAGIC %pip install -q lightgbm

# COMMAND ----------

dbutils.widgets.text("usuario", "")
dbutils.widgets.text("ambiente", "dev")
usuario = dbutils.widgets.get("usuario").strip().lower()
ambiente = dbutils.widgets.get("ambiente").strip().lower()
assert usuario, "Falta el parámetro usuario"
dbutils.widgets.text("motivo", "manual")
motivo = dbutils.widgets.get("motivo").strip() or "manual"

# COMMAND ----------

import os
import sys


def _raiz_repo():
    d = os.getcwd()
    for _ in range(8):
        if os.path.exists(os.path.join(d, "src", "xm_demanda")):
            return d
        d = os.path.dirname(d)
    raise FileNotFoundError("No encuentro src/xm_demanda: el job debe apuntar a los notebooks del bundle o del Git folder.")


raiz = _raiz_repo()
sys.path.insert(0, os.path.join(raiz, "src"))
sys.dont_write_bytecode = True

from xm_demanda.utils.ambiente import ubicacion

u = ubicacion(usuario, ambiente)
esquema = u["fqn"]
T_FEATURES = f"{esquema}.features_demanda_diaria"
print(f"ambiente {ambiente} · esquema {esquema} · motivo: {motivo}")

# COMMAND ----------

import mlflow
import pandas as pd

from xm_demanda.model import datos, metricas, modelos, registro
from xm_demanda.utils.config import load_config

cfg = load_config(ambiente)
H = cfg["modelo"]["horizon_days"]
OBJETIVO, DIAS_VALID = f"y_h{H}", 14
mlflow.set_registry_uri("databricks-uc")
email = spark.sql("SELECT current_user()").first()[0]
mlflow.set_experiment(f"/Users/{email}/{cfg['experimento']}")

version_oro = spark.sql(f"DESCRIBE HISTORY {T_FEATURES}").agg({"version": "max"}).first()[0]
oro = spark.read.option("versionAsOf", version_oro).table(T_FEATURES).toPandas()
oro["fecha"] = pd.to_datetime(oro["fecha"])
oro = oro[oro["dias_con_datos"] >= 29].reset_index(drop=True)
ultima = oro.loc[oro[OBJETIVO].notna(), "fecha"].max()
corte = str((ultima - pd.Timedelta(days=DIAS_VALID)).date())
train, valid = datos.split_temporal(oro, corte, DIAS_VALID, OBJETIVO)
print(f"oro v{version_oro} · train hasta {corte} ({len(train):,} filas) · valid {len(valid):,} filas hasta {ultima.date()}")

# COMMAND ----------

estimador = modelos.GlobalLightGBM()
with mlflow.start_run(run_name=f"reentrenamiento_{ambiente}") as run:
    estimador.fit(train, OBJETIVO)
    m = metricas.metricas(valid[OBJETIVO], estimador.predict(valid))
    mlflow.log_params({"modelo": estimador.nombre, "ambiente": ambiente, "horizonte_dias": H, "corte": corte,
                       "dias_valid": DIAS_VALID, "motivo": motivo, **estimador.params})
    mlflow.log_metrics(m)
    mlflow.log_input(mlflow.data.load_delta(table_name=T_FEATURES, version=str(version_oro)), context="training")
    registro.registrar_en_run(estimador, valid.head(5).drop(columns=[OBJETIVO]),
                              code_paths=[os.path.join(raiz, "src", "xm_demanda")])

v = registro.registrar_version(run.info.run_id, u["modelo"])
cliente = mlflow.MlflowClient()
for llave, valor in {"datos_hasta": corte, "wape_validacion": f"{m['wape']:.6f}", "motivo": motivo,
                     "entrenado_en": ambiente, "oro_version": str(version_oro)}.items():
    cliente.set_model_version_tag(u["modelo"], v.version, llave, valor)
registro.poner_alias(u["modelo"], "candidato", v.version)
dbutils.jobs.taskValues.set(key="version_candidato", value=int(v.version))
print(f"{u['modelo']} v{v.version} @candidato · WAPE validación {m['wape']:.2%} · datos hasta {corte}")
