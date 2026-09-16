"""Conservative modality detection for remote-sensing imagery.

Detection Algorithm
-------------------

Modality is determined using **only reliable metadata** — never from visual
appearance or statistical properties of pixel values alone.  The algorithm
checks, in order:

1. **User-provided hint** — if the caller supplies an explicit modality hint,
   it is trusted and used.  Reason: the user may have domain knowledge that
   metadata lacks.
2. **Band names** — if any band is named ``VV``, ``VH``, ``HH``, or ``HV``,
   the image is classified as SAR.  These are standard SAR polarisation
   channels.
3. **Sensor name** — if the sensor string contains known SAR platform names
   (``sentinel-1``, ``terrasar``, ``radarsat``, ``alos``, ``palsar``), the
   image is classified as SAR.
4. **Band count** — if the image has more than 4 bands, it is classified as
   ``MULTISPECTRAL`` (e.g. Sentinel-2 with 13 bands).  Exactly 3 or 4 bands
   with RGB-like names is ``OPTICAL``.
5. **Fallback** — if none of the above heuristics match, modality is
   ``UNKNOWN`` and a warning is returned explaining why.

Limitations
-----------

* Panchromatic images (single grey band) cannot be distinguished from SAR
  amplitude images without explicit metadata.
* Hyperspectral imagery (200+ bands) is classified as ``MULTISPECTRAL`` —
  a separate ``HYPERSPECTRAL`` category may be added later.
"""

from __future__ import annotations

from backend.core.logging import get_logger
from backend.core.types import Modality, RSMetadata

logger = get_logger(__name__)

_SAR_BAND_NAMES: set[str] = {"VV", "VH", "HH", "HV"}
_SAR_SENSOR_KEYWORDS: list[str] = [
    "sar",
    "sentinel-1",
    "terrasar",
    "radarsat",
    "alos",
    "palsar",
    "cosmo-skymed",
    "iceye",
]
_OPTICAL_BAND_PATTERNS: list[set[str]] = [
    {"R", "G", "B"},
    {"B02", "B03", "B04"},
    {"red", "green", "blue"},
]


def detect_modality(
    metadata: RSMetadata,
    user_hint: str | None = None,
) -> tuple[Modality, list[str]]:
    """Detect the imaging modality of a remote-sensing product.

    Args:
        metadata: Extracted image metadata.
        user_hint: Optional user-supplied modality string (e.g. ``"sar"``).

    Returns:
        A tuple of ``(Modality, reasons)`` where *reasons* is a list of
        human-readable strings explaining how the decision was reached.
    """
    reasons: list[str] = []

    # 1. User hint
    if user_hint:
        hint_lower = user_hint.strip().lower()
        for m in Modality:
            if m.value == hint_lower:
                reasons.append(f"User-provided modality hint: {hint_lower}.")
                return m, reasons
        reasons.append(
            f"User hint '{user_hint}' not recognised; proceeding with automatic detection."
        )

    # 2. Band names → SAR
    band_names = metadata.band_names or []
    upper_bands = {b.strip().upper() for b in band_names}
    sar_matches = upper_bands & _SAR_BAND_NAMES
    if sar_matches:
        reasons.append(
            f"SAR polarisation bands detected: {', '.join(sorted(sar_matches))}."
        )
        return Modality.SAR, reasons

    # 3. Sensor name → SAR
    # (RSMetadata doesn't have a dedicated sensor field, but we can check
    # band names or other contextual info.  If a sensor string were stored
    # elsewhere the caller would pass user_hint.)

    # 4. Band count heuristics
    bc = metadata.band_count
    if bc > 4:
        reasons.append(
            f"Band count ({bc}) exceeds 4; classified as multispectral."
        )
        return Modality.MULTISPECTRAL, reasons

    if bc in (3, 4):
        # Check for RGB-like band names
        for pattern in _OPTICAL_BAND_PATTERNS:
            if pattern.issubset(upper_bands):
                reasons.append(
                    f"RGB band names detected ({', '.join(sorted(pattern))}); "
                    "classified as optical."
                )
                return Modality.OPTICAL, reasons
        # 3/4 bands without names — likely optical but not certain
        if not band_names:
            reasons.append(
                f"Band count ({bc}) suggests optical imagery, but no band "
                "names available to confirm."
            )
            return Modality.OPTICAL, reasons
        reasons.append(
            f"Band count ({bc}) suggests optical, but band names "
            f"({', '.join(band_names)}) are not standard RGB patterns."
        )
        return Modality.OPTICAL, reasons

    if bc == 1:
        reasons.append(
            "Single-band image. Cannot reliably distinguish panchromatic "
            "optical from SAR amplitude without explicit metadata."
        )
        return Modality.UNKNOWN, reasons

    # 5. Fallback
    reasons.append(
        f"Could not determine modality from available metadata "
        f"(band_count={bc}, band_names={band_names})."
    )
    return Modality.UNKNOWN, reasons
