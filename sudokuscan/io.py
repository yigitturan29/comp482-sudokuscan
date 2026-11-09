import json
from pathlib import Path

import cv2
import numpy as np

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}


def read_image(path):
    """Decode without silently rotating EXIF: annotation coordinates use stored pixels."""
    data = np.fromfile(str(path), dtype=np.uint8)
    image = cv2.imdecode(data, cv2.IMREAD_COLOR | cv2.IMREAD_IGNORE_ORIENTATION)
    if image is None or min(image.shape[:2]) < 16:
        raise ValueError(f"Unreadable or too small image: {path}")
    return image


def write_image(path, image):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    ok, data = cv2.imencode(path.suffix, image)
    if not ok:
        raise OSError(f"Cannot encode image: {path}")
    data.tofile(str(path))


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")


def image_paths(folder):
    return sorted(p for p in Path(folder).iterdir() if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS)


def load_annotation(path):
    value = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    corners = np.asarray(value["corners"], dtype=np.float64)
    grid = np.asarray(value["grid"])
    if corners.shape != (4, 2) or not np.isfinite(corners).all():
        raise ValueError("Annotation corners must be four finite [x,y] pairs, TL/TR/BR/BL")
    if grid.shape != (9, 9) or not np.isin(grid, np.arange(10)).all():
        raise ValueError("Annotation grid must contain 9x9 integers in 0..9")
    if not value.get("image"):
        raise ValueError("Annotation image name is missing")
    if not isinstance(value.get("conditions", []), list):
        raise ValueError("conditions must be a list")
    if set(value.get("conditions", [])) - {"C1", "C2", "C3", "C4", "C5"}:
        raise ValueError("Unknown condition label")
    value["corners"] = corners.tolist()
    value["grid"] = grid.astype(int).tolist()
    return value
