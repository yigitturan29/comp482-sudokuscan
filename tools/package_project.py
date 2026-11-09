"""Export only tracked source. Private photos, annotations and reports are ignored."""
from pathlib import Path
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    output = ROOT.parent / "SudokuScan_Calisma_Paketi.zip"
    result = subprocess.run(["git","archive","--format=zip","HEAD"],cwd=ROOT,capture_output=True,check=True)
    output.write_bytes(result.stdout)
    with zipfile.ZipFile(output) as archive:
        bad = archive.testzip()
        if bad:
            raise RuntimeError(f"Corrupted ZIP member: {bad}")
        print(f"{len(archive.namelist())} entries; {output.stat().st_size:,} bytes")
    print(output)


if __name__ == "__main__":
    main()
