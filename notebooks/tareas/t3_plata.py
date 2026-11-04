# Databricks notebook source
# MAGIC %md
# MAGIC # Tarea 3 · plata: formato ancho, sección CIIU y MERGE
# MAGIC Parámetros del job: `usuario`, `ambiente`. Falla si aparece un texto CIIU que `dim_ciiu` no conoce. En un ambiente
# MAGIC recién creado la tabla de plata aún no existe: el MERGE de la clase 6 la crea vacía la primera vez.

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
T_VALIDADA, T_DIARIA, T_CIIU = (f"{esquema}.{t}" for t in ("demanda_validada", "demanda_diaria", "dim_ciiu"))
print(f"ambiente {ambiente} · esquema {u['fqn']}")

# COMMAND ----------

from pyspark.sql import functions as F

import xm_demanda.silver.transform as silver

fuente = spark.table(T_VALIDADA).filter("_source_file <> 'sintetico_lab05'")
secciones = (spark.table(T_CIIU).filter("nombre_fuente IS NOT NULL")
             .select(F.col("nombre_fuente").alias("clasificacion_industrial"), F.col("codigo").alias("ciiu_seccion")))
ancho = silver.a_formato_ancho(fuente).join(F.broadcast(secciones), "clasificacion_industrial", "left")

sin_seccion = [r[0] for r in ancho.filter("ciiu_seccion IS NULL").select("clasificacion_industrial").distinct().collect()]
assert not sin_seccion, f"Textos CIIU sin sección (agrega el alias en ALIAS_CIIU): {sin_seccion}"

antes = spark.table(T_DIARIA).count() if spark.catalog.tableExists(T_DIARIA) else 0
silver.merge_demanda_diaria(spark, ancho, T_DIARIA)
ultima = spark.sql(f"DESCRIBE HISTORY {T_DIARIA} LIMIT 1").first()["operationMetrics"]
print(f"plata: {antes:,} → {spark.table(T_DIARIA).count():,} serie-días · insertadas {ultima.get('numTargetRowsInserted')}"
      f" · actualizadas {ultima.get('numTargetRowsUpdated')}")
