# Databricks notebook source
# MAGIC %md
# MAGIC # Tarea 0 · preparar ambiente: esquema, volumen, datos de referencia y modelo promovido
# MAGIC Parámetros del job: `usuario`, `ambiente`, `ambiente_origen` (por defecto `dev`). Idempotente: correrla dos veces deja
# MAGIC el ambiente igual. Lo que hace, y lo que haría en Azure:
# MAGIC
# MAGIC | Paso | Aquí (Free Edition) | En Azure Databricks |
# MAGIC |---|---|---|
# MAGIC | Esquema y volumen | `CREATE SCHEMA/VOLUME IF NOT EXISTS` | catálogo del ambiente creado por la plataforma (Terraform o bundle) |
# MAGIC | Archivos de landing | se copian los que falten desde el landing de `dev` | cada ambiente lee su fuente: qa una copia anonimizada, prod la real |
# MAGIC | `dim_ciiu` | `DEEP CLONE` desde `dev` | la misma tabla de referencia, publicada por su dueño |
# MAGIC | Modelo | `copy_model_version` de `@champion` y `@challenger` desde `dev` | promoción del artefacto o reentrenamiento en el ambiente (clase 15) |

# COMMAND ----------

dbutils.widgets.text("usuario", "")
dbutils.widgets.text("ambiente", "qa")
dbutils.widgets.text("ambiente_origen", "dev")
usuario = dbutils.widgets.get("usuario").strip().lower()
ambiente = dbutils.widgets.get("ambiente").strip().lower()
origen_amb = dbutils.widgets.get("ambiente_origen").strip().lower()
assert usuario, "Falta el parámetro usuario"
if ambiente == origen_amb:
    dbutils.notebook.exit(f"{ambiente} es el ambiente de origen: no se prepara, se usa como está")

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

destino, origen = ubicacion(usuario, ambiente), ubicacion(usuario, origen_amb)
print(f"{origen['fqn']} → {destino['fqn']}")

# COMMAND ----------

# 1 · Esquema y volumen del ambiente
spark.sql(f"CREATE SCHEMA IF NOT EXISTS {destino['fqn']} COMMENT 'xm-demanda · ambiente {ambiente} · lo crea el bundle'")
spark.sql(f"CREATE VOLUME IF NOT EXISTS {destino['fqn']}.raw COMMENT 'Archivos de landing y checkpoints del ambiente {ambiente}'")

# 2 · Archivos de landing que falten (nunca se sobrescribe uno que ya está)
dbutils.fs.mkdirs(destino["landing"])
ya = {f.name for f in dbutils.fs.ls(destino["landing"])}
nuevos = [f for f in dbutils.fs.ls(origen["landing"]) if not f.name.endswith("/") and f.name not in ya]
for f in nuevos:
    dbutils.fs.cp(f.path, f"{destino['landing']}/{f.name}")
print(f"landing: {len(ya)} archivos ya estaban · {len(nuevos)} copiados")

# 3 · Tabla de referencia
spark.sql(f"CREATE TABLE IF NOT EXISTS {destino['fqn']}.dim_ciiu DEEP CLONE {origen['fqn']}.dim_ciiu")
print("dim_ciiu:", spark.table(f"{destino['fqn']}.dim_ciiu").count(), "filas")

# COMMAND ----------

# 4 · Modelo: se promueve el artefacto (mismos pesos, mismo código empaquetado) con su linaje en un tag
import mlflow

from xm_demanda.monitoreo.linaje import linaje

mlflow.set_registry_uri("databricks-uc")
cliente = mlflow.MlflowClient()


def version_copiada(nombre_destino, uri_origen):
    """La versión del destino que ya es copia de uri_origen, o None. Así la tarea es idempotente."""
    try:
        versiones = cliente.search_model_versions(f"name='{nombre_destino}'")
    except Exception:  # noqa: BLE001  el modelo aún no existe en el ambiente
        return None
    for v in versiones:
        if cliente.get_model_version(nombre_destino, v.version).tags.get("origen") == uri_origen:
            return v.version
    return None


for alias in ("champion", "challenger"):
    src = cliente.get_model_version_by_alias(origen["modelo"], alias)
    uri = f"models:/{origen['modelo']}/{src.version}"
    v = version_copiada(destino["modelo"], uri)
    if v is None:
        nueva = cliente.copy_model_version(src_model_uri=uri, dst_name=destino["modelo"])
        v = nueva.version
        cliente.set_model_version_tag(destino["modelo"], v, "origen", uri)
        cliente.set_model_version_tag(destino["modelo"], v, "promovido_por", "job preparar_ambiente")
        for llave, valor in linaje(cliente, src).items():  # la copia hereda el linaje (clase 15)
            if valor is not None and valor == valor:
                cliente.set_model_version_tag(destino["modelo"], v, llave, str(valor))
    cliente.set_registered_model_alias(destino["modelo"], alias, v)
    print(f"{destino['modelo']}@{alias} → versión {v}  (copia de {uri})")
