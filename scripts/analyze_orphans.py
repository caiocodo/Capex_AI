from __future__ import annotations

import argparse
import sys
from pathlib import Path


def _bootstrap_local_src() -> None:
    repo_src = Path(__file__).resolve().parents[1] / "src"
    if str(repo_src) not in sys.path:
        sys.path.insert(0, str(repo_src))


def main() -> None:
    parser = argparse.ArgumentParser(description="Wrapper: análise de registros órfãos.")
    parser.add_argument("excel_path", help="Caminho do arquivo .xlsx")
    parser.add_argument(
        "--schema",
        default="configs/schema.yaml",
        help="Caminho do schema YAML (default: configs/schema.yaml)",
    )
    parser.add_argument("--export-csv", default=None, help="Caminho opcional para exportar CSV")
    args = parser.parse_args()

    _bootstrap_local_src()
    from capex_ai.analysis.runner import run_analysis

    output = run_analysis(
        analysis_id="orphan_records",
        excel_path=Path(args.excel_path),
        schema_path=Path(args.schema),
        params={},
    )

    print("Análise de órfãos concluída.")
    print(f"- Universo analisado: {output.universe_analyzed}")
    print(f"- Filtros aplicados: {output.applied_filters}")
    print(f"- Campos usados: {output.fields_used}")
    print(f"- Limitações de qualidade: {output.data_quality_limitations}")

    if output.dataframe is not None:
        print("\nPrévia (top 10):")
        print(output.dataframe.head(10).to_string(index=False))
        if args.export_csv:
            output.dataframe.to_csv(args.export_csv, index=False)
            print(f"\nCSV exportado em: {args.export_csv}")


if __name__ == "__main__":
    main()
