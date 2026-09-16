"""Step execution engine.

[PHASE 4 SCAFFOLDING]
This module is scaffolding for the future autonomous agent layer.
It is not currently wired into the Phase 2 query flow and should not produce fake results.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

from backend.core.types import RSDataObject, AnalysisResult, ExecutionStep
from backend.core.evidence import Evidence
from backend.core.confidence import ConfidenceScore
from backend.core.logging import get_logger
from .planner import ExecutionPlan, PlannedStep

logger = get_logger(__name__)

@dataclass
class StepResult:
    step_id: str
    status: str
    output: Any
    evidence: list[Evidence] = field(default_factory=list)
    confidence: ConfidenceScore | None = None
    error: Exception | None = None

@dataclass
class ExecutionContext:
    results: dict[str, StepResult] = field(default_factory=dict)

class ExecutionEngine:
    """Executes the planned steps."""
    
    def execute(self, plan: ExecutionPlan, images: list[RSDataObject], query: str) -> AnalysisResult:
        """Execute the plan and return the result."""
        context = ExecutionContext()
        trace = []
        
        for idx, step in enumerate(plan.steps):
            duration = 1.0 # Mock duration
            try:
                res = self._execute_step(step, context)
                context.results[step.step_id] = res
                self._record_trace(step, res, duration, trace, idx)
            except Exception as e:
                res = self._handle_step_failure(step, e)
                context.results[step.step_id] = res
                self._record_trace(step, res, duration, trace, idx)
                
        return self._assemble_final_result(list(context.results.values()), trace)

    def _execute_step(self, step: PlannedStep, context: ExecutionContext) -> StepResult:
        """Execute a single step."""
        logger.warning(f"Executor invoked for {step.step_id} - this is unimplemented Phase 4 scaffolding.")
        raise NotImplementedError("Agentic execution engine is not yet implemented (Phase 4).")

    def _record_trace(self, step: PlannedStep, result: StepResult, duration: float, trace: list[ExecutionStep], idx: int):
        """Record the step execution in the trace."""
        trace.append(ExecutionStep(
            step_number=idx + 1,
            action=step.capability,
            status=result.status, # type: ignore
            duration_ms=duration * 1000,
            observable_output=str(result.output)
        ))

    def _handle_step_failure(self, step: PlannedStep, error: Exception) -> StepResult:
        """Handle step failure."""
        logger.error(f"Step {step.step_id} failed: {error}")
        return StepResult(step.step_id, "failed", None, error=error)

    def _assemble_final_result(self, step_results: list[StepResult], trace: list[ExecutionStep]) -> AnalysisResult:
        """Assemble the final analysis result."""
        raise NotImplementedError("Result assembly via executor is not yet implemented.")

    def _fuse_evidence(self, step_results: list[StepResult]) -> list[Evidence]:
        """Fuse evidence from all steps."""
        fused = []
        for r in step_results:
            fused.extend(r.evidence)
        return fused

    def _compute_final_confidence(self, step_results: list[StepResult]) -> ConfidenceScore:
        """Compute the final confidence score."""
        return ConfidenceScore(value=0.9, source="executor", method="mock", calibrated=False)
