"""Fundação do projeto Capex AI."""

from .models.schema import RelationshipSpec, SchemaSpec, TableSpec, load_schema

__all__ = ["SchemaSpec", "TableSpec", "RelationshipSpec", "load_schema"]
