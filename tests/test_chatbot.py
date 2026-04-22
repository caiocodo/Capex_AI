from __future__ import annotations

import importlib
import importlib.util
from pathlib import Path

import pytest

pytestmark = pytest.mark.core


def _pd() -> object:
    try:
        return importlib.import_module("pandas")
    except ModuleNotFoundError:
        pytest.fail(
            "Dependencia obrigatoria ausente: pandas. "
            "Execute `python scripts/preflight_check.py` para validar o runtime."
        )


def _load_chatbot_module() -> object:
    module_path = Path("scripts/chatbot.py")
    spec = importlib.util.spec_from_file_location("capex_chatbot_script", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_select_projects_table_option_1_returns_top_10_by_linecost_then_budget() -> None:
    chatbot = _load_chatbot_module()
    overview = _pd().DataFrame(
        {
            "wonum": [
                "WO-LOW",
                "WO-TIE-LOW-BUDGET",
                "WO-TIE-HIGH-BUDGET",
                "WO-TOP",
                "WO-04",
                "WO-05",
                "WO-06",
                "WO-07",
                "WO-08",
                "WO-09",
                "WO-10",
                "WO-11",
            ],
            "budget_sum": [999, 10, 20, 5, 40, 50, 60, 70, 80, 90, 100, 110],
            "cumulative_linecost_sum": [1, 100, 100, 200, 90, 80, 70, 60, 50, 40, 30, 20],
        }
    )

    result = chatbot._select_projects_table(overview=overview, choice="1")

    assert len(result) == 10
    assert result["wonum"].tolist() == [
        "WO-TOP",
        "WO-TIE-HIGH-BUDGET",
        "WO-TIE-LOW-BUDGET",
        "WO-04",
        "WO-05",
        "WO-06",
        "WO-07",
        "WO-08",
        "WO-09",
        "WO-10",
    ]


def test_select_projects_table_option_2_returns_top_10_by_linecost_then_budget() -> None:
    chatbot = _load_chatbot_module()
    overview = _pd().DataFrame(
        {
            "wonum": [
                "WO-LOW",
                "WO-TIE-LOW-BUDGET",
                "WO-TIE-HIGH-BUDGET",
                "WO-TOP",
                "WO-04",
                "WO-05",
                "WO-06",
                "WO-07",
                "WO-08",
                "WO-09",
                "WO-10",
                "WO-11",
            ],
            "budget_sum": [999, 10, 20, 5, 40, 50, 60, 70, 80, 90, 100, 110],
            "cumulative_linecost_sum": [1, 100, 100, 200, 90, 80, 70, 60, 50, 40, 30, 20],
        }
    )

    result = chatbot._select_projects_table(overview=overview, choice="2")

    assert len(result) == 10
    assert result["wonum"].tolist() == [
        "WO-TOP",
        "WO-TIE-HIGH-BUDGET",
        "WO-TIE-LOW-BUDGET",
        "WO-04",
        "WO-05",
        "WO-06",
        "WO-07",
        "WO-08",
        "WO-09",
        "WO-10",
    ]


def test_select_projects_table_rejects_invalid_option() -> None:
    chatbot = _load_chatbot_module()
    overview = _pd().DataFrame({"wonum": ["WO1"]})

    with pytest.raises(ValueError, match="Opcao invalida"):
        chatbot._select_projects_table(overview=overview, choice="3")
