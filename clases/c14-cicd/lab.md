# Lab 14 — De un tag a producción, con pruebas y una aprobación

**Duración:** 45 min + 20 min · **Modalidad:** individual, en tu propio fork · **Rama:** `feature/c14-cicd`

## Objetivo

Configurar el fork para que GitHub Actions despliegue el bundle; completar el job `deploy-prod`; ver un PR detenido por las pruebas y un push directo a `main` rechazado; promover el tag `v1.0.0` de qa a prod con una aprobación, y auditar desde Databricks qué versión corre en cada ambiente.

## Antes de empezar

| Requisito | Si no lo tienes |
|---|---|
| Lab 13 completo: dev y qa desplegados, `verificar()` en OK, PR fusionado | Termínalo: `deploy-qa` usa tu `databricks.yml` |
| Fork público | GitHub → **Settings** → **General** → *Danger zone* → **Change visibility** |
| Actions habilitado en el fork | Pestaña **Actions** → *I understand my workflows, go ahead and enable them* |

## Pasos

Abre `clases/c14-cicd/notebooks/lab14_cicd_promocion`. Widget `usuario`.

| Sección | Dónde | Qué haces | Qué debes ver |
|---|---|---|---|
| 1 | notebook | Leer CI, CD y entrega continua; cómo se autentica el pipeline | — |
| 2 | Databricks y GitHub | Token personal; secrets `DATABRICKS_HOST` y `DATABRICKS_TOKEN`; variable `DATABRICKS_DEPLOY=true`; environments `dev`, `qa`, `prod` (prod con *Required reviewers*); ruleset de `main` | — |
| 3 TODO | `.github/workflows/ci.yml` | `deploy-prod`: `needs: deploy-qa`, `environment: prod`, y correr `preparar_ambiente` y `job_diario` en prod | `tests/unit/test_cicd.py` sin skip |
| 4a | GitHub | PR que rompe `test_usuario_invalido` | `test` en rojo; merge bloqueado |
| 4b–c | GitHub | Arreglar, push, merge | Checks en verde; `deploy-dev` en verde |
| 4d | terminal o Git folder | `git push` directo a `main` | Rechazado por el ruleset |
| 4e | GitHub | Tag `v1.0.0` | `deploy-qa` en verde (unos 8 min); `deploy-prod` en **Waiting** → *Review deployments* → **Approve** |
| 4 | notebook | Auditoría de los tres jobs | `git_sha`, `run_as`, última corrida por ambiente |
| 5 | notebook | Promover código vs. promover modelos | Modelo de prod con tag `origen` |
| Preguntas | notebook | sin `needs`; quién aprueba en XM | — |
| `verificar()` | notebook | 8 comprobaciones en OK | El commit ya es el del tag |

## Criterios de aceptación

- [ ] Secrets, variable, environments y ruleset configurados en el fork
- [ ] `deploy-prod` completo; `tests/unit/test_cicd.py` sin skip
- [ ] Un PR detenido por CI y un push directo rechazado
- [ ] Tag `v1.0.0` en qa y en prod, con la aprobación registrada
- [ ] qa y prod con el mismo `git_sha`; última corrida exitosa en ambos
- [ ] Las dos preguntas respondidas
- [ ] `verificar()` en OK

**Hito 6: CI/CD operando.**

## Comparar con la solución de referencia

```bash
git fetch upstream --tags
git diff s14 -- .github/workflows ci tests/unit/test_cicd.py
```

## Si algo falla

| Síntoma | Causa probable | Solución |
|---|---|---|
| `validate`, `deploy-*` en gris (*skipped*) | Falta la variable `DATABRICKS_DEPLOY` | Paso 3 de la sección 2 |
| `Error: … default auth: cannot configure default credentials` | Falta un secret o el host termina en `/` | Revisa los dos secrets |
| `deploy-prod` no espera aprobación | El environment `prod` no tiene *Required reviewers*, o el fork es privado | Sección 2, paso 4 |
| `bundle run job_diario -t qa` falla en `chequeo` | qa no tiene el archivo tardío (oro hasta el 25-jul) | Correcto: el pipeline se detuvo. Revisa el lab 12, sección 7 |
| `deploy-qa` tarda mucho | Cola de Free Edition (5 tareas por cuenta) | Esperar; no relanzar el tag |
| El token venció | Los PAT duran lo que pediste | Genera otro y actualiza el secret |

## Extensión opcional

1. **OIDC en vez de token.** Lee la guía de federación de identidad para GitHub Actions. ¿Qué tendrías que crear en Databricks y qué cambiaría en `ci.yml`? (Pista: `permissions: id-token: write` y `DATABRICKS_AUTH_TYPE: github-oidc`.)
2. **Fijar versiones.** Cambia `databricks/setup-cli@main` por una versión fija. ¿Qué riesgo elimina?
3. **Azure DevOps.** Recorre `ci/azure-pipelines.yml` y `ci/plantilla-bundle.yml`. ¿Dónde se configuran allí las aprobaciones?

## Así sería en Azure Databricks

| En Free Edition (hoy) | En Azure Databricks (XM) |
|---|---|
| Token personal en GitHub Secrets | Federación OIDC o *service connection* de Entra ID: sin secretos guardados |
| Un host para los tres targets | Un host por target, en *variable groups* o environments |
| Aprobación: tú mismo | Grupo de aprobadores de prod, con separación de funciones |
| Auditoría: GitHub + tags del job | GitHub/Azure DevOps + `system.access.audit` en Databricks |
