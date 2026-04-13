from __future__ import annotations

import argparse
import sys
from pathlib import Path


def _bootstrap_local_src() -> None:
    repo_src = Path(__file__).resolve().parents[1] / "src"
    if str(repo_src) not in sys.path:
        sys.path.insert(0, str(repo_src))


def _format_brl(value: object) -> str:
    numeric = float(value)
    formatted = f"{numeric:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {formatted}"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Retorna a visão semanal das 4 últimas semanas por budgetcode para um wonum."
    )
    parser.add_argument("--wonum", required=True, help="WONUM a consultar")
    parser.add_argument("--excel-path", required=True, help="Caminho do arquivo .xlsx")
    parser.add_argument(
        "--schema",
        default="configs/schema.yaml",
        help="Caminho do schema YAML (default: configs/schema.yaml)",
    )
    args = parser.parse_args()

    _bootstrap_local_src()
    from capex_ai.io.excel_loader import load_canonical_workbook_from_schema_file
    from capex_ai.modeling.budget_views import get_weekly_budget_view
    from capex_ai.models.schema import load_schema

    schema = load_schema(Path(args.schema))
    frames = load_canonical_workbook_from_schema_file(
        excel_path=Path(args.excel_path),
        schema_path=Path(args.schema),
    )
    result = get_weekly_budget_view(
        frames=frames,
        schema=schema,
        wonum=args.wonum,
    )

    if result.empty:
        print(f"Nenhuma visão semanal encontrada para wonum '{args.wonum}'.")
        raise SystemExit(1)

    for idx, (ref_date, block) in enumerate(result.groupby("ref_date", sort=False)):
        if idx > 0:
            print()
        display = block.copy()
        display["budget_sum"] = display["budget_sum"].map(_format_brl)
        display["linecost_sum"] = display["linecost_sum"].map(_format_brl)
        print(f"[ref_date] {ref_date.date()}")
        print(display.to_string(index=False))


if __name__ == "__main__":
    main()
