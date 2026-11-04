# Databricks notebook source
# MAGIC %md
# MAGIC # Clase 13 — Declarative Automation Bundles y ambientes: el mismo código en dev, qa y prod
# MAGIC
# MAGIC En la clase 12 el job se creó con la Jobs API desde un notebook, y corría la copia de tu Git folder. Funciona, pero no
# MAGIC es un producto: no hay una forma repetible de llevar **exactamente lo mismo** a otro ambiente. Hoy el job, sus tareas y
# MAGIC sus ambientes se declaran en el repositorio y se despliegan con un solo comando. Eso es un **bundle**.
# MAGIC
# MAGIC ```
# MAGIC   repositorio (Git)                                  workspace
# MAGIC   ├── databricks.yml   qué es, a dónde va      deploy -t dev  ─►  workspace.c01_<usuario>       [dev] tu espacio
# MAGIC   ├── resources/*.yml  qué corre (jobs)         deploy -t qa   ─►  workspace.c01_<usuario>_qa    copia fiel de prod
# MAGIC   ├── notebooks/tareas tareas delgadas          deploy -t prod ─►  workspace.c01_<usuario>_prod  lo que consume el negocio
# MAGIC   └── src/xm_demanda   la lógica, con tests
# MAGIC ```
# MAGIC
# MAGIC Tres `TODO`: `esquema_de()` en `src/xm_demanda/utils/ambiente.py` (sección 2), la variable `usuario` (sección 4) y el
# MAGIC target `qa` (sección 5) en `databricks.yml`. Dos preguntas por escrito. Requiere el lab 12 completo, incluida la
# MAGIC sección 7 (el archivo tardío en tu landing), y haber hecho **Pull** de `main` en tu Git folder.

# COMMAND ----------

# MAGIC %pip install -q pytest pyyaml

# COMMAND ----------

dbutils.widgets.text("usuario", "")
usuario = dbutils.widgets.get("usuario").strip().lower()
assert usuario, "Escribe tu usuario (el sufijo de tu esquema c01_<usuario>)."

# COMMAND ----------

import importlib
import os
import sys
from datetime import timedelta

import pandas as pd
import yaml
from databricks.sdk import WorkspaceClient


def _raiz_repo():
    d = os.getcwd()
    for _ in range(8):
        if os.path.exists(os.path.join(d, "databricks.yml")):
            return d
        d = os.path.dirname(d)
    raise FileNotFoundError("No encuentro databricks.yml: ejecuta este notebook desde tu Git folder.")


raiz = _raiz_repo()
sys.path.insert(0, os.path.join(raiz, "src"))
sys.dont_write_bytecode = True
import xm_demanda.utils.ambiente as amb

importlib.reload(amb)
w = WorkspaceClient()
email = w.current_user.me().user_name
print("Raíz del bundle:", raiz, "| tú:", email)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1 · Qué es un bundle y por qué no basta con un job bien hecho
# MAGIC
# MAGIC ![Anatomía de un bundle](./../img/bundle_anatomia.png)
# MAGIC
# MAGIC | Pieza de `databricks.yml` | Qué declara | En este repositorio |
# MAGIC |---|---|---|
# MAGIC | `bundle.name` | el producto | `xm-demanda` |
# MAGIC | `include` | dónde están los recursos | `resources/*.yml`: `job_diario` y `preparar_ambiente` |
# MAGIC | `variables` | lo que cambia sin tocar el código | `usuario`, `git_sha` (lo llena CI/CD en la clase 14) |
# MAGIC | `targets` | los ambientes y sus reglas | `dev` (modo desarrollo), `qa` y `prod` (modo producción) |
# MAGIC | `sync.exclude` | qué **no** viaja al workspace | material de clase, datos crudos, docs, tests |
# MAGIC | sustituciones | valores que resuelve el deploy | `${bundle.target}`, `${var.usuario}`, `${workspace.current_user.userName}` |
# MAGIC
# MAGIC El cambio de fondo es de **fuente de verdad**. Con el job de la clase 12, la verdad estaba en el workspace: si alguien
# MAGIC editaba un timeout en la interfaz, el repo ya no describía lo que corría. Con un bundle, la verdad está en Git: el
# MAGIC workspace es el resultado de un `deploy`, y en modo producción los recursos quedan bloqueados para edición en la UI.
# MAGIC
# MAGIC Tres formas de desplegar el **mismo** bundle, con el mismo resultado:
# MAGIC
# MAGIC | Desde | Cómo | Cuándo |
# MAGIC |---|---|---|
# MAGIC | El workspace | abrir `databricks.yml` → panel **Deployments** (ícono de cohete) → target → **Deploy** | hoy: no hay que instalar nada |
# MAGIC | La CLI | `databricks bundle validate -t qa` · `databricks bundle deploy -t qa` · `databricks bundle run job_diario -t qa` | en tu computador, o en un runner |
# MAGIC | CI/CD | los mismos comandos dentro de GitHub Actions o Azure DevOps | clase 14: nadie despliega a mano a qa ni a prod |

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2 · Qué cambia entre ambientes, qué no, y el TODO 1
# MAGIC
# MAGIC ![Ambientes en Free Edition y en Azure](./../img/ambientes_free_azure.png)
# MAGIC
# MAGIC | Cambia entre dev, qa y prod | No cambia nunca |
# MAGIC |---|---|
# MAGIC | **dónde** se escribe (esquema aquí; catálogo y workspace en Azure) | el código de `src/` y de las tareas |
# MAGIC | **con qué datos**: dev y qa pueden usar copias; prod lee la fuente oficial de XM | el DAG y la política de fallas |
# MAGIC | **quién** ejecuta: tú en dev; un *service principal* en qa y prod | el contrato de oro y las reglas de calidad |
# MAGIC | **cada cuánto**: en dev, calendario en pausa; en prod, a las 6:00 o al llegar el archivo | la versión del modelo que se promueve |
# MAGIC | **quién se entera**: tu correo en dev; el grupo de operación en prod | |
# MAGIC
# MAGIC En el sector esto no es estética. Si el pronóstico publicado a planeación se calcula con un código distinto del que se
# MAGIC probó, la trazabilidad que pide un auditor (¿qué versión, con qué datos, quién la aprobó?) se rompe en el primer paso.
# MAGIC
# MAGIC Todas las tareas obtienen los nombres de un solo lugar: `ubicacion(usuario, ambiente)` en
# MAGIC `src/xm_demanda/utils/ambiente.py`, que lee `conf/<ambiente>.yml`. **TODO 1:** completa `esquema_de()`:
# MAGIC
# MAGIC | Entrada | Salida |
# MAGIC |---|---|
# MAGIC | `esquema_de(" Ana ", "dev", "")` | `"c01_ana"` (se normaliza) |
# MAGIC | `esquema_de("ana", "qa", "_qa")` | `"c01_ana_qa"` |
# MAGIC | `esquema_de("ana", "staging", "")` | `ValueError`: un ambiente no se adivina |
# MAGIC | `esquema_de("ana-perez", "dev", "")` | `ValueError`: `PATRON_USUARIO` no admite guiones ni espacios |
# MAGIC
# MAGIC ¿Por qué tanto rigor con un nombre? Porque el nombre del esquema termina dentro de un `CREATE SCHEMA` y de un `GRANT`:
# MAGIC un usuario mal escrito no debe crear un ambiente nuevo en silencio.

# COMMAND ----------

import pytest

codigo = pytest.main(["-q", "-p", "no:cacheprovider", "-rs",
                      os.path.join(raiz, "tests", "unit", "test_ambiente.py"),
                      os.path.join(raiz, "tests", "unit", "test_config.py")])
print("pytest →", codigo, "(0 = todo pasó)")

# COMMAND ----------

importlib.reload(amb)
filas = []
for a in amb.AMBIENTES:
    u = amb.ubicacion(usuario, a)
    filas.append({"ambiente": a, "esquema": u["fqn"], "landing": u["landing"], "modelo": u["modelo"]})
display(pd.DataFrame(filas))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3 · Del diccionario de la clase 12 al YAML del bundle
# MAGIC
# MAGIC `resources/job_diario.yml` es el mismo job de la clase 12, con dos diferencias: las tareas viven ahora en
# MAGIC `notebooks/tareas/` (el producto) y no en `clases/c12-jobs/` (material de clase), y reciben un parámetro nuevo,
# MAGIC `ambiente`, cuyo valor no lo decide nadie a mano: es `${bundle.target}`.
# MAGIC
# MAGIC | Clase 12 (`job.py` + Jobs API) | Clase 13 (bundle) |
# MAGIC |---|---|
# MAGIC | `definicion_job(usuario, ruta_tareas, email)` | `resources/job_diario.yml` |
# MAGIC | `jobs/create` o `jobs/reset` | `databricks bundle deploy` |
# MAGIC | `ruta_tareas` = tu Git folder | `notebook_path: ../notebooks/tareas/…`, relativo al YAML |
# MAGIC | el nombre lo arma `nombre_job()` | `[xm-demanda] diario · ${var.usuario} · ${bundle.target}` |
# MAGIC | `email` del notebook | `${workspace.current_user.userName}` |
# MAGIC
# MAGIC Y una regla nueva, que vale para todo lo que es infraestructura: **dos descripciones del mismo job se separan solas**.
# MAGIC `tests/unit/test_bundle.py` lee el YAML y lo compara con `job.py`: mismo orden de tareas, mismas dependencias, misma
# MAGIC política de fallas, y el chequeo dependiendo de bronce. Si alguien cambia uno y no el otro, el CI lo detiene.
# MAGIC
# MAGIC Limpieza: los YAML que traía la plantilla del repo (`job_features`, `job_inference`, `job_train`, `pipeline_silver`)
# MAGIC apuntaban a catálogos `dev/qa/prod` que Free Edition no tiene, y nunca se desplegaron. Se borraron: un recurso que no se
# MAGIC despliega confunde. Los notebooks `notebooks/01…05` quedan como referencia de las clases 5 a 11; lo que se despliega es
# MAGIC `notebooks/tareas/`.

# COMMAND ----------

job_yaml = yaml.safe_load(open(os.path.join(raiz, "resources", "job_diario.yml")))["resources"]["jobs"]["job_diario"]
print(job_yaml["name"])
print("parámetros:", {p["name"]: p["default"] for p in job_yaml["parameters"]})
for t in job_yaml["tasks"]:
    extra = {k: t[k] for k in ("max_retries", "run_if", "timeout_seconds", "condition_task") if k in t}
    print(f"  {t['task_key']:17s} ← {[d['task_key'] for d in t.get('depends_on', [])]!s:24s} {extra}")

codigo = pytest.main(["-q", "-p", "no:cacheprovider", "-rs", os.path.join(raiz, "tests", "unit", "test_bundle.py")])
print("pytest test_bundle →", codigo)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4 · El primer deploy, el que falla, y el TODO 2
# MAGIC
# MAGIC 1. Abre `databricks.yml` en tu Git folder (la raíz del repo). Arriba a la derecha aparece el ícono de **Deployments**.
# MAGIC 2. En el panel, elige el target **dev** y haz clic en **Deploy**. Va a fallar: la variable `usuario` no tiene valor.
# MAGIC    Lee el mensaje: dice qué variable falta y dónde se puede poner. Eso es **validación**: el bundle se niega a desplegar
# MAGIC    algo ambiguo, antes de tocar el workspace.
# MAGIC 3. **TODO 2:** en `databricks.yml`, dale a `usuario` un `default` con tu usuario. Guarda.
# MAGIC 4. **Deploy** otra vez. En **Project output** verás la validación y el despliegue; en **Bundle resources**, los dos jobs.
# MAGIC
# MAGIC Lo que hace `mode: development` con tu deploy:
# MAGIC
# MAGIC | Efecto | Por qué |
# MAGIC |---|---|
# MAGIC | prefijo `[dev <tu usuario>]` en el nombre de cada job | en un workspace compartido, cada quien ve el suyo |
# MAGIC | calendarios y disparadores en pausa | un dev olvidado no corre todos los días |
# MAGIC | corre sobre los archivos de tu Git folder (*source-linked*) | editas, guardas y corres, sin redesplegar |
# MAGIC | sin bloqueo de despliegue, corridas concurrentes permitidas | iterar rápido |
# MAGIC
# MAGIC La celda de abajo busca lo que desplegaste y lo describe como lo ve el workspace.

# COMMAND ----------

def jobs_del_bundle(recurso):
    """{ambiente: Job} de los jobs de este bundle para tu usuario (dev, qa, prod)."""
    encontrados = {}
    for j in w.jobs.list():
        nombre = (j.settings.name if j.settings else "") or ""
        for a in amb.AMBIENTES:
            if nombre.endswith(f"{recurso} · {usuario} · {a}"):
                encontrados[a] = w.jobs.get(j.job_id)
    return encontrados


def describir(job):
    s = job.settings
    return {
        "nombre": s.name,
        "job_id": job.job_id,
        "desplegado_por": s.deployment.kind.value if s.deployment else "API/UI",
        "edición": s.edit_mode.value if s.edit_mode else "—",
        "calendario": s.schedule.pause_status.value if s.schedule else "—",
        "tags": s.tags,
    }


diario = jobs_del_bundle("diario")
assert "dev" in diario, "No encuentro el job de dev: ¿hiciste Deploy al target dev?"
display(pd.DataFrame([describir(j) for j in diario.values()]))

# COMMAND ----------

corrida = w.jobs.run_now_and_wait(diario["dev"].job_id, timeout=timedelta(minutes=30))
print("dev:", corrida.state.result_state.value, "·", corrida.run_page_url)
for t in corrida.tasks:
    print(f"  {t.task_key:17s} {t.state.result_state.value}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5 · qa: modo producción, el TODO 3, y un ambiente que se prepara solo
# MAGIC
# MAGIC **TODO 3:** escribe el target `qa` en `databricks.yml`. Mira `prod`: qa tiene que ser igual, porque qa existe para
# MAGIC probar **exactamente** lo que irá a producción. Si qa se configura distinto, lo que pasa en qa no dice nada de prod.
# MAGIC
# MAGIC | | `mode: development` | `mode: production` |
# MAGIC |---|---|---|
# MAGIC | nombres | `[dev usuario] …` | tal cual (`… · qa`) |
# MAGIC | calendarios | en pausa | como estén en el YAML |
# MAGIC | edición en la UI | permitida | bloqueada: se cambia en Git y se redespliega |
# MAGIC | exige | nada | `run_as` y `permissions` explícitos (o un service principal), y una sola copia (`root_path` fijo) |
# MAGIC | identidad | tú | en Free Edition, tú; en Azure, el service principal de qa |
# MAGIC
# MAGIC Luego: **Deployments** → target **qa** → **Deploy**. Y en **Bundle resources**, corre primero
# MAGIC `preparar_ambiente` (▶) y después `job_diario`. O deja que lo haga la celda de abajo.
# MAGIC
# MAGIC `preparar_ambiente` crea el esquema y el volumen de qa, copia los archivos de landing que falten, clona `dim_ciiu` con
# MAGIC `DEEP CLONE` y **promueve el modelo**: copia las versiones `@champion` y `@challenger` de dev al registro de qa con
# MAGIC `copy_model_version`, y deja en cada copia un tag `origen` con la versión de la que viene. En la clase 14 se discute si
# MAGIC eso es lo correcto (promover el artefacto) o si cada ambiente debería entrenar el suyo.

# COMMAND ----------

preparar, diario = jobs_del_bundle("preparar ambiente"), jobs_del_bundle("diario")
assert "qa" in preparar and "qa" in diario, "No encuentro los jobs de qa: ¿escribiste el target y desplegaste?"
for nombre, job in (("preparar_ambiente", preparar["qa"]), ("job_diario", diario["qa"])):
    r = w.jobs.run_now_and_wait(job.job_id, timeout=timedelta(minutes=30))
    print(f"qa · {nombre}: {r.state.result_state.value} en {(r.end_time - r.start_time) / 60000:.1f} min · {r.run_page_url}")

# COMMAND ----------

def resumen_ambiente(a):
    u = amb.ubicacion(usuario, a)
    fila = {"ambiente": a, "esquema": u["fqn"]}
    for t in ("demanda_raw_bronze", "demanda_diaria", "features_demanda_diaria", "pronostico_demanda"):
        fila[t] = spark.table(f"{u['fqn']}.{t}").count() if spark.catalog.tableExists(f"{u['fqn']}.{t}") else None
    if fila["pronostico_demanda"]:
        fila["pronóstico hasta"] = str(spark.sql(f"SELECT max(fecha_pronostico) FROM {u['fqn']}.pronostico_demanda "
                                                 "WHERE alias = 'champion'").first()[0])
    return fila


display(pd.DataFrame([resumen_ambiente(a) for a in ("dev", "qa")]))

import mlflow

mlflow.set_registry_uri("databricks-uc")
cliente = mlflow.MlflowClient()
for a in ("dev", "qa"):
    m = amb.ubicacion(usuario, a)["modelo"]
    for alias in ("champion", "challenger"):
        mv = cliente.get_model_version_by_alias(m, alias)
        print(f"{m}@{alias} → v{mv.version}  origen: {mv.tags.get('origen', '(entrenado aquí)')}")

# COMMAND ----------

# MAGIC %md
# MAGIC Lee las dos tablas juntas. qa tiene **sus propias** tablas, construidas por el job de qa desde su propio landing: no lee
# MAGIC nada de dev, salvo lo que `preparar_ambiente` copió de forma explícita y trazable. Si bronce de qa tiene más filas que
# MAGIC bronce de dev, es normal: en dev, bronce acumula también las pruebas de las clases 4 y 5; en qa entra solo lo que está
# MAGIC hoy en landing. Lo que sí debe coincidir es el resultado: el pronóstico llega hasta el mismo día.
# MAGIC
# MAGIC ## 6 · prod, y cómo sería en Azure
# MAGIC
# MAGIC **No despliegues prod a mano.** En la clase 14 lo hace el pipeline de CI/CD, después de qa y con una aprobación. Ese es
# MAGIC el punto: a producción no se llega por un clic de alguien, se llega por un camino que deja rastro.
# MAGIC
# MAGIC | Aquí (Free Edition) | En Azure Databricks (XM) |
# MAGIC |---|---|
# MAGIC | un workspace, un catálogo `workspace`, un esquema por ambiente | un workspace por ambiente; un catálogo por ambiente ligado a su workspace (*workspace-catalog binding*), en el mismo metastore regional |
# MAGIC | `workspace.host` implícito | `workspace.host` del workspace de cada target |
# MAGIC | `run_as: user_name` = tú | `run_as: service_principal_name` = el SP de Entra ID de qa o prod |
# MAGIC | `permissions`: tú | grupos: `analitica-xm-desarrollo` (CAN_VIEW en prod), `analitica-xm-operacion` (CAN_MANAGE_RUN) |
# MAGIC | el bundle crea el esquema (tarea 0) | la plataforma (Terraform) crea workspaces, catálogos, almacenamiento y redes; el bundle despliega el **producto** |
# MAGIC
# MAGIC La última fila es la frontera que más se discute en los equipos: **Terraform para la plataforma, bundles para el
# MAGIC producto**. El equipo de analítica no debería necesitar permisos para crear un workspace para desplegar su job.

# COMMAND ----------

# MAGIC %md
# MAGIC **Pregunta 1 (respóndela aquí):** un compañero edita el timeout de la tarea `inferencia` directamente en la interfaz del
# MAGIC job de qa porque "era urgente". ¿Qué pasa con ese cambio en el siguiente deploy? ¿Por qué el modo producción intenta
# MAGIC impedirlo, y qué debería haber hecho?
# MAGIC
# MAGIC > Tu respuesta:
# MAGIC
# MAGIC **Pregunta 2 (respóndela aquí):** en analitica_trv (o en tu proyecto real) hoy no hay ambientes. Si mañana se crean
# MAGIC `analitica_trv_dev`, `_qa` y `analitica_trv`, ¿qué tres cosas de su código tendrían que cambiar para poder usar un
# MAGIC bundle como este? Piensa en nombres escritos a mano, en quién ejecuta y en de dónde salen los datos.
# MAGIC
# MAGIC > Tu respuesta:

# COMMAND ----------

# MAGIC %md
# MAGIC ## Verificación
# MAGIC Cuando todo esté en OK: commit `feat(c13): bundle con ambientes dev y qa, tareas parametrizadas por ambiente` desde el
# MAGIC Git folder (incluye `databricks.yml` y `src/xm_demanda/utils/ambiente.py`), push, PR, CI en verde, merge.

# COMMAND ----------

def verificar():
    checks = []
    importlib.reload(amb)
    try:
        checks.append(("esquema_de() implementada", amb.esquema_de("Ana", "qa", "_qa") == "c01_ana_qa"))
    except NotImplementedError:
        checks.append(("esquema_de() implementada", False))
    bundle = yaml.safe_load(open(os.path.join(raiz, "databricks.yml")))
    checks.append(("databricks.yml: usuario con default", bool(bundle["variables"]["usuario"].get("default"))))
    qa = bundle["targets"].get("qa") or {}
    checks.append(("databricks.yml: target qa en modo producción con run_as y permissions",
                   qa.get("mode") == "production" and bool(qa.get("run_as")) and bool(qa.get("permissions"))))
    diario = jobs_del_bundle("diario")
    dev = diario.get("dev")
    checks.append(("Job de dev desplegado por el bundle, con prefijo [dev …]",
                   bool(dev) and dev.settings.deployment is not None and dev.settings.name.startswith("[dev")))
    jq = diario.get("qa")
    checks.append(("Job de qa desplegado sin prefijo y con tag ambiente=qa",
                   bool(jq) and not jq.settings.name.startswith("[dev") and (jq.settings.tags or {}).get("ambiente") == "qa"))
    ultima = list(w.jobs.list_runs(job_id=jq.job_id, limit=1)) if jq else []
    checks.append(("Última corrida del job de qa exitosa",
                   bool(ultima) and ultima[0].state.result_state is not None and ultima[0].state.result_state.value == "SUCCESS"))
    try:
        u = amb.ubicacion(usuario, "qa")
        mv = mlflow.MlflowClient().get_model_version_by_alias(u["modelo"], "champion")
        checks.append(("Modelo de qa @champion con tag origen (promovido)", "origen" in mv.tags))
        hasta = {a: str(spark.sql(f"SELECT max(fecha_pronostico) FROM {amb.ubicacion(usuario, a)['fqn']}.pronostico_demanda "
                                  "WHERE alias = 'champion'").first()[0]) for a in ("dev", "qa")}
        checks.append((f"Pronóstico de dev y qa hasta el mismo día ({hasta['dev']} · {hasta['qa']})", hasta["dev"] == hasta["qa"]))
    except Exception as e:  # noqa: BLE001
        checks.append((f"qa poblado ({type(e).__name__})", False))
    print()
    for nombre, ok in checks:
        print(("OK   " if ok else "FALTA") + "  " + nombre)
    print("\nListo: commit y push." if all(ok for _, ok in checks) else "\nRevisa los puntos marcados FALTA.")


verificar()
