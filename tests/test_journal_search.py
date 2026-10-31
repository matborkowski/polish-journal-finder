
import sys
from pathlib import Path

import pytest

# Make project modules available during testing.
PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR / "src"))

from journal_data import load_journals
from journal_search import search_journals


@pytest.fixture(scope="module")
def dataset():
    return load_journals()


def test_all_journals(dataset):
    journals, disciplines = dataset

    results = search_journals(journals, disciplines)

    assert len(results) == 34088
    assert results["journal_id"].is_unique


def test_chemistry(dataset):
    journals, disciplines = dataset

    results = search_journals(
        journals,
        disciplines,
        selected_disciplines=["nauki chemiczne"],
    )

    assert len(results) == 3185


def test_chemistry_minimum_100(dataset):
    journals, disciplines = dataset

    results = search_journals(
        journals,
        disciplines,
        selected_disciplines=["nauki chemiczne"],
        min_points=100,
    )

    assert len(results) == 1010
    assert (results["points"] >= 100).all()
    assert results["nauki chemiczne"].eq("x").all()


def test_exactly_200_points(dataset):
    journals, disciplines = dataset

    results = search_journals(
        journals,
        disciplines,
        exact_points=200,
    )

    assert len(results) == 879
    assert results["points"].eq(200).all()


def test_chemistry_200_points(dataset):
    journals, disciplines = dataset

    results = search_journals(
        journals,
        disciplines,
        selected_disciplines=["nauki chemiczne"],
        exact_points=200,
    )

    independent_ids = set(
        journals.loc[
            journals["nauki chemiczne"].eq("x")
            & journals["points"].eq(200),
            "journal_id",
        ]
    )

    assert set(results["journal_id"]) == independent_ids
    assert len(results) == 160


def test_and_mode(dataset):
    journals, disciplines = dataset

    selected = ["nauki chemiczne", "inżynieria chemiczna"]

    results = search_journals(
        journals,
        disciplines,
        selected_disciplines=selected,
        discipline_mode="AND",
    )

    assert results[selected].eq("x").all().all()


def test_or_mode(dataset):
    journals, disciplines = dataset

    selected = ["nauki chemiczne", "inżynieria chemiczna"]

    results = search_journals(
        journals,
        disciplines,
        selected_disciplines=selected,
        discipline_mode="OR",
    )

    expected_ids = set(
        journals.loc[journals[selected].eq("x").any(axis=1), "journal_id"]
    )

    assert set(results["journal_id"]) == expected_ids


def test_search_by_issn(dataset):
    journals, disciplines = dataset

    results = search_journals(
        journals,
        disciplines,
        query="2053-1583",
    )

    assert "1" in set(results["journal_id"])


def test_unknown_discipline(dataset):
    journals, disciplines = dataset

    with pytest.raises(ValueError):
        search_journals(
            journals,
            disciplines,
            selected_disciplines=["nieistniejaca dyscyplina"],
        )
