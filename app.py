from io import BytesIO
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import urlopen
import unicodedata

import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data" / "reviews-clients.xlsx"
# DATA = "https://raw.githubusercontent.com/alanaolivieri/n8n-automation/main/data/reviews-clients.xlsx"

COLOR_BACKGROUND = "#f3f5f3"
COLOR_TEXT = "#172c32"
COLOR_HEADER = "#123b39"
COLOR_BRAND = "#a5dace"
COLOR_SUBTITLE = "#c4d8d3"
COLOR_SURFACE = "#ffffff"
COLOR_BORDER = "#dee5df"
COLOR_ACCENT = "#398878"
FONT_FAMILY = "Segoe UI, sans-serif"
CONTENT_WIDTH = 1400
CHART_HEIGHT = 420
CACHE_TTL_SECONDS = 300
REQUEST_TIMEOUT_SECONDS = 20
WORST_COMMENTS_LIMIT = 5
SORT_OPTIONS = ("Menor valoración primero", "Mayor valoración primero", "Nombre A–Z")
STYLE = f"""
<style>
.stApp {{background:{COLOR_BACKGROUND};color:{COLOR_TEXT};font-family:{FONT_FAMILY}}}
.block-container {{max-width:{CONTENT_WIDTH}px;padding-top:2rem}}
.hero {{background:{COLOR_HEADER};color:{COLOR_SURFACE};padding:32px;border-radius:14px;margin-bottom:24px}}
.hero small {{color:{COLOR_BRAND};letter-spacing:3px}}
.hero h1 {{color:{COLOR_SURFACE};font-size:2.5rem;font-weight:600}}
.hero p {{color:{COLOR_SUBTITLE}}}
[data-testid="stMetric"] {{background:{COLOR_SURFACE};border:1px solid {COLOR_BORDER};border-radius:14px;padding:20px}}
</style>
"""
HERO = """
<div class="hero"><small>DONAINDUSTRIA 4.0 / RECURSOS</small>
<h1>La voz detrás de los datos.</h1>
<p>Explora los comentarios, compara sus valoraciones y encuentra dónde centrar la atención.</p></div>
"""


def normalize(value: object) -> str:
    """Normaliza cabeceras sin alterar los datos originales."""
    text = unicodedata.normalize("NFD", str(value).strip().lower())
    return "".join(character for character in text if unicodedata.category(character) != "Mn")


def find_column(columns: dict[str, str], aliases: tuple[str, ...]) -> str | None:
    """Devuelve la primera columna reconocida por sus alias."""
    return next((columns[alias] for alias in aliases if alias in columns), None)


def prepare(raw: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Unifica columnas y descarta puntuaciones no numéricas o infinitas."""
    columns = {normalize(column): column for column in raw.columns}
    rating = find_column(columns, ("estrellitas", "valoracion", "rating", "estrellas"))
    comment = find_column(columns, ("review", "comentario"))
    if rating is None or comment is None:
        raise ValueError("El Excel debe incluir Review o Comentario y estrellitas o Valoración.")

    result = pd.DataFrame(index=raw.index)
    names = [find_column(columns, ("nombre",)), find_column(columns, ("apellido",))]
    name_columns = [column for column in names if column is not None]
    if name_columns:
        result["Persona"] = raw[name_columns].fillna("").astype(str).agg(" ".join, axis=1).str.strip()
    else:
        result["Persona"] = "Sin nombre"
    result["Persona"] = result["Persona"].replace("", "Sin nombre")
    result["Comentario"] = raw[comment].fillna("").astype(str)
    scores = raw[rating].astype(str).str.strip().str.replace(",", ".", regex=False)
    result["Valoración"] = pd.to_numeric(scores, errors="coerce")
    valid = result["Valoración"].notna() & result["Valoración"].abs().ne(float("inf"))
    return result.loc[valid].reset_index(drop=True), int((~valid).sum())


@st.cache_data(ttl=CACHE_TTL_SECONDS, show_spinner=False)
def read_excel(source: str, version: int | None = None) -> pd.DataFrame:
    """Lee la primera hoja; version invalida la caché si cambia el archivo local."""
    if source.startswith("https://"):
        with urlopen(source, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            content = BytesIO(response.read())
        return pd.read_excel(content, engine="openpyxl")
    return pd.read_excel(source, engine="openpyxl")


def load_data() -> tuple[pd.DataFrame, int] | None:
    """Resuelve la fuente configurada y muestra errores de carga comprensibles."""
    try:
        version = None
        if isinstance(DATA, Path):
            if not DATA.is_file():
                st.info("Falta el Excel. Coloca reviews-clients.xlsx en la carpeta data/ junto a app.py.")
                return None
            version = DATA.stat().st_mtime_ns
        return prepare(read_excel(str(DATA), version))
    except HTTPError as error:
        if error.code in (403, 404):
            st.warning("El Excel de GitHub no existe o no es accesible. Comprueba el repositorio, la rama y data/reviews-clients.xlsx.")
        else:
            st.warning("GitHub no ha podido servir el Excel. Inténtalo más tarde.")
    except (URLError, TimeoutError, OSError):
        st.error("No se ha podido leer el archivo. Comprueba la conexión o la disponibilidad del Excel local.")
    except ValueError as error:
        st.error(str(error))
    except Exception:
        st.error("No se puede abrir el Excel. Comprueba que sea un .xlsx válido y no tenga contraseña.")
    return None


def render_filters(data: pd.DataFrame) -> tuple[pd.DataFrame, str]:
    """Coloca los filtros en la página y devuelve la selección y el orden."""
    search_column, range_column, sort_column = st.columns((2, 2, 2))
    query = search_column.text_input("Buscar persona o comentario")
    low = float(data["Valoración"].min())
    high = float(data["Valoración"].max())
    if low < high:
        bounds = range_column.slider("Intervalo de valoración", low, high, (low, high))
    else:
        range_column.caption(f"Valoración disponible: {low:g}")
        bounds = (low, high)
    order = sort_column.selectbox("Ordenar tabla", SORT_OPTIONS)
    filtered = data[data["Valoración"].between(*bounds)]
    if query:
        matches = filtered["Persona"].str.contains(query, case=False, regex=False)
        matches |= filtered["Comentario"].str.contains(query, case=False, regex=False)
        filtered = filtered[matches]
    return filtered, order


def format_score(value: float) -> str:
    return "—" if pd.isna(value) else f"{value:.2f}".replace(".", ",")


def render_metrics(data: pd.DataFrame) -> None:
    scores = data["Valoración"]
    metrics = (
        ("Comentarios visibles", str(len(data))),
        ("Valoración media", format_score(scores.mean())),
        ("Menor valoración", format_score(scores.min())),
        ("Mayor valoración", format_score(scores.max())),
    )
    for container, (label, value) in zip(st.columns(4), metrics):
        container.metric(label, value)
    st.caption("Los indicadores y gráficos reflejan los filtros. No se presupone una escala máxima de cinco estrellas.")


def build_distribution(data: pd.DataFrame):
    """Crea barras horizontales con puntuaciones exactas y detalle al pasar el cursor."""
    counts = data.groupby("Valoración", sort=True).size().rename("Comentarios").reset_index()
    figure = px.bar(
        counts,
        x="Comentarios",
        y="Valoración",
        orientation="h",
        text="Comentarios",
        color_discrete_sequence=[COLOR_ACCENT],
    )
    figure.update_yaxes(type="category", categoryorder="array", categoryarray=counts["Valoración"].tolist())
    figure.update_xaxes(dtick=1, rangemode="tozero", title="Número de comentarios")
    figure.update_traces(hovertemplate="Valoración: %{y}<br>Comentarios: %{x}<extra></extra>")
    figure.update_layout(
        height=CHART_HEIGHT,
        paper_bgcolor=COLOR_SURFACE,
        plot_bgcolor=COLOR_SURFACE,
        font={"family": FONT_FAMILY, "color": COLOR_TEXT},
        margin={"l": 10, "r": 20, "t": 20, "b": 10},
        dragmode="pan",
    )
    return figure


def render_worst_comments(data: pd.DataFrame) -> None:
    st.subheader(f"Los {WORST_COMMENTS_LIMIT} comentarios peor valorados")
    st.caption("Una selección para empezar a revisar.")
    for _, row in data.nsmallest(WORST_COMMENTS_LIMIT, "Valoración").iterrows():
        with st.container(border=True):
            st.text(f"{row['Valoración']:g} · {row['Persona']}")
            st.text(row["Comentario"] or "Sin comentario")


def render_results(data: pd.DataFrame, order: str) -> None:
    chart_column, comments_column = st.columns(2, gap="large")
    with chart_column:
        st.subheader("Distribución de valoraciones")
        st.caption("Pasa el cursor para ver los valores. Usa la barra del gráfico para ampliar o restablecer la vista.")
        st.plotly_chart(build_distribution(data), use_container_width=True, config={"displaylogo": False})
    with comments_column:
        render_worst_comments(data)
    st.subheader("Todos los comentarios")
    key = "Persona" if order == SORT_OPTIONS[2] else "Valoración"
    visible = data.sort_values(key, ascending=order != SORT_OPTIONS[1], kind="stable")
    st.dataframe(visible, hide_index=True, use_container_width=True)


def main() -> None:
    st.set_page_config(page_title="Observatorio · Valoraciones", page_icon="🌿", layout="wide")
    st.markdown(STYLE, unsafe_allow_html=True)
    st.markdown(HERO, unsafe_allow_html=True)
    if st.button("Actualizar datos"):
        read_excel.clear()
    loaded = load_data()
    if loaded is None:
        return
    data, discarded = loaded
    if discarded:
        st.warning(f"Se han excluido {discarded} filas con puntuación vacía o no numérica.")
    if data.empty:
        st.info("El Excel no contiene valoraciones numéricas válidas.")
        return
    filtered, order = render_filters(data)
    render_metrics(filtered)
    if filtered.empty:
        st.info("No hay resultados con estos filtros.")
        return
    render_results(filtered, order)


if __name__ == "__main__":
    main()
