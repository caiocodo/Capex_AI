from __future__ import annotations

from pathlib import Path

import pytest

pd = pytest.importorskip("pandas")
pytest.importorskip("yaml")
pytest.importorskip("openpyxl")


def _write_min_schema(path: Path) -> None:
    path.write_text(
        """
version: 1
source:
  kind: excel_workbook

tables:
  - original_name: admafecost
    alias: admafecost
    columns: [wonum, afespend]
  - original_name: INV-AFE
    alias: inv_afe
    columns: [refwo, linecost]
  - original_name: INVOICECOST
    alias: invoicecost
    columns: [CHAVE_WO_CODE, linecost]
  - original_name: multiassetlocci
    alias: multiassetlocci
    columns: [recordkey, CHAVE_WO_CODE]
  - original_name: WO-AFES
    alias: wo_afes
    columns: [wonum]

relationships:
  - name: wo_afes_to_admafecost_by_wonum
    kind: operational_hypothesis
    left: {table_alias: wo_afes, column: wonum}
    right: {table_alias: admafecost, column: wonum}
  - name: wo_afes_to_inv_afe_by_wonum_refwo
    kind: operational_hypothesis
    left: {table_alias: wo_afes, column: wonum}
    right: {table_alias: inv_afe, column: refwo}
  - name: wo_afes_to_multiassetlocci_by_wonum_recordkey
    kind: operational_hypothesis
    left: {table_alias: wo_afes, column: wonum}
    right: {table_alias: multiassetlocci, column: recordkey}
  - name: invoicecost_to_multiassetlocci_by_chave_wo_code
    kind: operational_hypothesis
    left: {table_alias: invoicecost, column: CHAVE_WO_CODE}
    right: {table_alias: multiassetlocci, column: CHAVE_WO_CODE}
""".strip(),
        encoding="utf-8",
    )


def _write_min_workbook(path: Path) -> None:
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        pd.DataFrame({"wonum": ["WO1", "WO2"], "afespend": [10, 20]}).to_excel(
            writer, index=False, sheet_name="admafecost"
        )
        pd.DataFrame({"refwo": ["WO1"], "linecost": [5]}).to_excel(
            writer, index=False, sheet_name="INV-AFE"
        )
        pd.DataFrame({"CHAVE_WO_CODE": ["C1"], "linecost": [100]}).to_excel(
            writer, index=False, sheet_name="INVOICECOST"
        )
        pd.DataFrame({"recordkey": ["WO1"], "CHAVE_WO_CODE": ["C1"]}).to_excel(
            writer, index=False, sheet_name="multiassetlocci"
        )
        pd.DataFrame({"wonum": ["WO1", "WO2"]}).to_excel(
            writer, index=False, sheet_name="WO-AFES"
        )


def test_e2e_load_validate_materialize_and_analyze(tmp_path: Path) -> None:
    from capex_ai.analysis.orphan_records import analyze_orphan_records
    from capex_ai.io.excel_loader import load_canonical_workbook_from_schema_file
    from capex_ai.modeling.join_engine import materialize_base_views
    from capex_ai.models.schema import load_schema
    from capex_ai.validation.relations import validate_relationships

    workbook_path = tmp_path / "fixture.xlsx"
    schema_path = tmp_path / "schema.yaml"
    _write_min_workbook(workbook_path)
    _write_min_schema(schema_path)

    schema = load_schema(schema_path)
    frames = load_canonical_workbook_from_schema_file(workbook_path, schema_path)

    relation_results = validate_relationships(frames=frames, schema=schema)
    views = materialize_base_views(frames=frames, schema=schema, relation_results=relation_results)
    orphan_result = analyze_orphan_records(
        frames=frames,
        schema=schema,
        relation_results=relation_results,
    )

    assert set(frames.keys()) == {
        "admafecost",
        "inv_afe",
        "invoicecost",
        "multiassetlocci",
        "wo_afes",
    }
    assert len(relation_results) == 4
    assert set(views.keys()) == {"wo_consolidated", "wo_costs_invoices"}
    assert len(orphan_result.relation_reports) == 4
