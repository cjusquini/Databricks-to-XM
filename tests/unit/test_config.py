import pytest

from xm_demanda.utils.config import fqn, load_config, validar_config


def _validar(cfg):
    try:
        return validar_config(cfg)
    except NotImplementedError:
        pytest.skip("Pendiente: lab 8, sección 2")


def test_fqn_dev():
    cfg = load_config("dev")
    assert fqn(cfg, "silver", "silver_diaria") == "workspace.silver_energia.demanda_diaria"


@pytest.mark.parametrize("env", ["dev", "qa", "prod"])
def test_solo_cambia_el_ambiente(env):
    """Entre ambientes cambia dónde (sufijo del esquema); modelo y nombres de tablas no cambian.

    Clase 13: en Free Edition todos los ambientes viven en el catálogo workspace; en Azure cambiaría
    catalog por ambiente y esta prueba diría cfg["catalog"] == env.
    """
    base, cfg = load_config("dev"), load_config(env)
    assert cfg["catalog"] == "workspace"
    assert cfg["sufijo_esquema"] == ("" if env == "dev" else f"_{env}")
    assert cfg["modelo"] == base["modelo"] and cfg["tablas"] == base["tablas"]
    assert "{esquema}" in cfg["volumen_landing"]


@pytest.mark.parametrize("env", ["dev", "qa", "prod"])
def test_config_real_es_valida(env):
    _validar(load_config(env))


def test_validar_detecta_llave_faltante():
    cfg = load_config("dev")
    del cfg["modelo"]
    with pytest.raises(ValueError, match="modelo"):
        _validar(cfg)


@pytest.mark.parametrize("llave", ["db_password", "TOKEN", "api_key", "storage_secret"])
def test_validar_rechaza_secretos_en_texto_plano(llave):
    cfg = load_config("dev")
    cfg["conexion"] = {llave: "no-deberia-estar-aqui"}
    with pytest.raises(ValueError, match="secreto"):
        _validar(cfg)
