from pathlib import Path
import time

import cv2
import numpy as np

from .config import Config
from .debug import draw_debug
from .geometry import estimate_models, rectify, validate_quad
from .harris import detect_harris, draw_harris, refine_selected, validate_selection
from .io import read_image, write_image, write_json
from .preprocessing import preprocess
from .recognition import recognize
from .validity import check_validity


class PuzzleNotFoundError(RuntimeError):
    pass


def scan_image(path, outdir, config=None, tesseract_cmd=None):
    """Automatic grader path: never consumes annotations or manual coordinates."""
    from student_corner_selection import select_outer_corners
    config = config or Config()
    started = time.perf_counter()
    path, outdir = Path(path), Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    base = outdir / path.stem
    result_path = outdir / f"{path.stem}_result.json"
    # Remove only this input's previous generated outputs, so an unsuccessful rerun
    # cannot leave apparently current grid/rectification files from an earlier run.
    for suffix in ("_grid.txt", "_harris.png", "_debug.png", "_rect_A3.png", "_rect_A4.png", "_rect_H4.png"):
        stale = Path(str(base) + suffix)
        if stale.is_file():
            stale.unlink()
    result = {"image": path.name, "conditions": [], "corners": [], "grid": [],
              "A3": None, "A4": None, "H4": None,
              "a3_corner_err_px": None, "a4_rms_px": None,
              "verdict": "not_found", "processing_ok": False}
    try:
        image = read_image(path)
        pre = preprocess(image, config)
        harris = detect_harris(pre, config)
        write_image(str(base) + "_harris.png", draw_harris(harris))
        result["harris"] = {"candidate_count": len(harris.candidates), "block_size": harris.block_size,
                            "ksize": config.harris_ksize, "k": config.harris_k,
                            "threshold": config.harris_threshold, "working_size": list(pre.gray.shape[::-1])}
        if len(harris.candidates) < 4:
            raise PuzzleNotFoundError("Fewer than four Harris candidates")
        indices = select_outer_corners(pre, harris, config)
        if indices is None:
            result["error_code"] = "puzzle_not_found"
        else:
            initial = validate_selection(indices, harris)
            selected = refine_selected(pre, initial)
            corners = validate_quad(selected * pre.scale_xy)
            result["corners"] = corners.astype(float).tolist()
            result["harris_candidate_indices"] = np.asarray(indices).astype(int).tolist()
            result["harris_selected_before_refinement"] = (initial * pre.scale_xy).astype(float).tolist()
            write_image(str(base) + "_harris.png", draw_harris(harris, selected))
            models = estimate_models(corners, config.target_size)
            result.update(models)
            images = rectify(image, models, config.target_size)
            for name, rectified in images.items():
                write_image(str(base) + f"_rect_{name}.png", rectified)
            recognition = recognize(images["H4"], config, tesseract_cmd,
                                    deadline=started + config.image_budget_s)
            verdict, conflicts = check_validity(recognition.grid)
            result.update(grid=recognition.grid.tolist(), verdict=verdict, conflicts=conflicts,
                          filled_mask=recognition.filled_mask.tolist(), ocr_confidence=recognition.confidence.tolist(),
                          unread_cells=recognition.unread_cells, processing_ok=True)
            if recognition.unread_cells:
                result["warnings"] = ["Filled cells without a recognized digit are written as 0; see unread_cells."]
            Path(str(base) + "_grid.txt").write_text(
                "\n".join("".join(str(int(x)) for x in row) for row in recognition.grid) + "\n", encoding="ascii")
            write_image(str(base) + "_debug.png", draw_debug(images["H4"], recognition, conflicts))
    except PuzzleNotFoundError as error:
        result.update(error_code="puzzle_not_found", error=str(error))
    except NotImplementedError as error:
        result.update(error_code="student_stage2_required", error=str(error))
    except Exception as error:
        # One bad image must not stop a grader batch. Preserve the cause rather
        # than labeling an OCR installation problem as an ordinary detection miss.
        result.update(verdict="not_found", processing_ok=False,
                      error_code=type(error).__name__, error=str(error))
    result["runtime_s"] = round(time.perf_counter() - started, 6)
    result["within_time_limit"] = result["runtime_s"] <= 20.0
    result["config"] = config.as_dict()
    write_json(result_path, result)
    return result
