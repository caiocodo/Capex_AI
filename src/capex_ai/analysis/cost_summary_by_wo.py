from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from capex_ai.models.schema import SchemaSpec
from capex_ai.validation.relations import RelationshipValidationResult, validate_relationships

DataFramesByAlias = dict[str, pd.DataFrame]

ADMA_COST_FIELDS = [
    "afeenteredinv",
    "afeopencommitment",
    "afespend",
    "afeuncommitted",
    "afewapprpo",
]


@dataclass(frozen=True)
class CostSummaryByWOResult:
    universe_analyzed: dict[str, int]
    applied_filters: str
    data_quality_limitations: list[str]
    fields_used: list[str]
    ambiguity_notes: list[str]
    dataframe: pd.DataFrame


def _numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce").fillna(0.0)


def _relation_notes(
    relation_results: list[RelationshipValidationResult],
    relation_names: list[str],
) -> list[str]:
    by_name = {item.relationship_name: item for item in relation_results}
    notes: list[str] = []
    for name in relation_names:
        item = by_name.get(name)
        if item is None:
            notes.append(f"Sem validação relacional disponível para: {name}.")
            continue
        if item.recommendation.value != "apta para join":
            notes.append(f"Relação '{name}' com recomendação: {item.recommendation.value}.")
        notes.extend(item.notes)
    return sorted(set(notes))


def summarize_costs_by_wo(
    frames: DataFramesByAlias,
    schema: SchemaSpec,
    relation_results: list[RelationshipValidationResult] | None = None,
) -> CostSummaryByWOResult:
    """Resumo conservador de custos por WO usando apenas campos explicitamente documentados."""
    if relation_results is None:
        relation_results = validate_relationships(frames=frames, schema=schema)

    wo_df = frames["wo_afes"].copy()
    wo_universe = wo_df[["wonum"]].dropna().drop_duplicates()

    adma_df = frames["admafecost"].copy()
    adma_available = [col for col in ADMA_COST_FIELDS if col in adma_df.columns]
    adma_grouped = pd.DataFrame(columns=["wonum"])
    if adma_available:
        adma_numeric = adma_df[["wonum", *adma_available]].copy()
        for col in adma_available:
            adma_numeric[col] = _numeric(adma_numeric[col])
        adma_grouped = (
            adma_numeric.groupby("wonum", dropna=True)[adma_available].sum().reset_index()
        )

    inv_afe_df = frames["inv_afe"].copy()
    inv_afe_grouped = pd.DataFrame(columns=["wonum", "inv_afe_linecost_total"])
    if "linecost" in inv_afe_df.columns and "refwo" in inv_afe_df.columns:
        inv_afe_tmp = inv_afe_df[["refwo", "linecost"]].copy()
        inv_afe_tmp["linecost"] = _numeric(inv_afe_tmp["linecost"])
        inv_afe_grouped = (
            inv_afe_tmp.groupby("refwo", dropna=True)["linecost"].sum().reset_index().rename(
                columns={"refwo": "wonum", "linecost": "inv_afe_linecost_total"}
            )
        )

    invoicecost_df = frames["invoicecost"].copy()
    multi_df = frames["multiassetlocci"].copy()
    invoicecost_grouped = pd.DataFrame(columns=["wonum", "invoicecost_linecost_total"])
    if (
        "CHAVE_WO_CODE" in invoicecost_df.columns
        and "linecost" in invoicecost_df.columns
        and "CHAVE_WO_CODE" in multi_df.columns
        and "recordkey" in multi_df.columns
    ):
        inv_tmp = invoicecost_df[["CHAVE_WO_CODE", "linecost"]].copy()
        inv_tmp["linecost"] = _numeric(inv_tmp["linecost"])
        bridge = multi_df[["CHAVE_WO_CODE", "recordkey"]].dropna()
        inv_to_wo = inv_tmp.merge(bridge, how="left", on="CHAVE_WO_CODE")
        invoicecost_grouped = (
            inv_to_wo.groupby("recordkey", dropna=True)["linecost"].sum().reset_index().rename(
                columns={"recordkey": "wonum", "linecost": "invoicecost_linecost_total"}
            )
        )

    summary = wo_universe.merge(adma_grouped, on="wonum", how="left")
    summary = summary.merge(inv_afe_grouped, on="wonum", how="left")
    summary = summary.merge(invoicecost_grouped, on="wonum", how="left")

    monetary_cols = [col for col in summary.columns if col != "wonum"]
    for col in monetary_cols:
        summary[col] = _numeric(summary[col])

    quality_notes = _relation_notes(
        relation_results,
        relation_names=[
            "wo_afes_to_admafecost_by_wonum",
            "wo_afes_to_inv_afe_by_wonum_refwo",
            "wo_afes_to_multiassetlocci_by_wonum_recordkey",
            "invoicecost_to_multiassetlocci_by_chave_wo_code",
        ],
    )

    ambiguity_notes = [
        (
            "Resumo conservador usa somente linecost (INV-AFE, INVOICECOST) "
            "e campos AFE explícitos do ADMAFECOST."
        ),
        (
            "Campos monetários alternativos (ex.: unitcost, quantity, internalcosts) "
            "não foram inferidos como custo final."
        ),
    ]

    fields_used = [
        "wo_afes.wonum",
        "admafecost.wonum",
        "admafecost.afeenteredinv",
        "admafecost.afeopencommitment",
        "admafecost.afespend",
        "admafecost.afeuncommitted",
        "admafecost.afewapprpo",
        "inv_afe.refwo",
        "inv_afe.linecost",
        "invoicecost.CHAVE_WO_CODE",
        "invoicecost.linecost",
        "multiassetlocci.CHAVE_WO_CODE",
        "multiassetlocci.recordkey",
    ]

    return CostSummaryByWOResult(
        universe_analyzed={
            "wo_afes_rows": len(wo_df),
            "wo_universe_distinct": len(wo_universe),
            "admafecost_rows": len(adma_df),
            "inv_afe_rows": len(inv_afe_df),
            "invoicecost_rows": len(invoicecost_df),
            "multiassetlocci_rows": len(multi_df),
        },
        applied_filters="sem filtros",
        data_quality_limitations=quality_notes,
        fields_used=fields_used,
        ambiguity_notes=ambiguity_notes,
        dataframe=summary.sort_values("wonum").reset_index(drop=True),
    )
