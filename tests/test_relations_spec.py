import pytest

pd = pytest.importorskip("pandas")
pytest.importorskip("yaml")


def test_validate_relationship_presence_returns_results_for_all_relationships() -> None:
    from capex_ai.models.schema import load_schema
    from capex_ai.validation.relations import validate_relationship_presence

    schema = load_schema("configs/schema.yaml")

    frames = {
        "wo_afes": pd.DataFrame({"wonum": ["WO1", None]}),
        "admafecost": pd.DataFrame({"wonum": ["WO1"]}),
        "inv_afe": pd.DataFrame({"refwo": ["WO1", None]}),
        "multiassetlocci": pd.DataFrame(
            {
                "recordkey": ["WO1", "WO2"],
                "CHAVE_WO_CODE": ["C1", None],
            }
        ),
        "invoicecost": pd.DataFrame({"CHAVE_WO_CODE": ["C1", "C2", None]}),
    }

    results = validate_relationship_presence(frames, schema)

    assert len(results) == 4
    by_name = {item.relationship_name: item for item in results}

    assert by_name["wo_afes_to_admafecost_by_wonum"].left_missing_count == 1
    assert by_name["wo_afes_to_inv_afe_by_wonum_refwo"].right_missing_count == 1
    assert by_name["invoicecost_to_multiassetlocci_by_chave_wo_code"].left_missing_count == 1
