"""Typed confidence scoring with source attribution.

Ensures confidence scores are never fabricated and always traceable.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

@dataclass
class ConfidenceScore:
    """Represents a typed confidence score with strict source attribution."""
    
    value: float | None  # None = unavailable
    source: str
    method: str  # human-readable explanation
    calibrated: bool = False  # whether post-hoc calibration was applied

    @staticmethod
    def unavailable(reason: str) -> ConfidenceScore:
        """Create a ConfidenceScore when confidence is genuinely unavailable.
        
        Args:
            reason: Explanation of why confidence is unavailable.
        """
        return ConfidenceScore(
            value=None, 
            source="unavailable", 
            method=reason,
            calibrated=False
        )

    @staticmethod
    def from_model_logits(value: float, method: str) -> ConfidenceScore:
        """Create a ConfidenceScore derived directly from model raw logits/probabilities.
        
        Args:
            value: The raw confidence score (e.g., 0.0 to 1.0).
            method: How this was derived (e.g., 'Softmax max probability').
        """
        return ConfidenceScore(
            value=value, 
            source="model_logits", 
            method=method,
            calibrated=False
        )

    @staticmethod
    def from_evidence_agreement(value: float, method: str) -> ConfidenceScore:
        """Create a ConfidenceScore based on agreement across multiple evidence sources.
        
        Args:
            value: The derived confidence score.
            method: How the agreement was measured.
        """
        return ConfidenceScore(
            value=value, 
            source="evidence_agreement", 
            method=method,
            calibrated=False
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert the confidence score to a dictionary.
        
        Returns:
            Dictionary representation.
        """
        return {
            "value": self.value,
            "source": self.source,
            "method": self.method,
            "calibrated": self.calibrated
        }
