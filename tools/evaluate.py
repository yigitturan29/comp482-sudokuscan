"""Evaluate automatic result files against annotations, including failed images."""
import argparse
from collections import Counter
import json
from pathlib import Path

import _bootstrap
import numpy as np

from sudokuscan.io import load_annotation, write_json
from sudokuscan.metrics import corner_error_percent, f1, recognition_metrics


def evaluate(annotations_dir, results_dir):
    samples = []
    confusion = np.zeros((10, 11), dtype=int)  # column 10 means failed/missing output
    for annotation_path in sorted(Path(annotations_dir).glob("*.json")):
        annotation = load_annotation(annotation_path)
        result_path = Path(results_dir) / f"{Path(annotation['image']).stem}_result.json"
        try:
            result = json.loads(result_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            result = {}
        truth = np.asarray(annotation["grid"], int)
        predicted = np.asarray(result.get("grid", []))
        success = (result.get("processing_ok", False) and predicted.shape == (9, 9)
                   and np.isin(predicted, np.arange(10)).all())
        if success:
            scores = recognition_metrics(truth, predicted, result.get("filled_mask"))
            for true, pred in zip(truth.ravel(), predicted.astype(int).ravel()):
                confusion[true, pred] += 1
        else:
            # A failed image does not get free accuracy for its empty cells.
            scores = {"cell_accuracy": 0.0, "grid_exact_match": False,
                      "empty_counts": {"tp": 0, "fp": 0, "fn": int(np.sum(truth == 0))},
                      "filled_counts": {"tp": 0, "fp": 0, "fn": int(np.sum(truth != 0))}}
            for true in truth.ravel():
                confusion[true, 10] += 1
        runtime = result.get("runtime_s")
        healthy = (isinstance(runtime, (int, float)) and 0 <= runtime <= 20 and
                   (success or result.get("error_code") == "puzzle_not_found"))
        samples.append({"image": annotation["image"], "conditions": annotation.get("conditions", []),
                        **scores, "processed": bool(success), "robust": bool(healthy), "runtime_s": runtime,
                        "corner_error_percent": corner_error_percent(result.get("corners", []), annotation["corners"]),
                        "error": result.get("error", result.get("error_code"))})
    if not samples:
        raise ValueError("No annotations found")

    def aggregate(rows):
        if not rows:
            return {"images": 0}
        empty, filled = Counter(), Counter()
        for row in rows:
            empty.update(row["empty_counts"])
            filled.update(row["filled_counts"])
        corners = [row["corner_error_percent"] for row in rows if row["corner_error_percent"] is not None]
        return {"images": len(rows), "cell_accuracy": float(np.mean([r["cell_accuracy"] for r in rows])),
                "empty_cell_f1": f1(empty), "filled_cell_f1": f1(filled),
                "grid_exact_match": float(np.mean([r["grid_exact_match"] for r in rows])),
                "robustness": float(np.mean([r["robust"] for r in rows])),
                "processing_success": float(np.mean([r["processed"] for r in rows])),
                "corner_error_percent": float(np.mean(corners)) if corners else None,
                "corner_images_scored": len(corners), "corner_images_missing": len(rows) - len(corners)}

    return {"overall": aggregate(samples),
            "by_condition": {condition: aggregate([r for r in samples if condition in r["conditions"]])
                             for condition in ("C1", "C2", "C3", "C4", "C5")},
            "confusion_labels_true": list(range(10)), "confusion_labels_pred": list(range(10)) + ["failed"],
            "confusion_matrix": confusion.tolist(), "samples": samples,
            "notes": ["Empty-cell F1 treats empty as positive; filled-cell F1 is also reported to remove ambiguity.",
                      "Failed/missing images receive zero cell accuracy; corner error is undefined and counted separately.",
                      "Robustness counts completed recognition or a controlled no-puzzle result within 20 seconds."]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--annotations", type=Path, required=True)
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("results/metrics.json"))
    args = parser.parse_args()
    report = evaluate(args.annotations, args.results)
    write_json(args.output, report)
    print(json.dumps(report["overall"], indent=2))


if __name__ == "__main__":
    main()
