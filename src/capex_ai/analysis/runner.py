from __future__ import annotations

from pathlib import Path

from capex_ai.analysis.base import AnalysisMetadata, AnalysisRunOutput, RegisteredAnalysis
from capex_ai.analysis.registry import get_analysis_registry


def list_available_analyses(
    registry: dict[str, RegisteredAnalysis] | None = None,
) -> list[AnalysisMetadata]:
    current_registry = registry if registry is not None else get_analysis_registry()
    return [item.metadata for item in current_registry.values()]


def _validate_required_params(analysis: RegisteredAnalysis, params: dict[str, str]) -> None:
    missing = [
        item.name
        for item in analysis.metadata.parameters
        if item.required and item.name not in params
    ]
    if missing:
        raise ValueError(
            f"Parâmetros obrigatórios ausentes para '{analysis.metadata.analysis_id}': {missing}"
        )


def run_analysis(
    analysis_id: str,
    excel_path: str | Path,
    schema_path: str | Path,
    params: dict[str, str] | None = None,
    registry: dict[str, RegisteredAnalysis] | None = None,
) -> AnalysisRunOutput:
    current_registry = registry if registry is not None else get_analysis_registry()
    if analysis_id not in current_registry:
        available = sorted(current_registry.keys())
        raise ValueError(f"Análise '{analysis_id}' não encontrada. Disponíveis: {available}")

    analysis = current_registry[analysis_id]
    normalized_params = params or {}
    _validate_required_params(analysis, normalized_params)

    from capex_ai.io.excel_loader import load_canonical_workbook_from_schema_file
    from capex_ai.models.schema import load_schema
    from capex_ai.validation.relations import validate_relationships

    schema = load_schema(schema_path)
    frames = load_canonical_workbook_from_schema_file(
        excel_path=excel_path,
        schema_path=schema_path,
    )
    relation_results = validate_relationships(frames=frames, schema=schema)

    return analysis.executor(frames, schema, relation_results, normalized_params)
