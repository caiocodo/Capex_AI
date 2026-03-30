from __future__ import annotations

import argparse
from pathlib import Path

from capex_ai.analysis.orphan_records import analyze_orphan_records
from capex_ai.io.excel_loader import load_canonical_workbook_from_schema_file
from capex_ai.models.schema import load_schema
from capex_ai.validation.relations import validate_relationships


def main() -> None:
    parser = argparse.ArgumentParser(description="Análise de registros órfãos/não conciliados.")
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

    result = analyze_orphan_records(
        frames=frames,
        schema=schema,
        relation_results=relation_results,
    )

    print("Análise de órfãos concluída.")
    print(f"- Universo analisado: {result.universe_analyzed}")
    print(f"- Filtros aplicados: {result.applied_filters}")
    print(f"- Campos usados: {result.fields_used}")
    print(f"- Limitações de qualidade: {result.data_quality_limitations}")

    rows: list[dict[str, object]] = []
    for item in result.relation_reports:
        print(f"\n[Relação] {item.relationship_name}")
        print(
            f"- Não conciliados: esquerda={item.unmatched_left_count}, "
            f"direita={item.unmatched_right_count}"
        )
        print(f"- Amostras esquerda: {item.unmatched_left_samples}")
        print(f"- Amostras direita: {item.unmatched_right_samples}")
        print(f"- Recomendação: {item.recommendation}")

        rows.append(
            {
                "relationship_name": item.relationship_name,
                "left_table": item.left_table,
                "right_table": item.right_table,
                "left_column": item.left_column,
                "right_column": item.right_column,
                "unmatched_left_count": item.unmatched_left_count,
                "unmatched_right_count": item.unmatched_right_count,
                "recommendation": item.recommendation,
            }
        )

    if args.export_csv:
        import pandas as pd

        pd.DataFrame(rows).to_csv(args.export_csv, index=False)
        print(f"\nCSV exportado em: {args.export_csv}")


if __name__ == "__main__":
    main()
