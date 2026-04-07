from __future__ import annotations

import importlib

import pytest

pytestmark = pytest.mark.core

REQUIRED_RUNTIME_MODULES = ["pandas", "yaml", "openpyxl"]


def test_runtime_dependencies_are_available_for_real_pipeline() -> None:
    missing: list[str] = []
    for module_name in REQUIRED_RUNTIME_MODULES:
        try:
            importlib.import_module(module_name)
        except ModuleNotFoundError:
            missing.append(module_name)

    if missing:
        pytest.fail(
            "Dependências obrigatórias ausentes para executar o pipeline real: "
            f"{missing}. Instale com `python -m pip install -e \".[dev]\"` "
            "ou `python -m pip install -r requirements.txt`."
        )
