"""Prepare public source and a separate private local dataset/results ZIP.

The public export is an exact git-archive snapshot; ignored data never enters it.
The private ZIP is for the user's own LMS delivery and is never published.
"""
import io
from pathlib import Path
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    output = ROOT / "output"
    output.mkdir(exist_ok=True)
    completed = subprocess.run(["git","archive","--format=zip","HEAD"],cwd=ROOT,capture_output=True,check=True)
    code_zip = ROOT.parent / "SudokuScan_Kod_Paketi.zip"
    code_zip.write_bytes(completed.stdout)
    public = output / "public_repository"
    public.mkdir(exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(completed.stdout)) as archive:
        for entry in archive.infolist():
            target = (public / entry.filename).resolve()
            if public.resolve() not in target.parents and target != public.resolve():
                raise RuntimeError("Archive member escapes public staging directory")
        archive.extractall(public)
        if archive.testzip():
            raise RuntimeError("Source archive failed CRC verification")
        print(f"Public source: {len(archive.namelist())} entries",flush=True)
    private_zip = ROOT.parent / "SudokuScan_Veri_ve_Sonuclar.zip"
    roots = [ROOT / "data/received_20261109_zip", ROOT / "results/zip_annotation_preview",
             ROOT / "results/zip_automatic", ROOT / "results/zip_ocr_study",
             ROOT / "results/model_comparison", ROOT / "report/private", ROOT / "output/private"]
    extras = [ROOT / "docs/GUNCEL_DURUM.md", ROOT / "results/zip_dataset_check.json",
              ROOT / "results/zip_automatic_metrics.json", ROOT / "results/zip_harris_study.csv"]
    files = [path for folder in roots if folder.exists() for path in folder.rglob("*") if path.is_file()]
    files += [path for path in extras if path.is_file()]
    with zipfile.ZipFile(private_zip,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=3) as archive:
        for path in sorted(files):
            if path.suffix in {".log",".aux"}:
                continue
            archive.write(path,path.relative_to(ROOT).as_posix())
    with zipfile.ZipFile(private_zip) as archive:
        if archive.testzip():
            raise RuntimeError("Private archive failed CRC verification")
        print(f"Private local archive: {len(archive.namelist())} files",flush=True)
    full_zip = ROOT.parent / "SudokuScan_Tam_Paket.zip"
    # Source and private data share the same root in the ready-to-extract bundle.
    # Keep only one copy of paths (e.g. the status document) found in both ZIPs.
    with zipfile.ZipFile(full_zip, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=3) as bundle:
        seen = set()
        for input_zip in (code_zip, private_zip):
            with zipfile.ZipFile(input_zip) as archive:
                for entry in archive.infolist():
                    if entry.is_dir() or entry.filename in seen:
                        continue
                    seen.add(entry.filename)
                    bundle.writestr("SudokuScan/" + entry.filename, archive.read(entry))
    with zipfile.ZipFile(full_zip) as archive:
        if archive.testzip():
            raise RuntimeError("Full archive failed CRC verification")
        print(f"Complete local bundle: {len(archive.namelist())} files", flush=True)
    print(code_zip)
    print(private_zip)
    print(full_zip)


if __name__ == "__main__":
    main()
