# Databricks notebook source
# MAGIC %md
# MAGIC # Tarea 1 · bronce: ingesta incremental con Auto Loader
# MAGIC Parámetros del job: `usuario`, `ambiente`, `forzar`. Lee los archivos nuevos de landing del ambiente (`availableNow`),
# MAGIC refresca la vista vigente y publica los *task values* `filas_nuevas` y `procesar`. Misma lógica de la clase 12: lo único
# MAGIC nuevo es que los nombres salen de `ubicacion(usuario, ambiente)`.

# COMMAND ----------

dbutils.widgets.text("usuario", "")
dbutils.widgets.text("ambiente", "dev")
usuario = dbutils.widgets.get("usuario").strip().lower()
ambiente = dbutils.widgets.get("ambiente").strip().lower()
assert usuario, "Falta el parámetro usuario"
dbutils.widgets.text("forzar", "no")
forzar = dbutils.widgets.get("forzar").strip().lower() == "si"

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
landing, checkpoint = u["landing"], u["checkpoint"]
tabla = f"{esquema}.demanda_raw_bronze"
print(f"ambiente {ambiente} · esquema {u['fqn']}")

# COMMAND ----------

import xm_demanda.ingest.bronze as bronze

antes = spark.table(tabla).count() if spark.catalog.tableExists(tabla) else 0
bronze.ingestar_bronce(spark, landing, tabla, checkpoint)
despues = spark.table(tabla).count()
nuevas = despues - antes

spark.sql(f"""
CREATE OR REPLACE VIEW {esquema}.demanda_raw_vigente
COMMENT 'Última publicación por serie-día-variable sobre demanda_raw_bronze'
AS
SELECT * EXCEPT (rn) FROM (
  SELECT *,
    row_number() OVER (
      PARTITION BY Fecha, CodigoVariable, CodigoSICAgente, MercadoComercializacion, TipoMercado, ClasificacionIndustrial
      ORDER BY _publication_date DESC, _ingested_at DESC
    ) AS rn
  FROM {tabla})
WHERE rn = 1
""")

procesar = "si" if nuevas > 0 or forzar else "no"
dbutils.jobs.taskValues.set(key="filas_nuevas", value=nuevas)
dbutils.jobs.taskValues.set(key="procesar", value=procesar)
print(f"bronce: {antes:,} → {despues:,} filas ({nuevas:,} nuevas) · forzar={forzar} · procesar={procesar}")
