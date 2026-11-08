
from pathlib import Path

import pytest
from openpyxl import load_workbook

from test_journal_search import dataset
from journal_search import search_journals


DATA_FILE = (
    Path(__file__).resolve().parent.parent
    / "data" / "raw" / "wykaz_czasopism_2024.xlsx"
)


@pytest.fixture(scope="module")
def reference_data():
    """Read ministerial records once using openpyxl."""

    workbook = load_workbook(
        DATA_FILE,
        read_only=True,
        data_only=True,
    )

    try:
        sheet = workbook["Czasopisma _nauk"]
        rows = sheet.iter_rows(values_only=True)

        headers = next(rows)

        # Skip the second row, as in journal_data.py.
        next(rows)

        records = list(rows)

        return headers, records

    finally:
        workbook.close()


def reference_search(
    reference_data,
    selected_disciplines,
    mode="OR",
    min_points=None,
    exact_points=None,
):
    """Independently calculate expected journal IDs."""

    headers, records = reference_data

    discipline_indices = [
        headers.index(name)
        for name in selected_disciplines
    ]

    matching_ids = set()

    for row in records:
        journal_id = row[1]
        points = row[8]

        if journal_id is None or points is None:
            continue

        points = float(points)

        if min_points is not None and points < min_points:
            continue

        if exact_points is not None and points != exact_points:
            continue

        markers = [
            str(row[index]).strip().lower() == "x"
            for index in discipline_indices
        ]

        if mode == "AND":
            matches = all(markers)
        else:
            matches = any(markers)

        if matches:
            matching_ids.add(str(journal_id).strip())

    return matching_ids


@pytest.mark.parametrize(
    "selected,mode,min_points,exact_points",
    [
        (["nauki chemiczne"], "OR", 100, None),
        (["nauki chemiczne"], "OR", None, 200),
        (["inżynieria chemiczna"], "OR", 100, None),
        (
            ["nauki chemiczne", "inżynieria chemiczna"],
            "AND", None, None,
        ),
        (
            ["nauki chemiczne", "inżynieria chemiczna"],
            "OR", None, None,
        ),
        (
            ["nauki chemiczne", "inżynieria chemiczna"],
            "AND", 140, None,
        ),
        (
            ["nauki chemiczne", "inżynieria chemiczna"],
            "OR", 140, None,
        ),
    ],
)
def test_reference_filters(
    dataset,
    reference_data,
    selected,
    mode,
    min_points,
    exact_points,
):
    journals, disciplines = dataset

    expected_ids = reference_search(
        reference_data,
        selected_disciplines=selected,
        mode=mode,
        min_points=min_points,
        exact_points=exact_points,
    )

    results = search_journals(
        journals,
        disciplines,
        selected_disciplines=selected,
        discipline_mode=mode,
        min_points=min_points,
        exact_points=exact_points,
    )

    actual_ids = set(results["journal_id"])

    missing = expected_ids - actual_ids
    unexpected = actual_ids - expected_ids

    assert not missing, (
        f"Missing journal IDs: {sorted(missing)}"
    )

    assert not unexpected, (
        f"Unexpected journal IDs: {sorted(unexpected)}"
    )

    assert len(results) == len(expected_ids)
