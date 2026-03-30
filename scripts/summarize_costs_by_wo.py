from __future__ import annotations

import argparse
from pathlib import Path

from capex_ai.analysis.cost_summary_by_wo import summarize_costs_by_wo
from capex_ai.io.excel_loader import load_canonical_workbook_from_schema_file
from capex_ai.models.schema import load_schema
from capex_ai.validation.relations import validate_relationships


def main() -> None:
    parser = argparse.ArgumentParser(description="Resumo conservador de custos por WO.")
    parser.add_argument("excel_path", help="Caminho do arquivo .xlsx")
    parser.add_argument(
        "--schema",
        default="configs/schema.yaml",
        help="Caminho do schema YAML (default: configs/schema.yaml)",
    )
    parser.add_argument("--export-csv", default=None, help="Caminho opcional para exportar CSV")
    args = parser.parse_args()

    schema = load_schema(Path(args.schema))
    frames = load_canonical_workbook_from_schema_file(
        excel_path=Path(args.excel_path),
        schema_path=Path(args.schema),
    )
    relation_results = validate_relationships(frames=frames, schema=schema)

    result = summarize_costs_by_wo(
        frames=frames,
        schema=schema,
        relation_results=relation_results,
    )

    print("Resumo de custos por WO concluído.")
    print(f"- Universo analisado: {result.universe_analyzed}")
    print(f"- Filtros aplicados: {result.applied_filters}")
    print(f"- Campos usados: {result.fields_used}")
    print(f"- Limitações de qualidade: {result.data_quality_limitations}")
    print(f"- Ambiguidades assumidas: {result.ambiguity_notes}")

    print("\nPrévia (top 10):")
    print(result.dataframe.head(10).to_string(index=False))

    if args.export_csv:
        result.dataframe.to_csv(args.export_csv, index=False)
        print(f"\nCSV exportado em: {args.export_csv}")


if __name__ == "__main__":
    main()
