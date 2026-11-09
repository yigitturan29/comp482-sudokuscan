from pathlib import Path
import sys

import cv2
import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

from demo import synthetic_fixture
from sudokuscan.comparison import measure_grid, obliqueness
from sudokuscan.geometry import estimate_models, rectify


def test_obliqueness_is_scale_and_rotation_invariant():
    quad = np.array([[0, 0], [100, 0], [80, 100], [20, 100]], float)
    angle = .37
    rotation = np.array([[np.cos(angle), -np.sin(angle)], [np.sin(angle), np.cos(angle)]])
    assert obliqueness(quad) == pytest.approx(2 / 3)
    assert obliqueness(quad @ rotation.T * 3 + [120, 85]) == pytest.approx(2 / 3, abs=1e-6)
    assert obliqueness([[0, 0], [100, 20], [120, 120], [20, 100]]) == pytest.approx(0)


def test_twenty_real_lines_are_measured_at_the_correct_spacing():
    image = np.full((450, 450, 3), 255, np.uint8)
    for location in range(0, 451, 50):
        p = min(location, 449)
        cv2.line(image, (0, p), (449, p), (0, 0, 0), 2)
        cv2.line(image, (p, 0), (p, 449), (0, 0, 0), 2)
    result = measure_grid(image, np.eye(3), np.eye(3))
    assert result["lines_found"] == 20
    assert result["spacing_pairs"] == 18
    assert result["position_mae_px"] < 2.5
    assert result["spacing_mae_px"] < 1.5
    assert result["straightness_rms_px"] < .8
    assert all(len(result[direction]["lines"]) == 10 for direction in ("horizontal", "vertical"))


def test_guides_cannot_invent_lines_in_blank_image():
    result = measure_grid(np.full((450, 450, 3), 255, np.uint8), np.eye(3), np.eye(3))
    assert result["lines_found"] == 0
    assert result["lines_missing"] == 20
    assert result["position_mae_px"] is None
    assert result["spacing_mae_px"] is None
    assert result["penalized_position_mae_px"] == 50
    assert all(not line["points"] for family in ("horizontal", "vertical") for line in result[family]["lines"])


def test_perspective_spacing_distortion_is_measured_from_image_pixels():
    image, corners = synthetic_fixture()
    models = estimate_models(corners)
    rectified = rectify(image, models)
    scores = {name: measure_grid(value, models[name], models["H4"]) for name, value in rectified.items()}
    assert scores["H4"]["lines_found"] == 20
    assert scores["H4"]["position_mae_px"] < 3
    assert scores["A3"]["penalized_position_mae_px"] > scores["H4"]["penalized_position_mae_px"] + 5
    assert scores["A4"]["penalized_position_mae_px"] > scores["H4"]["penalized_position_mae_px"] + 3


def test_non_square_rectification_is_rejected():
    with pytest.raises(ValueError):
        measure_grid(np.full((450, 300), 255, np.uint8), np.eye(3), np.eye(3))
