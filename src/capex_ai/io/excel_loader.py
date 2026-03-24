from __future__ import annotations

from pathlib import Path

import pandas as pd

from capex_ai.models.schema import SchemaSpec

DataFramesByAlias = dict[str, pd.DataFrame]


def load_tables_from_excel(excel_path: str | Path, schema: SchemaSpec) -> DataFramesByAlias:
    """Carrega abas do Excel usando o mapeamento explícito original_name -> alias."""
    workbook_path = Path(excel_path)
    frames: DataFramesByAlias = {}

    for table in schema.tables:
        frame = pd.read_excel(workbook_path, sheet_name=table.original_name)
        frames[table.alias] = frame

    return frames
