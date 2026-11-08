
from collections import defaultdict

from journal_data import load_journals


ISSN_COLUMNS = [
    "issn_1",
    "eissn_1",
    "issn_2",
    "eissn_2",
]


def normalize_issn(value):
    if value is None:
        return None

    text = str(value).strip().upper()
    if not text or text == "NAN":
        return None

    return text.replace("-", "").replace(" ", "")


def valid_issn(value):
    """Validate ISSN length, characters and check digit."""

    issn = normalize_issn(value)

    if issn is None or len(issn) != 8:
        return False

    if not issn[:7].isdigit():
        return False

    if not (issn[7].isdigit() or issn[7] == "X"):
        return False

    total = sum(
        int(digit) * weight
        for digit, weight in zip(issn[:7], range(8, 1, -1))
    )

    remainder = (11 - total % 11) % 11
    expected = "X" if remainder == 10 else str(remainder)

    return issn[7] == expected


def main():
    journals, _ = load_journals()

    issn_to_journals = defaultdict(set)
    invalid = []
    missing = 0

    for _, row in journals.iterrows():
        journal_id = str(row["journal_id"])

        identifiers = {
            normalize_issn(row[column])
            for column in ISSN_COLUMNS
            if normalize_issn(row[column]) is not None
        }

        if not identifiers:
            missing += 1

        for issn in identifiers:
            if not valid_issn(issn):
                invalid.append((journal_id, issn))
            else:
                issn_to_journals[issn].add(journal_id)

    shared = {
        issn: ids
        for issn, ids in issn_to_journals.items()
        if len(ids) > 1
    }

    print("=== RAPORT ISSN ===")
    print("Liczba czasopism:", len(journals))
    print("Bez ISSN:", missing)
    print("Niepoprawne ISSN:", len(invalid))
    print("ISSN przypisane do wielu czasopism:", len(shared))

    print("\nPrzyklady niepoprawnych ISSN:")
    for item in invalid[:10]:
        print(item)

    print("\nPrzyklady wspoldzielonych ISSN:")
    for issn, ids in list(shared.items())[:10]:
        print(issn, sorted(ids))


if __name__ == "__main__":
    main()
