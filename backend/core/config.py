"""Configuration management for SatQuery AI backend."""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Any

import yaml
from pydantic import AliasChoices, BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ServerConfig(BaseModel):
    """Server configuration settings."""
    application_name: str = "SatQuery AI"
    environment: str = "development"
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 1
    reload: bool = False
    cors_origins: list[str] = ["*"]


class ModelConfig(BaseModel):
    """Model deployment and inference configuration."""
    backend_type: str = "REAL"  # REAL, MOCK, CACHED
    timeout_seconds: int = 60
    device: str = "cpu"
    cache_dir: str = "./cache/models"
    vlm_model_name: str = "qwen2-vl-2b"
    grounding_model_name: str = "grounding-dino"


class PreprocessingConfig(BaseModel):
    """Preprocessing and alignment configuration."""
    target_resolution: tuple[int, int] = (1024, 1024)
    normalize: bool = True
    alignment_method: str = "sift"


class StorageConfig(BaseModel):
    """File storage configuration."""
    upload_dir: str = "./uploads"
    output_dir: str = "./outputs"
    max_upload_size_mb: int = 100
    allowed_formats: list[str] = [".tif", ".tiff", ".png", ".jpg", ".jpeg"]


class DemoConfig(BaseModel):
    """Demo mode configuration."""
    enabled: bool = False
    use_cached_responses: bool = True


class Settings(BaseSettings):
    """Main application settings loaded from environment and .env files."""
    
    server: ServerConfig = ServerConfig()
    model: ModelConfig = ModelConfig()
    preprocessing: PreprocessingConfig = PreprocessingConfig()
    storage: StorageConfig = StorageConfig()
    demo: DemoConfig = DemoConfig()
    
    log_level: str = Field(default="INFO", validation_alias=AliasChoices("log_level", "SATQUERY_LOG_LEVEL"))

    model_config = SettingsConfigDict(
        env_prefix="SATQUERY_",
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        case_sensitive=False,
    )

    @classmethod
    def from_yaml(cls, yaml_path: str) -> "Settings":
        """Load settings from a YAML configuration file."""
        if not os.path.exists(yaml_path):
            raise FileNotFoundError(f"Configuration file not found: {yaml_path}")
            
        with open(yaml_path, "r", encoding="utf-8") as f:
            yaml_data = yaml.safe_load(f) or {}
            
        return cls(**yaml_data)


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()
