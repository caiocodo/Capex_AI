from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from capex_ai.models.schema import SchemaSpec
from capex_ai.validation.relations import RelationshipValidationResult, validate_relationships

DataFramesByAlias = dict[str, pd.DataFrame]


@dataclass(frozen=True)
class OrphanRelationReport:
    relationship_name: str
    left_table: str
    right_table: str
    left_column: str
    right_column: str
    unmatched_left_count: int
    unmatched_right_count: int
    unmatched_left_samples: list[str]
    unmatched_right_samples: list[str]
    recommendation: str
    notes: list[str]


@dataclass(frozen=True)
class OrphanAnalysisResult:
    universe_analyzed: dict[str, int]
    applied_filters: str
    data_quality_limitations: list[str]
    fields_used: list[str]
    relation_reports: list[OrphanRelationReport]


def _to_orphan_report(item: RelationshipValidationResult) -> OrphanRelationReport:
    unmatched_left_count = item.left_metrics.matched_rows_count
    non_null_left = item.left_metrics.total_rows - item.left_metrics.null_count
    orphan_left_count = non_null_left - unmatched_left_count

    unmatched_right_count = item.right_metrics.matched_rows_count
    non_null_right = item.right_metrics.total_rows - item.right_metrics.null_count
    orphan_right_count = non_null_right - unmatched_right_count

    return OrphanRelationReport(
        relationship_name=item.relationship_name,
        left_table=item.left_table,
        right_table=item.right_table,
        left_column=item.left_column,
        right_column=item.right_column,
        unmatched_left_count=orphan_left_count,
        unmatched_right_count=orphan_right_count,
        unmatched_left_samples=item.unmatched_left_samples,
        unmatched_right_samples=item.unmatched_right_samples,
        recommendation=item.recommendation.value,
        notes=item.notes,
    )


def analyze_orphan_records(
    frames: DataFramesByAlias,
    schema: SchemaSpec,
    relation_results: list[RelationshipValidationResult] | None = None,
) -> OrphanAnalysisResult:
    """Análise operacional de registros órfãos/não conciliados por relação conhecida."""
    if relation_results is None:
        relation_results = validate_relationships(frames=frames, schema=schema)

    reports = [_to_orphan_report(item) for item in relation_results]

    limitations: list[str] = []
    for item in relation_results:
        if item.notes:
            limitations.extend(item.notes)

    return OrphanAnalysisResult(
        universe_analyzed={name: len(df) for name, df in frames.items()},
        applied_filters="sem filtros",
        data_quality_limitations=sorted(set(limitations)),
        fields_used=[
            f"{item.left_table}.{item.left_column} <-> {item.right_table}.{item.right_column}"
            for item in relation_results
        ],
        relation_reports=reports,
    )
