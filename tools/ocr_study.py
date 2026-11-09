"""Stage 5 raw/prepared and PSM measurements on AUTOMATIC H4 outputs only."""
import argparse
from collections import Counter
from dataclasses import replace
from pathlib import Path

import _bootstrap
import numpy as np

from sudokuscan.config import Config
from sudokuscan.io import load_annotation, read_image, write_image, write_json
from sudokuscan.metrics import f1, recognition_metrics
from sudokuscan.recognition import extract_cells, recognize_cells


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--annotations", type=Path, required=True)
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--outdir", type=Path, default=Path("results/ocr_study"))
    parser.add_argument("--tesseract-cmd")
    args = parser.parse_args()
    measurements, confusions, missing = [], Counter(), []
    for annotation_path in sorted(args.annotations.glob("*.json")):
        annotation = load_annotation(annotation_path)
        stem = Path(annotation["image"]).stem
        rectified_path = args.results / f"{stem}_rect_H4.png"
        if not rectified_path.exists():
            missing.append(annotation["image"])
            continue
        image = read_image(rectified_path)
        cells = extract_cells(image, Config())
        truth = np.asarray(annotation["grid"])
        for psm in (7, 8, 10, 13):
            for prepared in (False, True):
                config = replace(Config(), ocr_psm=psm)
                recognition = recognize_cells(cells, config, args.tesseract_cmd, prepared=prepared)
                scores = recognition_metrics(truth, recognition.grid, recognition.filled_mask)
                measurements.append({"image": annotation["image"], "psm": psm, "prepared": prepared,
                                     "grid": recognition.grid.tolist(), **scores,
                                     "empty_cell_f1": f1(scores["empty_counts"])})
                if psm == 10 and prepared:
                    for cell in cells:
                        true, predicted = int(truth[cell.row, cell.col]), int(recognition.grid[cell.row, cell.col])
                        if true != predicted:
                            key = f"{true}->{predicted}"
                            confusions[key] += 1
                            filename = f"{stem}_r{cell.row + 1}c{cell.col + 1}_true{true}_pred{predicted}"
                            write_image(args.outdir / "confusions" / f"{filename}_raw.png", cell.raw)
                            write_image(args.outdir / "confusions" / f"{filename}_prepared.png", cell.prepared)
        print(stem)
    write_json(args.outdir / "measurements.json", {"measurements": measurements,
                "common_confusions": confusions.most_common(), "missing_H4_images": missing,
                "note": "Missing detections are excluded from this OCR-only study; evaluate.py includes failures."})


if __name__ == "__main__":
    main()
