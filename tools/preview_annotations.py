"""Run stages 1/3/5/6 using declared manual annotations, bypassing student Stage 2.

Not a grading entry point, not hidden-set evaluation and not a Stage 4 analysis.
No prediction file named *_result.json is produced. Every output is labeled GT.
"""
import argparse
from pathlib import Path
import time

import _bootstrap
import cv2
import numpy as np

from sudokuscan.config import Config
from sudokuscan.debug import draw_debug
from sudokuscan.geometry import estimate_models, rectify
from sudokuscan.harris import detect_harris, draw_harris
from sudokuscan.io import load_annotation, read_image, write_image, write_json
from sudokuscan.metrics import f1, recognition_metrics
from sudokuscan.preprocessing import preprocess
from sudokuscan.recognition import extract_cells, recognize_cells
from sudokuscan.validity import check_validity


def preview(image_path, annotation_path, outdir, config=None, tesseract_cmd=None):
    config = config or Config()
    started = time.perf_counter()
    annotation = load_annotation(annotation_path)
    original = read_image(image_path)
    corners = np.asarray(annotation["corners"], np.float32)
    pre = preprocess(original, config)
    harris = detect_harris(pre, config)
    outdir = Path(outdir) / Path(image_path).stem
    outdir.mkdir(parents=True, exist_ok=True)
    write_image(outdir / "Harris_candidates_only.png", draw_harris(harris))
    labeled = pre.color.copy()
    for label, point in zip(("GT TL", "GT TR", "GT BR", "GT BL"), corners / pre.scale_xy):
        location = tuple(np.rint(point).astype(int))
        cv2.circle(labeled, location, 7, (0, 255, 0), 2)
        cv2.putText(labeled, label, (location[0] + 9, location[1] - 8),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,0,255), 2)
    write_image(outdir / "annotation_review.png", labeled)
    # Corner order is supplied by the annotation, including quarter-turn cases.
    # This bypass is confined to this explicitly named developer tool.
    models = estimate_models(corners, config.target_size)
    rectifications = rectify(original, models, config.target_size)
    for name, image in rectifications.items():
        write_image(outdir / f"GT_rect_{name}.png", image)
    cells = extract_cells(rectifications["H4"], config)
    truth = np.asarray(annotation["grid"], int)
    modes = {}
    for prepared in (False, True):
        mode = "prepared" if prepared else "raw"
        recognition = recognize_cells(cells, config, tesseract_cmd, prepared=prepared)
        scores = recognition_metrics(truth, recognition.grid, recognition.filled_mask)
        verdict, conflicts = check_validity(recognition.grid)
        modes[mode] = {**scores, "empty_cell_f1": f1(scores["empty_counts"]),
                       "filled_cell_f1": f1(scores["filled_counts"]),
                       "grid": recognition.grid.tolist(), "filled_mask": recognition.filled_mask.tolist(),
                       "confidence": recognition.confidence.tolist(), "unread_cells": recognition.unread_cells,
                       "verdict": verdict, "conflicts": conflicts}
        write_image(outdir / f"GT_debug_{mode}.png", draw_debug(rectifications["H4"], recognition, conflicts))
        (outdir / f"GT_grid_{mode}.txt").write_text(
            "\n".join("".join(map(str, row)) for row in recognition.grid) + "\n", encoding="ascii")
        if prepared:
            for cell in cells:
                expected, predicted = int(truth[cell.row,cell.col]), int(recognition.grid[cell.row,cell.col])
                if expected != predicted:
                    label = f"r{cell.row+1}c{cell.col+1}_true{expected}_pred{predicted}"
                    write_image(outdir / "confusions" / f"{label}_raw.png", cell.raw)
                    write_image(outdir / "confusions" / f"{label}_prepared.png", cell.prepared)
    sheet = np.full((9 * 128,9 * 128),255,np.uint8)
    for cell in cells:
        sheet[cell.row*128:(cell.row+1)*128,cell.col*128:(cell.col+1)*128] = cell.prepared
    write_image(outdir / "prepared_cells.png", sheet)
    record = {"image": annotation["image"], "puzzle_id": annotation.get("puzzle_id"),
              "conditions": annotation.get("conditions",[]),
              "kind": "manual_ground_truth_downstream_preview",
              "ground_truth_corners_used": True, "automatic_corner_selection_tested": False,
              "annotation_status": annotation.get("annotation_status", "unknown"),
              "warning": "Do not report these scores as end-to-end detector performance.",
              "harris_candidate_count": len(harris.candidates), "models_from_manual_corners": models,
              "ocr": modes, "runtime_s": round(time.perf_counter()-started,6), "config": config.as_dict()}
    write_json(outdir / "downstream_preview.json", record)
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--images", type=Path, required=True)
    parser.add_argument("--annotations", type=Path, required=True)
    parser.add_argument("--outdir", type=Path, default=Path("results/annotation_preview"))
    parser.add_argument("--tesseract-cmd")
    args = parser.parse_args()
    cv2.setNumThreads(1)
    records = []
    for annotation_path in sorted(args.annotations.glob("*.json")):
        annotation = load_annotation(annotation_path)
        try:
            record = preview(args.images / annotation["image"], annotation_path, args.outdir,
                             tesseract_cmd=args.tesseract_cmd)
            records.append(record)
            print(f"{annotation['image']}: GT raw={record['ocr']['raw']['cell_accuracy']:.3%}; "
                  f"GT prepared={record['ocr']['prepared']['cell_accuracy']:.3%}; "
                  f"{record['runtime_s']:.2f}s", flush=True)
        except Exception as error:
            records.append({"image": annotation["image"], "kind": "preview_error", "error": str(error)})
            print(f"{annotation['image']}: ERROR {error}", flush=True)
    write_json(args.outdir / "summary.json", {"kind": "manual_GT_downstream_only",
               "automatic_corner_selection_tested": False, "images": records})


if __name__ == "__main__":
    main()
