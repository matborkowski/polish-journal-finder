
import pandas as pd

from journal_data import load_journals


def search_journals(
    df,
    disciplines,
    query=None,
    selected_disciplines=None,
    discipline_mode="OR",
    min_points=None,
    exact_points=None,
):
    """Filter journals by title, ISSN, score and disciplines."""

    results = df.copy()

    # Search by title or ISSN.
    if query is not None and str(query).strip():
        term = str(query).strip().casefold()

        search_columns = [
            "title_1", "title_2",
            "issn_1", "eissn_1",
            "issn_2", "eissn_2",
        ]

        matches = pd.Series(False, index=results.index)

        for column in search_columns:
            text = results[column].fillna("").str.casefold()
            matches |= text.str.contains(term, regex=False)

        results = results.loc[matches]

    # Filter by minimum score.
    if min_points is not None:
        results = results.loc[results["points"] >= min_points]

    # Filter by exact score.
    if exact_points is not None:
        results = results.loc[results["points"] == exact_points]

    # Filter by scientific disciplines.
    if selected_disciplines:
        unknown = set(selected_disciplines) - set(disciplines)

        if unknown:
            raise ValueError(f"Unknown disciplines: {sorted(unknown)}")

        mode = discipline_mode.upper()

        if mode not in ("AND", "OR"):
            raise ValueError("Mode must be AND or OR.")

        markers = results[selected_disciplines].eq("x")

        if mode == "AND":
            matches = markers.all(axis=1)
        else:
            matches = markers.any(axis=1)

        results = results.loc[matches]

    return results.sort_values(
        by=["points", "journal_title"],
        ascending=[False, True],
    )



if __name__ == "__main__":
    journals, disciplines = load_journals()

    tests = [
        ("Wszystkie czasopisma", {}),
        ("Nauki chemiczne", {
            "selected_disciplines": ["nauki chemiczne"]
        }),
        ("Nauki chemiczne, minimum 100 pkt", {
            "selected_disciplines": ["nauki chemiczne"],
            "min_points": 100
        }),
        ("Wszystkie czasopisma, 200 pkt", {
            "exact_points": 200
        }),
        ("Nauki chemiczne, 200 pkt", {
            "selected_disciplines": ["nauki chemiczne"],
            "exact_points": 200
        }),
    ]

    print("=== TESTY WYSZUKIWARKI ===")

    for name, filters in tests:
        results = search_journals(
            df=journals,
            disciplines=disciplines,
            **filters
        )

        print(f"{name}: {len(results)}")
