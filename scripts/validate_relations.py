from __future__ import annotations

import argparse
import sys
from pathlib import Path


def _bootstrap_local_src() -> None:
    repo_src = Path(__file__).resolve().parents[1] / "src"
    if str(repo_src) not in sys.path:
        sys.path.insert(0, str(repo_src))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validação relacional operacional para as hipóteses do schema.yaml"
    )
    parser.add_argument("excel_path", help="Caminho do arquivo .xlsx")
    parser.add_argument(
        "--schema",
        default="configs/schema.yaml",
        help="Caminho do schema YAML (default: configs/schema.yaml)",
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        default=5,
        help="Número máximo de chaves não casadas exibidas por lado",
    )
    args = parser.parse_args()

    _bootstrap_local_src()
    from capex_ai.io.excel_loader import load_canonical_workbook_from_schema_file
    from capex_ai.models.schema import load_schema
    from capex_ai.validation.relations import validate_relationships

    schema = load_schema(Path(args.schema))
    frames = load_canonical_workbook_from_schema_file(
        excel_path=Path(args.excel_path),
        schema_path=Path(args.schema),
    )

    results = validate_relationships(
        frames=frames,
        schema=schema,
        max_unmatched_samples=args.sample_size,
    )

    print("Validação relacional concluída.")
    for result in results:
        print(f"\n[Relação] {result.relationship_name}")
        print(
            f"- Chaves: {result.left_table}.{result.left_column} "
            f"<-> {result.right_table}.{result.right_column}"
        )
        print(f"- Cardinalidade observada: {result.cardinality_observed}")
        print(f"- Recomendação: {result.recommendation.value}")
        print(
            "- Lado esquerdo: "
            f"linhas={result.left_metrics.total_rows}, "
            f"nulos={result.left_metrics.null_count} ({result.left_metrics.null_pct}%), "
            f"duplicidades_linhas={result.left_metrics.duplicate_rows_count}, "
            f"match={result.left_metrics.matched_rows_count} "
            f"({result.left_metrics.matched_rows_pct}%)"
        )
        print(
            "- Lado direito: "
            f"linhas={result.right_metrics.total_rows}, "
            f"nulos={result.right_metrics.null_count} ({result.right_metrics.null_pct}%), "
            f"duplicidades_linhas={result.right_metrics.duplicate_rows_count}, "
            f"match={result.right_metrics.matched_rows_count} "
            f"({result.right_metrics.matched_rows_pct}%)"
        )
        print(f"- Amostra não casados (esquerda): {result.unmatched_left_samples}")
        print(f"- Amostra não casados (direita): {result.unmatched_right_samples}")
        if result.notes:
            print(f"- Notas: {result.notes}")


if __name__ == "__main__":
    main()
