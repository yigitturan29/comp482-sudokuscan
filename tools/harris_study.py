"""One-factor-at-a-time Harris parameter measurements (no written conclusions)."""
import argparse
import csv
from dataclasses import replace
from pathlib import Path

import _bootstrap
import cv2
import numpy as np

from student_corner_selection import select_outer_corners
from sudokuscan.config import Config
from sudokuscan.harris import detect_harris, refine_selected, validate_selection
from sudokuscan.io import load_annotation, read_image
from sudokuscan.metrics import corner_error_percent
from sudokuscan.preprocessing import preprocess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--images", type=Path, required=True)
    parser.add_argument("--annotations", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=Path("results/harris_study.csv"))
    parser.add_argument("--upright-only", action="store_true", help="Exclude annotated quarter-turn inputs from detector-only study")
    args = parser.parse_args()
    annotations = sorted(args.annotations.glob("*.json"))
    if args.upright_only:
        annotations = [path for path in annotations if not load_annotation(path).get("normalizing_quarter_turn_clockwise", 0)]
    if len(annotations) < 6:
        parser.error("Parameter study requires at least 6 annotated images")
    base = Config()
    variants = [("baseline", base)]
    for name, values in (("harris_block_fraction", [0.002, 0.004, 0.006]),
                         ("harris_ksize", [5, 7]), ("harris_k", [0.03, 0.05, 0.06]),
                         ("harris_threshold", [0.003, 0.02, 0.05])):
        variants += [(f"{name}={value}", replace(base, **{name: value})) for value in values]
    rows = []
    cv2.setNumThreads(1)
    for annotation_path in annotations:
        annotation = load_annotation(annotation_path)
        image = read_image(args.images / annotation["image"])
        pre = preprocess(image, base)
        for label, config in variants:
            harris = detect_harris(pre, config)
            error, status = None, "not_found"
            try:
                indices = select_outer_corners(pre, harris, config)
                if indices is not None:
                    selected = refine_selected(pre, validate_selection(indices, harris))
                    error = corner_error_percent(selected * pre.scale_xy, annotation["corners"])
                    status = "ok"
            except NotImplementedError as exception:
                parser.exit(1, str(exception) + "\n")
            except Exception as exception:
                status = type(exception).__name__
            rows.append({"image": annotation["image"], "variant": label, "block_size": harris.block_size,
                         "ksize": config.harris_ksize, "k": config.harris_k,
                         "threshold": config.harris_threshold, "candidates": len(harris.candidates),
                         "corner_error_percent": error, "status": status})
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(args.out)


if __name__ == "__main__":
    main()
