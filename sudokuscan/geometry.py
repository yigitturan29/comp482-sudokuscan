import cv2
import numpy as np


def validate_quad(corners):
    points = np.asarray(corners, np.float32)
    if points.shape != (4, 2) or not np.isfinite(points).all():
        raise ValueError("Four finite corner coordinates are required")
    if not cv2.isContourConvex(points.reshape(-1, 1, 2)) or cv2.contourArea(points) < 25:
        raise ValueError("Corners must form a non-degenerate convex quadrilateral in TL,TR,BR,BL order")
    return points


def transform_points(points, matrix):
    points = np.asarray(points, np.float64)
    homogeneous = np.column_stack([points, np.ones(len(points))]) @ np.asarray(matrix).T
    if homogeneous.shape[1] == 3:
        if np.any(np.abs(homogeneous[:, 2]) < 1e-12):
            raise ValueError("Point maps to infinity")
        homogeneous = homogeneous[:, :2] / homogeneous[:, 2:3]
    return homogeneous


def estimate_models(corners, size=450):
    source = validate_quad(corners)
    # The PDF explicitly measures BR against (450,450). Use continuous boundary
    # coordinates [0,size], although raster sample centres run from 0 to size-1.
    target = np.array([[0, 0], [size, 0], [size, size], [0, size]], np.float32)
    A3 = cv2.getAffineTransform(source[[0, 1, 3]], target[[0, 1, 3]])
    # estimateAffine2D normally performs robust fitting and can drop the fourth
    # point. A very large threshold includes all four; then solve the full LS
    # system explicitly to guarantee the assignment's all-point LS objective.
    initial, inliers = cv2.estimateAffine2D(source, target, method=cv2.RANSAC,
                                          ransacReprojThreshold=float(size * 1e6),
                                          maxIters=100, confidence=0.99, refineIters=10)
    if initial is None or inliers is None or not np.all(inliers):
        raise ValueError("Four-point affine estimation failed")
    design = np.column_stack([source.astype(np.float64), np.ones(4)])
    A4 = np.linalg.lstsq(design, target.astype(np.float64), rcond=None)[0].T
    H4 = cv2.getPerspectiveTransform(source, target)
    br = transform_points(source[[2]], A3)[0]
    return {
        "A3": A3.tolist(), "A4": A4.tolist(), "H4": H4.tolist(),
        "a3_br_target": br.tolist(),
        "a3_corner_err_px": float(np.linalg.norm(br - target[2])),
        "a4_rms_px": float(np.sqrt(np.mean(np.sum((transform_points(source, A4) - target) ** 2, axis=1)))),
        "h4_max_residual_px": float(np.max(np.linalg.norm(transform_points(source, H4) - target, axis=1))),
        "target_boundary": [0, size],
    }


def rectify(image, models, size=450):
    output = {}
    for name in ("A3", "A4", "H4"):
        warp = cv2.warpPerspective if name == "H4" else cv2.warpAffine
        output[name] = warp(image, np.asarray(models[name]), (size, size),
                            flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_CONSTANT,
                            borderValue=(255, 255, 255))
    return output
