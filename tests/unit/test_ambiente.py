import pytest

from xm_demanda.utils.ambiente import AMBIENTES, esquema_de, ubicacion


def _esquema(*a):
    try:
        return esquema_de(*a)
    except NotImplementedError:
        pytest.skip("Pendiente: lab 13, sección 2")


def test_esquema_por_ambiente():
    assert _esquema("ana", "dev", "") == "c01_ana"
    assert _esquema("ana", "qa", "_qa") == "c01_ana_qa"
    assert _esquema("ana", "prod", "_prod") == "c01_ana_prod"


def test_usuario_se_normaliza():
    assert _esquema("  Ana_2 ", "dev", "") == "c01_ana_2"


@pytest.mark.parametrize("malo", ["", "ana-perez", "1ana", "ana; DROP", "a"])
def test_usuario_invalido(malo):
    with pytest.raises(ValueError, match="Usuario"):
        _esquema(malo, "dev", "")


def test_ambiente_desconocido_no_se_adivina():
    with pytest.raises(ValueError, match="Ambiente"):
        _esquema("ana", "staging", "")


@pytest.mark.parametrize("amb", AMBIENTES)
def test_ubicacion_coherente(amb):
    try:
        u = ubicacion("ana", amb)
    except NotImplementedError:
        pytest.skip("Pendiente: lab 13, sección 2")
    sufijo = "" if amb == "dev" else f"_{amb}"
    assert u["fqn"] == f"workspace.c01_ana{sufijo}"
    assert u["landing"] == f"/Volumes/workspace/c01_ana{sufijo}/raw/landing"
    assert u["modelo"] == f"workspace.c01_ana{sufijo}.demanda_7d"
    assert u["checkpoint"].startswith(u["volumen"])


def test_ambientes_no_comparten_nada():
    try:
        dev, qa, prod = (ubicacion("ana", a) for a in AMBIENTES)
    except NotImplementedError:
        pytest.skip("Pendiente: lab 13, sección 2")
    for llave in ("fqn", "landing", "modelo", "checkpoint"):
        assert len({dev[llave], qa[llave], prod[llave]}) == 3, llave
