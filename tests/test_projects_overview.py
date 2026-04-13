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


def _schema_for_projects() -> object:
    from capex_ai.models.schema import RelationshipSpec, SchemaSpec, SideSpec, TableSpec

    return SchemaSpec(
        version=1,
        source_kind="excel_workbook",
        tables=[
            TableSpec(
                original_name="WO-AFES",
                alias="wo_afes",
                columns=[
                    "wonum",
                    "TARGSTARTDATE",
                    "TARGCOMPDATE",
                    "EXTENDEDTARGCOMPDATE",
                    "WOBUDGET",
                ],
            ),
            TableSpec(
                original_name="multiassetlocci",
                alias="multiassetlocci",
                columns=["recordkey", "CHAVE_WO_CODE", "budget", "budgetcode"],
            ),
            TableSpec(
                original_name="INVOICECOST",
                alias="invoicecost",
                columns=["CHAVE_WO_CODE", "refwo", "linecost", "admchangedate"],
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
            ),
        ],
    )


def test_get_projects_overview_builds_budget_cost_dates_status_and_sorting() -> None:
    from capex_ai.modeling.projects_overview import get_projects_overview

    schema = _schema_for_projects()
    frames = {
        "wo_afes": _pd().DataFrame(
            {
                "wonum": ["WO1", "WO2", "WO3", "WO4"],
                "TARGSTARTDATE": ["2024-05-01", "2024-05-15", "2024-04-01", "2024-01-01"],
                "TARGCOMPDATE": ["2024-06-10", "2024-05-20", "2024-06-01", "2024-02-01"],
                "EXTENDEDTARGCOMPDATE": ["2024-06-15", None, None, None],
                "WOBUDGET": [1500, 1500, 0, 0],
            }
        ),
        "multiassetlocci": _pd().DataFrame(
            {
                "recordkey": ["WO1", "WO1", "WO2", "WO3"],
                "CHAVE_WO_CODE": ["C1", "C2", "C3", "C4"],
                "budget": [1000, 500, 1500, 0],
                "budgetcode": ["B1", "B2", "B1", "B0"],
            }
        ),
        "invoicecost": _pd().DataFrame(
            {
                "CHAVE_WO_CODE": ["C1", "C2", "C3", "C4"],
                "refwo": ["WO1", "WO1", "WO2", "WO3"],
                "linecost": [200, 100, 1600, 50],
                "admchangedate": [
                    "sábado, 1 de junho de 2024",
                    "quinta-feira, 20 de junho de 2024",
                    "quarta-feira, 5 de junho de 2024",
                    "terça-feira, 18 de junho de 2024",
                ],
            }
        ),
    }

    result = get_projects_overview(
        frames=frames,
        schema=schema,
        ref_date="2024-06-20",
    )

    assert list(result.columns) == [
        "wonum",
        "budget_sum",
        "cumulative_linecost_sum",
        "remaining_budget_pct",
        "targstartdate",
        "targcompdate",
        "extendedtargcompdate",
        "status",
    ]
    assert result["wonum"].tolist() == ["WO2", "WO1", "WO3"]

    wo2 = result.iloc[0]
    assert wo2["budget_sum"] == 1500
    assert wo2["cumulative_linecost_sum"] == 1600
    assert wo2["remaining_budget_pct"] == pytest.approx(-6.6666666667)
    assert wo2["status"] == "Fora da janela"

    wo1 = result.iloc[1]
    assert wo1["budget_sum"] == 1500
    assert wo1["cumulative_linecost_sum"] == 300
    assert wo1["remaining_budget_pct"] == pytest.approx(80.0)
    assert str(wo1["targstartdate"].date()) == "2024-05-01"
    assert str(wo1["targcompdate"].date()) == "2024-06-10"
    assert str(wo1["extendedtargcompdate"].date()) == "2024-06-15"
    assert wo1["status"] == "Em andamento"

    wo3 = result.iloc[2]
    assert wo3["budget_sum"] == 0
    assert wo3["cumulative_linecost_sum"] == 50
    assert _pd().isna(wo3["remaining_budget_pct"])


def test_get_projects_overview_uses_ref_date_to_limit_cumulative_cost() -> None:
    from capex_ai.modeling.projects_overview import get_projects_overview

    schema = _schema_for_projects()
    frames = {
        "wo_afes": _pd().DataFrame(
            {
                "wonum": ["WO1"],
                "TARGSTARTDATE": ["2024-05-01"],
                "TARGCOMPDATE": ["2024-06-10"],
                "EXTENDEDTARGCOMPDATE": [None],
                "WOBUDGET": [1000],
            }
        ),
        "multiassetlocci": _pd().DataFrame(
            {
                "recordkey": ["WO1"],
                "CHAVE_WO_CODE": ["C1"],
                "budget": [1000],
                "budgetcode": ["B1"],
            }
        ),
        "invoicecost": _pd().DataFrame(
            {
                "CHAVE_WO_CODE": ["C1", "C1"],
                "refwo": ["WO1", "WO1"],
                "linecost": [100, 250],
                "admchangedate": ["2024-06-01", "2024-06-25"],
            }
        ),
    }

    result = get_projects_overview(frames=frames, schema=schema, ref_date="2024-06-20")

    assert result.iloc[0]["cumulative_linecost_sum"] == 100


def test_get_projects_overview_handles_sparse_multiasset_for_projects() -> None:
    from capex_ai.modeling.projects_overview import get_projects_overview

    schema = _schema_for_projects()
    frames = {
        "wo_afes": _pd().DataFrame(
            {
                "wonum": ["WO-A", "WO-B", "WO-Z"],
                "TARGSTARTDATE": ["2024-05-01", "2024-05-01", "2024-05-01"],
                "TARGCOMPDATE": ["2024-06-30", "2024-06-30", "2024-06-30"],
                "EXTENDEDTARGCOMPDATE": [None, None, None],
                "WOBUDGET": [1000, 500, 0],
            }
        ),
        "multiassetlocci": _pd().DataFrame(
            {
                "recordkey": ["OTHER"],
                "CHAVE_WO_CODE": ["C-OTHER"],
                "budget": [999],
                "budgetcode": ["B-OTHER"],
            }
        ),
        "invoicecost": _pd().DataFrame(
            {
                "CHAVE_WO_CODE": [
                    "NO-BRIDGE-A1",
                    "NO-BRIDGE-A2",
                    "NO-BRIDGE-B1",
                    "NO-BRIDGE-B2",
                ],
                "refwo": ["WO-A", "WO-A", "WO-B", "WO-B"],
                "linecost": [100, 25, 50, 999],
                "admchangedate": ["2024-06-01", "2024-06-20", "2024-06-18", "2024-07-01"],
            }
        ),
    }

    result = get_projects_overview(frames=frames, schema=schema, ref_date="2024-06-20")

    assert result[["wonum", "budget_sum", "cumulative_linecost_sum"]].to_dict(
        orient="records"
    ) == [
        {"wonum": "WO-A", "budget_sum": 1000, "cumulative_linecost_sum": 125},
        {"wonum": "WO-B", "budget_sum": 500, "cumulative_linecost_sum": 50},
    ]
