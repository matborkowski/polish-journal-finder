
import sys
from pathlib import Path

import streamlit as st

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR / "src"))

from journal_data import load_journals
from journal_search import search_journals


st.set_page_config(
    page_title="Polish Journal Finder",
    page_icon="📚",
    layout="wide",
)


@st.cache_data
def get_data():
    return load_journals()


def reset_filters():
    st.session_state["query"] = ""
    st.session_state["selected_disciplines"] = []
    st.session_state["discipline_mode"] = "OR"
    st.session_state["score_mode"] = "Minimum"
    st.session_state["score_value"] = None


st.title("Lista ministerialna 2024")

st.write(
    "Wyszukiwarka czasopism naukowych z ministerialnego wykazu "
    "według tytułu, numeru ISSN, dyscypliny naukowej i punktacji."
)

st.caption(
    "Źródło danych: wykaz czasopism naukowych, styczeń 2024 r."
)

try:
    journals, disciplines = get_data()
except (FileNotFoundError, ValueError) as error:
    st.error(f"Nie udało się wczytać danych: {error}")
    st.stop()


# Filters
st.sidebar.header("Filtry wyszukiwania")

query = st.sidebar.text_input(
    "Tytuł czasopisma lub ISSN",
    placeholder="Wpisz tytuł lub numer ISSN",
    key="query",
)

selected_disciplines = st.sidebar.multiselect(
    "Dyscypliny naukowe",
    options=sorted(disciplines),
    placeholder="Wybierz dyscypliny naukowe",
    key="selected_disciplines",
)

discipline_mode = st.sidebar.radio(
    "Sposób łączenia dyscyplin",
    options=["OR", "AND"],
    horizontal=True,
    key="discipline_mode",
    help=(
        "OR: czasopismo przypisane do co najmniej jednej "
        "wybranej dyscypliny. "
        "AND: czasopismo przypisane do wszystkich."
    ),
)

score_mode = st.sidebar.radio(
    "Rodzaj filtrowania punktacji",
    options=["Minimum", "Dokładnie"],
    horizontal=True,
    key="score_mode",
)

score_options = sorted(
    journals["points"].dropna().unique().tolist()
)

score_value = st.sidebar.selectbox(
    "Punktacja",
    options=[None] + score_options,
    format_func=lambda value: (
        "Dowolna" if value is None else f"{value} pkt"
    ),
    key="score_value",
)

st.sidebar.button(
    "Wyczyść filtry",
    on_click=reset_filters,
    use_container_width=True,
)


minimum_score = (
    score_value if score_mode == "Minimum" else None
)

exact_score = (
    score_value if score_mode == "Dokładnie" else None
)


# Search
results = search_journals(
    df=journals,
    disciplines=disciplines,
    query=query,
    selected_disciplines=selected_disciplines,
    discipline_mode=discipline_mode,
    min_points=minimum_score,
    exact_points=exact_score,
)


st.subheader("Wyniki wyszukiwania")

col1, col2, col3 = st.columns(3)

col1.metric("Znalezione czasopisma", f"{len(results):,}")
col2.metric("Wszystkie czasopisma", f"{len(journals):,}")
col3.metric("Wybrane dyscypliny", len(selected_disciplines))


# Active filters summary
active_filters = []

if query.strip():
    active_filters.append(f"Tytuł / ISSN: {query.strip()}")

if selected_disciplines:
    active_filters.append(
        f"Dyscypliny ({discipline_mode}): "
        + ", ".join(selected_disciplines)
    )

if score_value is not None:
    active_filters.append(
        f"Punktacja: {score_mode.lower()} {score_value}"
    )

if active_filters:
    st.info("Aktywne filtry: " + " | ".join(active_filters))


# Results
display_columns = [
    "journal_id",
    "journal_title",
    "issn_1",
    "eissn_1",
    "points",
]

display_data = results[display_columns].rename(
    columns={
        "journal_id": "ID",
        "journal_title": "Tytuł czasopisma",
        "issn_1": "ISSN",
        "eissn_1": "eISSN",
        "points": "Punkty",
    }
)

if results.empty:
    st.warning(
        "Nie znaleziono czasopism spełniających "
        "wybrane kryteria. Spróbuj zmienić filtry."
    )
else:
    st.dataframe(
        display_data,
        use_container_width=True,
        hide_index=True,
    )

    csv_data = display_data.to_csv(
        index=False
    ).encode("utf-8-sig")

    st.download_button(
        label="Pobierz wyniki (CSV)",
        data=csv_data,
        file_name="polish_journal_finder_results.csv",
        mime="text/csv",
    )


st.divider()

st.caption(
    "Polish Journal Finder — dane na podstawie "
    "ministerialnego wykazu ze stycznia 2024 r. "
    "Wyniki mają charakter informacyjny."
)
