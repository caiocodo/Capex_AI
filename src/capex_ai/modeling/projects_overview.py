from __future__ import annotations

from typing import Any

import pandas as pd

from capex_ai.models.schema import SchemaSpec

DataFramesByAlias = dict[str, pd.DataFrame]

_PT_MONTHS = {
    "janeiro": 1,
    "fevereiro": 2,
    "março": 3,
    "marco": 3,
    "abril": 4,
    "maio": 5,
    "junho": 6,
    "julho": 7,
    "agosto": 8,
    "setembro": 9,
    "outubro": 10,
    "novembro": 11,
    "dezembro": 12,
}


def _relation_keys(schema: SchemaSpec, left_table: str, right_table: str) -> tuple[str, str]:
    for rel in schema.relationships:
        if rel.left.table_alias == left_table and rel.right.table_alias == right_table:
            return rel.left.column, rel.right.column
    raise KeyError(f"Relação não encontrada no schema para {left_table} -> {right_table}.")


def _normalize_ref_date(ref_date: Any | None) -> pd.Timestamp:
    if ref_date is None:
        return pd.Timestamp.today().normalize()
    return pd.Timestamp(ref_date).normalize()


def _parse_datetime(series: pd.Series) -> pd.Series:
    parsed = pd.to_datetime(series, errors="coerce", format="mixed")
    missing = parsed.isna() & series.notna()
    if not missing.any():
        return parsed

    parts = (
        series[missing]
        .astype(str)
        .str.lower()
        .str.extract(r"(?P<day>\d{1,2})\s+de\s+(?P<month>[a-zç]+)\s+de\s+(?P<year>\d{4})")
    )
    month = parts["month"].map(_PT_MONTHS)
    reparsed = pd.to_datetime(
        {
            "year": pd.to_numeric(parts["year"], errors="coerce"),
            "month": month,
            "day": pd.to_numeric(parts["day"], errors="coerce"),
        },
        errors="coerce",
    )
    parsed.loc[missing] = reparsed.to_numpy()
    return parsed


def _project_budget_totals(frames: DataFramesByAlias) -> pd.DataFrame:
    wo_df = frames["wo_afes"][["wonum", "WOBUDGET"]].copy()
    wo_df["WOBUDGET"] = pd.to_numeric(wo_df["WOBUDGET"], errors="coerce").fillna(0.0)
    return (
        wo_df.groupby("wonum", dropna=True)["WOBUDGET"]
        .sum()
        .reset_index()
        .rename(columns={"WOBUDGET": "budget_sum"})
    )


def _project_cumulative_costs(
    frames: DataFramesByAlias,
    schema: SchemaSpec,
    ref_date: pd.Timestamp,
) -> pd.DataFrame:
    invoice_df = frames["invoicecost"].copy()
    if "refwo" in invoice_df.columns:
        invoice_df = invoice_df[["refwo", "linecost", "admchangedate"]].copy()
        invoice_df["admchangedate"] = _parse_datetime(invoice_df["admchangedate"])
        invoice_df["linecost"] = pd.to_numeric(invoice_df["linecost"], errors="coerce").fillna(
            0.0
        )
        invoice_df = invoice_df.dropna(subset=["refwo", "admchangedate"])
        invoice_df = invoice_df[invoice_df["admchangedate"] <= ref_date]

        if invoice_df.empty:
            return pd.DataFrame(columns=["wonum", "cumulative_linecost_sum"])

        return (
            invoice_df.groupby("refwo", dropna=True)["linecost"]
            .sum()
            .reset_index()
            .rename(columns={"refwo": "wonum", "linecost": "cumulative_linecost_sum"})
        )

    _invoice_left, invoice_right = _relation_keys(schema, "invoicecost", "multiassetlocci")
    bridge = (
        frames["multiassetlocci"][["recordkey", invoice_right]]
        .dropna()
        .drop_duplicates()
        .copy()
    )

    invoice_df = invoice_df[[invoice_right, "linecost", "admchangedate"]].copy()
    invoice_df["admchangedate"] = _parse_datetime(invoice_df["admchangedate"])
    invoice_df["linecost"] = pd.to_numeric(invoice_df["linecost"], errors="coerce").fillna(0.0)
    invoice_df = invoice_df.dropna(subset=["admchangedate"])
    invoice_df = invoice_df[invoice_df["admchangedate"] <= ref_date]

    if invoice_df.empty:
        return pd.DataFrame(columns=["wonum", "cumulative_linecost_sum"])

    joined = invoice_df.merge(bridge, how="inner", on=invoice_right)
    return (
        joined.groupby("recordkey", dropna=True)["linecost"]
        .sum()
        .reset_index()
        .rename(columns={"recordkey": "wonum", "linecost": "cumulative_linecost_sum"})
    )


def _project_dates_and_status(wo_df: pd.DataFrame, ref_date: pd.Timestamp) -> pd.DataFrame:
    projects = wo_df[
        ["wonum", "TARGSTARTDATE", "TARGCOMPDATE", "EXTENDEDTARGCOMPDATE"]
    ].drop_duplicates(subset=["wonum"]).copy()
    projects = projects.rename(
        columns={
            "TARGSTARTDATE": "targstartdate",
            "TARGCOMPDATE": "targcompdate",
            "EXTENDEDTARGCOMPDATE": "extendedtargcompdate",
        }
    )

    for col in ("targstartdate", "targcompdate", "extendedtargcompdate"):
        projects[col] = pd.to_datetime(projects[col], errors="coerce")

    end_ref = projects["extendedtargcompdate"].combine_first(projects["targcompdate"])
    window_start = ref_date - pd.Timedelta(days=14)
    projects["status"] = "Fora da janela"
    in_progress = end_ref.notna() & (end_ref >= window_start) & (end_ref <= ref_date)
    projects.loc[in_progress, "status"] = "Em andamento"
    return projects


def get_projects_overview(
    frames: DataFramesByAlias,
    schema: SchemaSpec,
    ref_date: Any | None = None,
) -> pd.DataFrame:
    normalized_ref_date = _normalize_ref_date(ref_date)

    projects = _project_dates_and_status(frames["wo_afes"], normalized_ref_date)
    budget_totals = _project_budget_totals(frames=frames)
    cost_totals = _project_cumulative_costs(
        frames=frames,
        schema=schema,
        ref_date=normalized_ref_date,
    )

    result = projects.merge(budget_totals, how="left", on="wonum")
    result = result.merge(cost_totals, how="left", on="wonum")
    result["budget_sum"] = pd.to_numeric(result["budget_sum"], errors="coerce").fillna(0.0)
    result["cumulative_linecost_sum"] = pd.to_numeric(
        result["cumulative_linecost_sum"], errors="coerce"
    ).fillna(0.0)
    result["remaining_budget_pct"] = pd.NA

    non_zero_budget = result["budget_sum"] != 0
    result.loc[non_zero_budget, "remaining_budget_pct"] = (
        (
            result.loc[non_zero_budget, "budget_sum"]
            - result.loc[non_zero_budget, "cumulative_linecost_sum"]
        )
        / result.loc[non_zero_budget, "budget_sum"]
    ) * 100

    result = result[
        ~((result["budget_sum"] == 0) & (result["cumulative_linecost_sum"] == 0))
    ].copy()

    return result.sort_values(
        ["budget_sum", "cumulative_linecost_sum", "wonum"],
        ascending=[False, False, True],
    ).reset_index(drop=True)[
        [
            "wonum",
            "budget_sum",
            "cumulative_linecost_sum",
            "remaining_budget_pct",
            "targstartdate",
            "targcompdate",
            "extendedtargcompdate",
            "status",
        ]
    ]
