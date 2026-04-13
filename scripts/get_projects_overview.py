from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd


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


def _format_date(value: object) -> str:
    if pd.isna(value):
        return ""
    return str(value.date())


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Retorna uma tabela de projetos com budget, custo acumulado e datas."
    )
    parser.add_argument("--excel-path", required=True, help="Caminho do arquivo .xlsx")
    parser.add_argument("--ref-date", default=None, help="Data de referência em YYYY-MM-DD")
    parser.add_argument(
        "--schema",
        default="configs/schema.yaml",
        help="Caminho do schema YAML (default: configs/schema.yaml)",
    )
    args = parser.parse_args()

    _bootstrap_local_src()
    from capex_ai.io.excel_loader import load_canonical_workbook_from_schema_file
    from capex_ai.modeling.projects_overview import get_projects_overview
    from capex_ai.models.schema import load_schema

    schema = load_schema(Path(args.schema))
    frames = load_canonical_workbook_from_schema_file(
        excel_path=Path(args.excel_path),
        schema_path=Path(args.schema),
    )
    result = get_projects_overview(
        frames=frames,
        schema=schema,
        ref_date=args.ref_date,
    )

    display = result.copy()
    display["budget_sum"] = display["budget_sum"].map(_format_brl)
    display["cumulative_linecost_sum"] = display["cumulative_linecost_sum"].map(_format_brl)
    display["remaining_budget_pct"] = display["remaining_budget_pct"].map(_format_pct)
    display["targstartdate"] = display["targstartdate"].map(_format_date)
    display["targcompdate"] = display["targcompdate"].map(_format_date)
    display["extendedtargcompdate"] = display["extendedtargcompdate"].map(_format_date)
    print(display.to_string(index=False))


if __name__ == "__main__":
    main()
