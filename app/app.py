"""Databricks App (clase 11): demanda observada vs. estimada por segmento.

Lee la vista `v_observado_vs_estimado` de cada esquema que le haya dado permiso a la app
(`GRANT USE SCHEMA` + `GRANT SELECT` a su service principal). Corre con la identidad de la app:
Unity Catalog decide qué ve, y el selector de esquemas solo muestra esos.

Recursos (app.yaml): un SQL warehouse con clave `sql-warehouse` y permiso CAN USE.
"""

import os

import altair as alt
import pandas as pd
import streamlit as st
from databricks import sql
from databricks.sdk.core import Config

CATALOGO = os.getenv("XM_CATALOGO", "workspace")
VISTA = "v_observado_vs_estimado"
LLAVE = [
    "codigo_sic_agente",
    "mercado_comercializacion",
    "tipo_mercado",
    "clasificacion_industrial",
]
COLORES = {"observado": "#1B1B2F", "champion": "#7C3AED", "challenger": "#B45309"}

st.set_page_config(page_title="XM · Observado vs. estimado", page_icon="⚡", layout="wide")


@st.cache_resource
def conexion():
    cfg = Config()  # en la app: credenciales del service principal, inyectadas por Databricks
    return sql.connect(
        server_hostname=cfg.host.replace("https://", ""),
        http_path=f"/sql/1.0/warehouses/{os.environ['XM_WAREHOUSE_ID']}",
        credentials_provider=lambda: cfg.authenticate,
    )


@st.cache_data(ttl=300, show_spinner="Consultando el SQL warehouse…")
def consultar(consulta: str) -> pd.DataFrame:
    with conexion().cursor() as cursor:
        cursor.execute(consulta)
        return cursor.fetchall_arrow().to_pandas()


def wape(d: pd.DataFrame) -> float:
    d = d[d["demanda_observada_kwh"].notna()]
    energia = d["demanda_observada_kwh"].abs().sum()
    return float(d["error_abs_kwh"].sum() / energia) if energia > 0 else float("nan")


@st.cache_data(ttl=15)
def esquemas_visibles() -> list[str]:
    """information_schema solo devuelve lo que la app tiene permiso de ver. Caché corta: un
    REVOKE se nota en segundos."""
    with conexion().cursor() as cursor:
        cursor.execute(
            f"SELECT DISTINCT table_schema FROM {CATALOGO}.information_schema.tables "
            f"WHERE table_name = '{VISTA}' ORDER BY 1"
        )
        return cursor.fetchall_arrow().to_pandas()["table_schema"].tolist()


esquemas = esquemas_visibles()

st.title("Demanda de energía: observado vs. estimado")
if not esquemas:
    st.warning(
        "La app no ve ninguna vista todavía. Desde tu notebook: "
        "`GRANT USE SCHEMA ON SCHEMA workspace.c01_<usuario> TO <app>` y "
        f"`GRANT SELECT ON TABLE workspace.c01_<usuario>.{VISTA} TO <app>`."
    )
    st.stop()

with st.sidebar:
    st.header("Filtros")
    esquema = st.selectbox(
        "Esquema", esquemas, help="Solo aparecen los esquemas que le dieron permiso a la app"
    )
    assert esquema in esquemas  # el nombre va dentro del SQL: solo valores de la lista blanca
    datos = consultar(f"SELECT * FROM {CATALOGO}.{esquema}.{VISTA}")
    datos["fecha_pronostico"] = pd.to_datetime(datos["fecha_pronostico"])
    tipos = st.multiselect(
        "Tipo de mercado", sorted(datos["tipo_mercado"].unique()), placeholder="Todos"
    )
    mercados = ["Todos", *sorted(datos["mercado_comercializacion"].unique())]
    mercado = st.selectbox("Mercado de comercialización", mercados)
    modelos = sorted(datos["alias"].unique())
    alias = st.multiselect("Modelo", modelos, default=modelos)

d = datos[datos["alias"].isin(alias)]
if tipos:
    d = d[d["tipo_mercado"].isin(tipos)]
if mercado != "Todos":
    d = d[d["mercado_comercializacion"] == mercado]
if d.empty:
    st.info("No hay filas con esos filtros.")
    st.stop()

# --- Indicadores ---
ultimo_observado = d.loc[d["demanda_observada_kwh"].notna(), "fecha_pronostico"].max()
cols = st.columns(len(alias) + 2)
for col, a in zip(cols, alias, strict=False):
    sub = d[d["alias"] == a]
    version = sub["modelo_version"].iloc[0] if len(sub) else "?"
    col.metric(f"WAPE @{a} (v{version})", f"{wape(sub):.1%}", help="Solo días que ya ocurrieron")
por_dia_serie = d.drop_duplicates(["fecha_pronostico", *LLAVE])
energia_gwh = por_dia_serie["demanda_observada_kwh"].sum() / 1e6
cols[-2].metric("Energía observada", f"{energia_gwh:,.0f} GWh")
cols[-1].metric("Series", f"{d.groupby(LLAVE).ngroups:,}")

# --- Serie diaria: suma de las series filtradas ---
estimado = d.groupby(["fecha_pronostico", "alias"], as_index=False)["demanda_estimada_kwh"].sum()
estimado = estimado.rename(columns={"demanda_estimada_kwh": "kwh", "alias": "serie"})
observado = (
    d[d["alias"] == alias[0]]
    .groupby("fecha_pronostico", as_index=False)["demanda_observada_kwh"]
    .sum(min_count=1)
    .dropna()
    .rename(columns={"demanda_observada_kwh": "kwh"})
    .assign(serie="observado")
)
diaria = pd.concat([observado, estimado], ignore_index=True).assign(gwh=lambda x: x["kwh"] / 1e6)

lineas = (
    alt.Chart(diaria)
    .mark_line(point=True)
    .encode(
        x=alt.X("fecha_pronostico:T", title="Día pronosticado"),
        y=alt.Y("gwh:Q", title="GWh/día", scale=alt.Scale(zero=False)),
        color=alt.Color(
            "serie:N",
            scale=alt.Scale(domain=list(COLORES), range=list(COLORES.values())),
            title=None,
        ),
        strokeDash=alt.condition(
            alt.datum.serie == "challenger", alt.value([5, 4]), alt.value([0])
        ),
        tooltip=["fecha_pronostico:T", "serie:N", alt.Tooltip("gwh:Q", format=",.2f")],
    )
)
medio_dia = pd.Timedelta(hours=12)
futuro = pd.DataFrame(
    {"inicio": [ultimo_observado + medio_dia], "fin": [d["fecha_pronostico"].max() + medio_dia]}
)
sombra = alt.Chart(futuro).mark_rect(opacity=0.12, color="#6B7280").encode(x="inicio:T", x2="fin:T")
st.subheader("Observado vs. estimado")
st.caption("La franja gris es el futuro: pronósticos que todavía no se pueden comparar.")
st.altair_chart(sombra + lineas, use_container_width=True)

# --- Dónde está el error ---
izq, der = st.columns(2)
with izq:
    st.subheader("WAPE por tipo de mercado")
    seg = pd.DataFrame(
        [
            {
                "alias": a,
                "tipo_mercado": t,
                "wape": wape(g),
                "energia_gwh": g["demanda_observada_kwh"].sum() / 1e6,
            }
            for (a, t), g in d.groupby(["alias", "tipo_mercado"])
        ]
    )
    st.dataframe(seg.style.format({"wape": "{:.1%}", "energia_gwh": "{:,.0f}"}), hide_index=True)
with der:
    st.subheader("Series con más error absoluto")
    top = (
        d[d["alias"] == alias[0]]
        .groupby(["codigo_sic_agente", "mercado_comercializacion", "tipo_mercado"])["error_abs_kwh"]
        .sum()
        .div(1e6)
        .nlargest(10)
        .rename("error_gwh")
        .reset_index()
    )
    st.dataframe(top.style.format({"error_gwh": "{:,.2f}"}), hide_index=True)

generado = pd.to_datetime(datos["generado_en"]).max()
st.caption(
    f"Fuente: {CATALOGO}.{esquema}.{VISTA} · generado {generado:%Y-%m-%d %H:%M} · la app lee con "
    "su propio service principal: si le quitas el permiso, tu esquema desaparece del selector."
)
