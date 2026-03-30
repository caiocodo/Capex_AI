from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from capex_ai.models.schema import SchemaSpec
    from capex_ai.validation.relations import RelationshipValidationResult

DataFramesByAlias = dict[str, Any]


@dataclass(frozen=True)
class AnalysisParameter:
    name: str
    required: bool
    description: str


@dataclass(frozen=True)
class AnalysisMetadata:
    analysis_id: str
    friendly_name: str
    description: str
    parameters: list[AnalysisParameter]
    output_format: str


@dataclass(frozen=True)
class AnalysisRunOutput:
    metadata: AnalysisMetadata
    universe_analyzed: dict[str, int]
    applied_filters: str
    data_quality_limitations: list[str]
    fields_used: list[str]
    dataframe: Any
    details: dict[str, Any]


AnalysisExecutor = Callable[
    [DataFramesByAlias, "SchemaSpec", list["RelationshipValidationResult"], dict[str, str]],
    AnalysisRunOutput,
]


@dataclass(frozen=True)
class RegisteredAnalysis:
    metadata: AnalysisMetadata
    executor: AnalysisExecutor
