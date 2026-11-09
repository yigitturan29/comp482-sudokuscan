import json
from pathlib import Path
import sys
import subprocess

import cv2
import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

from demo import GRID, render_grid, synthetic_fixture
from student_corner_selection import select_outer_corners
from evaluate import evaluate
from sudokuscan.config import Config
from sudokuscan.geometry import estimate_models, rectify, transform_points
from sudokuscan.harris import detect_harris, validate_selection
from sudokuscan.io import read_image, write_image, write_json
from sudokuscan.metrics import binary_counts, corner_error_percent, f1
from sudokuscan.pipeline import scan_image
from sudokuscan.preprocessing import preprocess
from sudokuscan.recognition import Cell, extract_cells, find_tesseract, recognize_cells
from sudokuscan.validity import check_validity


def test_projective_models_and_true_four_point_least_squares():
    corners = np.array([[120, 80], [810, 140], [730, 840], [210, 720]], np.float32)
    target = np.array([[0, 0], [450, 0], [450, 450], [0, 450]])
    models = estimate_models(corners)
    assert np.max(np.linalg.norm(transform_points(corners, models["H4"]) - target, axis=1)) < 1e-6
    assert np.max(np.abs(transform_points(corners[[0, 1, 3]], models["A3"]) - target[[0, 1, 3]])) < 1e-6
    assert models["a3_corner_err_px"] > 10
    design = np.column_stack([corners, np.ones(4)])
    residual = transform_points(corners, models["A4"]) - target
    assert np.allclose(design.T @ residual, 0, atol=1e-6)  # LS normal-equation orthogonality
    assert models["a4_rms_px"] > 0


def test_affine_parallelogram_and_raster_boundary():
    corners = np.array([[100, 80], [600, 100], [650, 620], [150, 600]], np.float32)
    models = estimate_models(corners)
    assert models["a3_corner_err_px"] < 1e-6
    assert models["a4_rms_px"] < 1e-6
    assert models["target_boundary"] == [0, 450]
    for image in rectify(np.full((800, 800, 3), 255, np.uint8), models).values():
        assert image.shape == (450, 450, 3)


def test_original_coordinate_scale_and_harris_provenance():
    image = np.full((1600, 2401, 3), 255, np.uint8)
    cv2.rectangle(image, (200, 150), (1900, 1400), (0, 0, 0), 12)
    pre = preprocess(image, Config())
    assert pre.color.shape[1] == 1400
    assert pre.scale_xy[0] == 2401 / pre.color.shape[1]
    assert pre.scale_xy[1] == 1600 / pre.color.shape[0]
    result = detect_harris(pre, Config())
    assert len(result.candidates) >= 4
    assert all(result.response[round(y), round(x)] > 0 for x, y in result.candidates)
    with pytest.raises(ValueError):
        validate_selection(np.array([[0.0, 0.0]] * 4), result)
    with pytest.raises(ValueError):
        validate_selection([0, 0, 1, 2], result)


def test_blank_image_has_no_harris_candidates_or_filled_cells():
    image = np.full((450, 450, 3), 255, np.uint8)
    assert len(detect_harris(preprocess(image, Config()), Config()).candidates) == 0
    assert not any(cell.filled for cell in extract_cells(image, Config()))


def test_blank_input_is_a_controlled_not_found(tmp_path):
    path = tmp_path / "blank.png"
    write_image(path, np.full((450, 450, 3), 255, np.uint8))
    result = scan_image(path, tmp_path / "out")
    assert result["verdict"] == "not_found"
    assert result["error_code"] == "puzzle_not_found"
    assert result["runtime_s"] <= 20


def test_cli_controlled_not_found_is_a_completed_batch(tmp_path):
    images = tmp_path / "images"
    images.mkdir()
    for name in ("one.png", "two.png"):
        write_image(images / name, np.full((300, 300, 3), 255, np.uint8))
    output = tmp_path / "out"
    run = subprocess.run([sys.executable, str(ROOT / "sudoku_scan.py"), "--batch", str(images),
                          "--outdir", str(output)], capture_output=True, text=True, timeout=30)
    assert run.returncode == 0, run.stderr
    assert len(list(output.glob("*_result.json"))) == 2
    assert all(json.loads(path.read_text())["verdict"] == "not_found" for path in output.glob("*_result.json"))


def test_cli_attempts_later_images_after_a_decode_error(tmp_path):
    images = tmp_path / "images"
    images.mkdir()
    (images / "a_bad.png").write_bytes(b"not an image")
    write_image(images / "b_blank.png", np.full((300, 300, 3), 255, np.uint8))
    output = tmp_path / "out"
    run = subprocess.run([sys.executable, str(ROOT / "sudoku_scan.py"), "--batch", str(images),
                          "--outdir", str(output)], capture_output=True, text=True, timeout=30)
    assert run.returncode == 1
    assert json.loads((output / "a_bad_result.json").read_text())["error_code"] == "ValueError"
    assert json.loads((output / "b_blank_result.json").read_text())["error_code"] == "puzzle_not_found"


def test_empty_detection_and_cell_preparation_on_clean_fixture():
    image = cv2.resize(render_grid(), (451, 451), interpolation=cv2.INTER_AREA)[:450, :450]
    cells = extract_cells(image, Config())
    detected = np.array([cell.filled for cell in cells]).reshape(9, 9)
    assert np.array_equal(detected, GRID != 0)
    assert all(cell.prepared.shape == (128, 128) for cell in cells)
    assert all(np.all(cell.prepared[:10] == 255) for cell in cells)


def test_filled_detection_survives_a_realistic_cast_shadow():
    image = cv2.resize(render_grid(), (451, 451), interpolation=cv2.INTER_AREA)[:450, :450]
    shadowed = image.copy()
    shadowed[:, :225] = np.rint(shadowed[:, :225].astype(float) * 0.35).astype(np.uint8)
    cells = extract_cells(shadowed, Config())
    predicted = np.array([cell.filled for cell in cells]).reshape(9,9)
    assert np.array_equal(predicted, GRID != 0)
    # The unprepared arm must retain the original intensity for a fair ablation.
    assert cells[0].raw.mean() < cells[8].raw.mean() / 2


@pytest.mark.parametrize("positions", [[(0, 0), (0, 8)], [(0, 0), (8, 0)], [(0, 0), (2, 2)]])
def test_row_column_and_box_conflicts(positions):
    grid = np.zeros((9, 9), int)
    for row, col in positions:
        grid[row, col] = 5
    verdict, conflicts = check_validity(grid)
    assert verdict == "invalid"
    assert {tuple(p) for p in conflicts} == set(positions)


def test_zeros_are_not_conflicts_and_known_puzzle_is_valid():
    assert check_validity(np.zeros((9, 9), int)) == ("valid", [])
    assert check_validity(GRID) == ("valid", [])


def test_metrics_definitions():
    counts = binary_counts([True, True, False, False], [True, False, True, False])
    assert counts == {"tp": 1, "fp": 1, "fn": 1}
    assert f1(counts) == 0.5
    true = np.array([[0, 0], [100, 0], [100, 100], [0, 100]])
    assert corner_error_percent(true + [3, 4], true) == pytest.approx(5.0)


def test_failure_outputs_do_not_crash_or_reuse_stale_outputs(tmp_path):
    image = tmp_path / "bad.png"
    image.write_bytes(b"not an image")
    output = tmp_path / "out"
    output.mkdir()
    (output / "bad_grid.txt").write_text("stale")
    result = scan_image(image, output)
    assert result["verdict"] == "not_found"
    assert result["error_code"] == "ValueError"
    assert not (output / "bad_grid.txt").exists()
    assert json.loads((output / "bad_result.json").read_text())["verdict"] == "not_found"


def test_automatic_selection_uses_harris_points_and_rejects_a_plain_rectangle():
    image, truth = synthetic_fixture()
    pre = preprocess(image, Config())
    harris = detect_harris(pre, Config())
    indices = select_outer_corners(pre, harris, Config())
    assert indices is not None
    predicted = validate_selection(indices,harris) * pre.scale_xy
    assert corner_error_percent(predicted,truth) < 2.0
    rectangle = np.full((700,900,3),255,np.uint8)
    cv2.rectangle(rectangle,(80,70),(800,630),(0,0,0),4)
    pre = preprocess(rectangle,Config())
    assert select_outer_corners(pre,detect_harris(pre,Config()),Config()) is None


def test_larger_background_rectangle_does_not_win_over_grid():
    image, truth = synthetic_fixture()
    canvas = np.full((1200,1800,3),245,np.uint8)
    canvas[:,:1400]=image
    cv2.rectangle(canvas,(1430,40),(1770,1150),(0,0,0),8)
    pre=preprocess(canvas,Config())
    harris=detect_harris(pre,Config())
    indices=select_outer_corners(pre,harris,Config())
    assert indices is not None
    assert corner_error_percent(harris.candidates[indices]*pre.scale_xy,truth) < 2.0


def test_automatic_pipeline_writes_required_files(tmp_path):
    try:
        find_tesseract()
        import pytesseract
    except (RuntimeError, ImportError):
        pytest.skip("Tesseract OCR not installed")
    path = tmp_path / "fixture.png"
    image, truth = synthetic_fixture()
    write_image(path, image)
    result = scan_image(path, tmp_path / "out")
    assert result["processing_ok"]
    assert corner_error_percent(result["corners"],truth) < 2.0
    assert len(set(result["harris_candidate_indices"])) == 4
    assert result["corner_selection"]["corner_source"] == "Harris candidate indices"
    assert (tmp_path / "out" / "fixture_harris.png").exists()
    for model in ("A3","A4","H4"):
        assert read_image(tmp_path / "out" / f"fixture_rect_{model}.png").shape[:2] == (450,450)
    lines=(tmp_path / "out" / "fixture_grid.txt").read_text().splitlines()
    assert len(lines)==9 and all(len(line)==9 and line.isdigit() for line in lines)


def test_unicode_image_paths(tmp_path):
    path = tmp_path / "çalışma_öğrenci.png"
    image = np.full((30, 40, 3), 192, np.uint8)
    write_image(path, image)
    assert np.array_equal(read_image(path), image)


def test_quarter_turn_orientation_is_chosen_from_ocr(tmp_path):
    try:
        find_tesseract()
        import pytesseract
    except (RuntimeError, ImportError):
        pytest.skip("Tesseract OCR not installed")
    image, truth = synthetic_fixture()
    rotated = cv2.rotate(image,cv2.ROTATE_90_CLOCKWISE)
    expected_corners = np.column_stack([image.shape[0]-1-truth[:,1],truth[:,0]])
    path=tmp_path / "rotated.png"
    write_image(path,rotated)
    result=scan_image(path,tmp_path / "out")
    assert result["processing_ok"]
    assert corner_error_percent(result["corners"],expected_corners) < 2.0
    assert np.mean(np.asarray(result["grid"])==GRID) >= .95


def test_missing_results_get_no_free_empty_cell_accuracy(tmp_path):
    annotations = tmp_path / "annotations"
    annotations.mkdir()
    write_json(annotations / "a.json", {"image": "a.jpg", "conditions": ["C1"],
               "corners": [[0, 0], [100, 0], [100, 100], [0, 100]], "grid": GRID.tolist()})
    report = evaluate(annotations, tmp_path / "missing")
    assert report["overall"]["cell_accuracy"] == 0
    assert report["overall"]["empty_cell_f1"] == 0
    assert report["overall"]["corner_images_missing"] == 1
    assert np.array(report["confusion_matrix"])[:, 10].sum() == 81


def test_tesseract_multipage_ocr_mapping():
    try:
        find_tesseract()
        import pytesseract
    except (RuntimeError, ImportError):
        pytest.skip("Tesseract OCR not installed")
    cells = extract_cells(cv2.resize(render_grid(), (451, 451))[:450, :450], Config())
    result = recognize_cells(cells, Config())
    assert np.mean(result.grid == GRID) >= 0.95
    assert np.array_equal(result.filled_mask, GRID != 0)


def test_tesseract_blank_page_does_not_shift_following_page():
    try:
        find_tesseract()
        import pytesseract
    except (RuntimeError, ImportError):
        pytest.skip("Tesseract OCR not installed")
    cells = extract_cells(cv2.resize(render_grid(), (451, 451))[:450, :450], Config())
    filled = [cell for cell in cells if cell.filled]
    # Deliberate OCR failure on a page after the explicit filled/empty decision.
    # This verifies TSV page numbering rather than merely counting output words.
    first = filled[0]
    first.prepared[:] = 255
    result = recognize_cells(cells, Config())
    assert result.grid[first.row, first.col] == 0
    second = filled[1]
    assert result.grid[second.row, second.col] == GRID[second.row, second.col]
    assert [first.row, first.col] in result.unread_cells
