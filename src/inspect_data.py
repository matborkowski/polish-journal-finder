
from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
FILE_PATH = BASE_DIR / "data" / "raw" / "wykaz_czasopism_2024.xlsx"

# Pierwszy wiersz arkusza zawiera nazwy dyscyplin.
# Pomijamy drugi wiersz zawierajacy opisy i kody kolumn.
df = pd.read_excel(
    FILE_PATH,
    sheet_name="Czasopisma _nauk",
    header=0,
    skiprows=[1],
    dtype=str,
)

# Pierwsze dziewiec kolumn to informacje o czasopismach.
metadata_names = [
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

df.columns = metadata_names + list(df.columns[9:])

# Usuwamy wiersze, ktore nie maja identyfikatora.
df = df.dropna(subset=["journal_id"]).copy()

# Normalizujemy punktacje do wartosci liczbowych.
df["points"] = pd.to_numeric(df["points"], errors="coerce")

# Pozostale kolumny reprezentuja dyscypliny naukowe.
disciplines = list(df.columns[9:])

print("=== POLISH JOURNAL FINDER ===")

print("\nLiczba rekordow:", len(df))
print("Liczba dyscyplin:", len(disciplines))

print("\nDostepne punktacje:")
print(df["points"].value_counts(dropna=False).sort_index())

print("\nBrakujace tytuly:")
print(df["title_1"].isna().sum())

print("\nBrakujace punktacje:")
print(df["points"].isna().sum())

print("\nPowtarzajace sie identyfikatory:")
print(df["journal_id"].duplicated().sum())

print("\nWartosci oznaczen dyscyplin:")
values = pd.unique(df[disciplines].to_numpy().ravel())
print(values[:30])

print("\nPrzykladowe czasopisma:")
print(df[["journal_id", "title_1", "points"]].head(10).to_string(index=False))

# Pierwszy test filtrowania.
discipline = "nauki chemiczne"

chemistry = df[
    df[discipline].fillna("").str.strip().str.lower().eq("x")
]

print("\nCzasopisma przypisane do nauk chemicznych:")
print(len(chemistry))

print("\nPrzykladowe czasopisma z punktacja co najmniej 100:")
results = chemistry[chemistry["points"] >= 100]

print(results[["title_1", "points"]].head(20).to_string(index=False))
print("\nLiczba takich czasopism:", len(results))


print("\n=== ANALIZA TYTULOW ===")

print("\nTytul 1 pusty:")
print(df["title_1"].isna().sum())

print("\nTytul 2 pusty:")
print(df["title_2"].isna().sum())

print("\nOba tytuly puste:")
both_missing = df["title_1"].isna() & df["title_2"].isna()
print(both_missing.sum())

print("\nTytul 1 pusty, Tytul 2 dostepny:")
only_second = df["title_1"].isna() & df["title_2"].notna()
print(only_second.sum())

print("\nPrzyklady rekordow bez Tytulu 1:")
print(
    df.loc[
        df["title_1"].isna(),
        ["journal_id", "title_1", "title_2", "issn_1", "eissn_1", "points"]
    ].head(20).to_string(index=False)
)

print("\nPrzyklady rekordow bez obu tytulow:")
print(
    df.loc[
        both_missing,
        ["journal_id", "title_1", "title_2", "issn_1", "eissn_1", "points"]
    ].head(20).to_string(index=False)
)
