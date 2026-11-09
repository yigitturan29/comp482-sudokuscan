"""Offline measurements of actual grid-line pixels in A3/A4/H4 images.

Canonical grid lines transferred through the detected models provide search
guides, never measured answers. Every accepted line needs visible image ink.
Missing/clipped lines remain missing instead of being replaced by guide points.
This module is independent of the timed recognition entry point.
"""
import cv2
import numpy as np

from .geometry import transform_points, validate_quad


def obliqueness(corners):
    """Opposite-side length ratio minus one; a proxy, not a camera angle."""
    quad = validate_quad(corners).astype(float)
    lengths = np.linalg.norm(np.roll(quad, -1, axis=0) - quad, axis=1)
    ratios = [max(lengths[a], lengths[b]) / min(lengths[a], lengths[b])
              for a, b in ((0, 2), (1, 3))]
    return float(max(ratios) - 1.0)


def _homogeneous(matrix):
    matrix = np.asarray(matrix, dtype=float)
    if matrix.shape == (2, 3):
        matrix = np.vstack([matrix, [0, 0, 1]])
    if matrix.shape != (3, 3) or not np.isfinite(matrix).all():
        raise ValueError("Expected a finite affine or projective matrix")
    return matrix


def _measure_line(ink, endpoints, direction, index, size):
    cell = size / 9.0
    ideal = index * cell
    vector = endpoints[1] - endpoints[0]
    length = np.linalg.norm(vector)
    record = {"index": index, "ideal_position_px": ideal, "found": False,
              "position_error_px": None, "straightness_rms_px": None,
              "center_position_px": None, "points": [], "guide": endpoints.tolist()}
    if length < 5:
        return record
    normal = np.array([-vector[1], vector[0]]) / length
    # Ignore the perpendicular line intersections so they cannot supply the ink
    # evidence for an otherwise absent line. The same rule is used for all models.
    t = np.linspace(0.012, 0.988, 180)
    distance_to_intersection = np.abs(t[:, None] - np.linspace(0, 1, 10)).min(axis=1)
    t = t[distance_to_intersection > 0.012]
    centers = endpoints[0] + t[:, None] * vector
    offsets = np.linspace(-0.22 * cell, 0.22 * cell, 45)
    locations = centers[None, :, :] + offsets[:, None, None] * normal
    valid = ((locations[:, :, 0] >= 0) & (locations[:, :, 0] <= size - 1)
             & (locations[:, :, 1] >= 0) & (locations[:, :, 1] <= size - 1))
    response = cv2.remap(ink, locations[:, :, 0].astype(np.float32),
                         locations[:, :, 1].astype(np.float32), cv2.INTER_LINEAR,
                         borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    counts = valid.sum(axis=1)
    means = (response * valid).sum(axis=1) / np.maximum(counts, 1)
    means[counts < 24] = 0
    best = int(np.argmax(means))
    record["guide_search_mean_ink"] = float(means[best])
    if means[best] < 0.035:
        return record
    # Search locally around the strongest continuous parallel response. A digit
    # outside this strip cannot pull an individual sample onto a glyph stroke.
    local = np.abs(offsets - offsets[best]) <= cell * 0.075
    weights = np.where(valid & local[:, None], response, -1)
    chosen = weights.argmax(axis=0)
    strengths = weights[chosen, np.arange(len(t))]
    points = locations[chosen, np.arange(len(t))]
    keep = strengths >= max(0.04, float(means[best]) * 0.30)
    points = points[keep]
    if len(points) < 24:
        return record
    vx, vy, x0, y0 = cv2.fitLine(points.astype(np.float32), cv2.DIST_HUBER,
                                0, 0.01, 0.01).ravel().astype(float)
    residual = (points - [x0, y0]) @ np.array([-vy, vx])
    # Remove isolated glyph/shadow-edge outliers, retaining pixel-level bends.
    points = points[np.abs(residual) <= cell * 0.12]
    if len(points) < 24:
        return record
    vx, vy, x0, y0 = cv2.fitLine(points.astype(np.float32), cv2.DIST_L2,
                                0, 0.01, 0.01).ravel().astype(float)
    residual = (points - [x0, y0]) @ np.array([-vy, vx])
    variable_axis = 0 if direction == "horizontal" else 1
    coordinate_axis = 1 - variable_axis
    span = float(np.ptp(points[:, variable_axis]))
    if span < size * 0.25:
        return record
    middle = (size - 1) / 2
    if direction == "horizontal":
        if abs(vx) < 1e-6:
            return record
        center_position = y0 + (middle - x0) * vy / vx
    else:
        if abs(vy) < 1e-6:
            return record
        center_position = x0 + (middle - y0) * vx / vy
    record.update(found=True, points=points.tolist(),
                  position_error_px=float(np.mean(np.abs(points[:, coordinate_axis] - ideal))),
                  straightness_rms_px=float(np.sqrt(np.mean(residual ** 2))),
                  center_position_px=float(center_position),
                  fitted_line=[vx, vy, x0, y0], visible_span_px=span)
    return record


def measure_grid(rectified, model, homography):
    """Attempt all 20 lines and measure spacing, location and straightness.

    Search radius is 0.22 cell. Position error is the mean absolute distance of
    observed line pixels from x/y=0,50,...,450. Spacing uses adjacent detected
    line intersections with the image midline. Missing lines are counted; an
    additional position score charges one cell width per missing line.
    """
    gray = cv2.cvtColor(rectified, cv2.COLOR_BGR2GRAY) if rectified.ndim == 3 else rectified
    if gray.ndim != 2 or gray.shape[0] != gray.shape[1] or gray.shape[0] < 90:
        raise ValueError("Expected a square rectified grid of at least 90 pixels")
    size = gray.shape[0]
    cell = size / 9.0
    kernel = max(3, round(cell * 0.26) | 1)
    background = cv2.morphologyEx(gray, cv2.MORPH_CLOSE,
                                  cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel, kernel)))
    normalized = cv2.divide(gray, np.maximum(background, 1), scale=255)
    ink = (255 - normalized).astype(np.float32) / 255.0
    transfer = _homogeneous(model) @ np.linalg.inv(_homogeneous(homography))
    families = {}
    for direction in ("horizontal", "vertical"):
        lines = []
        for index in range(10):
            p = index * cell
            canonical = [[0, p], [size, p]] if direction == "horizontal" else [[p, 0], [p, size]]
            guides = transform_points(canonical, transfer)
            lines.append(_measure_line(ink, guides, direction, index, size))
        adjacent = [abs((b["center_position_px"] - a["center_position_px"]) - cell)
                    for a, b in zip(lines[:-1], lines[1:]) if a["found"] and b["found"]]
        families[direction] = {"lines": lines, "found": sum(row["found"] for row in lines),
                               "spacing_errors_px": adjacent,
                               "spacing_pairs": len(adjacent)}
    found = [line for family in families.values() for line in family["lines"] if line["found"]]
    spacing = [error for family in families.values() for error in family["spacing_errors_px"]]
    missing = 20 - len(found)
    return {**families, "lines_found": len(found), "lines_missing": missing,
            "position_mae_px": float(np.mean([line["position_error_px"] for line in found])) if found else None,
            "penalized_position_mae_px": float((sum(line["position_error_px"] for line in found) + missing * cell) / 20),
            "straightness_rms_px": float(np.mean([line["straightness_rms_px"] for line in found])) if found else None,
            "spacing_mae_px": float(np.mean(spacing)) if spacing else None,
            "spacing_pairs": len(spacing),
            "missing_line_penalty_px": cell,
            "method": "pixel-supported tracing around model-transferred guides; missing lines not imputed"}


def draw_measured_lines(rectified, measurement):
    overlay = rectified.copy()
    if overlay.ndim == 2:
        overlay = cv2.cvtColor(overlay, cv2.COLOR_GRAY2BGR)
    for direction, color in (("horizontal", (70, 180, 40)), ("vertical", (230, 120, 0))):
        for record in measurement[direction]["lines"]:
            if not record["found"]:
                continue
            points = np.rint(record["points"]).astype(np.int32)
            cv2.polylines(overlay, [points], False, color, 1, cv2.LINE_AA)
            point = tuple(points[len(points) // 2])
            cv2.putText(overlay, f"{direction[0]}{record['index']}", point,
                        cv2.FONT_HERSHEY_SIMPLEX, .32, (0, 0, 200), 1, cv2.LINE_AA)
    return overlay
