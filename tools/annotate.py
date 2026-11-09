"""Manual ground-truth annotation GUI. It is never called by sudoku_scan.py."""
import argparse
import datetime
from pathlib import Path
import tkinter as tk
from tkinter import messagebox

import _bootstrap
import cv2
from PIL import Image, ImageTk

from sudokuscan.geometry import validate_quad
from sudokuscan.io import load_annotation, read_image, write_json
from sudokuscan.validity import check_validity


class Annotator:
    def __init__(self, path, outdir):
        self.path, self.outdir = Path(path), Path(outdir)
        self.image = read_image(path)
        height, width = self.image.shape[:2]
        self.scale = min(1000 / width, 700 / height, 1)
        self.display_size = (round(width * self.scale), round(height * self.scale))
        self.scale_xy = (width / self.display_size[0], height / self.display_size[1])
        self.points = []
        self.root = tk.Tk()
        self.root.title(f"Ground truth only - {self.path.name}")
        tk.Label(self.root, text="4 köşeye sırayla tıkla: TL, TR, BR, BL. Sağ tık: son noktayı sil. Boş hücre: 0.").pack()
        frame = tk.Frame(self.root)
        frame.pack()
        self.canvas = tk.Canvas(frame, width=self.display_size[0], height=self.display_size[1], background="gray")
        self.canvas.grid(row=0, column=0, rowspan=20)
        rgb = cv2.cvtColor(self.image, cv2.COLOR_BGR2RGB)
        self.photo = ImageTk.PhotoImage(Image.fromarray(rgb).resize(self.display_size))
        self.canvas.create_image(0, 0, image=self.photo, anchor="nw")
        self.canvas.bind("<Button-1>", self.click)
        self.canvas.bind("<Button-3>", self.undo)
        panel = tk.Frame(frame, padx=12)
        panel.grid(row=0, column=1, sticky="n")
        self.cells = []
        grid_frame = tk.Frame(panel)
        grid_frame.pack()
        validate = (self.root.register(lambda value: value == "" or (len(value) == 1 and value in "0123456789")), "%P")
        for row in range(9):
            entries = []
            for col in range(9):
                entry = tk.Entry(grid_frame, width=2, justify="center", font=("Consolas", 15),
                                 validate="key", validatecommand=validate)
                entry.insert(0, "0")
                entry.grid(row=row, column=col, padx=(3 if col % 3 == 0 else 0, 0),
                           pady=(3 if row % 3 == 0 else 0, 0))
                entries.append(entry)
            self.cells.append(entries)
        self.conditions = {}
        for code in ("C1", "C2", "C3", "C4", "C5"):
            self.conditions[code] = tk.BooleanVar()
            tk.Checkbutton(panel, text=code, variable=self.conditions[code]).pack(anchor="w")
        self.fields = {}
        for key, title in (("puzzle_id", "Bulmaca kimliği (P1/P2/P3)"), ("source", "Bulmacanın kaynağı"),
                           ("capture_date", "Çekim tarihi YYYY-MM-DD")):
            tk.Label(panel, text=title).pack(anchor="w")
            self.fields[key] = tk.Entry(panel, width=30)
            self.fields[key].pack(anchor="w")
        self.card = tk.BooleanVar()
        tk.Checkbutton(panel, text="Numara/tarih kartını fotoğrafta kontrol ettim", variable=self.card).pack(anchor="w")
        tk.Button(panel, text="JSON kaydet", command=self.save).pack(fill="x", pady=10)
        self.status = tk.Label(panel, text="0/4 köşe")
        self.status.pack()
        existing = self.outdir / f"{self.path.stem}.json"
        if existing.exists():
            value = load_annotation(existing)
            self.points = value["corners"]
            for row in range(9):
                for col in range(9):
                    self.cells[row][col].delete(0, "end")
                    self.cells[row][col].insert(0, str(value["grid"][row][col]))
            for code in value.get("conditions", []):
                self.conditions[code].set(True)
            for key, entry in self.fields.items():
                entry.insert(0, value.get(key, ""))
            self.card.set(value.get("card_checked", False))
        self.redraw()

    def click(self, event):
        if len(self.points) < 4:
            self.points.append([event.x * self.scale_xy[0], event.y * self.scale_xy[1]])
            self.redraw()

    def undo(self, event):
        if self.points:
            self.points.pop()
            self.redraw()

    def redraw(self):
        self.canvas.delete("marks")
        for index, point in enumerate(self.points):
            x, y = point[0] / self.scale_xy[0], point[1] / self.scale_xy[1]
            self.canvas.create_oval(x - 5, y - 5, x + 5, y + 5, outline="lime", width=2, tags="marks")
            self.canvas.create_text(x + 14, y - 8, text=("TL", "TR", "BR", "BL")[index], fill="red", tags="marks")
        self.status.config(text=f"{len(self.points)}/4 köşe")

    def save(self):
        try:
            validate_quad(self.points)
            grid = [[int(cell.get() or "0") for cell in row] for row in self.cells]
            verdict, _ = check_validity(grid)
            if verdict == "invalid":
                raise ValueError("Yazdığın Sudoku'da tekrar eden rakamlar var; ground truth'u düzelt.")
            metadata = {key: entry.get().strip() for key, entry in self.fields.items()}
            if not all(metadata.values()):
                raise ValueError("Bulmaca kimliği, kaynak ve çekim tarihini doldur.")
            datetime.date.fromisoformat(metadata["capture_date"])
            conditions = [code for code, variable in self.conditions.items() if variable.get()]
            if not conditions or not self.card.get():
                raise ValueError("Koşul etiketlerini seç ve fotoğraftaki numara/tarih kartını kontrol et.")
            output = self.outdir / f"{self.path.stem}.json"
            write_json(output, {"image": self.path.name, "conditions": conditions, "corners": self.points,
                                "grid": grid, **metadata, "card_checked": True})
            messagebox.showinfo("Kaydedildi", str(output))
        except Exception as error:
            messagebox.showerror("Kontrol et", str(error))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--outdir", type=Path, default=Path("data/personal/annotations"))
    args = parser.parse_args()
    Annotator(args.input, args.outdir).root.mainloop()


if __name__ == "__main__":
    main()
