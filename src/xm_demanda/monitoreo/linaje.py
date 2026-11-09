"""Lo que hay que saber de una versión del modelo para monitorearla y compararla con honestidad.

- `datos_hasta`: la última fecha que el modelo vio al entrenar. Sin ella no se puede elegir un
  periodo de comparación que ninguno de los dos modelos haya visto (sería comparar con fuga).
- `wape_validacion`: el error que prometió en validación; la referencia del monitoreo.

Las versiones entrenadas por el job de reentrenamiento traen ambos datos como tags. Las de la
clase 9 los tienen en su run (parámetro `corte`, métrica `wape`); las copias promovidas los
heredan en tags (tarea 0).
"""

import math


def linaje(cliente, mv) -> dict:
    """{"datos_hasta": "AAAA-MM-DD" | None, "wape_validacion": float | nan} de una ModelVersion."""
    tags = mv.tags or {}
    datos_hasta, wape = tags.get("datos_hasta"), tags.get("wape_validacion")
    if (datos_hasta is None or wape is None) and getattr(mv, "run_id", None):
        try:
            run = cliente.get_run(mv.run_id)
            datos_hasta = datos_hasta or run.data.params.get("corte")
            wape = wape if wape is not None else run.data.metrics.get("wape")
        except Exception:  # noqa: BLE001  el run no es accesible desde este ambiente
            pass
    wape = float(wape) if wape is not None else math.nan
    return {"datos_hasta": datos_hasta, "wape_validacion": wape}
