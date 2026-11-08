
from collections import defaultdict

import pandas as pd

from inspect_issn import normalize_issn, valid_issn


ISSN_COLUMNS = ["issn_1", "eissn_1", "issn_2", "eissn_2"]


def get_identifiers(row):
    """Return valid ISSNs from all four fields."""
    identifiers = set()

    for column in ISSN_COLUMNS:
        issn = normalize_issn(row.get(column))

        if issn and valid_issn(issn):
            identifiers.add(issn)

    return identifiers


def compare_journals(old_df, new_df):
    """Compare two journal lists using validated ISSNs.

    Matching is accepted only when it is one-to-one.
    Uncertain or unmatched records are not classified
    as new or removed.
    """

    for df in (old_df, new_df):
        required = {"journal_id", "points", *ISSN_COLUMNS}

        if not required.issubset(df.columns):
            raise ValueError("Missing required columns.")

        if df["journal_id"].isna().any():
            raise ValueError("Missing journal ID.")

        if df["journal_id"].astype(str).duplicated().any():
            raise ValueError("Duplicate journal ID.")

    old_records = {
        str(row["journal_id"]): row
        for _, row in old_df.iterrows()
    }

    new_records = {
        str(row["journal_id"]): row
        for _, row in new_df.iterrows()
    }

    # Index ISSNs from the new list.
    new_issn_index = defaultdict(set)

    for new_id, row in new_records.items():
        for issn in get_identifiers(row):
            new_issn_index[issn].add(new_id)

    # Find candidates for each old journal.
    candidates = {}

    for old_id, row in old_records.items():
        matches = set()

        for issn in get_identifiers(row):
            matches.update(new_issn_index.get(issn, set()))

        candidates[old_id] = matches

    # Reverse mapping detects many-to-one conflicts.
    reverse_candidates = defaultdict(set)

    for old_id, new_ids in candidates.items():
        for new_id in new_ids:
            reverse_candidates[new_id].add(old_id)

    output = []

    for old_id, old_row in old_records.items():
        possible = candidates[old_id]

        if not possible:
            output.append({
                "old_id": old_id,
                "new_id": None,
                "status": "unresolved",
                "old_points": old_row["points"],
                "new_points": None,
                "points_change": None,
                "candidate_ids": [],
            })
            continue

        if (
            len(possible) == 1
            and len(reverse_candidates[next(iter(possible))]) == 1
        ):
            new_id = next(iter(possible))
            new_row = new_records[new_id]

            old_points = int(old_row["points"])
            new_points = int(new_row["points"])

            output.append({
                "old_id": old_id,
                "new_id": new_id,
                "status": "matched",
                "old_points": old_points,
                "new_points": new_points,
                "points_change": new_points - old_points,
                "candidate_ids": [new_id],
            })

        else:
            output.append({
                "old_id": old_id,
                "new_id": None,
                "status": "ambiguous",
                "old_points": old_row["points"],
                "new_points": None,
                "points_change": None,
                "candidate_ids": sorted(possible),
            })

    # New-list records without any ISSN candidate.
    for new_id, new_row in new_records.items():
        if new_id not in reverse_candidates:
            output.append({
                "old_id": None,
                "new_id": new_id,
                "status": "unresolved",
                "old_points": None,
                "new_points": new_row["points"],
                "points_change": None,
                "candidate_ids": [],
            })

    return pd.DataFrame(output)


def build_comparison_report(old_df, new_df):
    """Build an auditable report covering both journal lists."""

    comparison = compare_journals(old_df, new_df)

    old_candidates = defaultdict(set)
    new_candidates = defaultdict(set)

    for _, row in comparison.iterrows():
        old_id = row["old_id"]
        new_id = row["new_id"]

        if old_id is not None:
            for candidate in row["candidate_ids"]:
                old_candidates[old_id].add(candidate)
                new_candidates[candidate].add(old_id)

        if row["status"] == "matched":
            old_candidates[old_id].add(new_id)
            new_candidates[new_id].add(old_id)

    matched_old = set(
        comparison.loc[
            comparison["status"] == "matched", "old_id"
        ]
    )
    matched_new = set(
        comparison.loc[
            comparison["status"] == "matched", "new_id"
        ]
    )

    old_report = []
    for journal_id in old_df["journal_id"].astype(str):
        candidates = sorted(old_candidates[journal_id])

        status = (
            "matched" if journal_id in matched_old
            else "ambiguous" if candidates
            else "unresolved"
        )

        old_report.append({
            "journal_id": journal_id,
            "status": status,
            "candidate_ids": candidates,
        })

    new_report = []
    for journal_id in new_df["journal_id"].astype(str):
        candidates = sorted(new_candidates[journal_id])

        status = (
            "matched" if journal_id in matched_new
            else "ambiguous" if candidates
            else "unresolved"
        )

        new_report.append({
            "journal_id": journal_id,
            "status": status,
            "candidate_ids": candidates,
        })

    old_report = pd.DataFrame(
        old_report,
        columns=["journal_id", "status", "candidate_ids"],
    )
    new_report = pd.DataFrame(
        new_report,
        columns=["journal_id", "status", "candidate_ids"],
    )

    summary = {
        "old_total": len(old_df),
        "new_total": len(new_df),
        "matched_pairs": len(matched_old),
        "old_ambiguous": int(
            old_report["status"].eq("ambiguous").sum()
        ),
        "new_ambiguous": int(
            new_report["status"].eq("ambiguous").sum()
        ),
        "old_unresolved": int(
            old_report["status"].eq("unresolved").sum()
        ),
        "new_unresolved": int(
            new_report["status"].eq("unresolved").sum()
        ),
    }

    assert len(old_report) == len(old_df)
    assert len(new_report) == len(new_df)

    return {
        "comparison": comparison,
        "old_report": old_report,
        "new_report": new_report,
        "summary": summary,
    }
