import numpy as np
import pandas as pd
import pytest

from xm_demanda.inference.batch import (
    COLUMNAS_PRONOSTICO,
    LLAVE_PRONOSTICO,
    ddl_pronostico,
    filas_a_pronosticar,
    leer_predicciones,
    payload_endpoint,
    preparar_pronosticos,
    resumen_por_segmento,
    sql_merge_pronosticos,
    sql_vista_observado_vs_estimado,
)

LLAVE = {
    "codigo_sic_agente": "A",
    "mercado_comercializacion": "M",
    "tipo_mercado": "Regulado",
    "clasificacion_industrial": "SIN CLASIFICAR",
}
GENERADO = pd.Timestamp("2026-07-26 06:00")


def _oro(n_dias=40, h=7):
    fechas = pd.date_range("2026-06-16", periods=n_dias, freq="D")
    df = pd.DataFrame({"fecha": fechas, **LLAVE})
    df["demanda_real_kwh"] = 1000.0
    df["dias_con_datos"] = np.arange(1, n_dias + 1) + 20
    df["y_h7"] = df["demanda_real_kwh"].shift(-h)
    return df


def _preparar(*args, **kwargs):
    try:
        return preparar_pronosticos(*args, **kwargs)
    except NotImplementedError:
        pytest.skip("Pendiente: lab 11, sección 3")


def test_filas_produccion_son_los_ultimos_h_dias_sin_objetivo():
    oro = _oro()
    f = filas_a_pronosticar(oro, "y_h7", 7)
    assert len(f) == 7
    assert "y_h7" not in f.columns
    assert f["fecha"].min() == oro["fecha"].max() - pd.Timedelta(days=6)


def test_filas_backtest_incluyen_pasado_y_futuro_con_historia():
    oro = _oro()
    f = filas_a_pronosticar(oro, "y_h7", 7, desde="2026-07-01")
    assert f["fecha"].min() == pd.Timestamp("2026-07-02")
    assert (f["dias_con_datos"] >= 29).all()
    corto = filas_a_pronosticar(oro.assign(dias_con_datos=10), "y_h7", 7, desde="2026-07-01")
    assert corto.empty


def test_preparar_columnas_fechas_y_metadatos():
    filas = filas_a_pronosticar(_oro(), "y_h7", 7)
    p = _preparar(
        filas, np.full(len(filas), 950.0), 7, "lightgbm_global", 3, "champion", 15, GENERADO
    )
    assert list(p.columns) == COLUMNAS_PRONOSTICO
    assert (p["fecha_pronostico"] - p["fecha_emision"] == pd.Timedelta(days=7)).all()
    assert p["modelo_version"].eq("3").all()
    assert p["alias"].eq("champion").all() and p["generado_en"].eq(GENERADO).all()
    assert p["demanda_estimada_kwh"].dtype == float
    assert p["version_datos"].eq(15).all()


def test_preparar_no_publica_negativos_ni_vacios():
    filas = filas_a_pronosticar(_oro(), "y_h7", 7)
    p = _preparar(filas, [-5.0] + [1.0] * (len(filas) - 1), 7, "m", "1", "champion", 15, GENERADO)
    assert p["demanda_estimada_kwh"].min() == 0
    with pytest.raises(ValueError):
        _preparar(filas, [np.nan] * len(filas), 7, "m", "1", "champion", 15, GENERADO)
    with pytest.raises(ValueError):
        _preparar(filas, [1.0], 7, "m", "1", "champion", 15, GENERADO)


def test_preparar_respeta_el_indice_de_las_filas():
    filas = filas_a_pronosticar(_oro(), "y_h7", 7)
    filas.index = filas.index + 100  # índice que no empieza en 0
    p = _preparar(filas, np.arange(len(filas), dtype=float), 7, "m", "1", "c", 15, GENERADO)
    assert p["demanda_estimada_kwh"].tolist() == list(range(len(filas)))


def test_merge_usa_la_llave_completa():
    q = sql_merge_pronosticos("cat.esq.pronostico_demanda", "nuevos")
    for c in LLAVE_PRONOSTICO:
        assert f"t.{c} = s.{c}" in q
    assert "WHEN NOT MATCHED THEN INSERT *" in q


def test_vista_es_left_join_por_fecha_objetivo():
    q = sql_vista_observado_vs_estimado("v", "p", "o")
    assert "LEFT JOIN o AS o ON o.fecha = p.fecha_pronostico" in q


def test_payload_serializable_con_fechas_y_nulos():
    import json

    f = filas_a_pronosticar(_oro(), "y_h7", 7).assign(lag_1=np.nan)
    body = payload_endpoint(f.head(2))
    texto = json.dumps(body)
    assert '"2026-' in texto and "null" in texto
    assert body["dataframe_split"]["columns"] == list(f.columns)


def test_resumen_por_segmento_ignora_el_futuro():
    obs = pd.DataFrame(
        {
            "tipo_mercado": ["Regulado", "Regulado", "No Regulado"],
            "demanda_observada_kwh": [100.0, None, 50.0],
            "error_abs_kwh": [10.0, None, 10.0],
        }
    )
    r = resumen_por_segmento(obs, "tipo_mercado").set_index("tipo_mercado")
    assert r.loc["Regulado", "wape"] == pytest.approx(0.10)
    assert r.loc["No Regulado", "wape"] == pytest.approx(0.20)
    assert r.loc["Regulado", "filas"] == 1


def test_leer_predicciones_acepta_series_con_nombre_y_arreglos():
    assert leer_predicciones({"predictions": [{"demanda_estimada_kwh": 2.5}]}) == [2.5]
    assert leer_predicciones({"predictions": [1, 2]}) == [1.0, 2.0]


def test_ddl_declara_exactamente_las_columnas_del_contrato():
    import re

    ddl = ddl_pronostico("cat.esq.pronostico_demanda")
    columnas = re.findall(r"^\s+(\w+) (?:DATE|STRING|DOUBLE|BIGINT|TIMESTAMP)", ddl, re.M)
    assert columnas == COLUMNAS_PRONOSTICO
    assert "CLUSTER BY (fecha_pronostico)" in ddl
