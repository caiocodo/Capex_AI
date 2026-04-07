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

def _schema_for_relation() -> object:
    from capex_ai.models.schema import RelationshipSpec, SchemaSpec, SideSpec

    return SchemaSpec(
        version=1,
        source_kind="excel_workbook",
        tables=[],
        relationships=[
            RelationshipSpec(
                name="wo_to_adm",
                kind="operational_hypothesis",
                left=SideSpec(table_alias="wo_afes", column="wonum"),
                right=SideSpec(table_alias="admafecost", column="wonum"),
            )
        ],
    )

def test_analyze_orphan_records_counts_and_samples() -> None:
    from capex_ai.analysis.orphan_records import analyze_orphan_records

    schema = _schema_for_relation()
    frames = {
        "wo_afes": _pd().DataFrame({"wonum": ["WO1", "WO2", "WO3"]}),
        "admafecost": _pd().DataFrame({"wonum": ["WO1", "WOX"]}),
    }

    result = analyze_orphan_records(frames=frames, schema=schema)

    assert result.applied_filters == "sem filtros"
    assert len(result.relation_reports) == 1

    rel = result.relation_reports[0]
    assert rel.unmatched_left_count == 2
    assert rel.unmatched_right_count == 1
    assert rel.unmatched_left_samples == ["WO2", "WO3"]
    assert rel.unmatched_right_samples == ["WOX"]
