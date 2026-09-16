"""Exception hierarchy for SatQuery AI.

Defines all custom exceptions used throughout the backend application.
"""

from __future__ import annotations

from typing import Any, Dict, Optional


class SatQueryError(Exception):
    """Base exception for all SatQuery AI specific errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None, original_exception: Optional[Exception] = None):
        """Initialize the exception.
        
        Args:
            message: Human-readable error message.
            details: Optional dictionary with structured error details.
            original_exception: Optional reference to the underlying exception.
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}
        self.original_exception = original_exception


class ValidationError(SatQueryError):
    """Raised when input validation fails."""
    pass


class ImageLoadError(SatQueryError):
    """Raised when an image fails to load or parse."""
    pass


class UnsupportedFormatError(SatQueryError):
    """Raised when an uploaded file format is not supported."""
    pass


class ModelNotLoadedError(SatQueryError):
    """Raised when attempting to use a model that has not been initialized."""
    pass


class ModelInferenceError(SatQueryError):
    """Raised when model inference fails unexpectedly."""
    pass


class ModelTimeoutError(SatQueryError):
    """Raised when model inference exceeds the configured timeout."""
    pass


class PreprocessingError(SatQueryError):
    """Raised when the preprocessing pipeline fails."""
    pass


class AlignmentError(SatQueryError):
    """Raised when spatial alignment between multiple images fails."""
    pass


class RoutingError(SatQueryError):
    """Raised when query routing fails to determine the target pipeline."""
    pass


class PlanningError(SatQueryError):
    """Raised when execution planning fails."""
    pass


class EvidenceError(SatQueryError):
    """Raised when evidence assembly or validation fails."""
    pass


class UploadError(SatQueryError):
    """Raised when a file upload fails (e.g., size limit, format, path traversal)."""
    pass


class DemoModeError(SatQueryError):
    """Raised when there is a configuration error related to demo mode."""
    pass
