"""Required automatic single-image and batch entry points."""
import argparse
import json
from pathlib import Path

import cv2

from sudokuscan.config import Config
from sudokuscan.io import image_paths
from sudokuscan.pipeline import scan_image


def main():
    parser = argparse.ArgumentParser(description="SudokuScan: Harris -> A3/A4/H4 -> OCR -> validity")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--input", type=Path)
    source.add_argument("--batch", type=Path)
    parser.add_argument("--outdir", type=Path, required=True)
    parser.add_argument("--config", type=Path, help="One global JSON config; no per-image tuning")
    parser.add_argument("--tesseract-cmd")
    args = parser.parse_args()
    try:
        config = Config(**json.loads(args.config.read_text(encoding="utf-8-sig"))) if args.config else Config()
        if args.batch:
            paths = image_paths(args.batch)
            if not paths:
                parser.error("No images found in batch directory")
            stems = [path.stem.casefold() for path in paths]
            if len(stems) != len(set(stems)):
                parser.error("Batch contains duplicate base names; rename files to prevent output collisions")
        else:
            paths = [args.input]
    except (ValueError, OSError, TypeError) as error:
        parser.error(str(error))
    cv2.setNumThreads(1)
    succeeded = 0
    for path in paths:
        result = scan_image(path, args.outdir, config, args.tesseract_cmd)
        succeeded += int(result["processing_ok"])
        print(f"{path.name}: {result['verdict']} ({result['runtime_s']:.3f}s) "
              f"{result.get('error', '')}")
    # Reports for failures are written, and all images are attempted. Nonzero
    # exit status makes an unfinished implementation visible to scripts/users.
    return 0 if succeeded == len(paths) else 1


if __name__ == "__main__":
    raise SystemExit(main())
