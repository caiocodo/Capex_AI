from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class TableSpec:
    original_name: str
    alias: str
    columns: list[str]


@dataclass(frozen=True)
class SideSpec:
    table_alias: str
    column: str


@dataclass(frozen=True)
class RelationshipSpec:
    name: str
    kind: str
    left: SideSpec
    right: SideSpec


@dataclass(frozen=True)
class SchemaSpec:
    version: int
    source_kind: str
    tables: list[TableSpec]
    relationships: list[RelationshipSpec]


def _to_table_spec(raw: dict[str, Any]) -> TableSpec:
    return TableSpec(
        original_name=str(raw["original_name"]),
        alias=str(raw["alias"]),
        columns=[str(col) for col in raw["columns"]],
    )


def _to_relationship_spec(raw: dict[str, Any]) -> RelationshipSpec:
    left = SideSpec(
        table_alias=str(raw["left"]["table_alias"]),
        column=str(raw["left"]["column"]),
    )
    right = SideSpec(
        table_alias=str(raw["right"]["table_alias"]),
        column=str(raw["right"]["column"]),
    )
    return RelationshipSpec(name=str(raw["name"]), kind=str(raw["kind"]), left=left, right=right)


def load_schema(path: str | Path) -> SchemaSpec:
    schema_path = Path(path)
    raw_data = yaml.safe_load(schema_path.read_text(encoding="utf-8"))

    tables = [_to_table_spec(item) for item in raw_data["tables"]]
    relationships = [_to_relationship_spec(item) for item in raw_data["relationships"]]

    return SchemaSpec(
        version=int(raw_data["version"]),
        source_kind=str(raw_data["source"]["kind"]),
        tables=tables,
        relationships=relationships,
    )
