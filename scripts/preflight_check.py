from __future__ import annotations

import importlib
from pathlib import Path

REQUIRED_MODULES = ("pandas", "yaml", "openpyxl")
REQUIRED_PATHS = (
    Path("configs/schema.yaml"),
    Path("tests/fixtures/Capex AI - Dados.xlsx"),
)


def main() -> int:
    missing_modules: list[str] = []
    for module_name in REQUIRED_MODULES:
        try:
            importlib.import_module(module_name)
        except ModuleNotFoundError:
            missing_modules.append(module_name)

    missing_paths = [str(path) for path in REQUIRED_PATHS if not path.exists()]

    if not missing_modules and not missing_paths:
        print("Preflight OK: runtime e arquivos obrigatórios estão prontos.")
        return 0

    print("Preflight FALHOU: ambiente não está pronto para pipeline real.")
    if missing_modules:
        print(f"- Módulos ausentes: {missing_modules}")
        print(
            "  Instalação sugerida: python -m pip install -e \".[dev]\" "
            "ou python -m pip install -r requirements.txt"
        )
    if missing_paths:
        print(f"- Arquivos obrigatórios ausentes: {missing_paths}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
