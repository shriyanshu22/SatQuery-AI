from __future__ import annotations

import os
from typing import Any
import numpy as np
from PIL import Image

from backend.core.protocols import VLMProtocol, ModelInfo, VLMResult
from backend.core.confidence import ConfidenceScore
from backend.core.evidence import Evidence, MetadataEvidence
from backend.core.logging import get_logger

logger = get_logger(__name__)

# Try importing transformers dependencies, but don't fail at import time
# so that the class can be mocked or instantiated without loading PyTorch
try:
    import torch
    from transformers import Qwen2_5_VLForConditionalGeneration, AutoProcessor, BitsAndBytesConfig
    from qwen_vl_utils import process_vision_info
    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False


class QwenVLM(VLMProtocol):
    """
    Qwen2.5-VL-3B-Instruct VLM implementation.
    Loads lazily in INT4 format to conserve VRAM (~4-5GB).
    """

    def __init__(self, model_id: str = "Qwen/Qwen2.5-VL-3B-Instruct"):
        self.model_id = model_id
        self._model = None
        self._processor = None
        self._device_map = "auto"

    def _load_model(self) -> None:
        if not HAS_TRANSFORMERS:
            raise RuntimeError("transformers, torch, and qwen_vl_utils are required for QwenVLM.")
        
        if self._model is not None:
            return

        logger.info(f"Loading {self.model_id} lazily in INT4 precision...")
        
        # Suppress symlink warning
        os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
        
        quantization_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_quant_type="nf4"
        )
        
        self._processor = AutoProcessor.from_pretrained(self.model_id)
        
        self._model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
            self.model_id,
            device_map=self._device_map,
            quantization_config=quantization_config,
            torch_dtype=torch.float16
        )
        
        logger.info(f"Model {self.model_id} loaded successfully.")

    def is_loaded(self) -> bool:
        """Check if the model is currently loaded in memory."""
        return self._model is not None

    def get_model_info(self) -> ModelInfo:
        """Get metadata about this model."""
        device = None
        if self._model is not None and hasattr(self._model, "device"):
            device = str(self._model.device)
            
        return ModelInfo(
            name=self.model_id,
            version="2.5",
            backend_type="transformers_int4",
            description="Qwen2.5-VL-3B-Instruct VLM for remote sensing VQA.",
            device=device,
            parameters=3_000_000_000
        )

    def predict(self, image: np.ndarray, prompt: str, **kwargs: Any) -> VLMResult:
        """Run VLM inference on an image and prompt."""
        self._load_model()
        
        if not HAS_TRANSFORMERS:
            raise RuntimeError("Transformers is not installed.")

        # Convert numpy array (e.g. from RSDataObject) to PIL Image
        # Assuming the image is RGB or RGBA uint8
        if image.dtype != np.uint8:
            # Normalize to 0-255 if it's float
            if image.max() <= 1.0:
                img_array = (image * 255).astype(np.uint8)
            else:
                img_array = image.astype(np.uint8)
        else:
            img_array = image

        pil_image = Image.fromarray(img_array)
        
        # Prepare conversational format for Qwen2.5-VL
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "image": pil_image
                    },
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            }
        ]
        
        text_prompt = self._processor.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        
        image_inputs, video_inputs = process_vision_info(messages)
        
        inputs = self._processor(
            text=[text_prompt],
            images=image_inputs,
            videos=video_inputs,
            padding=True,
            return_tensors="pt",
        )
        inputs = inputs.to(self._model.device)
        
        # Generate output
        with torch.no_grad():
            generated_ids = self._model.generate(**inputs, max_new_tokens=kwargs.get("max_tokens", 256))
            
        # Extract only the generated part
        generated_ids_trimmed = [
            out_ids[len(in_ids):] for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
        ]
        
        output_text = self._processor.batch_decode(
            generated_ids_trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False
        )[0]
        
        # Fallback confidence score since text generation models don't easily provide confidence
        conf = ConfidenceScore(
            value=0.8, 
            source="qwen_vl", 
            method="heuristic"
        )
        
        # Generate metadata evidence
        evidence_list = [
            MetadataEvidence(
                source_file="inference",
                crs=None,
                resolution=None,
                bounds=None,
                band_count=img_array.shape[-1] if len(img_array.shape) > 2 else 1,
                acquisition_date=None
            )
        ]
        
        return VLMResult(
            answer=output_text.strip(),
            evidence=evidence_list,
            confidence=conf,
            raw_output={"full_response": output_text}
        )
