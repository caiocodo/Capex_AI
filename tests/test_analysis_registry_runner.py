import pytest

pd = pytest.importorskip("pandas")
pytest.importorskip("yaml")


def test_registry_lists_available_analyses() -> None:
    from capex_ai.analysis.runner import list_available_analyses

    metas = list_available_analyses()
    ids = {item.analysis_id for item in metas}

    assert "orphan_records" in ids
    assert "cost_summary_by_wo" in ids


def test_runner_executes_analysis_with_injected_registry(monkeypatch: pytest.MonkeyPatch) -> None:
    from capex_ai.analysis.base import AnalysisMetadata, AnalysisRunOutput, RegisteredAnalysis
    from capex_ai.analysis.runner import run_analysis

    def fake_schema(_path):
        return object()

    frames = {
        "wo_afes": pd.DataFrame({"wonum": ["WO1"]}),
        "admafecost": pd.DataFrame({"wonum": ["WO1"]}),
    }

    def fake_load_frames(excel_path, schema_path):
        return frames

    def fake_validate(frames, schema):
        return []

    monkeypatch.setattr("capex_ai.models.schema.load_schema", fake_schema)
    monkeypatch.setattr(
        "capex_ai.io.excel_loader.load_canonical_workbook_from_schema_file",
        fake_load_frames,
    )
    monkeypatch.setattr("capex_ai.validation.relations.validate_relationships", fake_validate)

    def fake_executor(frames, schema, relation_results, params):
        return AnalysisRunOutput(
            metadata=AnalysisMetadata(
                analysis_id="fake",
                friendly_name="Fake",
                description="Fake",
                parameters=[],
                output_format="table",
            ),
            universe_analyzed={"wo_afes": 1},
            applied_filters="sem filtros",
            data_quality_limitations=[],
            fields_used=["wo_afes.wonum"],
            dataframe=pd.DataFrame({"wonum": ["WO1"]}),
            details={},
        )

    registry = {
        "fake": RegisteredAnalysis(
            metadata=AnalysisMetadata(
                analysis_id="fake",
                friendly_name="Fake",
                description="Fake",
                parameters=[],
                output_format="table",
            ),
            executor=fake_executor,
        )
    }

    output = run_analysis(
        analysis_id="fake",
        excel_path="dummy.xlsx",
        schema_path="dummy.yaml",
        params={},
        registry=registry,
    )

    assert output.metadata.analysis_id == "fake"
    assert output.universe_analyzed["wo_afes"] == 1


def test_runner_validates_required_params() -> None:
    from capex_ai.analysis.base import (
        AnalysisMetadata,
        AnalysisParameter,
        AnalysisRunOutput,
        RegisteredAnalysis,
    )
    from capex_ai.analysis.runner import run_analysis

    def fake_executor(frames, schema, relation_results, params):
        return AnalysisRunOutput(
            metadata=AnalysisMetadata(
                analysis_id="needs_param",
                friendly_name="Needs Param",
                description="Needs Param",
                parameters=[AnalysisParameter(name="required_x", required=True, description="x")],
                output_format="table",
            ),
            universe_analyzed={},
            applied_filters="sem filtros",
            data_quality_limitations=[],
            fields_used=[],
            dataframe=None,
            details={},
        )

    registry = {
        "needs_param": RegisteredAnalysis(
            metadata=AnalysisMetadata(
                analysis_id="needs_param",
                friendly_name="Needs Param",
                description="Needs Param",
                parameters=[AnalysisParameter(name="required_x", required=True, description="x")],
                output_format="table",
            ),
            executor=fake_executor,
        )
    }

    with pytest.raises(ValueError, match="Parâmetros obrigatórios ausentes"):
        run_analysis(
            analysis_id="needs_param",
            excel_path="dummy.xlsx",
            schema_path="dummy.yaml",
            params={},
            registry=registry,
        )


def test_runner_unknown_analysis_has_clear_error() -> None:
    from capex_ai.analysis.runner import run_analysis

    with pytest.raises(ValueError, match="não encontrada"):
        run_analysis(
            analysis_id="nao_existe",
            excel_path="dummy.xlsx",
            schema_path="dummy.yaml",
            params={},
            registry={},
        )
