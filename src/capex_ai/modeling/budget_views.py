from __future__ import annotations

import pandas as pd

from capex_ai.models.schema import SchemaSpec

DataFramesByAlias = dict[str, pd.DataFrame]


def _relation_keys(schema: SchemaSpec, left_table: str, right_table: str) -> tuple[str, str]:
    for rel in schema.relationships:
        if rel.left.table_alias == left_table and rel.right.table_alias == right_table:
            return rel.left.column, rel.right.column
    raise KeyError(f"Relação não encontrada no schema para {left_table} -> {right_table}.")


def _empty_budget_by_budgetcode() -> pd.DataFrame:
    return pd.DataFrame(columns=["budgetcode", "budget_sum"])


def _empty_weekly_budget_view() -> pd.DataFrame:
    return pd.DataFrame(
        columns=[
            "ref_date",
            "budgetcode",
            "budget_sum",
            "linecost_sum",
            "remaining_budget_pct",
            "remaining_budget_pct_delta_vs_prev_week",
        ]
    )


def _sort_budgetcode(frame: pd.DataFrame, *, ascending: bool) -> pd.DataFrame:
    sorted_frame = frame.copy()
    sorted_frame["_budgetcode_num"] = pd.to_numeric(sorted_frame["budgetcode"], errors="coerce")
    sorted_frame["_budgetcode_text"] = sorted_frame["budgetcode"].astype(str)
    sorted_frame = sorted_frame.sort_values(
        ["_budgetcode_num", "_budgetcode_text"],
        ascending=[ascending, ascending],
        na_position="last",
    )
    return sorted_frame.drop(columns=["_budgetcode_num", "_budgetcode_text"])


def _multiasset_rows_for_wonum(
    frames: DataFramesByAlias,
    schema: SchemaSpec,
    wonum: str,
) -> pd.DataFrame:
    left_key, right_key = _relation_keys(schema, "wo_afes", "multiassetlocci")
    wo_df = frames["wo_afes"][[left_key]].dropna().drop_duplicates().copy()
    multi_df = frames["multiassetlocci"].copy()

    joined = wo_df.merge(
        multi_df,
        how="inner",
        left_on=left_key,
        right_on=right_key,
    )
    return joined.loc[joined[left_key].astype(str) == str(wonum)].reset_index(drop=True)


def get_budget_by_budgetcode(
    frames: DataFramesByAlias,
    schema: SchemaSpec,
    wonum: str,
) -> pd.DataFrame:
    rows = _multiasset_rows_for_wonum(frames=frames, schema=schema, wonum=wonum)
    if rows.empty:
        return _empty_budget_by_budgetcode()

    budget_rows = rows[["budgetcode", "budget"]].dropna(subset=["budgetcode"]).copy()
    if budget_rows.empty:
        return _empty_budget_by_budgetcode()

    budget_rows["budget"] = pd.to_numeric(budget_rows["budget"], errors="coerce").fillna(0.0)
    return (
        budget_rows.groupby("budgetcode", dropna=True)["budget"]
        .sum()
        .reset_index()
        .rename(columns={"budget": "budget_sum"})
        .pipe(_sort_budgetcode, ascending=True)
        .reset_index(drop=True)
    )


def get_weekly_budget_view(
    frames: DataFramesByAlias,
    schema: SchemaSpec,
    wonum: str,
) -> pd.DataFrame:
    budget_by_code = get_budget_by_budgetcode(frames=frames, schema=schema, wonum=wonum)
    if budget_by_code.empty:
        return _empty_weekly_budget_view()

    multi_rows = _multiasset_rows_for_wonum(frames=frames, schema=schema, wonum=wonum)
    multi_for_invoice = (
        multi_rows[["CHAVE_WO_CODE", "budgetcode"]].dropna().drop_duplicates().copy()
    )
    if multi_for_invoice.empty:
        return _empty_weekly_budget_view()

    _invoice_left, invoice_right = _relation_keys(schema, "invoicecost", "multiassetlocci")
    invoice_df = frames["invoicecost"][[invoice_right, "linecost", "admchangedate"]].copy()
    invoice_df["admchangedate"] = pd.to_datetime(invoice_df["admchangedate"], errors="coerce")
    invoice_df["linecost"] = pd.to_numeric(invoice_df["linecost"], errors="coerce").fillna(0.0)
    invoice_df = invoice_df.dropna(subset=["admchangedate"])
    if invoice_df.empty:
        return _empty_weekly_budget_view()

    merged = multi_for_invoice.merge(invoice_df, how="inner", on="CHAVE_WO_CODE")
    if merged.empty:
        return _empty_weekly_budget_view()

    merged["ref_date"] = merged["admchangedate"].dt.to_period("W-SUN").dt.end_time.dt.normalize()
    weekly = (
        merged.groupby(["ref_date", "budgetcode"], dropna=True)["linecost"]
        .sum()
        .reset_index()
        .rename(columns={"linecost": "weekly_linecost"})
    )

    weekly = weekly.sort_values(["budgetcode", "ref_date"], ascending=[True, True]).reset_index(
        drop=True
    )
    all_ref_dates = weekly["ref_date"].drop_duplicates().sort_values(ascending=True).tolist()
    last_4_ref_dates = list(reversed(all_ref_dates[-4:]))
    if not last_4_ref_dates:
        return _empty_weekly_budget_view()

    budgetcodes = budget_by_code[["budgetcode"]].drop_duplicates().copy()
    all_ref_dates_df = pd.DataFrame({"ref_date": all_ref_dates})
    full_grid = all_ref_dates_df.merge(budgetcodes, how="cross")

    result = full_grid.merge(weekly, how="left", on=["ref_date", "budgetcode"])
    result["weekly_linecost"] = pd.to_numeric(
        result["weekly_linecost"], errors="coerce"
    ).fillna(0.0)
    result = result.sort_values(["budgetcode", "ref_date"], ascending=[True, True]).reset_index(
        drop=True
    )
    result["linecost_sum"] = result.groupby("budgetcode")["weekly_linecost"].cumsum()
    result = result.merge(budget_by_code, how="left", on="budgetcode")
    result["budget_sum"] = pd.to_numeric(result["budget_sum"], errors="coerce").fillna(0.0)
    result["remaining_budget_pct"] = pd.NA

    non_zero_budget = result["budget_sum"] != 0
    result.loc[non_zero_budget, "remaining_budget_pct"] = (
        (result.loc[non_zero_budget, "budget_sum"] - result.loc[non_zero_budget, "linecost_sum"])
        / result.loc[non_zero_budget, "budget_sum"]
    ) * 100

    result = result.sort_values(["budgetcode", "ref_date"], ascending=[True, True]).reset_index(
        drop=True
    )
    result["remaining_budget_pct_delta_vs_prev_week"] = result.groupby("budgetcode")[
        "remaining_budget_pct"
    ].diff()
    first_occurrence = result.groupby("budgetcode").cumcount() == 0
    result.loc[first_occurrence, "remaining_budget_pct_delta_vs_prev_week"] = "Primeira ocorrência"

    result = result[result["ref_date"].isin(last_4_ref_dates)].copy()
    result = result[~((result["budget_sum"] == 0) & (result["linecost_sum"] == 0))].copy()
    result["remaining_budget_pct_delta_vs_prev_week"] = result[
        "remaining_budget_pct_delta_vs_prev_week"
    ].where(
        ~result["remaining_budget_pct_delta_vs_prev_week"].isna(),
        "Primeira ocorrência",
    )

    result = result.sort_values(
        ["ref_date", "budgetcode"],
        ascending=[False, True],
        kind="stable",
    ).reset_index(drop=True)
    return result[
        [
            "ref_date",
            "budgetcode",
            "budget_sum",
            "linecost_sum",
            "remaining_budget_pct",
            "remaining_budget_pct_delta_vs_prev_week",
        ]
    ]
