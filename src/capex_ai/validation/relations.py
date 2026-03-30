from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from capex_ai.models.schema import SchemaSpec


@dataclass(frozen=True)
class RelationshipValidationResult:
    relationship_name: str
    left_table: str
    right_table: str
    left_column: str
    right_column: str
    left_missing_count: int
    right_missing_count: int


DataFramesByAlias = dict[str, pd.DataFrame]


def validate_relationship_presence(
    frames: DataFramesByAlias,
    schema: SchemaSpec,
) -> list[RelationshipValidationResult]:
    """Validação estrutural mínima: presença de colunas e nulos em chaves de relacionamento."""
    results: list[RelationshipValidationResult] = []

    for rel in schema.relationships:
        left_df = frames[rel.left.table_alias]
        right_df = frames[rel.right.table_alias]

        if rel.left.column not in left_df.columns:
            raise KeyError(
                f"Coluna ausente no lado esquerdo: {rel.left.table_alias}.{rel.left.column}"
            )
        if rel.right.column not in right_df.columns:
            raise KeyError(
                f"Coluna ausente no lado direito: {rel.right.table_alias}.{rel.right.column}"
            )

        left_missing = int(left_df[rel.left.column].isna().sum())
        right_missing = int(right_df[rel.right.column].isna().sum())

        results.append(
            RelationshipValidationResult(
                relationship_name=rel.name,
                left_table=rel.left.table_alias,
                right_table=rel.right.table_alias,
                left_column=rel.left.column,
                right_column=rel.right.column,
                left_missing_count=left_missing,
                right_missing_count=right_missing,
            )
        )

    return results
