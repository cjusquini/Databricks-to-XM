# Lab 13 — El mismo código en dev y qa, desplegado con un bundle

**Duración:** 50 min (con el notebook guiado) · **Modalidad:** individual, en tu propio fork · **Rama:** `feature/c13-bundles`

## Objetivo

Declarar el producto como un bundle (código, jobs y ambientes), desplegarlo a `dev` y a `qa` desde el workspace, preparar `qa` desde `dev` (esquema, landing, `dim_ciiu` y modelo promovido) y comprobar que `qa` reproduce el pronóstico de `dev` con sus propias tablas.

## Antes de empezar

| Requisito | Si no lo tienes |
|---|---|
| Lab 12 completo, incluida la sección 7: el archivo `demanda_2026-07-27_tardio.csv` en tu landing | Sin él, oro de qa llega al 25 de julio y el chequeo de qa falla (correctamente) |
| `politica()` de la clase 12 resuelta | `tests/unit/test_bundle.py` la usa para comparar el YAML con `job.py` |
| `dev` con `demanda_7d@champion` y `@challenger` | Lab 9, sección 10 |
| Git folder en `main` actualizado | GitHub: **Sync fork** → Databricks: Git → **Pull** |
| Rama nueva | Git → Create branch → `feature/c13-bundles` |

## Pasos

Abre `clases/c13-bundles/notebooks/lab13_bundles_ambientes`. Widget `usuario`.

| Sección | Qué haces | Qué debes ver |
|---|---|---|
| 1 | Leer la anatomía del bundle y las tres formas de desplegar | — |
| 2 TODO 1 | `esquema_de()` en `src/xm_demanda/utils/ambiente.py` | `test_ambiente.py` sin skip; la tabla de `ubicacion()` para dev, qa y prod |
| 3 | Comparar `job.py` con `resources/job_diario.yml` | El DAG impreso desde el YAML; `test_bundle.py` en verde (salvo los skip de los TODO 2 y 3) |
| 4 | Deploy a **dev** desde el panel **Deployments** | Primero falla por la variable `usuario`; **TODO 2**: dale `default` y vuelve a desplegar. El job `[dev …] [xm-demanda] diario · <usuario> · dev` aparece y corre en menos de un minuto |
| 5 TODO 3 | Target `qa` en `databricks.yml`, igual a `prod` | Deploy a **qa**; `preparar_ambiente` y `job_diario` de qa en `SUCCESS` (8–12 min, más si hay cola) |
| 5 | Comparar dev y qa | Tablas propias en `c01_<usuario>_qa`; modelo de qa con tag `origen`; pronóstico hasta el mismo día |
| 6 | Leer prod y "así sería en Azure" | **No despliegues prod**: lo hace la clase 14 |
| Preguntas | editar en la UI un job desplegado; qué cambiaría en su proyecto para usar un bundle | — |
| `verificar()` | 8 comprobaciones en OK | Commit `feat(c13): bundle con ambientes dev y qa, tareas parametrizadas por ambiente` → push → PR → CI → merge |

## Criterios de aceptación

- [ ] `esquema_de()` implementada; `tests/unit/test_ambiente.py` y `test_bundle.py` sin skip
- [ ] `databricks.yml` con `usuario` y el target `qa` en modo producción
- [ ] Job de dev desplegado por el bundle y ejecutado
- [ ] `c01_<usuario>_qa` poblado por el job de qa; modelo de qa promovido con linaje
- [ ] Las dos preguntas respondidas
- [ ] `verificar()` en OK; PR en verde

## Comparar con la solución de referencia

`https://github.com/<docente>/Databricks-to-XM/compare/s13...<tu_usuario>:Databricks-to-XM:main`

```bash
git fetch upstream --tags
git diff s13 -- databricks.yml resources notebooks/tareas src/xm_demanda/utils conf
```

## Con la CLI (opcional)

Si tienes la CLI instalada (`databricks auth login --host <url del workspace>`):

```bash
databricks bundle validate -t qa      # resuelve variables y valida contra el workspace
databricks bundle summary -t qa       # qué recursos hay desplegados y dónde
databricks bundle deploy -t qa
databricks bundle run preparar_ambiente -t qa
databricks bundle run job_diario -t qa
```

## Extensión opcional

1. **`bundle destroy` en dev.** ¿Qué borra y qué no? (Pista: los jobs sí; tus tablas no, porque no son recursos del bundle.) ¿Qué pasaría si el esquema fuera un recurso `schemas:` del bundle?
2. **Un preset.** Agrega `presets: { tags: { centro_costo: analitica } }` al target `qa` y redespliega. ¿Dónde aparece?
3. **Python en vez de YAML.** Los bundles aceptan recursos definidos en Python (`databricks-bundles`). ¿Qué ganaría `job_diario` si se generara desde `job.py` en lugar de mantener las dos versiones con un test?

## Así sería en Azure Databricks

| En Free Edition (hoy) | En Azure Databricks (XM) |
|---|---|
| Un workspace; ambientes = esquemas `c01_<usuario>`, `_qa`, `_prod` | Un workspace por ambiente; catálogos `dev`, `qa`, `prod` con *workspace-catalog binding* |
| `run_as`: tu usuario | `run_as.service_principal_name`: un SP de Entra ID por ambiente |
| La tarea 0 crea esquema y siembra datos desde dev | Terraform crea la plataforma; cada ambiente lee su propia fuente |
| Deploy desde el panel **Deployments** | Deploy solo desde CI/CD; los humanos no tienen permiso de escritura en prod |
