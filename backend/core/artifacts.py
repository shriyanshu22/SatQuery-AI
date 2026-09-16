"""Artifact storage system for derived outputs.

Artifacts are secondary products created during preprocessing — previews,
normalised images, tiles, aligned rasters, SAR visualisations, etc.  They are
always *derived* from a source image and must never replace the original data.

Every artifact carries:

* A stable ``artifact_id`` for referencing.
* The ``source_image_id`` linking back to the original ``RSDataObject``.
* A ``description`` of how it was produced (traceability).
* Filesystem path management that never exposes raw server paths to clients.
"""

from __future__ import annotations

import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

from backend.core.logging import get_logger

logger = get_logger(__name__)


class ArtifactType(str, Enum):
    """Categories of derived artifacts."""

    PREVIEW = "preview"
    NORMALIZED = "normalized"
    TILE = "tile"
    ALIGNED = "aligned"
    SAR_VISUALIZATION = "sar_visualization"
    REPROJECTED = "reprojected"
    RGB_COMPOSITE = "rgb_composite"


@dataclass
class Artifact:
    """A derived output produced from a source image.

    Attributes:
        artifact_id: Unique identifier for this artifact.
        artifact_type: Category of the artifact.
        source_image_id: ``image_id`` of the ``RSDataObject`` this was derived from.
        path: Absolute filesystem path to the artifact file.
        created_at: ISO-8601 timestamp of creation.
        description: Human-readable explanation of how this artifact was produced.
        metadata: Optional key–value pairs with additional context.
    """

    artifact_id: str
    artifact_type: ArtifactType
    source_image_id: str
    path: str
    created_at: str
    description: str
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def filename(self) -> str:
        """Return just the filename component (safe for API responses)."""
        return os.path.basename(self.path)


class ArtifactStore:
    """Manages creation, storage, and retrieval of derived artifacts.

    All artifacts are written under a configurable *root directory*.  The store
    organises files into subdirectories by source image ID so they are easy to
    locate and clean up.

    Args:
        root_dir: Base directory for all artifacts (e.g. ``./outputs/artifacts``).
    """

    def __init__(self, root_dir: str) -> None:
        self._root = Path(root_dir)
        self._root.mkdir(parents=True, exist_ok=True)
        self._artifacts: dict[str, Artifact] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def create(
        self,
        artifact_type: ArtifactType,
        source_image_id: str,
        extension: str,
        description: str,
        metadata: dict[str, Any] | None = None,
    ) -> tuple[str, Path]:
        """Reserve a new artifact slot and return ``(artifact_id, file_path)``.

        The caller is responsible for writing actual data to the returned
        ``file_path``.  After writing, call :meth:`register` to finalise.

        Args:
            artifact_type: Category.
            source_image_id: The source image this is derived from.
            extension: File extension including the dot (e.g. ``".png"``).
            description: What this artifact represents.
            metadata: Optional extra metadata dict.

        Returns:
            A tuple of ``(artifact_id, absolute_path)``.
        """
        artifact_id = str(uuid.uuid4())
        img_dir = self._root / source_image_id
        img_dir.mkdir(parents=True, exist_ok=True)

        filename = f"{artifact_type.value}_{artifact_id[:8]}{extension}"
        file_path = img_dir / filename

        artifact = Artifact(
            artifact_id=artifact_id,
            artifact_type=artifact_type,
            source_image_id=source_image_id,
            path=str(file_path),
            created_at=datetime.now(timezone.utc).isoformat(),
            description=description,
            metadata=metadata or {},
        )
        self._artifacts[artifact_id] = artifact
        logger.info(
            "artifact_created",
            artifact_id=artifact_id,
            artifact_type=artifact_type.value,
            source_image_id=source_image_id,
        )
        return artifact_id, file_path

    def register(self, artifact_id: str) -> Artifact:
        """Finalise an artifact after the caller has written data to disk.

        Raises:
            KeyError: If the artifact_id was not previously created.
            FileNotFoundError: If the expected file does not exist on disk.
        """
        artifact = self._artifacts.get(artifact_id)
        if artifact is None:
            raise KeyError(f"Unknown artifact: {artifact_id}")
        if not os.path.exists(artifact.path):
            raise FileNotFoundError(f"Artifact file missing: {artifact.path}")
        return artifact

    def get(self, artifact_id: str) -> Artifact | None:
        """Retrieve a registered artifact by ID."""
        return self._artifacts.get(artifact_id)

    def list_for_image(self, source_image_id: str) -> list[Artifact]:
        """Return all artifacts derived from a given source image."""
        return [
            a for a in self._artifacts.values()
            if a.source_image_id == source_image_id
        ]

    @property
    def root_dir(self) -> Path:
        """Return the root artifact directory."""
        return self._root
