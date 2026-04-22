from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

DEFAULT_EXCEL_PATH = Path("tests/fixtures/Capex AI - Dados.xlsx")
DEFAULT_REF_DATE = "2026-03-02"
DEFAULT_SCHEMA_PATH = Path("configs/schema.yaml")


def _bootstrap_local_src() -> None:
    repo_src = Path(__file__).resolve().parents[1] / "src"
    if str(repo_src) not in sys.path:
        sys.path.insert(0, str(repo_src))


def _format_brl(value: object) -> str:
    numeric = float(value)
    formatted = f"{numeric:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {formatted}"


def _format_pct(value: object) -> str:
    if pd.isna(value):
        return "N/A"
    return f"{float(value):.2f}%"


def _format_datetime(value: object) -> str:
    if pd.isna(value):
        return ""
    return pd.Timestamp(value).strftime("%Y-%m-%d %H:%M")


def _select_projects_table(overview: pd.DataFrame, choice: str) -> pd.DataFrame:
    if choice not in {"1", "2"}:
        raise ValueError("Opcao invalida. Escolha 1 ou 2.")

    sorted_overview = _top_projects_by_linecost_then_budget(overview=overview)

    if choice == "1":
        budget_columns = [
            col
            for col in (
                "wonum",
                "budget_sum",
                "cumulative_linecost_sum",
                "remaining_budget_pct",
            )
            if col in sorted_overview.columns
        ]
        return sorted_overview[budget_columns]

    return sorted_overview


def _top_projects_by_linecost_then_budget(overview: pd.DataFrame) -> pd.DataFrame:
    return (
        overview.sort_values(
            ["cumulative_linecost_sum", "budget_sum", "wonum"],
            ascending=[False, False, True],
        )
        .head(10)
        .reset_index(drop=True)
    )


def _format_projects_table(result: pd.DataFrame) -> str:
    display = result.copy()
    display["budget_sum"] = display["budget_sum"].map(_format_brl)
    display["cumulative_linecost_sum"] = display["cumulative_linecost_sum"].map(_format_brl)
    display["remaining_budget_pct"] = display["remaining_budget_pct"].map(_format_pct)
    for col in ("targstartdate", "targcompdate", "extendedtargcompdate"):
        if col in display.columns:
            display[col] = display[col].map(_format_datetime)
    return display.to_string(index=False)


def _prompt_choice() -> str:
    print("Qual funcao voce deseja rodar?")
    print("1 - Top 10 budget por projeto")
    print("2 - Top 10 projetos por linecost, depois budget")
    return input("Digite 1 ou 2: ").strip()


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Chatbot de terminal para escolher uma analise Capex."
    )
    parser.add_argument(
        "--excel-path",
        default=str(DEFAULT_EXCEL_PATH),
        help=f"Caminho do arquivo .xlsx (default: {DEFAULT_EXCEL_PATH})",
    )
    parser.add_argument(
        "--ref-date",
        default=DEFAULT_REF_DATE,
        help=f"Data de referencia em YYYY-MM-DD (default: {DEFAULT_REF_DATE})",
    )
    parser.add_argument(
        "--schema",
        default=str(DEFAULT_SCHEMA_PATH),
        help=f"Caminho do schema YAML (default: {DEFAULT_SCHEMA_PATH})",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    choice = _prompt_choice()

    _bootstrap_local_src()
    from capex_ai.io.excel_loader import load_canonical_workbook_from_schema_file
    from capex_ai.modeling.projects_overview import get_projects_overview
    from capex_ai.models.schema import load_schema

    schema_path = Path(args.schema)
    schema = load_schema(schema_path)
    frames = load_canonical_workbook_from_schema_file(
        excel_path=Path(args.excel_path),
        schema_path=schema_path,
    )
    overview = get_projects_overview(
        frames=frames,
        schema=schema,
        ref_date=args.ref_date,
    )

    try:
        result = _select_projects_table(overview=overview, choice=choice)
    except ValueError as exc:
        print(str(exc))
        raise SystemExit(2) from exc

    print(_format_projects_table(result))


if __name__ == "__main__":
    main()
