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
        description="Carga operacional de workbook Excel com 5 abas canônicas."
    )
    parser.add_argument("excel_path", help="Caminho do arquivo .xlsx de origem")
    parser.add_argument(
        "--schema",
        default="configs/schema.yaml",
        help="Caminho do schema YAML (default: configs/schema.yaml)",
    )
    args = parser.parse_args()

    _bootstrap_local_src()
    from capex_ai.io.excel_loader import load_canonical_workbook_from_schema_file

    frames = load_canonical_workbook_from_schema_file(
        excel_path=Path(args.excel_path),
        schema_path=Path(args.schema),
    )

    print("Carga concluída com sucesso.")
    print(f"Total de tabelas carregadas: {len(frames)}")
    for alias, frame in frames.items():
        print(f"- {alias}: {len(frame)} linhas, {len(frame.columns)} colunas")


if __name__ == "__main__":
    main()
