from dataclasses import dataclass

import cv2
import numpy as np

from .config import Config


def odd_kernel(length, fraction, minimum=3):
    maximum = length if length % 2 else length - 1
    result = max(minimum, int(round(length * fraction)) | 1)
    return min(result, maximum)


@dataclass
class Preprocessed:
    color: np.ndarray
    gray: np.ndarray
    normalized: np.ndarray
    ink: np.ndarray
    scale_xy: np.ndarray  # original pixels / working pixels, separately per axis


def preprocess(image, config: Config):
    height, width = image.shape[:2]
    scale = min(1.0, config.detection_max_side / max(height, width))
    work = cv2.resize(image, (max(16, round(width * scale)), max(16, round(height * scale))),
                      interpolation=cv2.INTER_AREA) if scale < 1 else image.copy()
    gray = cv2.cvtColor(work, cv2.COLOR_BGR2GRAY)
    reference = min(gray.shape)
    gray = cv2.GaussianBlur(gray, (odd_kernel(reference, config.blur_fraction),) * 2, 0)
    background = cv2.GaussianBlur(gray, (odd_kernel(reference, config.illumination_fraction),) * 2, 0)
    # Division compensates for slowly varying illumination; it is not histogram equalization.
    normalized = cv2.divide(gray, np.maximum(background, 1), scale=230)
    ink = cv2.adaptiveThreshold(normalized, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                               cv2.THRESH_BINARY_INV,
                               odd_kernel(reference, config.adaptive_fraction), config.adaptive_c)
    return Preprocessed(work, gray, normalized, ink,
                        np.array([width / work.shape[1], height / work.shape[0]], dtype=np.float64))
