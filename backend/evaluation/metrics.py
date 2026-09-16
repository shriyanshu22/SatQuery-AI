"""Metrics for evaluating remote sensing analysis capabilities."""

from __future__ import annotations

import numpy as np


class MetricSuite:
    """Collection of evaluation metrics for remote sensing analysis."""

    @staticmethod
    def vqa_accuracy(predictions: list[str], ground_truth: list[str]) -> float:
        """Exact-match accuracy for VQA."""
        if not predictions or len(predictions) != len(ground_truth):
            return 0.0
        matches = sum(1 for p, g in zip(predictions, ground_truth) if p == g)
        return matches / len(predictions)

    @staticmethod
    def vqa_accuracy_relaxed(predictions: list[str], ground_truth: list[str]) -> float:
        """Relaxed accuracy — case-insensitive, stripped."""
        if not predictions or len(predictions) != len(ground_truth):
            return 0.0
        matches = sum(
            1 for p, g in zip(predictions, ground_truth)
            if p.strip().lower() == g.strip().lower()
        )
        return matches / len(predictions)

    @staticmethod
    def compute_iou_single(box_a: dict, box_b: dict) -> float:
        """Compute IoU between two bounding boxes.
        
        Boxes are dicts with keys: 'xmin', 'ymin', 'xmax', 'ymax'.
        """
        x_left = max(box_a['xmin'], box_b['xmin'])
        y_top = max(box_a['ymin'], box_b['ymin'])
        x_right = min(box_a['xmax'], box_b['xmax'])
        y_bottom = min(box_a['ymax'], box_b['ymax'])

        if x_right < x_left or y_bottom < y_top:
            return 0.0

        intersection_area = (x_right - x_left) * (y_bottom - y_top)
        
        box_a_area = (box_a['xmax'] - box_a['xmin']) * (box_a['ymax'] - box_a['ymin'])
        box_b_area = (box_b['xmax'] - box_b['xmin']) * (box_b['ymax'] - box_b['ymin'])
        
        union_area = box_a_area + box_b_area - intersection_area
        
        return intersection_area / union_area if union_area > 0 else 0.0

    @staticmethod
    def grounding_iou(pred_boxes: list[dict], gt_boxes: list[dict]) -> float:
        """Mean Intersection over Union for bounding boxes."""
        if not pred_boxes or not gt_boxes or len(pred_boxes) != len(gt_boxes):
            return 0.0
        ious = [MetricSuite.compute_iou_single(p, g) for p, g in zip(pred_boxes, gt_boxes)]
        return sum(ious) / len(ious)

    @staticmethod
    def grounding_precision_at_iou(pred_boxes: list[dict], gt_boxes: list[dict], iou_threshold: float = 0.5) -> float:
        """Precision at IoU threshold."""
        if not pred_boxes or len(pred_boxes) != len(gt_boxes):
            return 0.0
        matches = sum(
            1 for p, g in zip(pred_boxes, gt_boxes)
            if MetricSuite.compute_iou_single(p, g) >= iou_threshold
        )
        return matches / len(pred_boxes)

    @staticmethod
    def change_detection_f1(pred_mask: np.ndarray, gt_mask: np.ndarray) -> float:
        """F1 score for binary change detection."""
        p, r = MetricSuite.change_detection_precision_recall(pred_mask, gt_mask)
        if p + r == 0:
            return 0.0
        return 2 * (p * r) / (p + r)

    @staticmethod
    def change_detection_iou(pred_mask: np.ndarray, gt_mask: np.ndarray) -> float:
        """IoU for change detection masks."""
        intersection = np.logical_and(pred_mask, gt_mask).sum()
        union = np.logical_or(pred_mask, gt_mask).sum()
        if union == 0:
            return 1.0 if intersection == 0 else 0.0
        return intersection / union

    @staticmethod
    def change_detection_precision_recall(pred_mask: np.ndarray, gt_mask: np.ndarray) -> tuple[float, float]:
        """Precision and recall for change detection."""
        true_positives = np.logical_and(pred_mask, gt_mask).sum()
        predicted_positives = pred_mask.sum()
        actual_positives = gt_mask.sum()
        
        precision = true_positives / predicted_positives if predicted_positives > 0 else 0.0
        recall = true_positives / actual_positives if actual_positives > 0 else 0.0
        
        return float(precision), float(recall)

    @staticmethod
    def routing_accuracy(predicted_intents: list[str], ground_truth_intents: list[str]) -> float:
        """Accuracy of intent classification."""
        return MetricSuite.vqa_accuracy(predicted_intents, ground_truth_intents)

    @staticmethod
    def routing_confusion_matrix(predicted: list[str], ground_truth: list[str]) -> dict:
        """Confusion matrix for routing."""
        matrix = {}
        for p, g in zip(predicted, ground_truth):
            if g not in matrix:
                matrix[g] = {}
            if p not in matrix[g]:
                matrix[g][p] = 0
            matrix[g][p] += 1
        return matrix
