from __future__ import annotations

import importlib
from dataclasses import dataclass

import pytest

pytestmark = pytest.mark.core


def _excel_loader_module():
    return importlib.import_module("capex_ai.io.excel_loader")


def _pd() -> object:
    try:
        return importlib.import_module("pandas")
    except ModuleNotFoundError:
        pytest.fail(
            "Dependência obrigatória ausente: pandas. "
            "Execute `python scripts/preflight_check.py` para validar o runtime."
        )


@dataclass(frozen=True)
class _Table:
    original_name: str
    alias: str
    columns: list[str]


@dataclass(frozen=True)
class _Schema:
    tables: list[_Table]


class _FakeExcelFile:
    def __init__(self, sheet_names: list[str]):
        self.sheet_names = sheet_names


def test_load_canonical_workbook_success(monkeypatch: pytest.MonkeyPatch) -> None:
    schema = _Schema(
        tables=[
            _Table(original_name="admafecost", alias="admafecost", columns=["wonum", "siteid"]),
            _Table(original_name="INV-AFE", alias="inv_afe", columns=["invoicenum", "refwo"]),
        ]
    )

    def fake_excel_file(_path: object) -> _FakeExcelFile:
        return _FakeExcelFile(sheet_names=["admafecost", "INV-AFE"])

    def fake_read_excel(_path: object, sheet_name: str) -> _pd().DataFrame:
        if sheet_name == "admafecost":
            return _pd().DataFrame({" WONUM ": ["WO1"], "SITEID": ["S1"]})
        return _pd().DataFrame({"INVOICENUM": ["I1"], " refwo ": ["WO1"]})

    monkeypatch.setattr(_pd(), "ExcelFile", fake_excel_file)
    monkeypatch.setattr(_pd(), "read_excel", fake_read_excel)

    result = _excel_loader_module().load_canonical_workbook("fake.xlsx", schema)

    assert set(result.keys()) == {"admafecost", "inv_afe"}
    assert list(result["admafecost"].columns) == ["wonum", "siteid"]
    assert list(result["inv_afe"].columns) == ["invoicenum", "refwo"]


def test_load_canonical_workbook_missing_sheet(monkeypatch: pytest.MonkeyPatch) -> None:
    schema = _Schema(
        tables=[
            _Table(original_name="admafecost", alias="admafecost", columns=["wonum"]),
            _Table(original_name="INV-AFE", alias="inv_afe", columns=["refwo"]),
        ]
    )

    monkeypatch.setattr(
        _pd(),
        "ExcelFile",
        lambda _path: _FakeExcelFile(sheet_names=["admafecost"]),
    )

    with pytest.raises(
        _excel_loader_module().MissingWorksheetError,
        match="Workbook sem abas esperadas",
    ):
        _excel_loader_module().load_canonical_workbook("fake.xlsx", schema)


def test_load_canonical_workbook_missing_required_column(monkeypatch: pytest.MonkeyPatch) -> None:
    schema = _Schema(
        tables=[
            _Table(original_name="admafecost", alias="admafecost", columns=["wonum", "siteid"]),
        ]
    )

    monkeypatch.setattr(
        _pd(),
        "ExcelFile",
        lambda _path: _FakeExcelFile(sheet_names=["admafecost"]),
    )
    monkeypatch.setattr(
        _pd(),
        "read_excel",
        lambda _path, sheet_name: _pd().DataFrame({"wonum": ["WO1"]}),
    )

    with pytest.raises(
        _excel_loader_module().MissingRequiredColumnsError,
        match="colunas obrigatórias",
    ):
        _excel_loader_module().load_canonical_workbook("fake.xlsx", schema)


def test_column_normalization_trim_case_and_single_spaces(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    schema = _Schema(
        tables=[
            _Table(original_name="T1", alias="t1", columns=["Cost Center", "Code"]),
        ]
    )

    monkeypatch.setattr(_pd(), "ExcelFile", lambda _path: _FakeExcelFile(sheet_names=["T1"]))
    monkeypatch.setattr(
        _pd(),
        "read_excel",
        lambda _path, sheet_name: _pd().DataFrame(
            {
                "  COST   CENTER  ": ["CC1"],
                " code ": ["A1"],
            }
        ),
    )

    result = _excel_loader_module().load_canonical_workbook("fake.xlsx", schema)

    assert list(result["t1"].columns) == ["Cost Center", "Code"]
