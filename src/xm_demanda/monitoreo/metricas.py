"""Qué tan bien está pronosticando el modelo y si el mundo cambió. Funciones puras sobre pandas.

Dos preguntas distintas, que se responden distinto:
- **Desempeño** (necesita lo observado): ¿el error de los últimos días es peor que el de validación?
- **Drift** (no necesita lo observado): ¿las entradas del modelo ya no se parecen a las del
  entrenamiento? Avisa antes, porque no espera a que llegue el dato real.
"""

import numpy as np
import pandas as pd

EPS = 1e-6


def error_diario(obs: pd.DataFrame) -> pd.DataFrame:
    """WAPE y sesgo por fecha_pronostico y alias, sobre filas que ya tienen demanda observada.

    `obs`: filas de v_observado_vs_estimado (fecha_pronostico, alias, modelo_version,
    demanda_estimada_kwh, demanda_observada_kwh). Sesgo > 0: el modelo sobreestima.
    Devuelve: fecha_pronostico, alias, modelo_version, wape, sesgo, series, energia_gwh.
    """
    d = obs.dropna(subset=["demanda_observada_kwh"]).copy()
    d["abs_err"] = (d["demanda_estimada_kwh"] - d["demanda_observada_kwh"]).abs()
    d["err"] = d["demanda_estimada_kwh"] - d["demanda_observada_kwh"]
    d["abs_obs"] = d["demanda_observada_kwh"].abs()
    g = d.groupby(["fecha_pronostico", "alias", "modelo_version"], as_index=False).agg(
        abs_err=("abs_err", "sum"), err=("err", "sum"), abs_obs=("abs_obs", "sum"),
        series=("abs_obs", "size"),
    )
    g["wape"] = g["abs_err"] / g["abs_obs"].where(g["abs_obs"] > 0)
    g["sesgo"] = g["err"] / g["abs_obs"].where(g["abs_obs"] > 0)
    g["energia_gwh"] = g["abs_obs"] / 1e6
    return g[["fecha_pronostico", "alias", "modelo_version", "wape", "sesgo", "series",
              "energia_gwh"]]


def wape_ventana(diario: pd.DataFrame, alias: str, hasta, dias: int) -> float:
    """WAPE ponderado por energía de los últimos `dias` hasta `hasta` (incluido) para un alias.

    No es el promedio de los WAPE diarios: un día festivo de baja demanda no pesa lo mismo
    que un martes. Si no hay días en la ventana devuelve nan.
    """
    hasta = pd.Timestamp(hasta)
    d = diario[(diario["alias"] == alias)
               & (pd.to_datetime(diario["fecha_pronostico"]) > hasta - pd.Timedelta(days=dias))
               & (pd.to_datetime(diario["fecha_pronostico"]) <= hasta)]
    energia = d["energia_gwh"].sum()
    return float((d["wape"] * d["energia_gwh"]).sum() / energia) if energia > 0 else float("nan")


def psi(referencia, actual, bins: int = 10) -> float:
    """Population Stability Index de `actual` respecto a `referencia`.

    Cortes por cuantiles de la referencia (cada bin tiene ~10 % de la referencia), con los
    extremos abiertos para que un valor nunca visto caiga en el primer o el último bin.
    PSI = Σ (a − r) · ln(a / r). Lectura habitual: < 0,10 estable · 0,10–0,25 moderado ·
    > 0,25 alto.
    """
    r = pd.Series(referencia, dtype=float).dropna().to_numpy()
    a = pd.Series(actual, dtype=float).dropna().to_numpy()
    if len(r) == 0 or len(a) == 0:
        return float("nan")
    cortes = np.unique(np.quantile(r, np.linspace(0, 1, bins + 1))[1:-1])
    pr = np.bincount(np.searchsorted(cortes, r, side="right"), minlength=len(cortes) + 1) / len(r)
    pa = np.bincount(np.searchsorted(cortes, a, side="right"), minlength=len(cortes) + 1) / len(a)
    pr, pa = np.clip(pr, EPS, None), np.clip(pa, EPS, None)
    return float(np.sum((pa - pr) * np.log(pa / pr)))


def nivel_psi(valor: float, moderado: float = 0.10, alto: float = 0.25) -> str:
    """'estable', 'moderado' o 'alto' según los umbrales; 'sin datos' si es nan."""
    if valor != valor:  # nan
        return "sin datos"
    return "alto" if valor >= alto else "moderado" if valor >= moderado else "estable"


def drift_features(
    ref: pd.DataFrame, act: pd.DataFrame, columnas: list[str], **umbrales
) -> pd.DataFrame:
    """PSI y nivel por columna, de mayor a menor drift."""
    filas = [{"columna": c, "psi": psi(ref[c], act[c])} for c in columnas]
    out = pd.DataFrame(filas)
    out["nivel"] = [nivel_psi(v, **umbrales) for v in out["psi"]]
    return out.sort_values("psi", ascending=False, ignore_index=True)
