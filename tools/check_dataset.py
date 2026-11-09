"""Check dataset coverage and metadata without modifying phone originals."""
import argparse
from collections import Counter
from pathlib import Path

import _bootstrap
from PIL import Image

from sudokuscan.geometry import validate_quad
from sudokuscan.io import image_paths, load_annotation, write_json
from sudokuscan.validity import check_validity


def check_dataset(images, annotations):
    paths = image_paths(images)
    issues, details = [], []
    coverage = Counter()
    puzzles, sources = set(), set()
    if len(paths) < 10:
        issues.append(f"At least 10 photos required; found {len(paths)}")
    for path in paths:
        row = {"image": path.name}
        try:
            annotation = load_annotation(Path(annotations) / f"{path.stem}.json")
            if annotation["image"] != path.name:
                raise ValueError("Annotation image name does not match")
            validate_quad(annotation["corners"])
            with Image.open(path) as image:
                width, height = image.size
                exif = image.getexif()
                # DateTimeOriginal lives in the nested Exif IFD in many phones.
                try:
                    capture = exif.get_ifd(34665).get(36867)
                except (KeyError, TypeError, ValueError):
                    capture = None
                row.update(width=width, height=height, has_exif=bool(exif),
                           exif_datetime_original=capture, exif_orientation=exif.get(274, 1))
            for x, y in annotation["corners"]:
                if not (0 <= x < width and 0 <= y < height):
                    raise ValueError("Corner lies outside stored image pixels")
            if check_validity(annotation["grid"])[0] != "valid":
                issues.append(f"{path.name}: annotated givens conflict")
            coverage.update(set(annotation.get("conditions", [])))
            puzzles.add(annotation.get("puzzle_id", ""))
            source = annotation.get("source", "").strip()
            if source and source not in {"NOT_YET_PROVIDED", "UNKNOWN"}:
                sources.add(source)
            else:
                issues.append(f"{path.name}: original puzzle source not recorded")
            if annotation.get("annotation_status", "").endswith("requires_student_review"):
                issues.append(f"{path.name}: draft annotation has not been reviewed by the student")
            if annotation.get("normalizing_quarter_turn_clockwise", 0):
                issues.append(f"{path.name}: sideways stored pixels; core upright-input compliance needs review")
            if not annotation.get("card_checked"):
                issues.append(f"{path.name}: handwritten card has not been visually confirmed")
            if not annotation.get("capture_date"):
                issues.append(f"{path.name}: capture_date metadata missing")
            if not row["has_exif"]:
                issues.append(f"{path.name}: EXIF missing; verify this is an unedited phone original")
            if row["exif_orientation"] != 1:
                row["coordinate_note"] = "Stored pixels used; do not compare with an auto-rotated viewer."
        except Exception as error:
            issues.append(f"{path.name}: {error}")
        details.append(row)
    puzzles.discard("")
    sources.discard("")
    for condition, minimum in (("C1", 1), ("C2", 3), ("C3", 1), ("C4", 1), ("C5", 1)):
        if coverage[condition] < minimum:
            issues.append(f"{condition}: need {minimum}, found {coverage[condition]}")
    if len(puzzles) < 3 or len(sources) < 3:
        issues.append("Need at least 3 different puzzles from 3 different sources")
    return {"photos": len(paths), "coverage": dict(coverage), "puzzles": sorted(puzzles),
            "sources": sorted(sources), "issues": issues, "metadata_checks_passed": not issues,
            "notes": ["This tool cannot prove ownership, authenticity of EXIF or that the card is legible.",
                      "C2 must also cover genuinely different viewing angles; counts alone do not prove this."],
            "files": details}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--images", type=Path, default=Path("data/personal/images"))
    parser.add_argument("--annotations", type=Path, default=Path("data/personal/annotations"))
    parser.add_argument("--output", type=Path, default=Path("results/dataset_check.json"))
    args = parser.parse_args()
    report = check_dataset(args.images, args.annotations)
    write_json(args.output, report)
    print(f"{report['photos']} photos; coverage: {report['coverage']}")
    for issue in report["issues"]:
        print(" -", issue)
    return 0 if report["metadata_checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
