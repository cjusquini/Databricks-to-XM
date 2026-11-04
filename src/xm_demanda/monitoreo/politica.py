"""Política de reentrenamiento y de promoción, como código: explícita, probada y auditable.

"Reentrenar cuando el modelo empeore" no es una política: no dice cuánto, medido cómo, ni quién
decide. Estas dos funciones sí. Las usan las tareas de monitoreo y de reentrenamiento del job;
sus umbrales viven en conf/base.yml (monitoreo, promocion), no en el código.
"""

import math


def decidir_reentrenamiento(
    wape_reciente: float,
    wape_referencia: float,
    psi_max: float,
    dias_desde_entrenamiento: int,
    umbrales: dict,
) -> dict:
    """¿Hay que reentrenar? Tres disparadores independientes; basta uno.

    - degradación: wape_reciente > wape_referencia · (1 + umbrales["tolerancia_degradacion"])
    - drift: psi_max ≥ umbrales["psi_alto"]
    - calendario: dias_desde_entrenamiento ≥ umbrales["dias_max_sin_reentrenar"]
    Un valor nan (sin datos observados todavía, o sin drift calculable) no dispara nada.
    Devuelve {"reentrenar": bool, "motivos": [str, ...]} con un motivo legible por disparador.
    Ejemplo: decidir_reentrenamiento(0.07, 0.05, 0.05, 10, U) →
    {"reentrenar": True, "motivos": ["degradación: WAPE 7.0 % vs. 5.0 % de referencia (+40 %)"]}
    """
    motivos = []
    tol = umbrales["tolerancia_degradacion"]
    if not math.isnan(wape_reciente) and not math.isnan(wape_referencia):
        if wape_reciente > wape_referencia * (1 + tol):
            cambio = wape_reciente / wape_referencia - 1
            motivos.append(
                f"degradación: WAPE {wape_reciente:.1%} vs. {wape_referencia:.1%} de referencia "
                f"(+{cambio:.0%})"
            )
    if not math.isnan(psi_max) and psi_max >= umbrales["psi_alto"]:
        motivos.append(f"drift: PSI máximo {psi_max:.2f} ≥ {umbrales['psi_alto']:.2f}")
    if dias_desde_entrenamiento >= umbrales["dias_max_sin_reentrenar"]:
        motivos.append(
            f"calendario: {dias_desde_entrenamiento} días desde el entrenamiento "
            f"(máximo {umbrales['dias_max_sin_reentrenar']})"
        )
    return {"reentrenar": bool(motivos), "motivos": motivos}


def decidir_promocion(
    wape_champion: float, wape_challenger: float, dias_comparados: int, reglas: dict
) -> dict:
    """¿El challenger reemplaza al champion? Solo si gana por un margen y con evidencia suficiente.

    - evidencia: dias_comparados ≥ reglas["dias_minimos"] (un mes bueno no basta, clase 9)
    - margen: mejora relativa (wape_champion − wape_challenger) / wape_champion
      ≥ reglas["mejora_minima"]
    Devuelve {"promover": bool, "motivo": str, "mejora": float}.
    """
    if dias_comparados < reglas["dias_minimos"]:
        motivo = f"evidencia insuficiente: {dias_comparados} días (mínimo {reglas['dias_minimos']})"
        return {"promover": False, "mejora": float("nan"), "motivo": motivo}
    mejora = (wape_champion - wape_challenger) / wape_champion
    if mejora >= reglas["mejora_minima"]:
        return {"promover": True, "mejora": mejora,
                "motivo": f"challenger mejora el WAPE {mejora:.1%} en {dias_comparados} días"}
    motivo = f"mejora de {mejora:.1%} por debajo del mínimo de {reglas['mejora_minima']:.0%}"
    return {"promover": False, "mejora": mejora, "motivo": motivo}
