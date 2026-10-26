"""Inferencia batch: de filas de oro y un modelo registrado a filas de `pronostico_demanda`.

Tres reglas de producción, todas aquí y todas probadas en tests/unit/test_inference.py:

1. Cada pronóstico dice qué modelo lo produjo (nombre y versión) y cuándo. Sin eso, la
   pregunta "¿qué modelo publicó la cifra del 30 de julio?" no tiene respuesta.
2. La escritura es idempotente: la llave es (fecha_pronostico, serie, modelo_version).
   Repetir la corrida actualiza las mismas filas; nunca duplica.
3. Champion y challenger escriben en la misma tabla con su versión: así se comparan
   con datos observados sin desplegar nada (modo "sombra").
"""

import numpy as np
import pandas as pd

from xm_demanda.silver.transform import LLAVE_SERIE

LLAVE_PRONOSTICO = ["fecha_pronostico", *LLAVE_SERIE, "modelo_version"]
COLUMNAS_PRONOSTICO = [
    "fecha_emision",
    "fecha_pronostico",
    *LLAVE_SERIE,
    "demanda_estimada_kwh",
    "modelo",
    "modelo_version",
    "alias",
    "version_datos",
    "generado_en",
]
HISTORIA_MINIMA = 29  # 28 días para media_28 + el propio día (clase 9)


def filas_a_pronosticar(
    oro: pd.DataFrame, objetivo: str, horizonte: int, desde: str | None = None
) -> pd.DataFrame:
    """Filas de oro sobre las que se emite un pronóstico, sin la columna objetivo.

    - `desde=None` (producción): las de los últimos `horizonte` días, cuyo objetivo aún no
      ocurrió. Cada una pronostica un día distinto de la semana siguiente.
    - `desde="2026-06-30"` (backtest + futuro): todas las filas con fecha > desde. Las que ya
      tienen objetivo permiten comparar observado vs. estimado.
    Solo filas con historia suficiente para que el modelo tenga escala (media_28).
    """
    fecha = pd.to_datetime(oro["fecha"])
    if desde is None:
        mascara = (fecha > fecha.max() - pd.Timedelta(days=horizonte)) & oro[objetivo].isna()
    else:
        mascara = fecha > pd.Timestamp(desde)
    mascara &= oro["dias_con_datos"] >= HISTORIA_MINIMA
    return oro[mascara].drop(columns=[objetivo]).reset_index(drop=True)


def preparar_pronosticos(
    filas: pd.DataFrame,
    yhat,
    horizonte: int,
    modelo: str,
    version: str,
    alias: str,
    version_datos: int,
    generado_en: pd.Timestamp,
) -> pd.DataFrame:
    """Arma las filas de `pronostico_demanda` con las columnas de COLUMNAS_PRONOSTICO, en orden.

    fecha_emision = la fecha de la fila de oro; fecha_pronostico = fecha_emision + horizonte;
    la llave de la serie; demanda_estimada_kwh = yhat como float, nunca negativa; y los
    metadatos modelo, modelo_version (texto), alias, version_datos (la versión Delta de oro
    que se leyó) y generado_en. Lanza ValueError si yhat no tiene una predicción por fila o
    trae nulos o infinitos: un pronóstico vacío no se publica.
    """
    # TODO (lab 11, sección 3): implementar. Pistas: np.asarray(yhat, dtype=float),
    # np.isfinite, pd.Timedelta(days=horizonte), .clip(lower=0) y COLUMNAS_PRONOSTICO.
    raise NotImplementedError("preparar_pronosticos: completa esta función (lab 11, sección 3)")


def ddl_pronostico(tabla: str) -> str:
    """Contrato de la tabla de pronósticos: tipos, NOT NULL, comentarios y clustering.

    Una sola definición para el lab y para el job de producción (notebooks/05_batch_inference.py).
    """
    return f"""CREATE TABLE IF NOT EXISTS {tabla} (
  fecha_emision DATE NOT NULL COMMENT 'Fecha de la fila de oro desde la que se pronostica (t)',
  fecha_pronostico DATE NOT NULL COMMENT 'Día pronosticado: t + horizonte',
  codigo_sic_agente STRING NOT NULL,
  mercado_comercializacion STRING NOT NULL,
  tipo_mercado STRING NOT NULL,
  clasificacion_industrial STRING NOT NULL,
  demanda_estimada_kwh DOUBLE NOT NULL COMMENT 'Demanda estimada en kWh, nunca negativa',
  modelo STRING COMMENT 'Estimador (lightgbm_global, naive_festivo…)',
  modelo_version STRING NOT NULL COMMENT 'Versión del modelo registrado en Unity Catalog',
  alias STRING COMMENT 'Alias con el que se resolvió la versión al correr',
  version_datos BIGINT COMMENT 'Versión Delta de features_demanda_diaria que se leyó',
  generado_en TIMESTAMP COMMENT 'Cuándo se generó la fila (hora de Bogotá)'
)
CLUSTER BY (fecha_pronostico)
COMMENT 'Pronóstico de demanda a 7 días por serie. Llave: fecha_pronostico + serie + versión'"""


def sql_merge_pronosticos(tabla: str, vista_origen: str) -> str:
    """MERGE idempotente de una vista temporal sobre la tabla de pronósticos."""
    on = " AND ".join(f"t.{c} = s.{c}" for c in LLAVE_PRONOSTICO)
    return (
        f"MERGE INTO {tabla} AS t USING {vista_origen} AS s ON {on} "
        "WHEN MATCHED THEN UPDATE SET * WHEN NOT MATCHED THEN INSERT *"
    )


def sql_vista_observado_vs_estimado(vista: str, tabla_pronostico: str, tabla_oro: str) -> str:
    """Vista que une cada pronóstico con lo que de verdad se consumió ese día (si ya pasó).

    LEFT JOIN: los pronósticos del futuro quedan con demanda_observada_kwh nula.
    """
    on = " AND ".join(f"o.{c} = p.{c}" for c in LLAVE_SERIE)
    llave = ", ".join(f"p.{c}" for c in LLAVE_SERIE)
    return f"""CREATE OR REPLACE VIEW {vista}
COMMENT 'Pronóstico a 7 días vs. lo observado, por serie, día y versión del modelo'
AS SELECT
  p.fecha_emision, p.fecha_pronostico, {llave},
  p.modelo, p.modelo_version, p.alias, p.version_datos,
  p.demanda_estimada_kwh,
  o.demanda_real_kwh AS demanda_observada_kwh,
  abs(o.demanda_real_kwh - p.demanda_estimada_kwh) AS error_abs_kwh,
  p.generado_en
FROM {tabla_pronostico} AS p
LEFT JOIN {tabla_oro} AS o ON o.fecha = p.fecha_pronostico AND {on}"""


def payload_endpoint(filas: pd.DataFrame) -> dict:
    """Filas de oro → cuerpo `dataframe_split` para un endpoint de Model Serving.

    JSON no sabe de fechas ni de NaN: las fechas viajan como texto ISO y los NaN como null.
    La firma del modelo (clase 9) se encarga de devolverlas a su tipo del otro lado.
    """
    df = filas.copy()
    for c in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[c]):
            df[c] = df[c].dt.strftime("%Y-%m-%dT%H:%M:%S")
        elif pd.api.types.is_bool_dtype(df[c]):
            df[c] = df[c].astype(bool)
    df = df.astype(object).where(pd.notna(df), None)
    return {"dataframe_split": {"columns": list(df.columns), "data": df.values.tolist()}}


def leer_predicciones(respuesta) -> list[float]:
    """Respuesta de un endpoint → lista de floats.

    El pyfunc de la clase 9 devuelve una Series con nombre, y el endpoint la serializa como
    [{"demanda_estimada_kwh": 7953.7}, ...]; un modelo que devuelve un arreglo, como [7953.7].
    """
    preds = respuesta["predictions"] if isinstance(respuesta, dict) else respuesta.predictions
    return [float(next(iter(p.values()))) if isinstance(p, dict) else float(p) for p in preds]


def resumen_por_segmento(obs: pd.DataFrame, segmento: str) -> pd.DataFrame:
    """WAPE y energía por segmento sobre la vista observado vs. estimado (filas con observado)."""
    d = obs[obs["demanda_observada_kwh"].notna()]
    g = d.groupby(segmento).agg(
        error=("error_abs_kwh", "sum"),
        energia=("demanda_observada_kwh", lambda s: np.abs(s).sum()),
        filas=("error_abs_kwh", "size"),
    )
    g["wape"] = g["error"] / g["energia"].replace(0, np.nan)
    g["energia_gwh"] = g["energia"] / 1e6
    return g[["wape", "energia_gwh", "filas"]].sort_values("wape", ascending=False).reset_index()
