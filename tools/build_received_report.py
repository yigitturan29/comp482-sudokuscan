"""Build an IEEEtran development report from reproducible OCR measurements.

The generated manuscript contains personal dataset details and stays outside Git.
"""
import argparse
from collections import Counter
from pathlib import Path
import json

import _bootstrap
import cv2
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from sudokuscan.io import load_annotation, read_image, write_image, write_json
from sudokuscan.metrics import f1
from sudokuscan.recognition import extract_cells
from sudokuscan.config import Config

ROOT = Path(__file__).resolve().parents[1]


def tex_escape(value):
    return str(value).replace("\\", r"\textbackslash{}").replace("_", r"\_").replace("%",r"\%")


def generate(student_number):
    summary = json.loads((ROOT / "results/annotation_preview/summary.json").read_text(encoding="utf-8"))
    records = [row for row in summary["images"] if "ocr" in row]
    folder = ROOT / "report/private"
    figures = folder / "figures"
    figures.mkdir(parents=True, exist_ok=True)
    stats = {}
    for mode in ("raw", "prepared"):
        empty, filled = Counter(), Counter()
        for record in records:
            empty.update(record["ocr"][mode]["empty_counts"])
            filled.update(record["ocr"][mode]["filled_counts"])
        stats[mode] = {"correct": sum(round(r["ocr"][mode]["cell_accuracy"]*81) for r in records),
                       "cells": len(records)*81,
                       "cell_accuracy": float(np.mean([r["ocr"][mode]["cell_accuracy"] for r in records])),
                       "grid_exact_match": float(np.mean([r["ocr"][mode]["grid_exact_match"] for r in records])),
                       "empty_cell_f1": f1(empty), "filled_cell_f1": f1(filled)}
    x = np.arange(len(records))
    fig, ax = plt.subplots(figsize=(7,2.8), layout="constrained")
    ax.bar(x-.18,[r["ocr"]["raw"]["cell_accuracy"]*100 for r in records],.36,label="Raw crop",color="#9bacbd")
    ax.bar(x+.18,[r["ocr"]["prepared"]["cell_accuracy"]*100 for r in records],.36,label="Prepared crop",color="#087f8c")
    ax.set_xticks(x,[f"{i+1:02d}" for i in range(len(records))])
    ax.set(xlabel="Photo ID (manual annotation geometry)",ylabel="Cell accuracy (%)",ylim=(0,105))
    ax.spines[["top","right"]].set_visible(False)
    ax.legend(loc="lower left",frameon=False,ncol=2)
    fig.savefig(figures / "ocr_accuracy.pdf")
    plt.close(fig)
    examples = [(7,5,5),(8,1,1),(9,6,4),(10,7,4)]
    canvas = np.full((2*185,2*340,3),255,np.uint8)
    failures = []
    for index,(photo,row,col) in enumerate(examples):
        rec = records[photo-1]
        annotation = load_annotation(ROOT / "data/received_20261109/annotations" / f"photo_{photo:02d}.json")
        rectified = read_image(ROOT / "results/annotation_preview" / f"photo_{photo:02d}" / "GT_rect_H4.png")
        cell = extract_cells(rectified,Config())[row*9+col]
        true = annotation["grid"][row][col]
        pred = rec["ocr"]["prepared"]["grid"][row][col]
        x0,y0=(index%2)*340,(index//2)*185
        cv2.putText(canvas,f"Photo {photo:02d} r{row+1}c{col+1}: {true} -> {pred}",
                    (x0+7,y0+22),cv2.FONT_HERSHEY_SIMPLEX,.48,(0,0,0),1)
        raw = cv2.resize(cell.raw,(128,128),interpolation=cv2.INTER_NEAREST)
        prepared = cv2.cvtColor(cell.prepared,cv2.COLOR_GRAY2BGR)
        canvas[y0+37:y0+165,x0+15:x0+143]=cv2.cvtColor(raw,cv2.COLOR_GRAY2BGR)
        canvas[y0+37:y0+165,x0+175:x0+303]=prepared
        failures.append({"image":annotation["image"],"row_1based":row+1,"col_1based":col+1,
                         "truth":true,"prediction":pred,"filled_detected":bool(rec["ocr"]["prepared"]["filled_mask"][row][col])})
    write_image(figures / "unread_examples.png",canvas)
    by_condition=[]
    for condition in ("C1","C2","C3","C4","C5"):
        subset=[r for r in records if condition in r["conditions"]]
        by_condition.append((condition,len(subset),np.mean([r["ocr"]["raw"]["cell_accuracy"] for r in subset])*100,
                             np.mean([r["ocr"]["prepared"]["cell_accuracy"] for r in subset])*100))
    write_json(ROOT / "results/annotation_preview/ocr_metrics.json",{
        "kind":"manual_GT_geometry_OCR_only","automatic_corner_detection_evaluated":False,
        "annotation_review_required":True,"stats":stats,"failure_examples":failures,
        "conditions_are_provisional":True,
        "note":"These are development results on the same ten images used to adjust preprocessing; no held-out or hidden-set claim."})
    accuracy_rows="\n".join(f"{i+1:02d} & {r['puzzle_id']} & {100*r['ocr']['raw']['cell_accuracy']:.2f} & "
                              f"{100*r['ocr']['prepared']['cell_accuracy']:.2f} & {r['runtime_s']:.2f} \\\\" for i,r in enumerate(records))
    condition_rows="\n".join(f"{c} & {n} & {raw:.2f} & {prepared:.2f} \\\\" for c,n,raw,prepared in by_condition)
    raw,prepared=stats["raw"],stats["prepared"]
    body = r'''\documentclass[conference,a4paper]{IEEEtran}
\usepackage[T1]{fontenc}
\usepackage{amsmath,graphicx,booktabs,array,url,xcolor}
\newcommand{\studenttask}[1]{\par\noindent\textbf{Pending evaluation.} #1\par}
\title{SudokuScan: Geometric Rectification and Digit Recognition\\{\large Development Report}}
\author{\IEEEauthorblockN{Student @STUDENT@}\IEEEauthorblockA{COMP 482, MEF University\\9 November 2026}}
\begin{document}
\maketitle
\begin{abstract}
This report records the current implementation and development measurements for
SudokuScan. Ten supplied photographs of three printed puzzles were copied without
altering image bytes. Draft manually annotated boundaries were used to isolate and
test rectification, digit preparation and OCR. With this supplied geometry,
prepared-cell recognition classified @CORRECT@ of 810 cells correctly
(@PREP@\%), compared with @RAW@\% for raw crops. These are downstream
development measurements, not end-to-end detection or hidden-test performance.
Automatic outer-corner selection and cross-model grid analysis remain in progress.
This report documents the current implementation and its measured scope.
\end{abstract}

\section{Introduction}
The project converts a photograph of a printed puzzle into an ordered set of
corners, three rectifications, a $9\times9$ grid of givens and a rule-validity
verdict. Printed strokes, faint grid lines, perspective, shadows and surrounding
objects make each step necessary. The implemented support modules cover size-aware
preprocessing, Harris candidates, geometric estimation, explicit filled-cell
detection, Tesseract OCR, validity checks and the specified command-line interface.
The current experiments isolate recognition using draft manual corner annotations;
no ground-truth lookup is allowed in the automatic interface.

\section{Corner Detection}
The working image has a maximum side of 1400 pixels. Smooth background division
compensates for uneven illumination before Harris detection. The response is
$R=\det(M)-k\operatorname{tr}(M)^2$, with $k=0.04$, Sobel aperture 3 and a
block width of approximately $0.003$ times the shorter working-image side, with
a minimum of two pixels. Candidates exceed $0.01\max(R)$. Local maximum filtering,
plateau merging and radius suppression reduce duplicate responses; the radius is
approximately $0.007$ times the shorter side. Separate horizontal and vertical
scale factors preserve original pixel coordinates after resizing.

\studenttask{The automatic selection function in
student\_corner\_selection.py is not yet implemented. Its interface returns four
distinct Harris candidate indices in TL/TR/BR/BL order. The six-image parameter
study and final automatic corner errors will be evaluated after this stage is implemented.}

The recognition experiment uses manually annotated corner proposals rather than
Harris predictions. Annotation review remains pending. In three sideways images,
corner ordering explicitly follows the upright puzzle rather than screen axes;
the resulting upright preview must not be described as an automatic orientation bonus.

\section{Rectification}
A3 uses \texttt{getAffineTransform} on TL, TR and BL. Its two-by-three matrix has
six coefficients, determined by three non-collinear point pairs. A4 invokes
\texttt{estimateAffine2D}, includes all four points and then explicitly refits
the full four-point linear least-squares problem. The refit prevents a robust
estimator from silently dropping the unused fourth corner. H4 uses
\texttt{getPerspectiveTransform} on four pairs. A homography has eight independent
parameters after common scale is removed.

The continuous target boundary is $(0,0),(450,0),(450,450),(0,450)$, matching
the assignment's residual convention. Raster samples range from 0 to 449.
The implementation reports the A3 BR target location and its distance to
$(450,450)$, A4 four-point RMS residual, and H4 maximum numerical residual.
All models and images in the annotation preview derive from manual boundaries.
The automatic pipeline cannot yet supply a measured corner error.

\section{Affine Versus Homography}
\studenttask{The cross-model comparison is not yet evaluated. The final experiment
requires at least eight photographs, an explicit obliqueness measure, ten grid
lines per direction, line position/spacing and straightness measurements, and
identical OCR on A3/A4/H4. A side-by-side figure of the most oblique photograph
and evidence-based conclusions remain to be added.}

\section{Recognition}
\subsection{Cells and Empty Detection}
H4 is divided into $50\times50$ cells. The final development configuration crops
an 8\% inner margin, four pixels per edge. The initial 12\% margin clipped some
low-positioned printed glyphs on the second puzzle. A rectangularly continuous
illumination estimate is computed over the full rectification using grayscale
morphological closing with an elliptical kernel of approximately $0.26$ cell
width (13 pixels at this resolution). Division by that estimate reduces cast
shadow variation. Normalized intensities above 210 are mapped to white before
cell-wise Otsu thresholding.

A cell is filled only when a non-border connected component covers at least
1.8\% of the inner crop and reaches 25\% of its height. Thus the empty decision
precedes OCR. On the present draft annotations, both empty-positive and
filled-positive F1 are @EMPTYF@. These numbers use manual geometry and are
development-set measurements.

\subsection{Preparation and OCR}
The strongest accepted component is isolated with a one-pixel halo. Its normalized
grayscale edges are retained, a two-pixel crop halo avoids clipping, and the glyph
is centered on a white $128\times128$ page. Glyphs larger than 40 pixels are
reduced; small glyphs are not enlarged on the first pass. Dolu cells are batched
as pages of a TIFF and processed by Tesseract 5.4 through pytesseract, with
\texttt{--oem 1 --psm 10} and whitelist \texttt{123456789}. An unread filled
cell receives one twofold enlargement retry with the same OCR settings.
The retry rule and filled mask are identical in the raw and prepared arms.
The raw arm receives the original unnormalized inner crop.

\begin{table}[t]\centering
\caption{Recognition with manual annotation geometry; not detector scores.}
\begin{tabular}{lrr}\toprule
Metric & Raw & Prepared\\\midrule
Correct cells / 810 & @RAWCORRECT@ & @CORRECT@\\
Cell accuracy (\%) & @RAW@ & @PREP@\\
Grid exact match (\%) & @RAWEXACT@ & @PREPEXACT@\\
Empty-cell F1 & @EMPTYF@ & @EMPTYF@\\
\bottomrule\end{tabular}\label{tab:ocr}
\end{table}
\begin{figure}[t]\centering
\includegraphics[width=\columnwidth]{figures/ocr_accuracy.pdf}
\caption{Stage 5 raw/prepared ablation with supplied draft corner annotations.
These same images were used to adjust preparation; this is not held-out evaluation.}
\end{figure}

\section{Results}
\begin{table}[t]\centering\small
\caption{Per-image downstream OCR. Runtime includes manual-geometry preprocessing,
three warps and two OCR arms; it is not automatic-detector runtime.}
\begin{tabular}{ccrrr}\toprule
Photo & Puzzle & Raw (\%) & Prepared (\%) & Time (s)\\\midrule
@IMAGE_ROWS@
\bottomrule\end{tabular}
\end{table}

\begin{table}[t]\centering\small
\caption{Provisional condition labels; overlapping subsets, manual geometry.}
\begin{tabular}{ccrr}\toprule
Condition & Images & Raw (\%) & Prepared (\%)\\\midrule
@CONDITION_ROWS@
\bottomrule\end{tabular}
\end{table}

The support code has 18 passing module tests, including affine least-squares
optimality, homography mapping, original-coordinate scaling, blank and malformed
inputs, row/column/box conflicts, Unicode paths, shadowed filled-cell detection,
multi-page OCR mapping and blank-page index preservation. The tests do not
establish hidden-set accuracy. End-to-end corner error, recognition accuracy,
grid exact match and robustness remain unmeasured because automatic selection
is unfinished. Development-set files referenced by the assignment were not supplied.
Recognition errors are not filled by solving Sudoku or consulting ground truth.
The validity verdict checks repeated givens only, and does not prove OCR correctness
or solution uniqueness.

\section{Failure Analysis}
The remaining prepared-arm errors are unread filled cells. Four concrete
examples are shown in Fig.~\ref{fig:failure}. Photo 07 r6c6 contains 6; photo 08
r2c2 contains 6; photo 09 r7c5 contains 1; photo 10 r8c5 contains 6. Each cell
passes the filled decision but returns no whitelisted digit after the retry.
This localizes the observed failure to preparation/OCR rather than empty-cell
classification in these examples. The weak, rasterized print and small glyphs
are visible in the crops; further experiments are needed to distinguish their
individual effects. No claim is made that an automatic detector would locate
these photographs correctly.
\begin{figure}[t]\centering
\includegraphics[width=\columnwidth]{figures/unread_examples.png}
\caption{Four actual downstream failures. Within each example, left: raw crop,
right: prepared page. A prediction of zero is an unread filled cell, not an empty
ground-truth cell.}\label{fig:failure}
\end{figure}

\section{Conclusion and Limitations}
The current package supplies working modules, traceable received-image copies,
draft annotations and a reproducible OCR ablation. It does not constitute a complete
project: automatic corner selection and Stage 4 remain incomplete, and personal
annotations require review. Prepared OCR reaches @PREP@\% on these manually
rectified development images. No extrapolation to hidden photographs is justified.
The final submission must replace missing end-to-end results, complete the required
parameter and PSM studies, and use the original phone files with EXIF retained.

\begin{thebibliography}{4}
\bibitem{brief} COMP 482, ``Project 1: SudokuScan,'' Fall 2026, supplied assignment brief.
\bibitem{features} OpenCV, ``Feature Detection.'' [Online]. Available:
\url{https://docs.opencv.org/4.x/dd/d1a/group__imgproc__feature.html}
\bibitem{geometry} OpenCV, ``Geometric Image Transformations.'' [Online]. Available:
\url{https://docs.opencv.org/4.x/da/d54/group__imgproc__transform.html}
\bibitem{tess} Tesseract, ``Command Line Usage.'' [Online]. Available:
\url{https://tesseract-ocr.github.io/tessdoc/Command-Line-Usage.html}
\end{thebibliography}

\appendices
\section{Received Data and Provenance}
For data collection, I selected three puzzles, arranged their printable documents,
prepared the printouts and took ten photographs in a 3/3/4 distribution. I also
added the handwritten student number and capture date outside each grid. All ten
images show the handwritten date 09.11.2026 and a student number outside the grid.
The supplied files are clipboard PNGs with zero EXIF fields. Their bytes and
SHA-256 hashes were preserved; no metadata or artificial capture date was inserted.
They cannot be certified as the unedited phone originals. Photos 02--04 are
sideways in stored pixels and have an explicit canonical orientation in draft
annotations. This manual orientation must not be counted as the optional
automatic-orientation feature. The print documents were assembled from online
Sudokus; the three original web sources were not recorded and distinct-source
compliance cannot be verified. Handwriting is on the puzzle sheet; strict
compliance with the brief's separate-card wording should be checked.

\section{Reproducibility}
Windows CPU; Python 3.11; OpenCV 4.10.0; NumPy 2.4.1; Pillow 11.1.0;
pytesseract 0.3.13; Tesseract 5.4.0.20240606. Use
\texttt{tools/preview\_annotations.py} to reproduce manual-geometry previews and
\texttt{python -m pytest -q} for tests. The grader interface is
\texttt{sudoku\_scan.py}; it never reads annotation files. Private photographs,
annotations and this report are excluded from the public code repository.
The repository records implementation, documentation and validation changes.

\section{AI-Use Disclosure}
The student's contributions comprise puzzle selection, preparation of printable
documents, printing, photography under different viewing and lighting conditions,
and handwritten identification/date marking. These physical data-collection
activities were performed by the student. The software and manuscript assistance
is recorded in the table below; annotation review is still pending.
\begin{center}\footnotesize\setlength{\tabcolsep}{3pt}
\begin{tabular}{p{.12\columnwidth}p{.18\columnwidth}p{.24\columnwidth}p{.32\columnwidth}}\toprule
Tool & Purpose / stage & What was asked & Kept, changed or rejected\\\midrule
OpenAI Codex & Stages 1, 3, 5, 6; Harris/NMS support &
Prepare support modules, interfaces and tests &
AI-generated code retained; student must verify permitted use and explain it.\\
OpenAI Codex & Data and documents &
Draft annotations, OCR tests and report &
AI-assisted annotation proposals, OCR experiments and this draft retained; student review pending.\\
OpenAI Codex & Student sections &
Outer-corner selection and Stage 4 &
Not generated; student must write them.\\\bottomrule
\end{tabular}
\end{center}
\noindent\textbf{Authorship confirmation.} Confirmation and signature are pending
completion of the selection method and comparison analysis. The final declaration
will be completed personally after all submitted components have been reviewed.
\end{document}
'''
    replacements={"@STUDENT@":tex_escape(student_number),"@CORRECT@":str(prepared["correct"]),
        "@RAWCORRECT@":str(raw["correct"]),"@PREP@":f"{prepared['cell_accuracy']*100:.2f}",
        "@RAW@":f"{raw['cell_accuracy']*100:.2f}","@EMPTYF@":f"{prepared['empty_cell_f1']:.3f}",
        "@RAWEXACT@":f"{raw['grid_exact_match']*100:.1f}","@PREPEXACT@":f"{prepared['grid_exact_match']*100:.1f}",
        "@IMAGE_ROWS@":accuracy_rows,"@CONDITION_ROWS@":condition_rows}
    for key,value in replacements.items():
        body=body.replace(key,value)
    body=body.replace("Dolu cells", "Filled cells")
    (folder / "report.tex").write_text(body,encoding="utf-8")
    print(folder / "report.tex")
    print(json.dumps(stats,indent=2))


if __name__ == "__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--student-number",default="STUDENT NUMBER")
    generate(parser.parse_args().student_number)
