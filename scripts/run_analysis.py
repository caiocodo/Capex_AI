from __future__ import annotations

import argparse
import sys
from pathlib import Path


def _bootstrap_local_src() -> None:
    repo_src = Path(__file__).resolve().parents[1] / "src"
    if str(repo_src) not in sys.path:
        sys.path.insert(0, str(repo_src))


def _parse_param_pairs(raw_params: list[str]) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for item in raw_params:
        if "=" not in item:
            raise ValueError(f"Parâmetro inválido '{item}'. Use formato chave=valor.")
        key, value = item.split("=", 1)
        parsed[key.strip()] = value.strip()
    return parsed


def main() -> None:
    parser = argparse.ArgumentParser(description="Runner único para análises operacionais.")
    parser.add_argument("--list", action="store_true", help="Lista análises disponíveis")
    parser.add_argument("--analysis-id", default=None, help="ID da análise para executar")
    parser.add_argument("--excel-path", default=None, help="Caminho do workbook .xlsx")
    parser.add_argument("--schema", default="configs/schema.yaml", help="Caminho do schema YAML")
    parser.add_argument(
        "--param",
        action="append",
        default=[],
        help="Parâmetro adicional no formato chave=valor (pode repetir)",
    )
    parser.add_argument("--export-csv", default=None, help="Exporta dataframe de saída para CSV")
    args = parser.parse_args()

    _bootstrap_local_src()
    from capex_ai.analysis.runner import list_available_analyses, run_analysis

    if args.list:
        analyses = list_available_analyses()
        print("Análises disponíveis:")
        for meta in analyses:
            print(f"- {meta.analysis_id}: {meta.friendly_name}")
            print(f"  descrição: {meta.description}")
            print(f"  parâmetros: {[p.name for p in meta.parameters]}")
            print(f"  saída: {meta.output_format}")
        return

    if not args.analysis_id:
        raise SystemExit("Use --analysis-id para executar uma análise, ou --list para listar.")
    if not args.excel_path:
        raise SystemExit("Use --excel-path para executar a análise selecionada.")

    params = _parse_param_pairs(args.param)

    output = run_analysis(
        analysis_id=args.analysis_id,
        excel_path=Path(args.excel_path),
        schema_path=Path(args.schema),
        params=params,
    )

    print(f"Análise executada: {output.metadata.analysis_id} - {output.metadata.friendly_name}")
    print(f"- Universo analisado: {output.universe_analyzed}")
    print(f"- Filtros aplicados: {output.applied_filters}")
    print(f"- Campos usados: {output.fields_used}")
    print(f"- Limitações de qualidade: {output.data_quality_limitations}")
    print(f"- Formato de saída: {output.metadata.output_format}")

    if output.details:
        print(f"- Detalhes: {output.details}")

    if output.dataframe is not None:
        print("\nPrévia (top 10):")
        print(output.dataframe.head(10).to_string(index=False))
        if args.export_csv:
            output.dataframe.to_csv(args.export_csv, index=False)
            print(f"\nCSV exportado em: {args.export_csv}")


if __name__ == "__main__":
    main()
