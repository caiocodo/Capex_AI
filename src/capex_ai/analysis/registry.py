from __future__ import annotations

from capex_ai.analysis.base import AnalysisMetadata, AnalysisRunOutput, RegisteredAnalysis


def _run_orphan_records(frames, schema, relation_results, params):
    from capex_ai.analysis.orphan_records import analyze_orphan_records

    result = analyze_orphan_records(
        frames=frames,
        schema=schema,
        relation_results=relation_results,
    )
    rows = [
        {
            "relationship_name": item.relationship_name,
            "left_table": item.left_table,
            "right_table": item.right_table,
            "left_column": item.left_column,
            "right_column": item.right_column,
            "unmatched_left_count": item.unmatched_left_count,
            "unmatched_right_count": item.unmatched_right_count,
            "recommendation": item.recommendation,
        }
        for item in result.relation_reports
    ]
    import pandas as pd

    return AnalysisRunOutput(
        metadata=ANALYSES["orphan_records"].metadata,
        universe_analyzed=result.universe_analyzed,
        applied_filters=result.applied_filters,
        data_quality_limitations=result.data_quality_limitations,
        fields_used=result.fields_used,
        dataframe=pd.DataFrame(rows),
        details={
            "relation_count": len(result.relation_reports),
        },
    )


def _run_cost_summary_by_wo(frames, schema, relation_results, params):
    from capex_ai.analysis.cost_summary_by_wo import summarize_costs_by_wo

    result = summarize_costs_by_wo(
        frames=frames,
        schema=schema,
        relation_results=relation_results,
    )
    return AnalysisRunOutput(
        metadata=ANALYSES["cost_summary_by_wo"].metadata,
        universe_analyzed=result.universe_analyzed,
        applied_filters=result.applied_filters,
        data_quality_limitations=result.data_quality_limitations,
        fields_used=result.fields_used,
        dataframe=result.dataframe,
        details={"ambiguity_notes": result.ambiguity_notes},
    )


ANALYSES: dict[str, RegisteredAnalysis] = {
    "orphan_records": RegisteredAnalysis(
        metadata=AnalysisMetadata(
            analysis_id="orphan_records",
            friendly_name="Registros órfãos / não conciliados",
            description="Mostra contagens e amostras de não conciliados por relação.",
            parameters=[],
            output_format="table + summary",
        ),
        executor=_run_orphan_records,
    ),
    "cost_summary_by_wo": RegisteredAnalysis(
        metadata=AnalysisMetadata(
            analysis_id="cost_summary_by_wo",
            friendly_name="Resumo de custos por WO",
            description="Resumo conservador por WO com campos monetários explicitamente usados.",
            parameters=[],
            output_format="table + summary",
        ),
        executor=_run_cost_summary_by_wo,
    ),
}


def get_analysis_registry() -> dict[str, RegisteredAnalysis]:
    return ANALYSES


def list_analysis_metadata() -> list[AnalysisMetadata]:
    return [item.metadata for item in ANALYSES.values()]
