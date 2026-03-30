from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from capex_ai.models.schema import SchemaSpec
from capex_ai.validation.relations import JoinRecommendation, RelationshipValidationResult

DataFramesByAlias = dict[str, pd.DataFrame]


@dataclass(frozen=True)
class JoinTrace:
    relation_name: str
    left_table: str
    right_table: str
    left_on: str
    right_on: str
    join_type: str
    rows_before_left: int
    rows_before_right: int
    rows_after: int
    unmatched_left_count: int
    unmatched_right_count: int
    warnings: list[str]


@dataclass(frozen=True)
class JoinResult:
    dataframe: pd.DataFrame
    trace: JoinTrace


def _find_relation(schema: SchemaSpec, left_table: str, right_table: str) -> tuple[str, str, str]:
    for rel in schema.relationships:
        if rel.left.table_alias == left_table and rel.right.table_alias == right_table:
            return rel.name, rel.left.column, rel.right.column
    raise KeyError(
        f"Relação não encontrada no schema para {left_table} -> {right_table}."
    )


def _relation_warning(relation_result: RelationshipValidationResult | None) -> list[str]:
    if relation_result is None:
        return ["Sem resultado de validação relacional para esta relação."]

    if relation_result.recommendation == JoinRecommendation.APTA:
        return []

    return [
        "Qualidade da relação pode comprometer o join: "
        f"{relation_result.recommendation.value}."
    ] + relation_result.notes


def execute_join(
    left_df: pd.DataFrame,
    right_df: pd.DataFrame,
    *,
    left_table: str,
    right_table: str,
    left_on: str,
    right_on: str,
    join_type: str,
    relation_name: str,
    relation_result: RelationshipValidationResult | None = None,
) -> JoinResult:
    """Executa join rastreável com suporte a left, inner e anti."""
    if join_type not in {"left", "inner", "anti"}:
        raise ValueError("join_type inválido. Use: left, inner ou anti.")

    if left_on not in left_df.columns:
        raise KeyError(f"Coluna ausente em {left_table}: {left_on}")
    if right_on not in right_df.columns:
        raise KeyError(f"Coluna ausente em {right_table}: {right_on}")

    rows_before_left = len(left_df)
    rows_before_right = len(right_df)

    left_keys = left_df[left_on].dropna().astype(str)
    right_keys = right_df[right_on].dropna().astype(str)

    right_distinct = set(right_keys.drop_duplicates().tolist())
    left_distinct = set(left_keys.drop_duplicates().tolist())

    unmatched_left_count = int((~left_keys.isin(right_distinct)).sum())
    unmatched_right_count = int((~right_keys.isin(left_distinct)).sum())

    warnings = _relation_warning(relation_result)
    if unmatched_left_count > 0:
        warnings.append(f"{unmatched_left_count} linhas da esquerda sem match no lado direito.")
    if join_type == "inner" and unmatched_left_count > 0:
        warnings.append("Join inner descartará linhas não casadas do lado esquerdo.")
    if join_type == "anti" and unmatched_left_count == 0:
        warnings.append("Join anti retornou conjunto vazio para não casados na esquerda.")

    if join_type == "anti":
        merged = left_df.merge(
            right_df[[right_on]].drop_duplicates(),
            how="left",
            left_on=left_on,
            right_on=right_on,
            indicator=True,
        )
        out = merged.loc[merged["_merge"] == "left_only", left_df.columns].copy()
    else:
        out = left_df.merge(
            right_df,
            how=join_type,
            left_on=left_on,
            right_on=right_on,
            suffixes=("", f"__{right_table}"),
        )

    trace = JoinTrace(
        relation_name=relation_name,
        left_table=left_table,
        right_table=right_table,
        left_on=left_on,
        right_on=right_on,
        join_type=join_type,
        rows_before_left=rows_before_left,
        rows_before_right=rows_before_right,
        rows_after=len(out),
        unmatched_left_count=unmatched_left_count,
        unmatched_right_count=unmatched_right_count,
        warnings=warnings,
    )
    return JoinResult(dataframe=out, trace=trace)


def _index_relation_results(
    relation_results: list[RelationshipValidationResult] | None,
) -> dict[str, RelationshipValidationResult]:
    if not relation_results:
        return {}
    return {r.relationship_name: r for r in relation_results}


def materialize_base_views(
    frames: DataFramesByAlias,
    schema: SchemaSpec,
    relation_results: list[RelationshipValidationResult] | None = None,
) -> dict[str, JoinResult]:
    """Materializa visões base sem regra de negócio, usando relações explícitas do schema."""
    relation_by_name = _index_relation_results(relation_results)

    views: dict[str, JoinResult] = {}

    # Visão 1: consolidada por WO (WO + ADMAFECOST + INV_AFE + MULTIASSETLOCCI)
    rel_name, left_key, right_key = _find_relation(schema, "wo_afes", "admafecost")
    step1 = execute_join(
        frames["wo_afes"],
        frames["admafecost"],
        left_table="wo_afes",
        right_table="admafecost",
        left_on=left_key,
        right_on=right_key,
        join_type="left",
        relation_name=rel_name,
        relation_result=relation_by_name.get(rel_name),
    )

    rel_name, left_key, right_key = _find_relation(schema, "wo_afes", "inv_afe")
    step2 = execute_join(
        step1.dataframe,
        frames["inv_afe"],
        left_table="wo_afes",
        right_table="inv_afe",
        left_on=left_key,
        right_on=right_key,
        join_type="left",
        relation_name=rel_name,
        relation_result=relation_by_name.get(rel_name),
    )

    rel_name, left_key, right_key = _find_relation(schema, "wo_afes", "multiassetlocci")
    step3 = execute_join(
        step2.dataframe,
        frames["multiassetlocci"],
        left_table="wo_afes",
        right_table="multiassetlocci",
        left_on=left_key,
        right_on=right_key,
        join_type="left",
        relation_name=rel_name,
        relation_result=relation_by_name.get(rel_name),
    )

    views["wo_consolidated"] = step3

    # Visão 2: custos/invoices ligados a WO
    rel_name, left_key, right_key = _find_relation(schema, "invoicecost", "multiassetlocci")
    cost_step1 = execute_join(
        frames["invoicecost"],
        frames["multiassetlocci"],
        left_table="invoicecost",
        right_table="multiassetlocci",
        left_on=left_key,
        right_on=right_key,
        join_type="left",
        relation_name=rel_name,
        relation_result=relation_by_name.get(rel_name),
    )

    rel_name, left_key, right_key = _find_relation(schema, "wo_afes", "multiassetlocci")
    cost_step2 = execute_join(
        cost_step1.dataframe,
        frames["wo_afes"],
        left_table="multiassetlocci",
        right_table="wo_afes",
        left_on=right_key,
        right_on=left_key,
        join_type="left",
        relation_name=rel_name,
        relation_result=relation_by_name.get(rel_name),
    )

    views["wo_costs_invoices"] = cost_step2

    return views
