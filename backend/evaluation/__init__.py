"""Evaluation framework and metrics for SatQuery AI."""

from __future__ import annotations

from .metrics import MetricSuite
from .benchmark import BenchmarkRunner, BenchmarkResult, ComparisonReport

__all__ = [
    "MetricSuite",
    "BenchmarkRunner",
    "BenchmarkResult",
    "ComparisonReport",
]
