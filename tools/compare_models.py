"""Reproduce Stage 4 measurements on automatic A3/A4/H4 outputs.

Uses annotations solely for recognition/corner evaluation. All transformation
matrices and search guides come from automatic result files.
"""
import argparse
from collections import Counter
import csv
from pathlib import Path
import json
import time

import _bootstrap
import cv2
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from sudokuscan.comparison import draw_measured_lines, measure_grid, obliqueness
from sudokuscan.config import Config
from sudokuscan.io import load_annotation, read_image, write_image, write_json
from sudokuscan.metrics import corner_error_percent, f1, recognition_metrics
from sudokuscan.recognition import recognize


MODELS = ("A3", "A4", "H4")
COLORS = {"A3": "#b94747", "A4": "#c88723", "H4": "#087f8c"}


def compare(annotations, results, outdir, tesseract_cmd=None):
    annotations, results, outdir = Path(annotations), Path(results), Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    cv2.setNumThreads(1)
    rows, samples, failures = [], [], []
    for path in sorted(annotations.glob("*.json")):
        annotation = load_annotation(path)
        stem = Path(annotation["image"]).stem
        started = time.perf_counter()
        try:
            automatic = json.loads((results / f"{stem}_result.json").read_text(encoding="utf-8"))
            if not automatic.get("processing_ok"):
                raise ValueError("No successful automatic result")
            size = round(automatic.get("target_boundary", [0, 450])[-1])
            config = Config(**automatic.get("config", {"target_size": size}))
            if config.target_size != size:
                raise ValueError("Result configuration and target boundary disagree")
            sample = {"image": annotation["image"], "conditions": annotation.get("conditions", []),
                      "obliqueness": obliqueness(automatic["corners"]),
                      "corner_error_percent": corner_error_percent(automatic["corners"], annotation["corners"]),
                      "a3_corner_err_px": automatic["a3_corner_err_px"],
                      "a4_rms_px": automatic["a4_rms_px"],
                      "h4_max_residual_px": automatic["h4_max_residual_px"], "models": {}}
            for model in MODELS:
                image = read_image(results / f"{stem}_rect_{model}.png")
                geometry = measure_grid(image, automatic[model], automatic["H4"])
                recognition = recognize(image, config, tesseract_cmd)
                scores = recognition_metrics(annotation["grid"], recognition.grid, recognition.filled_mask)
                sample["models"][model] = {"geometry": geometry, "ocr": {
                    **scores, "grid": recognition.grid.tolist(), "filled_mask": recognition.filled_mask.tolist(),
                    "unread_cells": recognition.unread_cells,
                    "confidence": recognition.confidence.tolist()}}
                rows.append({"image": annotation["image"], "model": model,
                             "obliqueness": sample["obliqueness"],
                             "a3_corner_err_px": sample["a3_corner_err_px"],
                             "a4_rms_px": sample["a4_rms_px"],
                             **{key: geometry[key] for key in ("lines_found", "lines_missing", "position_mae_px",
                                "penalized_position_mae_px", "spacing_mae_px", "spacing_pairs", "straightness_rms_px")},
                             "cell_accuracy": scores["cell_accuracy"], "grid_exact_match": scores["grid_exact_match"]})
                write_image(outdir / "line_overlays" / f"{stem}_{model}.png", draw_measured_lines(image, geometry))
            sample["runtime_s"] = time.perf_counter() - started
            samples.append(sample)
            write_json(outdir / "per_image" / f"{stem}.json", sample)
            print(f"{stem}: " + "; ".join(f"{model} OCR={sample['models'][model]['ocr']['cell_accuracy']:.2%}, "
                  f"lines={sample['models'][model]['geometry']['lines_found']}/20" for model in MODELS), flush=True)
        except Exception as error:
            # Remove partial rows so a failed image never quietly gets a score
            # based on a subset of models. The failure is retained explicitly.
            rows = [row for row in rows if row["image"] != annotation["image"]]
            failures.append({"image": annotation["image"], "error": str(error)})
            print(f"{stem}: ERROR {error}", flush=True)
    if len(samples) < 8:
        raise ValueError(f"At least eight complete images required; measured {len(samples)}; failures={failures}")
    summaries = {}
    for model in MODELS:
        subset = [row for row in rows if row["model"] == model]
        empty = Counter()
        for sample in samples:
            empty.update(sample["models"][model]["ocr"]["empty_counts"])
        values = {key: float(np.mean([row[key] for row in subset if row[key] is not None]))
                  if any(row[key] is not None for row in subset) else None
                  for key in ("cell_accuracy", "lines_found", "position_mae_px", "penalized_position_mae_px",
                              "spacing_mae_px", "straightness_rms_px")}
        summaries[model] = {"images": len(subset), **values,
                            "grid_exact_match": float(np.mean([row["grid_exact_match"] for row in subset])),
                            "empty_cell_f1": f1(empty),
                            "missing_lines_total": sum(row["lines_missing"] for row in subset)}
    most = max(samples, key=lambda sample: sample["obliqueness"])
    most_stem = Path(most["image"]).stem
    panel = np.full((size + 65, size * 3, 3), 255, np.uint8)
    for index, model in enumerate(MODELS):
        image = read_image(results / f"{most_stem}_rect_{model}.png")
        panel[65:, index*size:(index+1)*size] = image
        accuracy = most["models"][model]["ocr"]["cell_accuracy"]
        cv2.putText(panel, f"{model}: OCR {accuracy:.1%}", (index*size+12, 25),
                    cv2.FONT_HERSHEY_SIMPLEX, .65, (30, 30, 30), 1, cv2.LINE_AA)
        cv2.putText(panel, f"{most_stem}, obliqueness={most['obliqueness']:.3f}", (index*size+12, 51),
                    cv2.FONT_HERSHEY_SIMPLEX, .43, (60, 60, 60), 1, cv2.LINE_AA)
    write_image(outdir / "most_oblique.png", panel)
    _plots(rows, samples, outdir)
    with (outdir / "per_image.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)
    report = {"images": len(samples), "failures": failures, "summary": summaries,
              "most_oblique_image": most["image"], "most_oblique_score": most["obliqueness"],
              "obliqueness_definition": "max(top/bottom,bottom/top,left/right,right/left)-1",
              "notes": ["Same ten supplied development images; no held-out or hidden-set claim.",
                        "Matrices and line guides are automatic; annotations are only evaluation references.",
                        "Each model runs identical OCR configuration, without a wall-time cutoff in this offline study.",
                        "Missing lines are not imputed; a separate penalized score charges 50 px per missing line.",
                        "Both affine and projective maps preserve straight lines; position/spacing need not agree."]}
    write_json(outdir / "summary.json", report)
    print(json.dumps(report, indent=2), flush=True)
    return report


def _plots(rows, samples, outdir):
    samples = sorted(samples, key=lambda row: row["obliqueness"])
    plt.rcParams.update({"font.size":8,"axes.labelsize":8,"legend.fontsize":7})
    fig, ax = plt.subplots(figsize=(3.35, 2.15), layout="constrained")
    x = [sample["obliqueness"] for sample in samples]
    for key, name in (("a3_corner_err_px", "A3 BR residual"), ("a4_rms_px", "A4 RMS residual")):
        ax.plot(x, [sample[key] for sample in samples], "o-", label=name, linewidth=1.2, markersize=3)
    ax.set(xlabel="Opposite-side ratio minus one", ylabel="Corner residual (px)")
    ax.legend(frameon=False, fontsize=8)
    fig.savefig(outdir / "corner_residuals.pdf"); plt.close(fig)
    fig, axes = plt.subplots(1, 2, figsize=(6.8, 2.3), layout="constrained")
    for model in MODELS:
        subset = sorted((row for row in rows if row["model"] == model), key=lambda row: row["obliqueness"])
        x = [row["obliqueness"] for row in subset]
        axes[0].plot(x, [row["penalized_position_mae_px"] for row in subset], "o-", label=model, color=COLORS[model], markersize=3)
        axes[1].plot(x, [100*row["cell_accuracy"] for row in subset], "o-", label=model, color=COLORS[model], markersize=3)
    axes[0].set(ylabel="Position MAE + missing penalty (px)")
    axes[1].set(ylabel="Cell accuracy (%)", ylim=(0, 105))
    for ax in axes:
        ax.set_xlabel("Opposite-side ratio minus one"); ax.legend(frameon=False, fontsize=8)
    fig.savefig(outdir / "grid_and_ocr.pdf"); plt.close(fig)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--annotations", type=Path, required=True)
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--outdir", type=Path, default=Path("results/model_comparison"))
    parser.add_argument("--tesseract-cmd")
    args = parser.parse_args()
    compare(args.annotations, args.results, args.outdir, args.tesseract_cmd)
