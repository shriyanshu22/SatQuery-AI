"""Pydantic v2 request and response models."""

from __future__ import annotations
from typing import Any, Literal
from pydantic import BaseModel, ConfigDict


class QueryRequest(BaseModel):
    query: str
    image_ids: list[str] | None = None
    capabilities: list[str] | None = None
    include_evidence: bool = True
    include_trace: bool = True
    model_backend: str | None = None


class DemoQueryRequest(BaseModel):
    query: str
    demo_image_name: str
    demo_image_name_2: str | None = None


class ConfidenceSchema(BaseModel):
    value: float | None
    source: str
    method: str
    calibrated: bool


class EvidenceSchema(BaseModel):
    type: str
    data: dict[str, Any]


class ExecutionStepSchema(BaseModel):
    step_number: int
    action: str
    status: Literal["completed", "failed", "skipped"]
    duration_ms: float | None
    observable_output: str | None


class AnalysisResultSchema(BaseModel):
    answer: str
    confidence: ConfidenceSchema | None
    evidence: list[EvidenceSchema]
    execution_trace: list[ExecutionStepSchema]
    metadata: dict[str, Any]

    @classmethod
    def from_internal(cls, internal_result: "backend.core.types.AnalysisResult") -> "AnalysisResultSchema":
        from backend.core.evidence import serialize_evidence
        
        conf = internal_result.confidence
        confidence_schema = ConfidenceSchema(
            value=conf.value if conf else None,
            source=conf.source if conf else "unavailable",
            method=conf.method if conf else "none",
            calibrated=conf.calibrated if conf else False
        ) if conf else None

        evidence_schemas = []
        for ev in internal_result.evidence:
            ev_dict = serialize_evidence(ev)
            ev_type = ev_dict.pop("type", "unknown")
            evidence_schemas.append(EvidenceSchema(type=ev_type, data=ev_dict))

        trace_schemas = [
            ExecutionStepSchema(
                step_number=step.step_number,
                action=step.action,
                status=step.status,
                duration_ms=step.duration_ms,
                observable_output=step.observable_output
            ) for step in internal_result.execution_trace
        ]

        return cls(
            answer=internal_result.answer,
            confidence=confidence_schema,
            evidence=evidence_schemas,
            execution_trace=trace_schemas,
            metadata=internal_result.metadata
        )


class QueryResponse(BaseModel):
    task_id: str
    status: Literal["completed", "processing", "failed"]
    result: AnalysisResultSchema | None = None


class CapabilityInfo(BaseModel):
    name: str
    description: str
    available: bool
    model_backend: str


class HealthResponse(BaseModel):
    status: str
    version: str
    model_backend: str
    capabilities: list[str]


# ---------------------------------------------------------------------------
# Upload / Validation Schemas
# ---------------------------------------------------------------------------

class ValidationResultSchema(BaseModel):
    status: Literal["valid", "valid_with_warnings", "invalid"]
    warnings: list[str] = []
    errors: list[str] = []


class ImageMetadataSchema(BaseModel):
    crs: str | None = None
    resolution: tuple[float, float] | None = None
    bounds: tuple[float, float, float, float] | None = None
    band_count: int
    modality: str
    acquisition_date: str | None = None
    width: int
    height: int


class UploadResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    image_id: str
    filename: str
    file_format: str
    size_bytes: int
    validation: ValidationResultSchema
    metadata: ImageMetadataSchema
    preview_url: str | None = None


class ErrorResponse(BaseModel):
    error: str
    detail: str | None
    error_code: str


class DemoSampleInfo(BaseModel):
    name: str
    description: str
    format: str
    capabilities: list[str]
