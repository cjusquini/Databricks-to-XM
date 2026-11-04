# Databricks notebook source
# MAGIC %md
# MAGIC # Clase 14 — CI/CD y promoción entre ambientes: a producción se llega por un camino, no por un clic
# MAGIC
# MAGIC En la clase 13 desplegaste dev y qa a mano, desde el workspace. Hoy nadie despliega a mano: un **pipeline** en GitHub
# MAGIC Actions prueba cada cambio, despliega dev al hacer merge, y promueve un **tag** de versión a qa y, con una aprobación,
# MAGIC a prod. Este notebook no ejecuta el pipeline: lo explica, y después audita desde Databricks lo que el pipeline dejó.
# MAGIC
# MAGIC ```
# MAGIC   rama ──PR──► test · integration · validate ──merge──► deploy-dev
# MAGIC                (si algo falla, no hay merge)
# MAGIC   git tag v1.0.0 ──► CI ──► deploy-qa ──► [ aprobación en GitHub ] ──► deploy-prod
# MAGIC                            deploy + preparar_ambiente + job_diario        lo mismo, en prod
# MAGIC                            (el chequeo de frescura es la prueba de integración)
# MAGIC ```
# MAGIC
# MAGIC Un `TODO`: el job `deploy-prod` en `.github/workflows/ci.yml` (sección 3). Dos preguntas por escrito. Requiere el lab 13
# MAGIC completo, tu fork en GitHub **público** (las aprobaciones de *environments* en planes gratuitos solo existen en
# MAGIC repositorios públicos) y Actions habilitado en el fork.

# COMMAND ----------

# MAGIC %pip install -q pytest pyyaml

# COMMAND ----------

dbutils.widgets.text("usuario", "")
usuario = dbutils.widgets.get("usuario").strip().lower()
assert usuario, "Escribe tu usuario (el sufijo de tu esquema c01_<usuario>)."

# COMMAND ----------

import os
import sys

import mlflow
import pandas as pd
import pytest
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

w = WorkspaceClient()
mlflow.set_registry_uri("databricks-uc")
cliente = mlflow.MlflowClient()
print("Raíz:", raiz, "| tú:", w.current_user.me().user_name)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1 · CI, CD y entrega continua: tres cosas distintas
# MAGIC
# MAGIC ![El pipeline de CI/CD](./../img/pipeline_cicd.png)
# MAGIC
# MAGIC | Término | Pregunta que responde | En `ci.yml` |
# MAGIC |---|---|---|
# MAGIC | **Integración continua (CI)** | ¿este cambio rompe algo? | `test` (ruff + pytest unit, incluidas las pruebas del bundle y del pipeline), `integration` (Spark local), `validate` (el bundle contra el workspace real) |
# MAGIC | **Entrega continua (CD)** | ¿siempre tengo una versión lista para producción? | `deploy-dev` en cada merge; `deploy-qa` en cada tag |
# MAGIC | **Despliegue continuo** | ¿cada cambio llega solo a producción? | **no**, a propósito: `deploy-prod` espera una aprobación humana |
# MAGIC
# MAGIC ¿Por qué no despliegue continuo a prod? Porque el pronóstico de XM lo consumen planeación y terceros: una aprobación
# MAGIC deja escrito quién decidió publicar qué versión. Equipos con más madurez automatizan también esa decisión con
# MAGIC criterios medibles (la clase 15 hace eso para el modelo); pero la decisión sigue existiendo, solo cambia quién la toma.
# MAGIC
# MAGIC **Cómo se autentica el pipeline en Databricks:**
# MAGIC
# MAGIC | Mecanismo | Qué guarda GitHub | Dónde se usa |
# MAGIC |---|---|---|
# MAGIC | Token personal (PAT) | `DATABRICKS_TOKEN`, un secreto que vence | **aquí**: Free Edition, un estudiante, su fork |
# MAGIC | Token OAuth de un service principal | `DATABRICKS_CLIENT_ID` + secreto, o un token generado | equipos sin federación |
# MAGIC | **Federación de identidad (OIDC)** | nada secreto: GitHub emite un token por corrida y Databricks confía en él según una política (`repo:…:environment:prod`) | **lo recomendado** en producción; en Azure DevOps, la *service connection* con federación de Entra ID |
# MAGIC
# MAGIC La regla de fondo: un secreto que no existe no se puede filtrar. Con OIDC, el permiso de desplegar a prod queda atado a
# MAGIC **un repositorio y un environment**, no a una persona.

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2 · Configurar tu fork (en GitHub, unos 10 minutos)
# MAGIC
# MAGIC | Paso | Dónde | Qué |
# MAGIC |---|---|---|
# MAGIC | 1 | Databricks → tu avatar → **Settings** → **Developer** → **Access tokens** → **Generate new token** | comentario `github-actions-xm`, vida de 30 días. Cópialo: no se vuelve a mostrar |
# MAGIC | 2 | GitHub → tu fork → **Settings** → **Secrets and variables** → **Actions** → **Secrets** | `DATABRICKS_HOST` = la URL del workspace (sin `/` al final) · `DATABRICKS_TOKEN` = el token |
# MAGIC | 3 | misma página → pestaña **Variables** | `DATABRICKS_DEPLOY` = `true` (sin esto, los jobs de deploy se saltan) |
# MAGIC | 4 | **Settings** → **Environments** → **New environment** | `dev`, `qa` y `prod`. En `prod`: **Required reviewers** → tú mismo |
# MAGIC | 5 | **Settings** → **Rules** → **Rulesets** → **New branch ruleset** | sobre `main`: *Require a pull request before merging* y *Require status checks to pass* con `test` e `integration` |
# MAGIC
# MAGIC El paso 5 es el que convierte el CI en una regla y no en una sugerencia. Sin él, cualquiera con permisos de escritura
# MAGIC puede hacer `git push origin main` y el pipeline se entera después.

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3 · TODO: el job `deploy-prod`
# MAGIC
# MAGIC Abre `.github/workflows/ci.yml`. `deploy-qa` está completo: despliega el bundle a qa, corre `preparar_ambiente` y corre
# MAGIC el `job_diario`. Ese último paso es la **prueba de integración**: si el chequeo de frescura de la clase 12 falla en qa,
# MAGIC `databricks bundle run` termina con error y el pipeline se detiene.
# MAGIC
# MAGIC `deploy-prod` está a medias. Le faltan las dos líneas que lo hacen seguro, y los dos pasos que lo prueban:
# MAGIC
# MAGIC | Falta | Para qué |
# MAGIC |---|---|
# MAGIC | `needs: deploy-qa` | prod solo corre si qa terminó bien. Sin esto, prod y qa corren **en paralelo** |
# MAGIC | `environment: prod` | GitHub pausa el job hasta que un *required reviewer* apruebe, y registra quién fue |
# MAGIC | `bundle run preparar_ambiente -t prod` y `bundle run job_diario -t prod` | prod queda poblado y probado, igual que qa |
# MAGIC
# MAGIC `tests/unit/test_cicd.py` revisa estas reglas, y también que no haya tokens en el YAML, que el `GITHUB_TOKEN` tenga el
# MAGIC mínimo permiso y que el commit desplegado quede registrado (`BUNDLE_VAR_git_sha`). El pipeline se prueba a sí mismo.

# COMMAND ----------

codigo = pytest.main(["-q", "-p", "no:cacheprovider", "-rs", os.path.join(raiz, "tests", "unit", "test_cicd.py")])
print("pytest test_cicd →", codigo, "(0 = todo pasó)")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4 · El flujo en vivo
# MAGIC
# MAGIC | # | Haces | Esperas ver en GitHub → **Actions** |
# MAGIC |---|---|---|
# MAGIC | a | rama `c14-rompe`, cambia `PATRON_USUARIO` para que acepte guiones, PR a `main` | `test` en rojo (`test_usuario_invalido`); el botón de merge bloqueado por el ruleset |
# MAGIC | b | revierte el cambio en la misma rama, incluye el TODO de `deploy-prod`, push | `test`, `integration`, `validate` en verde; merge permitido |
# MAGIC | c | merge del PR | `deploy-dev` en verde: el job `[dev …]` se redesplegó con el tag `git_sha` del merge |
# MAGIC | d | `git push origin main` directo desde tu computador o desde el Git folder | rechazado: *protected branch*. Eso es "un merge que se salta CI", y no pasa |
# MAGIC | e | `git tag v1.0.0` sobre `main` y `git push origin v1.0.0` (o **Releases** → *Draft a new release*) | `deploy-qa` corre (unos 8 min); luego `deploy-prod` queda en **Waiting**: *Review deployments* → **Approve** |
# MAGIC
# MAGIC Mientras qa corre, abre en Databricks **Jobs & Pipelines**: vas a ver `[xm-demanda] diario · <usuario> · qa` ejecutándose
# MAGIC **como tú**, lanzado por el pipeline. En Free Edition hay 5 tareas simultáneas por cuenta: si el grupo lanza a la vez,
# MAGIC las corridas esperan en cola.

# COMMAND ----------

def jobs_del_bundle(recurso):
    encontrados = {}
    for j in w.jobs.list():
        nombre = (j.settings.name if j.settings else "") or ""
        for a in amb.AMBIENTES:
            if nombre.endswith(f"{recurso} · {usuario} · {a}"):
                encontrados[a] = w.jobs.get(j.job_id)
    return encontrados


def auditoria(job, a):
    s = job.settings
    corridas = list(w.jobs.list_runs(job_id=job.job_id, limit=1))
    ultima = corridas[0] if corridas else None
    return {
        "ambiente": a,
        "git_sha": (s.tags or {}).get("git_sha", "—")[:10],
        "creado_por": job.creator_user_name,
        "run_as": job.run_as_user_name,
        "última corrida": pd.Timestamp(ultima.start_time, unit="ms", tz="America/Bogota").strftime("%Y-%m-%d %H:%M") if ultima else "—",
        "resultado": ultima.state.result_state.value if ultima and ultima.state.result_state else "—",
        "disparo": ultima.trigger.value if ultima and ultima.trigger else "—",
    }


diario = jobs_del_bundle("diario")
display(pd.DataFrame([auditoria(j, a) for a, j in sorted(diario.items())]))

# COMMAND ----------

# MAGIC %md
# MAGIC Esta tabla responde, desde Databricks, las tres preguntas de un auditor: **qué versión** corre en cada ambiente
# MAGIC (`git_sha`, que el pipeline inyecta como variable del bundle), **con qué identidad** (`run_as`) y **cuándo** fue la
# MAGIC última corrida. La cuarta, **quién aprobó**, vive en GitHub: tu fork → **Actions** → la corrida del tag → `deploy-prod`,
# MAGIC o **Settings** → **Environments** → `prod` → historial de despliegues. En Azure, Azure DevOps guarda la aprobación y los
# MAGIC *audit logs* de Databricks (`system.access.audit`) registran cada cambio en el workspace; Free Edition no da acceso a
# MAGIC las tablas de sistema de la cuenta.

# COMMAND ----------

filas = []
for a in ("dev", "qa", "prod"):
    u = amb.ubicacion(usuario, a)
    try:
        mv = cliente.get_model_version_by_alias(u["modelo"], "champion")
        hasta = spark.sql(f"SELECT max(fecha_pronostico) FROM {u['fqn']}.pronostico_demanda WHERE alias = 'champion'").first()[0]
        filas.append({"ambiente": a, "modelo": f"{u['modelo']} v{mv.version}", "origen": mv.tags.get("origen", "(entrenado aquí)"),
                      "pronóstico hasta": str(hasta)})
    except Exception as e:  # noqa: BLE001
        filas.append({"ambiente": a, "modelo": f"(sin modelo: {type(e).__name__})"})
display(pd.DataFrame(filas))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5 · Promover código, promover modelos
# MAGIC
# MAGIC ![Promover código o promover el modelo](./../img/promocion_codigo_modelo.png)
# MAGIC
# MAGIC Lo que acabas de ver promueve **dos cosas por caminos distintos**. El código viaja por Git y el pipeline (el mismo
# MAGIC commit en qa y en prod). El modelo viaja como artefacto: `preparar_ambiente` copia la versión `@champion` de dev a cada
# MAGIC ambiente con `copy_model_version`, y deja el tag `origen`.
# MAGIC
# MAGIC | | Promover el modelo (lo que hacemos hoy) | Promover el código y reentrenar en cada ambiente |
# MAGIC |---|---|---|
# MAGIC | qué viaja | los pesos ya entrenados | el código de entrenamiento |
# MAGIC | qa prueba | exactamente el artefacto que irá a prod | que el entrenamiento funciona con los datos del ambiente |
# MAGIC | conviene cuando | entrenar es caro, o prod no tiene permiso de leer otros datos | prod tiene sus propios datos, y el modelo debe reentrenarse ahí (clase 15) |
# MAGIC | riesgo | un modelo entrenado con datos de dev llega a prod | el modelo de prod no es idéntico al probado en qa |
# MAGIC
# MAGIC Databricks recomienda por defecto **promover el código** (*deploy code, not models*): los datos de producción no deberían
# MAGIC salir de producción, ni siquiera dentro de un modelo. En la clase 15, el job de reentrenamiento entrena en el ambiente,
# MAGIC compara con el champion y promueve solo si gana. La promoción por copia queda para el arranque de un ambiente nuevo.

# COMMAND ----------

# MAGIC %md
# MAGIC **Pregunta 1 (respóndela aquí):** borra mentalmente `needs: deploy-qa` del job `deploy-prod`. ¿Qué pasa cuando haces
# MAGIC push de un tag con un error que solo se manifiesta al correr el job en qa? ¿Y qué protege `environment: prod` que `needs`
# MAGIC no protege?
# MAGIC
# MAGIC > Tu respuesta:
# MAGIC
# MAGIC **Pregunta 2 (respóndela aquí):** en XM, ¿quién debería ser el *required reviewer* de prod para el pronóstico de demanda:
# MAGIC el científico de datos que hizo el cambio, su líder técnico, o alguien de planeación? ¿Qué información necesita ver esa
# MAGIC persona para aprobar con criterio y no por costumbre?
# MAGIC
# MAGIC > Tu respuesta:

# COMMAND ----------

# MAGIC %md
# MAGIC ## Verificación
# MAGIC Cuando todo esté en OK, el commit ya está hecho: es el que desplegó el tag. Abre en GitHub el resumen de la corrida del
# MAGIC tag y guarda el enlace: es la evidencia de la promoción.

# COMMAND ----------

def verificar():
    checks = []
    wf = yaml.safe_load(open(os.path.join(raiz, ".github", "workflows", "ci.yml")))
    prod = wf["jobs"]["deploy-prod"]
    needs = prod.get("needs", [])
    needs = [needs] if isinstance(needs, str) else needs
    checks.append(("ci.yml: deploy-prod depende de deploy-qa", "deploy-qa" in needs))
    checks.append(("ci.yml: deploy-prod con environment prod (aprobación)", prod.get("environment") == "prod"))
    checks.append(("ci.yml: deploy-prod corre el job en prod",
                   any("bundle run job_diario -t prod" in p.get("run", "") for p in prod["steps"])))
    diario = jobs_del_bundle("diario")
    shas = {a: (j.settings.tags or {}).get("git_sha", "manual") for a, j in diario.items()}
    checks.append(("Jobs de qa y prod desplegados por el pipeline (git_sha ≠ manual)",
                   all(shas.get(a, "manual") != "manual" for a in ("qa", "prod"))))
    checks.append(("qa y prod corren el mismo commit", shas.get("qa") is not None and shas.get("qa") == shas.get("prod")))
    for a in ("qa", "prod"):
        corridas = list(w.jobs.list_runs(job_id=diario[a].job_id, limit=1)) if a in diario else []
        ok = bool(corridas) and corridas[0].state.result_state is not None and corridas[0].state.result_state.value == "SUCCESS"
        checks.append((f"Última corrida del job de {a} exitosa", ok))
    try:
        mv = cliente.get_model_version_by_alias(amb.ubicacion(usuario, "prod")["modelo"], "champion")
        checks.append(("Modelo de prod @champion con linaje (tag origen)", "origen" in mv.tags))
    except Exception:  # noqa: BLE001
        checks.append(("Modelo de prod @champion con linaje (tag origen)", False))
    print()
    for nombre, ok in checks:
        print(("OK   " if ok else "FALTA") + "  " + nombre)
    print("\nPromoción completa." if all(ok for _, ok in checks) else "\nRevisa los puntos marcados FALTA.")


verificar()
