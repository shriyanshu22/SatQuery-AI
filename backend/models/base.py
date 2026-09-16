"""Base architecture and registry for all models."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, Optional, Type, TypeVar

from backend.core.protocols import ModelInfo
from backend.core.exceptions import ModelNotLoadedError, SatQueryError

logger = logging.getLogger(__name__)

T = TypeVar("T")


class BaseModel(ABC):
    """Abstract base class for all model implementations."""
    
    def __init__(self, name: str) -> None:
        self.name = name
        self._loaded = False
        
    @abstractmethod
    def load(self) -> None:
        """Load the model into memory."""
        pass
        
    @abstractmethod
    def unload(self) -> None:
        """Unload the model from memory to free resources."""
        pass
        
    def is_loaded(self) -> bool:
        """Check if the model is currently loaded.
        
        Returns:
            True if loaded, False otherwise.
        """
        return self._loaded
        
    @abstractmethod
    def get_model_info(self) -> ModelInfo:
        """Get metadata about this model.
        
        Returns:
            ModelInfo instance.
        """
        pass

    def __enter__(self) -> "BaseModel":
        if not self.is_loaded():
            self.load()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.unload()


class ModelRegistry:
    """Singleton registry for managing model implementations."""
    
    _instance: Optional["ModelRegistry"] = None
    
    def __new__(cls) -> "ModelRegistry":
        if cls._instance is None:
            cls._instance = super(ModelRegistry, cls).__new__(cls)
            cls._instance._registry = {}
        return cls._instance
        
    def register(self, name: str, protocol_type: type, implementation_class: Type[BaseModel]) -> None:
        """Register a model implementation.
        
        Args:
            name: Unique name for this implementation.
            protocol_type: The protocol/interface this model implements.
            implementation_class: The class to instantiate.
        """
        key = (name, protocol_type)
        self._registry[key] = implementation_class
        logger.info(f"Registered model {name} for protocol {protocol_type.__name__}")
        
    def get(self, name: str, protocol_type: Type[T]) -> T:
        """Get an instance of a registered model.
        
        Args:
            name: Name of the implementation to retrieve.
            protocol_type: The expected protocol type.
            
        Returns:
            An instantiated model that satisfies the requested protocol.
            
        Raises:
            SatQueryError: If the model is not found.
        """
        key = (name, protocol_type)
        if key not in self._registry:
            raise SatQueryError(f"Model {name} implementing {protocol_type.__name__} not found in registry.")
            
        impl_class = self._registry[key]
        return impl_class(name)  # type: ignore

    def list_models(self) -> Dict[str, list[str]]:
        """List all registered models.
        
        Returns:
            Dictionary mapping protocol names to lists of model names.
        """
        result: Dict[str, list[str]] = {}
        for (name, proto), _ in self._registry.items():
            proto_name = proto.__name__
            if proto_name not in result:
                result[proto_name] = []
            result[proto_name].append(name)
        return result


def get_model(name: str, protocol_type: Type[T]) -> T:
    """Convenience function to get a model from the registry."""
    return ModelRegistry().get(name, protocol_type)
