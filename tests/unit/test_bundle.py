"""El bundle es código: se prueba en CI antes de desplegarse (clases 13 y 14).

No hablan con Databricks: leen databricks.yml y resources/*.yml y comprueban las reglas que,
si se rompen, solo se descubrirían en producción.
"""

from pathlib import Path

import pytest
import yaml

import xm_demanda.orquestacion.job as jobdef

RAIZ = Path(__file__).resolve().parents[2]


def _yaml(ruta):
    return yaml.safe_load((RAIZ / ruta).read_text(encoding="utf-8"))


BUNDLE = _yaml("databricks.yml")
JOB = _yaml("resources/job_diario.yml")["resources"]["jobs"]["job_diario"]
POLITICA = (
    "max_retries", "min_retry_interval_millis", "retry_on_timeout", "run_if", "timeout_seconds",
)


def test_bundle_incluye_los_recursos():
    assert BUNDLE["bundle"]["name"] == "xm-demanda"
    assert "resources/*.yml" in BUNDLE["include"]


def test_usuario_tiene_valor():
    if "default" not in BUNDLE["variables"]["usuario"]:
        pytest.skip("Pendiente: lab 13, sección 4 (default de la variable usuario)")
    assert BUNDLE["variables"]["usuario"]["default"].strip()


@pytest.mark.parametrize("target", ["qa", "prod"])
def test_targets_productivos(target):
    t = BUNDLE["targets"].get(target)
    if t is None:
        pytest.skip(f"Pendiente: lab 13, sección 5 (target {target})")
    assert t["mode"] == "production"
    assert "${bundle.target}" in t["workspace"]["root_path"], "una sola copia por ambiente"
    assert t["run_as"], "producción declara con qué identidad corre"
    assert any(p["level"] == "CAN_MANAGE" for p in t["permissions"])


def test_dev_es_modo_desarrollo():
    assert BUNDLE["targets"]["dev"]["mode"] == "development"
    assert BUNDLE["targets"]["dev"].get("default") is True


def test_sin_hosts_ni_tokens_en_el_repo():
    texto = (RAIZ / "databricks.yml").read_text(encoding="utf-8").lower()
    for ruta in (RAIZ / "resources").glob("*.yml"):
        texto += ruta.read_text(encoding="utf-8").lower()
    assert "dapi" not in texto and "token:" not in texto
    assert "cloud.databricks.com" not in texto, "el host lo pone quien despliega, no el repo"


def test_yaml_y_job_py_describen_el_mismo_dag():
    try:
        definicion = jobdef.definicion_job("ana", "/x", "ana@x.co")
    except NotImplementedError:
        pytest.skip("Pendiente: lab 12, sección 3 (politica)")
    esperado = {t["task_key"]: t for t in definicion["tasks"]}
    yaml_tareas = {t["task_key"]: t for t in JOB["tasks"]}
    assert list(yaml_tareas) == jobdef.TAREAS
    for k, t in yaml_tareas.items():
        assert t.get("depends_on", []) == esperado[k].get("depends_on", []), k
        for llave in POLITICA:
            assert t.get(llave) == esperado[k].get(llave), f"{k}.{llave}"
    assert JOB["tasks"][1]["condition_task"] == esperado["hay_datos_nuevos"]["condition_task"]


def test_chequeo_no_se_excluye_con_la_rama():
    chequeo = next(t for t in JOB["tasks"] if t["task_key"] == "chequeo")
    assert {d["task_key"] for d in chequeo["depends_on"]} == {"bronce", "inferencia"}
    assert chequeo["run_if"] == "ALL_DONE"


def test_parametros_y_ambiente():
    nombres = [p["name"] for p in JOB["parameters"]]
    assert set(nombres) == set(jobdef.PARAMETROS) | {"ambiente"}
    ambiente = next(p for p in JOB["parameters"] if p["name"] == "ambiente")
    assert ambiente["default"] == "${bundle.target}", "el ambiente lo decide el target"


def test_cada_notebook_existe():
    rutas = []
    for archivo in (RAIZ / "resources").glob("*.yml"):
        jobs = _yaml(archivo.relative_to(RAIZ)).get("resources", {}).get("jobs", {}) or {}
        for job in jobs.values():
            rutas += [t["notebook_task"]["notebook_path"] 
                      for t in job["tasks"] if "notebook_task" in t]
    assert rutas
    for r in rutas:
        assert (RAIZ / "resources" / r).resolve().exists(), r
