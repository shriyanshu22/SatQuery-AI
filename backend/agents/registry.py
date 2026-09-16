"""Tool and capability registry.

[PHASE 4 SCAFFOLDING]
This module is scaffolding for the future autonomous agent layer.
It is not currently wired into the Phase 2 query flow.
"""

from __future__ import annotations
from typing import Callable, Any

from backend.core.types import QueryIntent
from backend.api.schemas import CapabilityInfo
from .executor import StepResult

class CapabilityRegistry:
    """Registry for analysis capabilities and tools."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._registry = {}
            cls._instance._register_defaults()
        return cls._instance

    def _register_defaults(self):
        """Pre-register placeholder handlers."""
        def mock_handler(images: list[Any], query: str, **kwargs) -> StepResult:
            return StepResult(step_id="mock", status="completed", output="mock")
            
        for intent in QueryIntent:
            self.register(intent, mock_handler, f"{intent.name} Handler", [])

    def register(self, intent: QueryIntent, handler: Callable, description: str, required_inputs: list):
        """Register a new capability handler."""
        self._registry[intent] = {
            "handler": handler,
            "description": description,
            "required_inputs": required_inputs
        }

    def get_handler(self, intent: QueryIntent) -> Callable:
        """Get the handler for an intent."""
        if intent not in self._registry:
            raise KeyError(f"No handler registered for {intent}")
        return self._registry[intent]["handler"]

    def list_capabilities(self) -> list[CapabilityInfo]:
        """List all available capabilities."""
        caps = []
        for intent, data in self._registry.items():
            caps.append(CapabilityInfo(
                name=intent.name,
                description=data["description"],
                available=True,
                model_backend="mock"
            ))
        return caps

    def is_available(self, intent: QueryIntent) -> bool:
        """Check if a capability is available."""
        return intent in self._registry
