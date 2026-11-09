"""Política de reentrenamiento y de promoción, como código: explícita, probada y auditable.

"Reentrenar cuando el modelo empeore" no es una política: no dice cuánto, medido cómo, ni quién
decide. Estas dos funciones sí. Las usan las tareas de monitoreo y de reentrenamiento del job;
sus umbrales viven en conf/base.yml (monitoreo, promocion), no en el código.
"""



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
    # TODO (lab 15, sección 4): tres disparadores independientes; un nan no dispara nada.
    raise NotImplementedError("decidir_reentrenamiento: completa esta función (lab 15, sección 4)")


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
