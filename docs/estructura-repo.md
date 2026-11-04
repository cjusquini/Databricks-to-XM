# Estructura del repositorio

```
Databricks-to-XM/
├── README.md                  Plan del curso (15 clases)
├── CONTRIBUTING.md            Convenciones: ramas, nombres, config, tests
├── databricks.yml             Bundle: targets dev / qa / prod
├── resources/                 Definiciones del bundle (pipeline, jobs)
├── conf/                      Configuración por ambiente, sin secretos
├── src/xm_demanda/            Paquete Python con la lógica (ingest, quality, features, model, utils)
├── notebooks/tareas/          Notebooks delgados, uno por tarea de job (t0 preparar … t6 chequeo)
├── tests/unit | integration   pytest
├── app/                       Databricks App (Streamlit)
├── .github/workflows/ci.yml   CI/CD con GitHub Actions
├── ci/azure-pipelines.yml     Equivalente en Azure DevOps (referencia)
├── data/raw                   Dataset del caso
├── data/reference             Tablas de referencia (festivos, CIIU)
├── docs/                      Arquitectura, gobierno, ADRs, runbook, autoevaluación
└── clases/c01 … c15/          Material de cada clase: slides, lab, notebooks, lecturas
```

## Cómo crece el repo

| Clases | Qué se agrega |
|---|---|
| 1–2 | `docs/architecture.md`, ADR-001, primera tabla Delta |
| 3 | `docs/governance.md`, catálogos y grants |
| 4–7 | `src/xm_demanda/ingest`, `quality`, `features` |
| 8 | `validar_config`, contrato de oro como código, `tests/integration` con Spark, job `integration` en CI, el PR que debe fallar |
| 9–11 | `src/xm_demanda/model`, `inference`; `app/` |
| 12 | `src/xm_demanda/orquestacion` (job como código, chequeo de frescura) |
| 13 | `databricks.yml` con dev/qa/prod, `resources/job_diario.yml` y `job_preparar_ambiente.yml`, `notebooks/tareas/`, `src/xm_demanda/utils/ambiente.py`, `tests/unit/test_bundle.py` |
| 14 | `.github/workflows/ci.yml` con deploy-dev/qa/prod, `ci/azure-pipelines.yml`, `tests/unit/test_cicd.py` |
| 15 | notebook 06, `docs/runbook.md` |
