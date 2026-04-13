from __future__ import annotations

import importlib

import pytest

pytestmark = pytest.mark.core


def _pd() -> object:
    try:
        return importlib.import_module("pandas")
    except ModuleNotFoundError:
        pytest.fail(
            "Dependência obrigatória ausente: pandas. "
            "Execute `python scripts/preflight_check.py` para validar o runtime."
        )


def _schema_for_lookup() -> object:
    from capex_ai.models.schema import RelationshipSpec, SchemaSpec, SideSpec, TableSpec

    return SchemaSpec(
        version=1,
        source_kind="excel_workbook",
        tables=[
            TableSpec(original_name="WO-AFES", alias="wo_afes", columns=["wonum"]),
            TableSpec(
                original_name="multiassetlocci",
                alias="multiassetlocci",
                columns=["recordkey", "CHAVE_WO_CODE", "budget", "budgetcode"],
            ),
            TableSpec(
                original_name="INVOICECOST",
                alias="invoicecost",
                columns=["CHAVE_WO_CODE", "linecost", "admchangedate"],
            ),
        ],
        relationships=[
            RelationshipSpec(
                name="wo_afes_to_multiassetlocci_by_wonum_recordkey",
                kind="operational_hypothesis",
                left=SideSpec(table_alias="wo_afes", column="wonum"),
                right=SideSpec(table_alias="multiassetlocci", column="recordkey"),
            ),
            RelationshipSpec(
                name="invoicecost_to_multiassetlocci_by_chave_wo_code",
                kind="operational_hypothesis",
                left=SideSpec(table_alias="invoicecost", column="CHAVE_WO_CODE"),
                right=SideSpec(table_alias="multiassetlocci", column="CHAVE_WO_CODE"),
            )
        ],
    )


def test_get_budget_by_budgetcode_aggregates_duplicate_budgetcodes() -> None:
    from capex_ai.modeling.budget_views import get_budget_by_budgetcode

    schema = _schema_for_lookup()
    frames = {
        "wo_afes": _pd().DataFrame({"wonum": ["BM9-176428", "BM9-176428", "OTHER"]}),
        "multiassetlocci": _pd().DataFrame(
            {
                "recordkey": ["BM9-176428", "BM9-176428", "BM9-176428", "NOT-IN-WO"],
                "CHAVE_WO_CODE": ["C1", "C2", "C3", "CX"],
                "budget": [1000, 250, 2000, 3000],
                "budgetcode": ["BUD-1", "BUD-1", "BUD-2", "BUD-X"],
            }
        ),
        "invoicecost": _pd().DataFrame(columns=["CHAVE_WO_CODE", "linecost", "admchangedate"]),
    }

    result = get_budget_by_budgetcode(
        frames=frames,
        schema=schema,
        wonum="BM9-176428",
    )

    assert list(result.columns) == ["budgetcode", "budget_sum"]
    assert result.to_dict("records") == [
        {"budgetcode": "BUD-1", "budget_sum": 1250},
        {"budgetcode": "BUD-2", "budget_sum": 2000},
    ]


def test_get_budget_by_budgetcode_returns_empty_table_when_no_match() -> None:
    from capex_ai.modeling.budget_views import get_budget_by_budgetcode

    schema = _schema_for_lookup()
    frames = {
        "wo_afes": _pd().DataFrame({"wonum": ["OTHER"]}),
        "multiassetlocci": _pd().DataFrame(
            {
                "recordkey": ["OTHER"],
                "CHAVE_WO_CODE": ["C1"],
                "budget": [1000],
                "budgetcode": ["BUD-1"],
            }
        ),
        "invoicecost": _pd().DataFrame(columns=["CHAVE_WO_CODE", "linecost", "admchangedate"]),
    }

    result = get_budget_by_budgetcode(
        frames=frames,
        schema=schema,
        wonum="BM9-176428",
    )

    assert list(result.columns) == ["budgetcode", "budget_sum"]
    assert result.empty


def test_get_weekly_budget_view_returns_last_4_weeks_newest_first_with_delta() -> None:
    from capex_ai.modeling.budget_views import get_weekly_budget_view

    schema = _schema_for_lookup()
    frames = {
        "wo_afes": _pd().DataFrame({"wonum": ["BM9-176428"]}),
        "multiassetlocci": _pd().DataFrame(
            {
                "recordkey": ["BM9-176428", "BM9-176428", "BM9-176428", "BM9-176428"],
                "CHAVE_WO_CODE": ["C1", "C2", "C3", "C4"],
                "budget": [1000, 250, 2000, 0],
                "budgetcode": ["BUD-1", "BUD-1", "BUD-2", "BUD-0"],
            }
        ),
        "invoicecost": _pd().DataFrame(
            {
                "CHAVE_WO_CODE": ["C1", "C2", "C1", "C3", "C4", "C1", "C1"],
                "linecost": [5, 10, 100, 500, 50, 200, 10],
                "admchangedate": [
                    "2024-05-27",
                    "2024-05-27",
                    "2024-06-03",
                    "2024-06-10",
                    "2024-06-17",
                    "2024-06-17",
                    "2024-05-20",
                ],
            }
        ),
    }

    result = get_weekly_budget_view(frames=frames, schema=schema, wonum="BM9-176428")

    assert list(result.columns) == [
        "ref_date",
        "budgetcode",
        "budget_sum",
        "linecost_sum",
        "remaining_budget_pct",
        "remaining_budget_pct_delta_vs_prev_week",
    ]
    assert result["ref_date"].astype(str).tolist() == [
        "2024-06-23",
        "2024-06-23",
        "2024-06-23",
        "2024-06-16",
        "2024-06-16",
        "2024-06-09",
        "2024-06-09",
        "2024-06-02",
        "2024-06-02",
    ]
    assert result["budgetcode"].tolist() == [
        "BUD-0",
        "BUD-1",
        "BUD-2",
        "BUD-1",
        "BUD-2",
        "BUD-1",
        "BUD-2",
        "BUD-1",
        "BUD-2",
    ]
    assert result["budget_sum"].tolist() == [0, 1250, 2000, 1250, 2000, 1250, 2000, 1250, 2000]
    assert result["linecost_sum"].tolist() == [50, 325, 500, 125, 500, 125, 0, 25, 0]
    assert all(_pd().to_datetime(result["ref_date"]).dt.dayofweek == 6)

    first_row = result.iloc[0]
    assert _pd().isna(first_row["remaining_budget_pct"])
    assert first_row["remaining_budget_pct_delta_vs_prev_week"] == "Primeira ocorrência"

    second_row = result.iloc[1]
    assert second_row["remaining_budget_pct"] == pytest.approx(74.0)
    assert second_row["remaining_budget_pct_delta_vs_prev_week"] == pytest.approx(-16.0)

    third_row = result.iloc[2]
    assert third_row["remaining_budget_pct"] == pytest.approx(75.0)
    assert third_row["remaining_budget_pct_delta_vs_prev_week"] == pytest.approx(0.0)

    unchanged_row = result.iloc[5]
    assert unchanged_row["budgetcode"] == "BUD-1"
    assert unchanged_row["linecost_sum"] == 125
    assert unchanged_row["remaining_budget_pct"] == pytest.approx(90.0)

    carried_row = result.iloc[8]
    assert carried_row["budgetcode"] == "BUD-2"
    assert carried_row["linecost_sum"] == 0
    assert carried_row["remaining_budget_pct_delta_vs_prev_week"] == pytest.approx(0.0)


def test_get_weekly_budget_view_handles_zero_budget_explicitly() -> None:
    from capex_ai.modeling.budget_views import get_weekly_budget_view

    schema = _schema_for_lookup()
    frames = {
        "wo_afes": _pd().DataFrame({"wonum": ["BM9-176428"]}),
        "multiassetlocci": _pd().DataFrame(
            {
                "recordkey": ["BM9-176428"],
                "CHAVE_WO_CODE": ["C1"],
                "budget": [0],
                "budgetcode": ["BUD-0"],
            }
        ),
        "invoicecost": _pd().DataFrame(
            {
                "CHAVE_WO_CODE": ["C1"],
                "linecost": [50],
                "admchangedate": ["2024-06-17"],
            }
        ),
    }

    result = get_weekly_budget_view(frames=frames, schema=schema, wonum="BM9-176428")

    assert result.iloc[0]["budget_sum"] == 0
    assert _pd().isna(result.iloc[0]["remaining_budget_pct"])
    assert result.iloc[0]["remaining_budget_pct_delta_vs_prev_week"] == "Primeira ocorrência"


def test_get_weekly_budget_view_hides_only_rows_with_zero_budget_and_zero_cost() -> None:
    from capex_ai.modeling.budget_views import get_weekly_budget_view

    schema = _schema_for_lookup()
    frames = {
        "wo_afes": _pd().DataFrame({"wonum": ["BM9-176428"]}),
        "multiassetlocci": _pd().DataFrame(
            {
                "recordkey": ["BM9-176428", "BM9-176428"],
                "CHAVE_WO_CODE": ["C1", "C2"],
                "budget": [0, 100],
                "budgetcode": ["BUD-0", "BUD-1"],
            }
        ),
        "invoicecost": _pd().DataFrame(
            {
                "CHAVE_WO_CODE": ["C1"],
                "linecost": [50],
                "admchangedate": ["2024-06-17"],
            }
        ),
    }

    result = get_weekly_budget_view(frames=frames, schema=schema, wonum="BM9-176428")

    assert result["budgetcode"].tolist() == ["BUD-0", "BUD-1"]
