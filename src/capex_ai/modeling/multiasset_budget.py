from __future__ import annotations

import pandas as pd

from capex_ai.models.schema import SchemaSpec

DataFramesByAlias = dict[str, pd.DataFrame]


def _relation_keys(schema: SchemaSpec) -> tuple[str, str]:
    for rel in schema.relationships:
        if rel.left.table_alias == "wo_afes" and rel.right.table_alias == "multiassetlocci":
            return rel.left.column, rel.right.column
    raise KeyError("Relação não encontrada no schema para wo_afes -> multiassetlocci.")


def get_multiasset_budget_by_wonum(
    frames: DataFramesByAlias,
    schema: SchemaSpec,
    wonum: str,
) -> pd.DataFrame:
    left_key, right_key = _relation_keys(schema)

    wo_df = frames["wo_afes"][[left_key]].dropna().drop_duplicates().copy()
    multi_df = frames["multiassetlocci"][[right_key, "budget", "budgetcode"]].copy()

    joined = wo_df.merge(
        multi_df,
        how="inner",
        left_on=left_key,
        right_on=right_key,
    )

    result = joined.loc[joined[left_key].astype(str) == str(wonum), ["budget", "budgetcode"]]
    return result.reset_index(drop=True)
