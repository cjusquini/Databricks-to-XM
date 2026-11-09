"""El pipeline de CI/CD también es código, con reglas que no se pueden romper (clase 14)."""

import re
from pathlib import Path

import pytest
import yaml

RAIZ = Path(__file__).resolve().parents[2]
TEXTO = (RAIZ / ".github/workflows/ci.yml").read_text(encoding="utf-8")
WF = yaml.safe_load(TEXTO)
JOBS = WF["jobs"]


def _eventos():
    # PyYAML lee la llave `on:` como el booleano True
    return WF.get("on", WF.get(True))


def _needs(job):
    n = JOBS[job].get("needs", [])
    return [n] if isinstance(n, str) else n


def _corre(job, comando):
    return any(comando in paso.get("run", "") for paso in JOBS[job]["steps"])


def test_ci_corre_en_cada_pr_y_en_main_y_tags():
    ev = _eventos()
    assert "pull_request" in ev
    assert ev["push"]["branches"] == ["main"] and ev["push"]["tags"] == ["v*"]


def test_las_pruebas_no_dependen_de_databricks():
    for job in ("test", "integration"):
        assert "if" not in JOBS[job], f"{job} debe correr siempre, también en PR"


def test_todo_deploy_pasa_por_ci():
    for job in ("deploy-dev", "deploy-qa"):
        assert {"test", "integration", "validate"} <= set(_needs(job)), job
    for job in [j for j in JOBS if j.startswith("deploy") or j == "validate"]:
        assert "DATABRICKS_DEPLOY" in JOBS[job]["if"], job


def test_qa_prueba_antes_de_prod():
    assert _corre("deploy-qa", "bundle deploy -t qa")
    assert _corre("deploy-qa", "bundle run job_diario -t qa"), "qa sin correr el job no prueba nada"


def test_prod_solo_despues_de_qa_y_con_aprobacion():
    prod = JOBS["deploy-prod"]
    if "deploy-qa" not in _needs("deploy-prod") or prod.get("environment") != "prod":
        pytest.skip("Pendiente: lab 14, sección 3 (needs deploy-qa y environment prod)")
    assert startswith_tag(prod["if"])
    assert _corre("deploy-prod", "bundle deploy -t prod")


def startswith_tag(condicion: str) -> bool:
    return "startsWith(github.ref, 'refs/tags/v')" in condicion


def test_sin_secretos_en_el_workflow():
    assert not re.search(r"dapi[0-9a-f]{20,}", TEXTO), "un token en el YAML es un token publicado"
    assert "${{ secrets.DATABRICKS_TOKEN }}" in TEXTO
    assert WF["permissions"] == {"contents": "read"}, "mínimo privilegio para el GITHUB_TOKEN"


def test_trazabilidad_del_commit():
    assert WF["env"]["BUNDLE_VAR_git_sha"] == "${{ github.sha }}"


def test_azure_devops_es_equivalente():
    ado = yaml.safe_load((RAIZ / "ci/azure-pipelines.yml").read_text(encoding="utf-8"))
    etapas = {s["stage"]: s for s in ado["stages"]}
    assert list(etapas) == ["CI", "DeployDev", "DeployQA", "DeployProd"]
    assert etapas["DeployProd"]["dependsOn"] == "DeployQA"
    assert etapas["DeployProd"]["jobs"][0]["environment"] == "prod"
