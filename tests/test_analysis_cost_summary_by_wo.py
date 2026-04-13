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

def _schema_for_costs() -> object:
    from capex_ai.models.schema import RelationshipSpec, SchemaSpec, SideSpec

    return SchemaSpec(
        version=1,
        source_kind="excel_workbook",
        tables=[],
        relationships=[
            RelationshipSpec(
                name="wo_afes_to_admafecost_by_wonum",
                kind="operational_hypothesis",
                left=SideSpec(table_alias="wo_afes", column="wonum"),
                right=SideSpec(table_alias="admafecost", column="wonum"),
            ),
            RelationshipSpec(
                name="wo_afes_to_inv_afe_by_wonum_refwo",
                kind="operational_hypothesis",
                left=SideSpec(table_alias="wo_afes", column="wonum"),
                right=SideSpec(table_alias="inv_afe", column="refwo"),
            ),
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

def test_summarize_costs_by_wo_conservative_fields_and_totals() -> None:
    from capex_ai.analysis.cost_summary_by_wo import summarize_costs_by_wo

    schema = _schema_for_costs()
    frames = {
        "wo_afes": _pd().DataFrame({"wonum": ["WO1", "WO2"]}),
        "admafecost": _pd().DataFrame(
            {
                "wonum": ["WO1"],
                "afeenteredinv": [10],
                "afeopencommitment": [5],
                "afespend": [7],
                "afeuncommitted": [2],
                "afewapprpo": [1],
            }
        ),
        "inv_afe": _pd().DataFrame({"refwo": ["WO1", "WO1", "WO2"], "linecost": [3, 2, 4]}),
        "invoicecost": _pd().DataFrame({"CHAVE_WO_CODE": ["C1", "C2"], "linecost": [100, 50]}),
        "multiassetlocci": _pd().DataFrame(
            {"CHAVE_WO_CODE": ["C1", "C2"], "recordkey": ["WO1", "WO2"]}
        ),
    }

    result = summarize_costs_by_wo(frames=frames, schema=schema)

    assert result.applied_filters == "sem filtros"
    assert "wo_afes.wonum" in result.fields_used
    assert len(result.ambiguity_notes) >= 1

    wo1 = result.dataframe[result.dataframe["wonum"] == "WO1"].iloc[0]
    assert wo1["inv_afe_linecost_total"] == 5
    assert wo1["invoicecost_linecost_total"] == 100
    assert wo1["afespend"] == 7


def test_summarize_costs_by_wo_accepts_mixed_wonum_types() -> None:
    from capex_ai.analysis.cost_summary_by_wo import summarize_costs_by_wo

    schema = _schema_for_costs()
    frames = {
        "wo_afes": _pd().DataFrame({"wonum": ["WO1", 1002]}),
        "admafecost": _pd().DataFrame({"wonum": ["WO1", 1002], "afespend": [7, 11]}),
        "inv_afe": _pd().DataFrame({"refwo": ["WO1", 1002], "linecost": [3, 4]}),
        "invoicecost": _pd().DataFrame({"CHAVE_WO_CODE": ["C1", "C2"], "linecost": [100, 50]}),
        "multiassetlocci": _pd().DataFrame(
            {"CHAVE_WO_CODE": ["C1", "C2"], "recordkey": ["WO1", 1002]}
        ),
    }

    result = summarize_costs_by_wo(frames=frames, schema=schema)

    assert list(result.dataframe["wonum"]) == [1002, "WO1"]
