from dataclasses import dataclass, replace
import os
from pathlib import Path
import shutil
import tempfile
import time

import cv2
import numpy as np
from PIL import Image

from .config import Config


@dataclass
class Cell:
    row: int
    col: int
    raw: np.ndarray
    prepared: np.ndarray
    filled: bool
    ink_fraction: float
    component_area: int


@dataclass
class Recognition:
    grid: np.ndarray
    confidence: np.ndarray
    filled_mask: np.ndarray
    cells: list
    unread_cells: list


def find_tesseract(explicit=None):
    options = [explicit, os.environ.get("TESSERACT_CMD"), shutil.which("tesseract"),
               r"C:\Program Files\Tesseract-OCR\tesseract.exe",
               str(Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Tesseract-OCR" / "tesseract.exe"),
               str(Path.home() / "AppData" / "Local" / "Programs" / "Tesseract-OCR" / "tesseract.exe"),
               str(Path(__file__).resolve().parents[1] / ".tools" / "Tesseract-OCR" / "tesseract.exe")]
    for option in options:
        if option and Path(option).is_file():
            return str(Path(option).resolve())
    raise RuntimeError("Tesseract not installed. See README.md; set TESSERACT_CMD or --tesseract-cmd.")


def extract_cells(rectified, config: Config):
    gray = cv2.cvtColor(rectified, cv2.COLOR_BGR2GRAY) if rectified.ndim == 3 else rectified
    size = gray.shape[0]
    if gray.shape != (config.target_size, config.target_size):
        raise ValueError("Expected a square rectification matching target_size")
    cell_size = size // 9
    margin = round(cell_size * config.cell_margin)
    # Closing fills narrow dark strokes while retaining a wider shadow field.
    # Normalize the full rectification, avoiding artificial cell-edge backgrounds.
    kernel_size = max(3, round(cell_size * config.cell_background_fraction) | 1)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
    background = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, kernel)
    normalized = cv2.divide(gray, np.maximum(background, 1), scale=255)
    normalized[normalized > config.cell_max_ink_gray] = 255
    cells = []
    for row in range(9):
        for col in range(9):
            crop = gray[row * cell_size + margin:(row + 1) * cell_size - margin,
                        col * cell_size + margin:(col + 1) * cell_size - margin].copy()
            normalized_crop = normalized[row * cell_size + margin:(row + 1) * cell_size - margin,
                                         col * cell_size + margin:(col + 1) * cell_size - margin]
            if int(normalized_crop.max()) - int(normalized_crop.min()) < 15:
                mask = np.zeros_like(crop)
            else:
                _, mask = cv2.threshold(normalized_crop, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)
            count, labels, stats, _ = cv2.connectedComponentsWithStats(mask, 8)
            accepted = []
            for index in range(1, count):
                x, y, width, height, area = stats[index]
                # Explicit border-remnant removal; a clipped glyph is reported
                # as a failure rather than inferred from Sudoku constraints.
                touches = x == 0 or y == 0 or x + width >= crop.shape[1] or y + height >= crop.shape[0]
                if (not touches and area >= crop.size * config.component_area_fraction
                        and height >= crop.shape[0] * config.component_height_fraction):
                    accepted.append(index)
            label = max(accepted, key=lambda index: stats[index, cv2.CC_STAT_AREA]) if accepted else None
            prepared = np.full((128, 128), 255, np.uint8)
            area = 0
            if label is not None:
                x, y, width, height, area = stats[label]
                # Keep anti-aliased grayscale edges. Hard thresholding followed
                # by nearest-neighbour enlargement damaged OCR in the smoke test.
                # A one-pixel support halo removes other ink without clipping the
                # selected digit's soft edges; two pixels of crop halo retain it.
                support = cv2.dilate((labels == label).astype(np.uint8), np.ones((3, 3), np.uint8))
                cleaned = np.where(support, normalized_crop, 255).astype(np.uint8)
                x0, y0 = max(0, x - 2), max(0, y - 2)
                x1, y1 = min(crop.shape[1], x + width + 2), min(crop.shape[0], y + height + 2)
                glyph = cleaned[y0:y1, x0:x1]
                scale = min(1.0, 40 / max(glyph.shape))
                if scale < 1:
                    glyph = cv2.resize(glyph, (max(1, round(glyph.shape[1] * scale)),
                                              max(1, round(glyph.shape[0] * scale))), interpolation=cv2.INTER_AREA)
                top, left = (128 - glyph.shape[0]) // 2, (128 - glyph.shape[1]) // 2
                prepared[top:top + glyph.shape[0], left:left + glyph.shape[1]] = glyph
            cells.append(Cell(row, col, crop, prepared, label is not None,
                              float(np.count_nonzero(mask) / crop.size), int(area)))
    return cells


def recognize_cells(cells, config: Config, tesseract_cmd=None, prepared=True, deadline=None, *, _allow_retry=True):
    """One Tesseract call for a multi-page TIFF; each filled cell is a PSM-10 page.

    Empty detection always happens before OCR and is the same in the ablation.
    Unread pages receive one optional 2x retry with the same engine settings;
    this rule is identical for the raw and prepared ablation arms.
    No Sudoku correction or ground-truth lookup is performed.
    """
    filled = [cell for cell in cells if cell.filled]
    grid = np.zeros((9, 9), dtype=int)
    confidence = np.full((9, 9), -1.0)
    mask = np.asarray([cell.filled for cell in cells], dtype=bool).reshape(9, 9)
    if not filled:
        return Recognition(grid, confidence, mask, cells, [])
    import pytesseract
    pytesseract.pytesseract.tesseract_cmd = find_tesseract(tesseract_cmd)
    config_text = (f"--oem 1 --psm {config.ocr_psm} -c tessedit_char_whitelist=123456789 "
                   "-c tessedit_do_invert=0 -c user_defined_dpi=300")
    timeout = config.ocr_timeout_s
    if deadline is not None:
        timeout = min(timeout, deadline - time.perf_counter())
        if timeout <= 0:
            raise TimeoutError("Image processing time budget exhausted before OCR")
    with tempfile.TemporaryDirectory(prefix="sudokuscan_") as temporary:
        # ASCII temp name avoids Windows Tesseract Unicode filename limitations.
        path = str(Path(temporary) / "cells.tif")
        pages = [Image.fromarray(cell.prepared if prepared else cell.raw) for cell in filled]
        pages[0].save(path, save_all=True, append_images=pages[1:], compression="tiff_deflate")
        prior_threads = os.environ.get("OMP_THREAD_LIMIT")
        os.environ["OMP_THREAD_LIMIT"] = "1"
        try:
            data = pytesseract.image_to_data(path, lang="eng", config=config_text,
                                             output_type=pytesseract.Output.DICT, timeout=timeout)
        finally:
            if prior_threads is None:
                os.environ.pop("OMP_THREAD_LIMIT", None)
            else:
                os.environ["OMP_THREAD_LIMIT"] = prior_threads
    # Never drop blank pages from the index mapping: TSV page_num preserves them.
    page_words = {}
    for index, text in enumerate(data["text"]):
        text = str(text).strip()
        if not text:
            continue
        page = int(data["page_num"][index]) - 1
        page_words.setdefault(page, []).append((text, float(data["conf"][index])))
    for page, cell in enumerate(filled):
        words = page_words.get(page, [])
        text = "".join(item[0] for item in words)
        if len(text) == 1 and text in "123456789":
            grid[cell.row, cell.col] = int(text)
            confidence[cell.row, cell.col] = min(item[1] for item in words)
    unread = [[cell.row, cell.col] for cell in filled if grid[cell.row, cell.col] == 0]
    if unread and config.ocr_retry_unread and _allow_retry and (deadline is None or deadline-time.perf_counter() > 0.3):
        unread_set = {tuple(position) for position in unread}
        retry_cells = []
        for cell in cells:
            needs_retry = (cell.row, cell.col) in unread_set
            retry_cells.append(replace(cell, filled=needs_retry,
                prepared=cv2.resize(cell.prepared, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC) if needs_retry and prepared else cell.prepared,
                raw=cv2.resize(cell.raw, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC) if needs_retry and not prepared else cell.raw))
        try:
            retried = recognize_cells(retry_cells, config, tesseract_cmd, prepared, deadline, _allow_retry=False)
            for row, col in unread:
                if retried.grid[row,col]:
                    grid[row,col] = retried.grid[row,col]
                    confidence[row,col] = retried.confidence[row,col]
        except (RuntimeError, TimeoutError):
            # The first pass remains usable if a retry consumes its budget.
            pass
        unread = [[cell.row, cell.col] for cell in filled if grid[cell.row,cell.col] == 0]
    return Recognition(grid, confidence, mask, cells, unread)


def recognize(rectified, config, tesseract_cmd=None, prepared=True, deadline=None):
    return recognize_cells(extract_cells(rectified, config), config, tesseract_cmd, prepared, deadline)
