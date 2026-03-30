import pytest

pd = pytest.importorskip("pandas")
pytest.importorskip("yaml")


def _schema_for_joins() -> object:
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


def test_execute_join_left_has_trace_and_unmatched_warning() -> None:
    from capex_ai.modeling.join_engine import execute_join

    left_df = pd.DataFrame({"k": ["A", "B", "C"], "v1": [1, 2, 3]})
    right_df = pd.DataFrame({"k2": ["A", "B"], "v2": [10, 20]})

    result = execute_join(
        left_df,
        right_df,
        left_table="l",
        right_table="r",
        left_on="k",
        right_on="k2",
        join_type="left",
        relation_name="rel",
    )

    assert len(result.dataframe) == 3
    assert result.trace.rows_before_left == 3
    assert result.trace.rows_after == 3
    assert result.trace.unmatched_left_count == 1
    assert any("sem match" in warning for warning in result.trace.warnings)


def test_execute_join_inner_reduces_rows_and_warns() -> None:
    from capex_ai.modeling.join_engine import execute_join

    left_df = pd.DataFrame({"k": ["A", "B", "C"]})
    right_df = pd.DataFrame({"k2": ["A", "B"]})

    result = execute_join(
        left_df,
        right_df,
        left_table="l",
        right_table="r",
        left_on="k",
        right_on="k2",
        join_type="inner",
        relation_name="rel",
    )

    assert len(result.dataframe) == 2
    assert any("descartará" in warning for warning in result.trace.warnings)


def test_execute_join_anti_returns_only_unmatched_left() -> None:
    from capex_ai.modeling.join_engine import execute_join

    left_df = pd.DataFrame({"k": ["A", "B", "C"], "v": [1, 2, 3]})
    right_df = pd.DataFrame({"k2": ["A", "B"]})

    result = execute_join(
        left_df,
        right_df,
        left_table="l",
        right_table="r",
        left_on="k",
        right_on="k2",
        join_type="anti",
        relation_name="rel",
    )

    assert result.dataframe["k"].tolist() == ["C"]
    assert result.trace.rows_after == 1


def test_materialize_base_views_returns_expected_views_and_trace() -> None:
    from capex_ai.modeling.join_engine import materialize_base_views
    from capex_ai.validation.relations import validate_relationships

    schema = _schema_for_joins()
    frames = {
        "wo_afes": pd.DataFrame({"wonum": ["WO1", "WO2"]}),
        "admafecost": pd.DataFrame({"wonum": ["WO1"]}),
        "inv_afe": pd.DataFrame({"refwo": ["WO1"], "invoicecostid": [1]}),
        "multiassetlocci": pd.DataFrame(
            {
                "recordkey": ["WO1", "WO2"],
                "CHAVE_WO_CODE": ["C1", "C2"],
            }
        ),
        "invoicecost": pd.DataFrame({"CHAVE_WO_CODE": ["C1", "C9"], "linecost": [100, 200]}),
    }

    relation_results = validate_relationships(frames=frames, schema=schema)
    views = materialize_base_views(frames=frames, schema=schema, relation_results=relation_results)

    assert set(views.keys()) == {"wo_consolidated", "wo_costs_invoices"}
    assert views["wo_consolidated"].trace.join_type == "left"
    assert isinstance(views["wo_costs_invoices"].trace.warnings, list)
