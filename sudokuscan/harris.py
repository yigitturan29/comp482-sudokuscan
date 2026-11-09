from dataclasses import dataclass

import cv2
import numpy as np

from .config import Config
from .preprocessing import Preprocessed


@dataclass
class HarrisResult:
    response: np.ndarray
    candidates: np.ndarray
    scores: np.ndarray
    block_size: int
    nms_radius: int
    selection_debug: dict | None = None


def detect_harris(pre: Preprocessed, config: Config):
    """Harris response and discrete candidates only; no outer-corner selection."""
    reference = min(pre.gray.shape)
    block = max(2, round(reference * config.harris_block_fraction))
    radius = max(2, round(reference * config.nms_fraction))
    response = cv2.cornerHarris(pre.normalized.astype(np.float32) / 255.0,
                                block, config.harris_ksize, config.harris_k)
    peak = float(response.max())
    if peak <= 0:
        return HarrisResult(response, np.empty((0, 2), np.float32), np.empty(0), block, radius)
    local_max = cv2.dilate(response, np.ones((2 * radius + 1, 2 * radius + 1), np.uint8))
    maxima = (response >= local_max - peak * 1e-7) & (response > peak * config.harris_threshold)
    # Merge flat local-max plateaus; keep the strongest actual response pixel in each plateau.
    count, labels, stats, _ = cv2.connectedComponentsWithStats(maxima.astype(np.uint8), 8)
    points, scores = [], []
    for label in range(1, count):
        x, y, width, height = stats[label, :4]
        region = response[y:y + height, x:x + width]
        masked = np.where(labels[y:y + height, x:x + width] == label, region, -np.inf)
        dy, dx = np.unravel_index(np.argmax(masked), masked.shape)
        points.append([x + dx, y + dy])
        scores.append(float(region[dy, dx]))
    if not points:
        return HarrisResult(response, np.empty((0, 2), np.float32), np.empty(0), block, radius)
    points, scores = np.asarray(points, np.float32), np.asarray(scores)
    # Explicit radius suppression also handles equal-valued, separated maxima.
    kept = []
    for index in np.argsort(-scores, kind="stable"):
        if not kept or np.min(np.linalg.norm(points[kept] - points[index], axis=1)) > radius:
            kept.append(int(index))
        if len(kept) == config.max_candidates:
            break
    return HarrisResult(response, points[kept], scores[kept], block, radius)


def validate_selection(indices, harris: HarrisResult):
    """Validate a student rule's provenance: it must return indices into Harris candidates."""
    values = np.asarray(indices)
    if values.shape != (4,) or not np.issubdtype(values.dtype, np.integer):
        raise ValueError("select_outer_corners must return four integer indices in TL,TR,BR,BL order")
    if len(set(values.tolist())) != 4 or np.any(values < 0) or np.any(values >= len(harris.candidates)):
        raise ValueError("Corner indices must be distinct and inside the Harris candidate array")
    return harris.candidates[values].copy()


def refine_selected(pre, selected):
    radius = max(2, round(min(pre.gray.shape) * 0.004))
    height, width = pre.gray.shape
    points = selected.astype(np.float32).reshape(-1, 1, 2)
    if ((points[:, 0, 0] < radius + 1) | (points[:, 0, 0] >= width - radius - 1) |
        (points[:, 0, 1] < radius + 1) | (points[:, 0, 1] >= height - radius - 1)).any():
        return selected
    refined = cv2.cornerSubPix(pre.normalized, points.copy(), (radius, radius), (-1, -1),
                               (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_MAX_ITER, 40, 0.01))[:, 0]
    # A refinement is local; reject a jump to a different physical feature.
    moved = np.linalg.norm(refined - selected, axis=1) <= radius
    return np.where(moved[:, None], refined, selected)


def draw_harris(harris, selected=None):
    positive = np.maximum(harris.response, 0)
    maximum = float(positive.max())
    display = (np.sqrt(positive / maximum) * 255).astype(np.uint8) if maximum else np.zeros_like(positive, np.uint8)
    display = cv2.applyColorMap(display, cv2.COLORMAP_TURBO)
    for point in harris.candidates:
        cv2.circle(display, tuple(np.rint(point).astype(int)), 2, (255, 255, 255), 1)
    if selected is not None:
        for name, point in zip(("TL", "TR", "BR", "BL"), selected):
            position = tuple(np.rint(point).astype(int))
            cv2.circle(display, position, 7, (0, 255, 0), 2)
            cv2.putText(display, name, (position[0] + 8, position[1]), cv2.FONT_HERSHEY_SIMPLEX,
                        0.55, (0, 255, 0), 2)
    return display
