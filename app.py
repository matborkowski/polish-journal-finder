
import sys
from pathlib import Path

import streamlit as st

# Import existing search engine
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


st.title("Polish Journal Finder")

st.write(
    "Search the Polish ministerial list of scientific journals "
    "using journal titles, ISSN, scientific disciplines and scores."
)

st.caption("Data source: Polish ministerial journal list, January 2024")

try:
    journals, disciplines = get_data()
except (FileNotFoundError, ValueError) as error:
    st.error(f"Unable to load journal data: {error}")
    st.stop()


# Search filters
st.sidebar.header("Search filters")

query = st.sidebar.text_input(
    "Journal title or ISSN",
    placeholder="Enter title or ISSN",
)

selected_disciplines = st.sidebar.multiselect(
    "Scientific disciplines",
    options=sorted(disciplines),
)

discipline_mode = st.sidebar.radio(
    "Discipline matching",
    options=["OR", "AND"],
    horizontal=True,
    help="OR: any selected discipline; AND: all selected disciplines.",
)

score_options = sorted(journals["points"].dropna().unique().tolist())

minimum_score = st.sidebar.selectbox(
    "Minimum score",
    options=[None] + score_options,
    format_func=lambda value: "Any" if value is None else str(value),
)

exact_score = st.sidebar.selectbox(
    "Exact score",
    options=[None] + score_options,
    format_func=lambda value: "Any" if value is None else str(value),
)


# Execute search
results = search_journals(
    df=journals,
    disciplines=disciplines,
    query=query,
    selected_disciplines=selected_disciplines,
    discipline_mode=discipline_mode,
    min_points=minimum_score,
    exact_points=exact_score,
)

st.subheader("Search results")

col1, col2 = st.columns(2)

col1.metric("Matching journals", f"{len(results):,}")
col2.metric("Total journals", f"{len(journals):,}")

display_columns = [
    "journal_title",
    "issn_1",
    "eissn_1",
    "points",
]

display_data = results[display_columns].rename(
    columns={
        "journal_title": "Journal title",
        "issn_1": "ISSN",
        "eissn_1": "eISSN",
        "points": "Score",
    }
)

st.dataframe(
    display_data,
    use_container_width=True,
    hide_index=True,
)

csv_data = display_data.to_csv(index=False).encode("utf-8-sig")

st.download_button(
    label="Download results (CSV)",
    data=csv_data,
    file_name="polish_journal_finder_results.csv",
    mime="text/csv",
)

st.caption(
    "Results are based on the January 2024 ministerial dataset."
)
