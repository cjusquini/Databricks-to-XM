# Databricks notebook source
# MAGIC %md
# MAGIC # Tarea 4 · oro: features con contrato
# MAGIC Parámetros del job: `usuario`, `ambiente`. Publica el *task value* `ultima_fecha`.

# COMMAND ----------

dbutils.widgets.text("usuario", "")
dbutils.widgets.text("ambiente", "dev")
usuario = dbutils.widgets.get("usuario").strip().lower()
ambiente = dbutils.widgets.get("ambiente").strip().lower()
assert usuario, "Falta el parámetro usuario"

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
T_DIARIA, T_FEATURES = f"{esquema}.demanda_diaria", f"{esquema}.features_demanda_diaria"
print(f"ambiente {ambiente} · esquema {u['fqn']}")

# COMMAND ----------

import pandas as pd
from pyspark.sql import functions as F

import xm_demanda.features.build as fb
from xm_demanda.utils.config import load_config

cfg = load_config(ambiente)
festivos = spark.createDataFrame(pd.read_csv(os.path.join(raiz, "data", "reference", "festivos_co.csv"), parse_dates=["fecha"]))
festivos = festivos.withColumn("fecha", F.to_date("fecha"))
features = fb.construir_features(spark.table(T_DIARIA), festivos, cfg)
fb.merge_features(spark, features, T_FEATURES)

oro = spark.table(T_FEATURES)
assert set(oro.columns) == set(fb.columnas_contrato(cfg)), "La tabla de oro no cumple el contrato (clase 8)"
ultima_fecha = str(oro.agg(F.max("fecha")).first()[0])
dbutils.jobs.taskValues.set(key="ultima_fecha", value=ultima_fecha)
print(f"oro: {oro.count():,} filas · última fecha {ultima_fecha}")
