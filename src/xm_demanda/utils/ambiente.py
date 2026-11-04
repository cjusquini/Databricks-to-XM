"""Dónde vive cada cosa según el ambiente: un solo lugar para los nombres.

Free Edition: un catálogo (`workspace`) y un esquema por estudiante y ambiente:
c01_ana (dev), c01_ana_qa y c01_ana_prod. En Azure Databricks cada ambiente sería un catálogo
(dev, qa, prod) ligado a su propio workspace. Las tareas del job no cambian entre uno y
otro: solo llaman a ubicacion(usuario, ambiente). Funciones puras: tests/unit/test_ambiente.py.
"""

import re

from xm_demanda.utils.config import load_config

AMBIENTES = ("dev", "qa", "prod")
PATRON_USUARIO = re.compile(r"^[a-z][a-z0-9_]{1,30}$")


def esquema_de(usuario: str, ambiente: str, sufijo: str) -> str:
    """Nombre del esquema del estudiante en un ambiente: c01_<usuario><sufijo>.

    - `usuario` se normaliza (sin espacios, en minúsculas) y debe cumplir PATRON_USUARIO.
    - `ambiente` debe estar en AMBIENTES: nunca se adivina un ambiente.
    - `sufijo` viene de conf/<ambiente>.yml: "" en dev, "_qa" en qa, "_prod" en prod.
    Ejemplos: esquema_de(" Ana ", "dev", "") == "c01_ana";
    esquema_de("ana", "qa", "_qa") == "c01_ana_qa"; esquema_de("ana", "staging", "") → ValueError.
    """
    if ambiente not in AMBIENTES:
        raise ValueError(f"Ambiente desconocido: {ambiente!r}. Usa uno de {AMBIENTES}")
    u = usuario.strip().lower()
    if not PATRON_USUARIO.match(u):
        raise ValueError(f"Usuario inválido: {usuario!r}. Minúsculas, números y _, sin espacios")
    return f"c01_{u}{sufijo}"


def ubicacion(usuario: str, ambiente: str) -> dict:
    """Todos los nombres que necesitan las tareas, resueltos para un usuario y un ambiente."""
    cfg = load_config(ambiente)
    esquema = esquema_de(usuario, ambiente, cfg["sufijo_esquema"])
    catalogo = cfg["catalog"]
    fqn = f"{catalogo}.{esquema}"
    volumen = f"/Volumes/{catalogo}/{esquema}/raw"
    return {
        "ambiente": ambiente,
        "catalogo": catalogo,
        "esquema": esquema,
        "fqn": fqn,
        "volumen": volumen,
        "landing": cfg["volumen_landing"].format(catalogo=catalogo, esquema=esquema),
        "checkpoint": f"{volumen}/_checkpoints/bronze",
        "modelo": f"{fqn}.{cfg['modelo']['nombre']}",
        "experimento": cfg["experimento"],
    }
