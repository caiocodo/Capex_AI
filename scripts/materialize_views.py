from __future__ import annotations

import argparse
from pathlib import Path

from capex_ai.io.excel_loader import load_canonical_workbook_from_schema_file
from capex_ai.modeling.join_engine import materialize_base_views
from capex_ai.models.schema import load_schema
from capex_ai.validation.relations import validate_relationships


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Materializa visões base por joins com rastreabilidade."
    )
    parser.add_argument("excel_path", help="Caminho do arquivo .xlsx")
    parser.add_argument(
        "--schema",
        default="configs/schema.yaml",
        help="Caminho do schema YAML (default: configs/schema.yaml)",
    )
    args = parser.parse_args()

    schema = load_schema(Path(args.schema))
    frames = load_canonical_workbook_from_schema_file(
        excel_path=Path(args.excel_path),
        schema_path=Path(args.schema),
    )
    relation_results = validate_relationships(frames=frames, schema=schema)

    views = materialize_base_views(
        frames=frames,
        schema=schema,
        relation_results=relation_results,
    )

    print("Materialização concluída.")
    for view_name, join_result in views.items():
        trace = join_result.trace
        print(f"\n[View] {view_name}")
        print(
            f"- Join final: {trace.left_table}.{trace.left_on} "
            f"{trace.join_type} {trace.right_table}.{trace.right_on}"
        )
        print(
            f"- Linhas: esquerda={trace.rows_before_left}, direita={trace.rows_before_right}, "
            f"resultado={trace.rows_after}"
        )
        print(
            f"- Não casadas: esquerda={trace.unmatched_left_count}, "
            f"direita={trace.unmatched_right_count}"
        )
        if trace.warnings:
            print(f"- Warnings: {trace.warnings}")


if __name__ == "__main__":
    main()
