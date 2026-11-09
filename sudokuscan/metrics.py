"""Section 7 metric definitions; no Stage 4 interpretation or conclusions."""
import numpy as np


def binary_counts(truth_positive, predicted_positive):
    truth_positive, predicted_positive = np.asarray(truth_positive, bool), np.asarray(predicted_positive, bool)
    return {"tp": int(np.sum(truth_positive & predicted_positive)),
            "fp": int(np.sum(~truth_positive & predicted_positive)),
            "fn": int(np.sum(truth_positive & ~predicted_positive))}


def f1(counts):
    denominator = 2 * counts["tp"] + counts["fp"] + counts["fn"]
    return 2 * counts["tp"] / denominator if denominator else 1.0


def corner_error_percent(predicted, truth):
    truth, predicted = np.asarray(truth, float), np.asarray(predicted, float)
    side = float(np.mean(np.linalg.norm(np.roll(truth, -1, axis=0) - truth, axis=1)))
    if predicted.shape != (4, 2) or not np.isfinite(predicted).all() or side <= 0:
        return None
    return float(100 * np.mean(np.linalg.norm(predicted - truth, axis=1)) / side)


def recognition_metrics(truth, predicted, filled_mask=None):
    truth, predicted = np.asarray(truth, int), np.asarray(predicted, int)
    if truth.shape != (9, 9) or predicted.shape != (9, 9):
        raise ValueError("Expected two 9x9 grids")
    filled = np.asarray(filled_mask, bool) if filled_mask is not None else predicted != 0
    return {"cell_accuracy": float(np.mean(truth == predicted)),
            "grid_exact_match": bool(np.array_equal(truth, predicted)),
            "empty_counts": binary_counts(truth == 0, ~filled),
            "filled_counts": binary_counts(truth != 0, filled)}
