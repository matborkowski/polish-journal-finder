
from collections import Counter
from pathlib import Path

import pandas as pd

BASE = Path(__file__).resolve().parent.parent

source = BASE / "data/raw/wykaz_czasopism_2024.xlsx"
export = BASE / "polish_journal_finder_results.csv"

# Read source Excel independently of the search engine.
raw = pd.read_excel(
    source,
    sheet_name="Czasopisma _nauk",
    header=None,
    dtype=str,
)

headers = raw.iloc[0]
data = raw.iloc[2:].copy()

# Identify the scientific discipline.
discipline_names = headers.iloc[9:61].astype(str).str.strip()
matches = [
    i for i, name in enumerate(discipline_names)
    if name.casefold() == "nauki chemiczne"
]

if len(matches) != 1:
    raise ValueError("Discipline not uniquely identified.")

discipline_col = 9 + matches[0]

markers = (
    data.iloc[:, discipline_col]
    .fillna("")
    .astype(str)
    .str.strip()
    .str.casefold()
)

points = pd.to_numeric(data.iloc[:, 8], errors="coerce")

expected = data.loc[
    markers.eq("x") & points.ge(100)
].copy()

actual = pd.read_csv(export, dtype=str).fillna("")


def clean(value):
    if pd.isna(value):
        return ""
    return str(value).strip()


def source_record(row):
    title = row.iloc[2]
    if pd.isna(title):
        title = row.iloc[5]

    return (
        clean(title),
        clean(row.iloc[3]),
        clean(row.iloc[4]),
        str(int(float(row.iloc[8]))),
    )


def exported_record(row):
    return (
        clean(row["Journal title"]),
        clean(row["ISSN"]),
        clean(row["eISSN"]),
        clean(row["Score"]),
    )


expected_records = Counter(
    source_record(row) for _, row in expected.iterrows()
)

actual_records = Counter(
    exported_record(row) for _, row in actual.iterrows()
)

missing = expected_records - actual_records
extra = actual_records - expected_records

print("=== VALIDATION REPORT ===")
print("Source matches:", len(expected))
print("Exported records:", len(actual))
print("Missing records:", sum(missing.values()))
print("Unexpected records:", sum(extra.values()))

print("\nDiscipline markers:", markers.value_counts().to_dict())

if not missing and not extra:
    print("\nPASS: Export matches source records exactly.")
else:
    print("\nFAIL: Differences detected.")
    print("Missing examples:", list(missing.items())[:10])
    print("Unexpected examples:", list(extra.items())[:10])
