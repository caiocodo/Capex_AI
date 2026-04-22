from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.integration

pytest.importorskip("pandas")
pytest.importorskip("yaml")
pytest.importorskip("openpyxl")

RELEVANT_WONUMS = [
    "BM9-132818",
    "BM9-132814",
    "BM9-176552",
    "UDD-918308",
    "BM9-186541",
    "BM9-176428",
]

EXPECTED_RELEVANT_PROJECTS = [
    {
        "wonum": "BM9-176428",
        "budget_sum": 180232878.00,
        "cumulative_linecost_sum": 119549581.10,
        "remaining_budget_pct": 33.669382,
        "targstartdate": "2024-03-01",
        "targcompdate": "2025-10-01",
        "extendedtargcompdate": "2026-12-31",
    },
    {
        "wonum": "BM9-176552",
        "budget_sum": 41820336.74,
        "cumulative_linecost_sum": 35347074.22,
        "remaining_budget_pct": 15.478743,
        "targstartdate": "2024-02-29",
        "targcompdate": "2025-10-31",
        "extendedtargcompdate": "2026-12-31",
    },
    {
        "wonum": "UDD-918308",
        "budget_sum": 26246829.00,
        "cumulative_linecost_sum": 17474166.96,
        "remaining_budget_pct": 33.423702,
        "targstartdate": "2023-03-15",
        "targcompdate": "2025-01-31",
        "extendedtargcompdate": "2026-12-31",
    },
    {
        "wonum": "BM9-186541",
        "budget_sum": 25482921.30,
        "cumulative_linecost_sum": 12130080.66,
        "remaining_budget_pct": 52.399175,
        "targstartdate": "2024-04-30",
        "targcompdate": "2025-10-31",
        "extendedtargcompdate": "2026-12-31",
    },
    {
        "wonum": "BM9-132814",
        "budget_sum": 16434153.75,
        "cumulative_linecost_sum": 7080799.11,
        "remaining_budget_pct": 56.914124,
        "targstartdate": "2024-04-19",
        "targcompdate": "2025-12-19",
        "extendedtargcompdate": "2026-12-31",
    },
    {
        "wonum": "BM9-132818",
        "budget_sum": 14511999.28,
        "cumulative_linecost_sum": 9450391.55,
        "remaining_budget_pct": 34.878776,
        "targstartdate": "2024-04-29",
        "targcompdate": "2026-12-31",
        "extendedtargcompdate": "2026-12-31",
    },
]

def test_get_projects_overview_real_workbook_covers_relevant_wonums() -> None:
    from capex_ai.io.excel_loader import load_canonical_workbook_from_schema_file
    from capex_ai.modeling.projects_overview import get_projects_overview
    from capex_ai.models.schema import load_schema

    schema_path = Path("configs/schema.yaml")
    workbook_path = Path("tests/fixtures/Capex AI - Dados.xlsx")

    schema = load_schema(schema_path)
    frames = load_canonical_workbook_from_schema_file(
        excel_path=workbook_path,
        schema_path=schema_path,
    )

    result = get_projects_overview(frames=frames, schema=schema, ref_date="2026-03-02")
    relevant = result[result["wonum"].isin(RELEVANT_WONUMS)].reset_index(drop=True)

    assert set(relevant["wonum"]) == set(RELEVANT_WONUMS)
    assert relevant["wonum"].tolist() == [
        expected["wonum"] for expected in EXPECTED_RELEVANT_PROJECTS
    ]

    for index, expected in enumerate(EXPECTED_RELEVANT_PROJECTS):
        row = relevant.iloc[index]

        assert row["budget_sum"] == pytest.approx(expected["budget_sum"], abs=0.01)
        assert row["cumulative_linecost_sum"] == pytest.approx(
            expected["cumulative_linecost_sum"],
            abs=0.01,
        )
        assert row["remaining_budget_pct"] == pytest.approx(
            expected["remaining_budget_pct"],
            abs=0.000001,
        )
        assert str(row["targstartdate"].date()) == expected["targstartdate"]
        assert str(row["targcompdate"].date()) == expected["targcompdate"]
        assert str(row["extendedtargcompdate"].date()) == expected["extendedtargcompdate"]
        assert row["status"] == "Fora da janela"
