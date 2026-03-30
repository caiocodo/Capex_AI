from pathlib import Path

import pytest

pytest.importorskip("yaml")

SCHEMA_PATH = Path("configs/schema.yaml")

EXPECTED_ALIASES = {
    "admafecost",
    "inv_afe",
    "invoicecost",
    "multiassetlocci",
    "wo_afes",
}


def test_schema_has_expected_tables_and_aliases() -> None:
    from capex_ai.models.schema import load_schema

    schema = load_schema(SCHEMA_PATH)
    aliases = {table.alias for table in schema.tables}

    assert schema.version == 1
    assert len(schema.tables) == 5
    assert aliases == EXPECTED_ALIASES


def test_schema_has_relationship_hypotheses() -> None:
    from capex_ai.models.schema import load_schema

    schema = load_schema(SCHEMA_PATH)

    assert len(schema.relationships) == 4
    assert all(rel.kind == "operational_hypothesis" for rel in schema.relationships)
