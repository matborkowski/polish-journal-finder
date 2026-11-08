
import sys
from pathlib import Path

import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR / "src"))

from journal_comparison import compare_journals, build_comparison_report


def make_journal(journal_id, issn, points):
    return {
        "journal_id": journal_id,
        "issn_1": issn,
        "eissn_1": None,
        "issn_2": None,
        "eissn_2": None,
        "points": points,
    }


def test_matching_journals():
    old = pd.DataFrame([
        make_journal("1", "1234-5679", 100)
    ])
    new = pd.DataFrame([
        make_journal("101", "1234-5679", 140)
    ])

    result = compare_journals(old, new)

    assert len(result) == 1
    assert result.iloc[0]["status"] == "matched"
    assert result.iloc[0]["points_change"] == 40


def test_decrease_in_points():
    old = pd.DataFrame([
        make_journal("1", "1234-5679", 200)
    ])
    new = pd.DataFrame([
        make_journal("101", "1234-5679", 140)
    ])

    result = compare_journals(old, new)

    assert result.iloc[0]["points_change"] == -60


def test_no_matching_issn():
    old = pd.DataFrame([
        make_journal("1", "1234-5679", 100)
    ])
    new = pd.DataFrame([
        make_journal("101", "0378-5955", 140)
    ])

    result = compare_journals(old, new)

    assert len(result) == 2
    assert set(result["status"]) == {"unresolved"}
    assert result["points_change"].isna().all()


def test_ambiguous_matching():
    old = pd.DataFrame([
        make_journal("1", "1234-5679", 100)
    ])

    new = pd.DataFrame([
        make_journal("101", "1234-5679", 140),
        make_journal("102", "1234-5679", 200),
    ])

    result = compare_journals(old, new)

    assert len(result) == 1
    assert result.iloc[0]["status"] == "ambiguous"
    assert result.iloc[0]["new_id"] is None


def test_same_points():
    old = pd.DataFrame([
        make_journal("1", "1234-5679", 140)
    ])
    new = pd.DataFrame([
        make_journal("101", "1234-5679", 140)
    ])

    result = compare_journals(old, new)

    assert result.iloc[0]["status"] == "matched"
    assert result.iloc[0]["points_change"] == 0


def test_many_old_to_one_new():
    old = pd.DataFrame([
        make_journal("1", "1234-5679", 100),
        make_journal("2", "1234-5679", 140),
    ])

    new = pd.DataFrame([
        make_journal("101", "1234-5679", 200),
    ])

    result = compare_journals(old, new)

    assert len(result) == 2
    assert result["status"].eq("ambiguous").all()
    assert result["new_id"].isna().all()

    for candidates in result["candidate_ids"]:
        assert candidates == ["101"]


import pytest


@pytest.mark.parametrize(
    "old_column,new_column",
    [
        ("issn_1", "eissn_1"),
        ("issn_1", "issn_2"),
        ("eissn_1", "eissn_2"),
        ("issn_2", "issn_1"),
    ],
)
def test_issn_across_columns(old_column, new_column):
    old_record = make_journal("1", None, 100)
    new_record = make_journal("101", None, 140)

    old_record[old_column] = "1234-5679"
    new_record[new_column] = "1234-5679"

    old = pd.DataFrame([old_record])
    new = pd.DataFrame([new_record])

    result = compare_journals(old, new)

    assert len(result) == 1
    assert result.iloc[0]["status"] == "matched"
    assert result.iloc[0]["old_id"] == "1"
    assert result.iloc[0]["new_id"] == "101"
    assert result.iloc[0]["points_change"] == 40


def test_invalid_issn_not_matched():
    old = pd.DataFrame([
        make_journal("1", "1234-5678", 100)
    ])
    new = pd.DataFrame([
        make_journal("101", "1234-5678", 140)
    ])

    result = compare_journals(old, new)

    assert len(result) == 2
    assert result["status"].eq("unresolved").all()
    assert result["points_change"].isna().all()


def test_duplicate_journal_id():
    old = pd.DataFrame([
        make_journal("1", "1234-5679", 100),
        make_journal("1", "0378-5955", 140),
    ])
    new = pd.DataFrame([
        make_journal("101", "1234-5679", 200)
    ])

    with pytest.raises(ValueError):
        compare_journals(old, new)


def test_missing_issn():
    old = pd.DataFrame([
        make_journal("1", None, 100)
    ])
    new = pd.DataFrame([
        make_journal("101", None, 140)
    ])

    result = compare_journals(old, new)

    assert len(result) == 2
    assert result["status"].eq("unresolved").all()


def test_report_covers_both_lists():
    old = pd.DataFrame([
        make_journal("1", "1234-5679", 100),
        make_journal("2", None, 140),
    ])
    new = pd.DataFrame([
        make_journal("101", "1234-5679", 200),
        make_journal("102", None, 70),
    ])

    report = build_comparison_report(old, new)
    summary = report["summary"]

    assert summary["old_total"] == 2
    assert summary["new_total"] == 2
    assert summary["matched_pairs"] == 1
    assert summary["old_unresolved"] == 1
    assert summary["new_unresolved"] == 1

    assert set(report["old_report"]["journal_id"]) == {"1", "2"}
    assert set(report["new_report"]["journal_id"]) == {"101", "102"}


def test_report_preserves_ambiguous_candidates():
    old = pd.DataFrame([
        make_journal("1", "1234-5679", 100),
    ])
    new = pd.DataFrame([
        make_journal("101", "1234-5679", 140),
        make_journal("102", "1234-5679", 200),
    ])

    report = build_comparison_report(old, new)

    assert report["summary"]["matched_pairs"] == 0
    assert report["summary"]["old_ambiguous"] == 1
    assert report["summary"]["new_ambiguous"] == 2

    old_row = report["old_report"].iloc[0]
    assert old_row["candidate_ids"] == ["101", "102"]
    assert old_row["status"] == "ambiguous"

    assert report["new_report"]["status"].eq("ambiguous").all()
