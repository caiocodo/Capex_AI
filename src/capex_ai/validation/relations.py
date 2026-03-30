from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

import pandas as pd

from capex_ai.models.schema import SchemaSpec

DataFramesByAlias = dict[str, pd.DataFrame]


class JoinRecommendation(str, Enum):
    APTA = "apta para join"
    APTA_COM_RESSALVAS = "apta com ressalvas"
    NAO_APTA = "não apta"


@dataclass(frozen=True)
class SideMetrics:
    total_rows: int
    null_count: int
    null_pct: float
    distinct_non_null_keys: int
    duplicate_rows_count: int
    duplicate_keys_count: int
    matched_rows_count: int
    matched_rows_pct: float


@dataclass(frozen=True)
class RelationshipValidationResult:
    relationship_name: str
    left_table: str
    right_table: str
    left_column: str
    right_column: str
    missing_columns: list[str]
    cardinality_observed: str
    left_metrics: SideMetrics
    right_metrics: SideMetrics
    unmatched_left_samples: list[str]
    unmatched_right_samples: list[str]
    recommendation: JoinRecommendation
    notes: list[str]


def _side_metrics(keys: pd.Series, other_distinct_keys: set[str]) -> SideMetrics:
    total_rows = int(keys.shape[0])
    null_count = int(keys.isna().sum())
    null_pct = (null_count / total_rows * 100.0) if total_rows > 0 else 0.0

    non_null = keys.dropna().astype(str)
    distinct_non_null_keys = int(non_null.nunique())

    duplicate_mask = non_null.duplicated(keep=False)
    duplicate_rows_count = int(duplicate_mask.sum())
    duplicate_keys_count = int(non_null[duplicate_mask].nunique())

    matched_rows_count = int(non_null.isin(other_distinct_keys).sum())
    matched_rows_pct = (matched_rows_count / len(non_null) * 100.0) if len(non_null) > 0 else 0.0

    return SideMetrics(
        total_rows=total_rows,
        null_count=null_count,
        null_pct=round(null_pct, 2),
        distinct_non_null_keys=distinct_non_null_keys,
        duplicate_rows_count=duplicate_rows_count,
        duplicate_keys_count=duplicate_keys_count,
        matched_rows_count=matched_rows_count,
        matched_rows_pct=round(matched_rows_pct, 2),
    )


def _infer_cardinality(left_non_null: pd.Series, right_non_null: pd.Series) -> str:
    left_unique = left_non_null.is_unique
    right_unique = right_non_null.is_unique

    if left_unique and right_unique:
        return "1:1"
    if left_unique and not right_unique:
        return "1:N"
    if not left_unique and right_unique:
        return "N:1"
    return "N:N"


def _samples_unmatched(
    source_keys: pd.Series,
    target_distinct_keys: set[str],
    max_samples: int,
) -> list[str]:
    source_distinct = source_keys.dropna().astype(str).drop_duplicates()
    unmatched = source_distinct[~source_distinct.isin(target_distinct_keys)]
    return unmatched.head(max_samples).tolist()


def _recommend(
    missing_columns: list[str],
    cardinality_observed: str,
    left_metrics: SideMetrics,
    right_metrics: SideMetrics,
) -> tuple[JoinRecommendation, list[str]]:
    notes: list[str] = []

    if missing_columns:
        notes.append("Há colunas de relacionamento ausentes.")
        return JoinRecommendation.NAO_APTA, notes

    if left_metrics.null_pct > 5 or right_metrics.null_pct > 5:
        notes.append("Percentual de nulos acima de 5% em pelo menos um lado.")

    if left_metrics.matched_rows_pct < 90 or right_metrics.matched_rows_pct < 90:
        notes.append("Cobertura de match abaixo de 90% em pelo menos um lado.")

    if cardinality_observed == "N:N":
        notes.append("Cardinalidade observada N:N pode multiplicar linhas em join.")

    if not notes and cardinality_observed in {"1:1", "1:N", "N:1"}:
        return JoinRecommendation.APTA, ["Cobertura e qualidade das chaves estão adequadas."]

    if left_metrics.matched_rows_pct < 90 or right_metrics.matched_rows_pct < 90:
        return JoinRecommendation.NAO_APTA, notes

    return JoinRecommendation.APTA_COM_RESSALVAS, notes


def validate_relationships(
    frames: DataFramesByAlias,
    schema: SchemaSpec,
    max_unmatched_samples: int = 5,
) -> list[RelationshipValidationResult]:
    """Valida relações conhecidas como hipóteses operacionais."""
    results: list[RelationshipValidationResult] = []

    for rel in schema.relationships:
        if rel.left.table_alias not in frames:
            raise KeyError(f"Tabela ausente no input: {rel.left.table_alias}")
        if rel.right.table_alias not in frames:
            raise KeyError(f"Tabela ausente no input: {rel.right.table_alias}")

        left_df = frames[rel.left.table_alias]
        right_df = frames[rel.right.table_alias]

        missing_columns: list[str] = []
        if rel.left.column not in left_df.columns:
            missing_columns.append(f"{rel.left.table_alias}.{rel.left.column}")
        if rel.right.column not in right_df.columns:
            missing_columns.append(f"{rel.right.table_alias}.{rel.right.column}")

        if missing_columns:
            empty_side = SideMetrics(0, 0, 0.0, 0, 0, 0, 0, 0.0)
            recommendation, notes = _recommend(
                missing_columns=missing_columns,
                cardinality_observed="N/A",
                left_metrics=empty_side,
                right_metrics=empty_side,
            )
            results.append(
                RelationshipValidationResult(
                    relationship_name=rel.name,
                    left_table=rel.left.table_alias,
                    right_table=rel.right.table_alias,
                    left_column=rel.left.column,
                    right_column=rel.right.column,
                    missing_columns=missing_columns,
                    cardinality_observed="N/A",
                    left_metrics=empty_side,
                    right_metrics=empty_side,
                    unmatched_left_samples=[],
                    unmatched_right_samples=[],
                    recommendation=recommendation,
                    notes=notes,
                )
            )
            continue

        left_keys = left_df[rel.left.column]
        right_keys = right_df[rel.right.column]

        left_non_null_str = left_keys.dropna().astype(str)
        right_non_null_str = right_keys.dropna().astype(str)

        left_distinct = set(left_non_null_str.drop_duplicates().tolist())
        right_distinct = set(right_non_null_str.drop_duplicates().tolist())

        left_metrics = _side_metrics(left_keys, right_distinct)
        right_metrics = _side_metrics(right_keys, left_distinct)

        cardinality_observed = _infer_cardinality(left_non_null_str, right_non_null_str)

        unmatched_left_samples = _samples_unmatched(
            source_keys=left_keys,
            target_distinct_keys=right_distinct,
            max_samples=max_unmatched_samples,
        )
        unmatched_right_samples = _samples_unmatched(
            source_keys=right_keys,
            target_distinct_keys=left_distinct,
            max_samples=max_unmatched_samples,
        )

        recommendation, notes = _recommend(
            missing_columns=missing_columns,
            cardinality_observed=cardinality_observed,
            left_metrics=left_metrics,
            right_metrics=right_metrics,
        )

        results.append(
            RelationshipValidationResult(
                relationship_name=rel.name,
                left_table=rel.left.table_alias,
                right_table=rel.right.table_alias,
                left_column=rel.left.column,
                right_column=rel.right.column,
                missing_columns=missing_columns,
                cardinality_observed=cardinality_observed,
                left_metrics=left_metrics,
                right_metrics=right_metrics,
                unmatched_left_samples=unmatched_left_samples,
                unmatched_right_samples=unmatched_right_samples,
                recommendation=recommendation,
                notes=notes,
            )
        )

    return results


def validate_relationship_presence(
    frames: DataFramesByAlias,
    schema: SchemaSpec,
) -> list[RelationshipValidationResult]:
    """Compat: mantém nome antigo delegando para a validação relacional forte."""
    return validate_relationships(frames=frames, schema=schema)
