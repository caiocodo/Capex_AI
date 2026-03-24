import pytest

pd = pytest.importorskip("pandas")
pytest.importorskip("yaml")


def _schema_with_single_relation() -> object:
    from capex_ai.models.schema import RelationshipSpec, SchemaSpec, SideSpec

    relation = RelationshipSpec(
        name="wo_to_adm",
        kind="operational_hypothesis",
        left=SideSpec(table_alias="wo_afes", column="wonum"),
        right=SideSpec(table_alias="admafecost", column="wonum"),
    )
    return SchemaSpec(version=1, source_kind="excel_workbook", tables=[], relationships=[relation])


def test_relation_valid_with_observed_cardinality_and_apta() -> None:
    from capex_ai.validation.relations import JoinRecommendation, validate_relationships

    schema = _schema_with_single_relation()
    frames = {
        "wo_afes": pd.DataFrame({"wonum": ["A", "B", "C"]}),
        "admafecost": pd.DataFrame({"wonum": ["A", "A", "B", "C"]}),
    }

    result = validate_relationships(frames, schema)[0]

    assert result.cardinality_observed == "1:N"
    assert result.left_metrics.null_count == 0
    assert result.right_metrics.null_count == 0
    assert result.recommendation == JoinRecommendation.APTA


def test_relation_detects_nulls_and_percentual() -> None:
    from capex_ai.validation.relations import validate_relationships

    schema = _schema_with_single_relation()
    frames = {
        "wo_afes": pd.DataFrame({"wonum": ["A", None, "B", None]}),
        "admafecost": pd.DataFrame({"wonum": ["A", "B", "C", None]}),
    }

    result = validate_relationships(frames, schema)[0]

    assert result.left_metrics.null_count == 2
    assert result.left_metrics.null_pct == 50.0
    assert result.right_metrics.null_count == 1
    assert result.right_metrics.null_pct == 25.0


def test_relation_detects_unmatched_samples() -> None:
    from capex_ai.validation.relations import validate_relationships

    schema = _schema_with_single_relation()
    frames = {
        "wo_afes": pd.DataFrame({"wonum": ["A", "X", "Y"]}),
        "admafecost": pd.DataFrame({"wonum": ["A", "B"]}),
    }

    result = validate_relationships(frames, schema, max_unmatched_samples=2)[0]

    assert result.unmatched_left_samples == ["X", "Y"]
    assert result.unmatched_right_samples == ["B"]


def test_relation_detects_duplicates_per_side() -> None:
    from capex_ai.validation.relations import validate_relationships

    schema = _schema_with_single_relation()
    frames = {
        "wo_afes": pd.DataFrame({"wonum": ["A", "A", "B"]}),
        "admafecost": pd.DataFrame({"wonum": ["A", "B", "B", "B"]}),
    }

    result = validate_relationships(frames, schema)[0]

    assert result.left_metrics.duplicate_rows_count == 2
    assert result.left_metrics.duplicate_keys_count == 1
    assert result.right_metrics.duplicate_rows_count == 3
    assert result.right_metrics.duplicate_keys_count == 1


def test_relation_recommendation_nao_apta_for_low_match() -> None:
    from capex_ai.validation.relations import JoinRecommendation, validate_relationships

    schema = _schema_with_single_relation()
    frames = {
        "wo_afes": pd.DataFrame({"wonum": ["A", "B", "C", "D"]}),
        "admafecost": pd.DataFrame({"wonum": ["X", "Y", "Z", "A"]}),
    }

    result = validate_relationships(frames, schema)[0]

    assert result.left_metrics.matched_rows_pct == 25.0
    assert result.right_metrics.matched_rows_pct == 25.0
    assert result.recommendation == JoinRecommendation.NAO_APTA
