from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

from capex_ai.models.schema import SchemaSpec

DataFramesByAlias = dict[str, pd.DataFrame]


class WorkbookIngestionError(ValueError):
    """Erro base para ingestão operacional de workbook."""


class MissingWorksheetError(WorkbookIngestionError):
    """Uma aba esperada pelo schema não existe no workbook."""


class MissingRequiredColumnsError(WorkbookIngestionError):
    """Uma ou mais colunas obrigatórias estão ausentes em uma aba."""


class AmbiguousNormalizedColumnsError(WorkbookIngestionError):
    """Duas colunas reais colidem após normalização leve de nomes."""


def _normalize_column_name(name: str) -> str:
    trimmed = str(name).strip()
    single_spaced = re.sub(r"\s+", " ", trimmed)
    return single_spaced.casefold()


def _build_normalized_to_actual(columns: list[str]) -> dict[str, str]:
    normalized_map: dict[str, str] = {}

    for col in columns:
        normalized = _normalize_column_name(col)
        if normalized in normalized_map and normalized_map[normalized] != col:
            raise AmbiguousNormalizedColumnsError(
                "Conflito de colunas após normalização leve: "
                f"'{normalized_map[normalized]}' e '{col}'."
            )
        normalized_map[normalized] = col

    return normalized_map


def _canonicalize_columns(
    frame: pd.DataFrame,
    expected_columns: list[str],
    table_name: str,
) -> pd.DataFrame:
    actual_columns = [str(col) for col in frame.columns]
    normalized_actual = _build_normalized_to_actual(actual_columns)

    missing: list[str] = []
    rename_map: dict[str, str] = {}

    for expected in expected_columns:
        normalized_expected = _normalize_column_name(expected)
        actual_match = normalized_actual.get(normalized_expected)
        if actual_match is None:
            missing.append(expected)
            continue
        rename_map[actual_match] = expected

    if missing:
        raise MissingRequiredColumnsError(
            f"Aba '{table_name}' sem colunas obrigatórias: {missing}."
        )

    return frame.rename(columns=rename_map)


def load_canonical_workbook(excel_path: str | Path, schema: SchemaSpec) -> DataFramesByAlias:
    """Carrega e valida todas as tabelas canônicas do workbook de acordo com o schema."""
    workbook_path = Path(excel_path)
    frames: DataFramesByAlias = {}

    excel_file = pd.ExcelFile(workbook_path)
    available_sheets = set(excel_file.sheet_names)

    expected_sheets = [table.original_name for table in schema.tables]
    missing_sheets = [sheet for sheet in expected_sheets if sheet not in available_sheets]
    if missing_sheets:
        raise MissingWorksheetError(
            "Workbook sem abas esperadas: "
            f"{missing_sheets}. Abas disponíveis: {sorted(available_sheets)}."
        )

    for table in schema.tables:
        frame = pd.read_excel(workbook_path, sheet_name=table.original_name)
        frame = _canonicalize_columns(
            frame=frame,
            expected_columns=table.columns,
            table_name=table.original_name,
        )
        frames[table.alias] = frame

    return frames


def load_tables_from_excel(excel_path: str | Path, schema: SchemaSpec) -> DataFramesByAlias:
    """Compat: usa a API canônica de ingestão de workbook."""
    return load_canonical_workbook(excel_path=excel_path, schema=schema)


def load_canonical_workbook_from_schema_file(
    excel_path: str | Path,
    schema_path: str | Path = "configs/schema.yaml",
) -> DataFramesByAlias:
    from capex_ai.models.schema import load_schema

    schema = load_schema(schema_path)
    return load_canonical_workbook(excel_path=excel_path, schema=schema)
