
from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = BASE_DIR / "data" / "raw" / "wykaz_czasopism_2024.xlsx"

METADATA_COLUMNS = [
    "lp",
    "journal_id",
    "title_1",
    "issn_1",
    "eissn_1",
    "title_2",
    "issn_2",
    "eissn_2",
    "points",
]


def load_journals(file_path=DATA_FILE):
    """Load and validate the ministerial journal dataset."""

    df = pd.read_excel(
        file_path,
        sheet_name="Czasopisma _nauk",
        header=0,
        skiprows=[1],
        dtype=str,
    )

    df.columns = METADATA_COLUMNS + list(df.columns[9:])

    # Preserve all source records.
    if df["journal_id"].isna().any():
        raise ValueError("Some records have no journal identifier.")

    if df["journal_id"].duplicated().any():
        raise ValueError("Duplicate journal identifiers detected.")

    # Keep original titles and generate a display title.
    df["journal_title"] = df["title_1"].fillna(df["title_2"])

    if df["journal_title"].isna().any():
        raise ValueError("Some records have no journal title.")

    # Convert ministerial scores to numbers.
    df["points"] = pd.to_numeric(df["points"], errors="raise")

    # Validate scientific discipline markers.
    disciplines = list(df.columns[9:61])

    for discipline in disciplines:
        values = set(df[discipline].dropna().str.strip().str.lower())

        if not values.issubset({"x"}):
            raise ValueError(
                f"Unexpected value in discipline: {discipline}"
            )

    return df, disciplines


if __name__ == "__main__":
    journals, disciplines = load_journals()

    print("Dataset loaded successfully.")
    print("Journals:", len(journals))
    print("Disciplines:", len(disciplines))
    print("Missing display titles:", journals["journal_title"].isna().sum())
