"""Working downstream demo using declared synthetic ground-truth corners.

This does NOT implement or demonstrate automatic outer-corner selection.
It never writes grader-format prediction files for the synthetic photograph.
"""
import argparse
from pathlib import Path
import time

import _bootstrap
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from sudokuscan.config import Config
from sudokuscan.debug import draw_debug
from sudokuscan.geometry import estimate_models, rectify
from sudokuscan.harris import detect_harris, draw_harris
from sudokuscan.io import write_image, write_json
from sudokuscan.metrics import f1, recognition_metrics
from sudokuscan.preprocessing import preprocess
from sudokuscan.recognition import extract_cells, find_tesseract, recognize_cells
from sudokuscan.validity import check_validity

GRID = np.array([
    [5,3,0,0,7,0,0,0,0], [6,0,0,1,9,5,0,0,0], [0,9,8,0,0,0,0,6,0],
    [8,0,0,0,6,0,0,0,3], [4,0,0,8,0,3,0,0,1], [7,0,0,0,2,0,0,0,6],
    [0,6,0,0,0,0,2,8,0], [0,0,0,4,1,9,0,0,5], [0,0,0,0,8,0,0,7,9],
], dtype=int)


def render_grid(grid=GRID, size=900):
    image = Image.new("RGB", (size + 1, size + 1), "white")
    draw = ImageDraw.Draw(image)
    step = size // 9
    choices = ["C:/Windows/Fonts/arial.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]
    font = None
    for path in choices:
        if Path(path).exists():
            font = ImageFont.truetype(path, round(step * 0.58))
            break
    if font is None:
        font = ImageFont.load_default(size=round(step * 0.58))
    for index in range(10):
        width = 6 if index % 3 == 0 else 2
        draw.line((0, index * step, size, index * step), fill="black", width=width)
        draw.line((index * step, 0, index * step, size), fill="black", width=width)
    for row in range(9):
        for col in range(9):
            if grid[row, col]:
                draw.text(((col + 0.5) * step, (row + 0.5) * step), str(grid[row, col]),
                          fill="black", font=font, anchor="mm")
    return cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)


def synthetic_fixture():
    puzzle = render_grid()
    source = np.array([[0, 0], [900, 0], [900, 900], [0, 900]], np.float32)
    # Test fixture geometry, NOT an automatic detector or personal photograph.
    corners = np.array([[200, 110], [1130, 215], [1000, 1080], [280, 960]], np.float32)
    matrix = cv2.getPerspectiveTransform(source, corners)
    photo = cv2.warpPerspective(puzzle, matrix, (1400, 1200), borderValue=(218, 224, 230))
    cv2.putText(photo, "SYNTHETIC TEST - NOT PERSONAL DATA", (20, 1170),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (50, 50, 50), 2)
    return photo, corners


def run_demo(outdir, tesseract_cmd=None):
    started = time.perf_counter()
    cv2.setNumThreads(1)
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    config = Config()
    image, corners = synthetic_fixture()
    write_image(outdir / "synthetic_photo.png", image)
    write_json(outdir / "synthetic_annotation.json", {"image": "synthetic_photo.png", "conditions": [],
               "corners": corners.tolist(), "grid": GRID.tolist(), "synthetic": True})
    pre = preprocess(image, config)
    harris = detect_harris(pre, config)
    write_image(outdir / "harris_candidates_only.png", draw_harris(harris))
    models = estimate_models(corners)
    images = rectify(image, models)
    for name, rectified in images.items():
        write_image(outdir / f"known_GT_rect_{name}.png", rectified)
    # A labeled montage supports visual QA only; it is not the student's Stage 4 analysis.
    panels = []
    for name in ("A3", "A4", "H4"):
        panel = cv2.copyMakeBorder(images[name], 40, 0, 0, 0, cv2.BORDER_CONSTANT, value=(255, 255, 255))
        cv2.putText(panel, f"{name} - synthetic known corners", (12, 27), cv2.FONT_HERSHEY_SIMPLEX,
                    0.65, (30, 30, 30), 1)
        panels.append(panel)
    write_image(outdir / "rectification_montage.png", np.hstack(panels))
    cells = extract_cells(images["H4"], config)
    prepared_sheet = np.full((9 * 128, 9 * 128), 255, np.uint8)
    for cell in cells:
        prepared_sheet[cell.row * 128:(cell.row + 1) * 128, cell.col * 128:(cell.col + 1) * 128] = cell.prepared
    write_image(outdir / "prepared_cells.png", prepared_sheet)
    result = {"kind": "synthetic_downstream_test", "automatic_corner_selection": False,
              "warning": "Known synthetic ground-truth corners bypass Stage 2. Not a personal-data result.",
              "harris_candidate_count": len(harris.candidates), **models}
    try:
        result["tesseract_executable"] = find_tesseract(tesseract_cmd)
        recognition = recognize_cells(cells, config, tesseract_cmd)
        raw_recognition = recognize_cells(cells, config, tesseract_cmd, prepared=False)
        verdict, conflicts = check_validity(recognition.grid)
        result.update(ocr_tested=True, grid=recognition.grid.tolist(), verdict=verdict,
                      unread_cells=recognition.unread_cells,
                      prepared_metrics=recognition_metrics(GRID, recognition.grid, recognition.filled_mask),
                      raw_metrics=recognition_metrics(GRID, raw_recognition.grid, raw_recognition.filled_mask))
        result["prepared_metrics"]["empty_cell_f1"] = f1(result["prepared_metrics"]["empty_counts"])
        write_image(outdir / "known_GT_debug.png", draw_debug(images["H4"], recognition, conflicts))
        (outdir / "known_GT_grid.txt").write_text(
            "\n".join("".join(map(str, row)) for row in recognition.grid) + "\n", encoding="ascii")
    except (RuntimeError, ImportError) as error:
        result.update(ocr_tested=False, ocr_error=str(error))
    result["runtime_s"] = round(time.perf_counter() - started, 4)
    write_json(outdir / "demo_summary.json", result)
    print(f"Synthetic downstream demo: {outdir}")
    print(f"Harris candidates: {len(harris.candidates)}; automatic corner selection: NOT IMPLEMENTED")
    if result.get("ocr_tested"):
        print(f"Prepared cell accuracy: {result['prepared_metrics']['cell_accuracy']:.3%}")
        print(f"Raw cell accuracy: {result['raw_metrics']['cell_accuracy']:.3%}")
    else:
        print("OCR could not be run:", result.get("ocr_error"))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--outdir", type=Path, default=Path("results/demo"))
    parser.add_argument("--tesseract-cmd")
    args = parser.parse_args()
    run_demo(args.outdir, args.tesseract_cmd)


if __name__ == "__main__":
    main()
