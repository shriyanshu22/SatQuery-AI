"""Text-Guided Grounding Service."""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import List

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from backend.core.types import RSDataObject, AnalysisResult, ExecutionStep, QueryIntent
from backend.core.evidence import Evidence, MetadataEvidence, BoundingBoxEvidence
from backend.core.confidence import ConfidenceScore
from backend.core.protocols import GroundingProtocol, GroundingResult
from backend.preprocessing.adapters import ModelAdapter
from backend.core.logging import get_logger

logger = get_logger(__name__)


class GroundingService:
    """Service handling text-guided spatial grounding."""

    def __init__(self, model: GroundingProtocol, adapter: ModelAdapter):
        self.model = model
        self.adapter = adapter

    def ground_query(self, image: RSDataObject, text_query: str) -> AnalysisResult:
        """Locate objects or features in the image described by the text query.

        Args:
            image: The remote-sensing data object.
            text_query: Natural-language grounding query.

        Returns:
            Canonical AnalysisResult with spatial evidence.
        """
        logger.info(f"Grounding query '{text_query}' on image {image.image_id}")

        # 1. Adapt data
        adapted_data = self.adapter.adapt(image)

        # 2. Ensure loaded
        model_reused = self.model.is_loaded()
        if not model_reused:
            self.model.load()

        # 3. Predict with timing
        t0 = time.perf_counter()
        result = self.model.ground(adapted_data, text_query)
        inference_ms = (time.perf_counter() - t0) * 1000.0

        # 4. Assemble evidence
        evidence_list = self._extract_evidence(image, result)

        # 5. Build metadata
        model_info = self.model.get_model_info()
        raw = result.raw_output if isinstance(result.raw_output, dict) else {}

        metadata = {
            "model": model_info.name,
            "backend_type": model_info.backend_type,
            "model_reused": model_reused,
            "inference_duration_ms": round(inference_ms, 2),
            "num_detections": len(result.boxes),
        }
        # Merge raw output metadata (inference_duration_ms from model, thresholds, etc.)
        for key in ("box_threshold", "text_threshold", "normalised_query", "image_size"):
            if key in raw:
                metadata[key] = raw[key]

        # 6. Generate visualization if detections were found
        viz_path: str | None = None
        if result.boxes:
            viz_path = self._generate_visualization(image, result, text_query)

        # 7. Build answer
        n = len(result.boxes)
        if n == 0:
            answer = f"No regions matching '{text_query}' were detected in the image."
        else:
            labels_summary = ", ".join(
                sorted(set(b.label for b in result.boxes))
            )
            answer = f"Found {n} regions matching '{text_query}': {labels_summary}."
            if viz_path:
                answer += f" Visualization saved to {viz_path}"

        # 8. Trace
        trace = [
            ExecutionStep(
                step_number=1,
                action="input_validated",
                status="completed",
                duration_ms=None,
                observable_output=f"Image {image.image_id} adapted for grounding",
            ),
            ExecutionStep(
                step_number=2,
                action="grounding_tool_selected",
                status="completed",
                duration_ms=None,
                observable_output=f"Selected Grounding with {model_info.name}",
            ),
            ExecutionStep(
                step_number=3,
                action="model_loaded" if not model_reused else "model_reused",
                status="completed",
                duration_ms=None,
                observable_output=f"{model_info.name} {'reused from memory' if model_reused else 'loaded fresh'}",
            ),
            ExecutionStep(
                step_number=4,
                action="inference_executed",
                status="completed",
                duration_ms=round(inference_ms, 2),
                observable_output=f"Detected {n} bounding boxes",
            ),
        ]
        if viz_path:
            trace.append(
                ExecutionStep(
                    step_number=5,
                    action="visualization_generated",
                    status="completed",
                    duration_ms=None,
                    observable_output=f"Saved visualization to {viz_path}",
                )
            )

        return AnalysisResult(
            answer=answer,
            confidence=result.confidence,
            evidence=evidence_list,
            execution_trace=trace,
            metadata=metadata,
            warnings=[],
            errors=[],
            intent=QueryIntent.GROUNDING,
        )

    def _extract_evidence(
        self, image: RSDataObject, result: GroundingResult
    ) -> List[Evidence]:
        """Convert grounding results into formal Evidence objects."""
        evidence = list(result.evidence)

        # Bounding boxes
        if result.boxes:
            evidence.append(
                BoundingBoxEvidence(
                    boxes=result.boxes,
                    source_image_id=image.image_id,
                    model_source=self.model.get_model_info().name,
                )
            )

        # Metadata
        evidence.append(
            MetadataEvidence(
                source_file=image.image_id,
                crs=image.metadata.crs,
                resolution=image.metadata.resolution,
                bounds=image.metadata.bounds,
                band_count=image.metadata.band_count,
                acquisition_date=image.metadata.acquisition_date,
            )
        )

        return evidence

    def _generate_visualization(
        self, image: RSDataObject, result: GroundingResult, query: str
    ) -> str | None:
        """Draw real bounding boxes on the image and save to outputs/.

        Args:
            image: The source RSDataObject.
            result: GroundingResult with real bounding boxes.
            query: The original text query.

        Returns:
            Path to the saved visualization file, or None on error.
        """
        try:
            data = image.data
            # Transpose (C, H, W) → (H, W, C) if needed
            if len(data.shape) == 3 and data.shape[0] in (1, 3, 4):
                data = np.transpose(data, (1, 2, 0))
                if data.shape[2] == 1:
                    data = data[:, :, 0]
            if data.dtype != np.uint8:
                if data.max() <= 1.0:
                    data = (data * 255).astype(np.uint8)
                else:
                    data = data.astype(np.uint8)

            pil_img = Image.fromarray(data).convert("RGB")
            draw = ImageDraw.Draw(pil_img)

            # Use a set of distinct colours for different labels
            colours = [
                "#FF3333", "#33FF33", "#3333FF", "#FFFF33",
                "#FF33FF", "#33FFFF", "#FF8800", "#8800FF",
            ]
            label_set = sorted(set(b.label for b in result.boxes))
            colour_map = {
                label: colours[i % len(colours)]
                for i, label in enumerate(label_set)
            }

            for box in result.boxes:
                x1, y1 = box.x, box.y
                x2, y2 = box.x + box.w, box.y + box.h
                colour = colour_map.get(box.label, "#FF3333")
                draw.rectangle([x1, y1, x2, y2], outline=colour, width=3)
                label_text = f"{box.label} {box.confidence:.2f}"
                draw.text((x1 + 2, y1 + 2), label_text, fill=colour)

            # Save
            out_dir = Path("outputs") / "visualizations"
            out_dir.mkdir(parents=True, exist_ok=True)
            filename = f"grounding_{image.image_id[:8]}_{query.replace(' ', '_')[:20]}.png"
            out_path = out_dir / filename
            pil_img.save(str(out_path))
            logger.info(f"Visualization saved to {out_path}")
            return str(out_path)
        except Exception as e:
            logger.warning(f"Failed to generate visualization: {e}")
            return None
