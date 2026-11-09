"""Generate the measured IEEE report from the supplied JPEG dataset.

The manuscript contains personal dataset details and stays outside Git.
"""
import argparse
from collections import Counter
import csv
import json
from pathlib import Path
import re
import shutil

import _bootstrap
import cv2
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

from sudokuscan.config import Config
from sudokuscan.io import load_annotation, read_image
from sudokuscan.metrics import f1
from sudokuscan.recognition import extract_cells

ROOT = Path(__file__).resolve().parents[1]


def tex_escape(value):
    mapping = {'\\': r'\textbackslash{}', '&': r'\&', '%': r'\%', '$': r'\$', '#': r'\#',
               '_': r'\_', '{': r'\{', '}': r'\}', '~': r'\textasciitilde{}', '^': r'\textasciicircum{}'}
    return re.sub(r'[\\&%$#_{}~^]', lambda match: mapping[match.group()], str(value))


def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def generate(student_number, dataset, automatic_dir, comparison_dir):
    dataset, automatic_dir, comparison_dir = map(Path, (dataset, automatic_dir, comparison_dir))
    automatic = load(ROOT / 'results/zip_automatic_metrics.json')
    comparison = load(comparison_dir / 'summary.json')
    ocr = load(ROOT / 'results/zip_ocr_study/measurements.json')
    manual = load(ROOT / 'results/zip_annotation_preview/summary.json')
    manifest = load(dataset / 'manifest.json')
    folder = ROOT / 'report/private'
    figures = folder / 'figures'
    figures.mkdir(parents=True, exist_ok=True)
    for name in ('corner_residuals.pdf', 'grid_and_ocr.pdf', 'most_oblique.png'):
        shutil.copyfile(comparison_dir / name, figures / name)
    auto = automatic['overall']
    samples = [load(path) for path in sorted((comparison_dir / 'per_image').glob('*.json'))]
    if len(samples) < 8 or comparison['failures']:
        raise ValueError('The report requires at least eight complete cross-model experiments')
    auto_times = [row['runtime_s'] for row in automatic['samples']]
    manual_records = [row for row in manual['images'] if 'ocr' in row]
    if len(manual_records) != 10:
        raise ValueError('Expected ten manual-geometry OCR records')
    stats = {}
    for mode in ('raw', 'prepared'):
        stats[mode] = float(np.mean([row['ocr'][mode]['cell_accuracy'] for row in manual_records])) * 100
    psm_rows = []
    psm_accuracy = {}
    for psm in (7, 8, 10, 13):
        scores = []
        for prepared in (False, True):
            subset = [row for row in ocr['measurements'] if row['psm'] == psm and row['prepared'] == prepared]
            if len(subset) != 10:
                raise ValueError('Each PSM arm needs ten images')
            scores.append(float(np.mean([row['cell_accuracy'] for row in subset])) * 100)
        psm_accuracy[psm] = scores
        psm_rows.append(f'{psm} & {scores[0]:.2f} & {scores[1]:.2f}' + r' \\')
    harris = {}
    with (ROOT / 'results/zip_harris_study.csv').open(encoding='utf-8') as stream:
        for row in csv.DictReader(stream):
            harris.setdefault(row['variant'], []).append(row)
    harris_rows = []
    for name, rows in harris.items():
        errors = [float(row['corner_error_percent']) for row in rows if row['corner_error_percent']]
        name = name.replace('harris_block_fraction', 'block fraction').replace('harris_ksize', 'ksize').replace('harris_k', 'k').replace('harris_threshold', 'threshold')
        harris_rows.append(f'{tex_escape(name)} & {len(errors)}/{len(rows)} & '
                           f"{np.mean([int(row['candidates']) for row in rows]):.1f} & "
                           + (f'{np.mean(errors):.3f}' if errors else '--') + r' \\')
    model_rows = []
    for model in ('A3', 'A4', 'H4'):
        row = comparison['summary'][model]
        model_rows.append(f"{model} & {row['position_mae_px']:.2f} & {row['spacing_mae_px']:.2f} & "
                          f"{row['straightness_rms_px']:.2f} & {row['missing_lines_total']} & {100*row['cell_accuracy']:.2f}" + r' \\')
    image_rows = []
    for sample in samples:
        image_rows.append(tex_escape(Path(sample['image']).stem.replace('photo_', ''))
                          + f" & {sample['obliqueness']:.3f} & {sample['a3_corner_err_px']:.1f} & {sample['a4_rms_px']:.1f} & "
                          + ' & '.join(f"{100*sample['models'][model]['ocr']['cell_accuracy']:.1f}" for model in ('A3', 'A4', 'H4')) + r' \\')
    condition_rows = []
    for condition, row in automatic['by_condition'].items():
        condition_rows.append(f"{condition} & {row['images']} & {100*row.get('cell_accuracy', 0):.2f} & {100*row.get('grid_exact_match', 0):.1f}" + r' \\')
    # Four distinct image failures from the actual automatic H4 outputs.
    selected = []
    for sample in samples:
        truth = np.asarray(load_annotation(dataset / 'annotations' / (Path(sample['image']).stem + '.json'))['grid'])
        pred = np.asarray(sample['models']['H4']['ocr']['grid'])
        errors = np.argwhere(truth != pred)
        if len(errors):
            row, col = map(int, errors[0]); selected.append((sample, row, col, int(truth[row, col]), int(pred[row, col])))
    if len(selected) < 4:
        raise ValueError('Four distinct real failure images are needed for the selected report layout')
    plt.rcParams.update({'font.size': 8, 'axes.titlesize': 7.5})
    fig, axes = plt.subplots(2, 2, figsize=(3.35, 2.25), layout='constrained')
    failure_labels = []
    for ax, (sample, row, col, truth, pred) in zip(axes.ravel(), selected[:4]):
        stem = Path(sample['image']).stem
        image = read_image(automatic_dir / f'{stem}_rect_H4.png')
        cell = extract_cells(image, Config())[row * 9 + col]
        pair = np.concatenate([cv2.resize(cell.raw, (128, 128), interpolation=cv2.INTER_NEAREST), cell.prepared], axis=1)
        ax.imshow(pair, cmap='gray', vmin=0, vmax=255)
        title = f"{stem.replace('photo_', '')} r{row+1}c{col+1}: {truth} -> {pred}"
        ax.set_title(title); ax.axis('off'); failure_labels.append(title)
    fig.savefig(figures / 'failures.pdf'); plt.close(fig)
    near = min(samples, key=lambda sample: sample['obliqueness'])
    high = max(samples, key=lambda sample: sample['obliqueness'])
    largest_a3 = max(samples, key=lambda sample: sample['a3_corner_err_px'])
    a4_ok = [sample for sample in samples
             if sample['models']['A4']['ocr']['cell_accuracy'] >= sample['models']['H4']['ocr']['cell_accuracy'] - .01
             and sample['models']['A4']['geometry']['position_mae_px'] < 5]
    max_h4_residual = max(sample['h4_max_residual_px'] for sample in samples)
    confusion = ', '.join(f'{key} ({count})' for key, count in ocr['common_confusions'])
    body = r'''\documentclass[conference,a4paper]{IEEEtran}
\usepackage[T1]{fontenc}
\usepackage{amsmath,graphicx,booktabs,array,url}
\title{SudokuScan: Harris-Based Grid Rectification and Recognition}
\author{\IEEEauthorblockN{Student @STUDENT@}\IEEEauthorblockA{COMP 482, MEF University\\9 November 2026}}
\begin{document}
\maketitle
\begin{abstract}
A CPU pipeline locates Sudoku grids with Harris candidates, estimates three
geometric maps, extracts givens with Tesseract and checks rule conflicts.
All computational stages were implemented and evaluated on ten supplied JPEG
photographs of three printed puzzles. Automatic H4 recognition classified
@CORRECT@/810 cells correctly (@AUTOACC@\%), with @EXACT@/10 exact grids and
@CORNER@\% mean normalized corner error. Identical OCR on A3 and A4 reached
@A3ACC@\% and @A4ACC@\%. Measured line positions and spacing explain much of
this difference; all three maps preserve line straightness. These are results
on the same photographs used in development, with draft manual references,
not an independent or hidden-test evaluation.
\end{abstract}

\section{Introduction}
The objective is to convert a printed-grid photograph into four ordered corners,
three rectifications, a $9\times9$ grid of givens and a validity verdict. The
implementation separates preprocessing, Harris detection/selection, geometric
mapping, recognition and validity checks. It does not solve the puzzle or infer
unread digits from Sudoku constraints. The automatic command-line path never
loads annotation files. Separate offline tools compute the model comparison,
parameter studies and evaluation against references.

\section{Corner Detection}
The detector resizes inputs to at most 1400 pixels on the longest side. Gaussian
noise reduction and grayscale morphological closing provide a size-aware
illumination-normalized image. Kernel widths are fractions of the shorter side:
0.003 for smoothing, 0.015 for the closing background and 0.035 for adaptive
thresholding. Separate x/y resize factors retain original pixel coordinates.
Harris uses
\begin{equation}
R=\det(M)-k\operatorname{tr}(M)^2,
\end{equation}
with $k=0.04$, derivative aperture 3 and block width approximately 0.003 times the
shorter working-image side, minimum two pixels. The response threshold is
$0.0001\max(R)$. Local maxima, plateau merging and radius suppression remove
near-duplicates; the suppression radius is approximately 0.007 times the shorter
side. The response map, all candidates and final four points are saved.

Contours supply convex quadrilateral search regions only. Each proposal corner
is associated with the seven closest Harris candidates within 5.5\% of mean
side length. The best three regions undergo two rounds of candidate-only
coordinate descent. A temporary 191-pixel warp tests evidence for ten lines in
each direction: directional opening and projections reward line positions and
penalize between-line ink. The global acceptance score is 0.24. Four distinct
returned indices must belong to the Harris candidate array, after which
\texttt{cornerSubPix} may refine them locally. There are no filename-specific
rules, clicks or per-image parameters.

Opposite-edge alignment and midpoint height determine geometric corner order.
Cyclic orders can be tested with mean single-character OCR confidence. A trial
with mean confidence at least 70 and recognized/filled fraction at least 0.85
ends the search. Wrong-orientation trials omit enlargement retries; the selected
orientation can retry unread cells. Annotation order is not used by this process.

\begin{table}[t]\centering\footnotesize
\caption{Harris one-factor study: seven upright images, 84 experiments. Error is
mean corner error (\% side) on detections; failures are counted separately.}
\begin{tabular}{lrrr}\toprule
Variant & Found & Candidates & Error\\\midrule
@HARRIS_ROWS@
\bottomrule\end{tabular}
\end{table}
The subset is photos 01 and 05--10. Sideways inputs are excluded from this
detector-only study to separate orientation from boundary localization. Higher
thresholds discard weak shadowed corners; their low successful-only error does
not compensate for missing grids. The 0.002 block fraction has a small advantage
on this development set; the retained 0.003 baseline is not claimed optimal on
unseen images. Every run uses one common configuration.

\section{Rectification}
An affine map $q=A[x,y,1]^T$ has six unknown coefficients. Three non-collinear
point pairs supply six scalar equations. A3 uses TL, TR and BL with
\texttt{getAffineTransform}; BR is reserved for its residual. A4 invokes
\texttt{estimateAffine2D} using all four corners and explicitly refits all four
pairs with linear least squares, preventing an implicit robust inlier subset.
A homography $\lambda[u,v,1]^T=H[x,y,1]^T$ has nine coefficients with one common
scale, hence eight independent parameters; four point pairs in general position
supply eight equations. H4 uses \texttt{getPerspectiveTransform}.

The continuous target boundary is $(0,0),(450,0),(450,450),(0,450)$ and the raster
is $450\times450$. A3 reports the transformed BR and its distance to $(450,450)$.
A4 reports the four-point RMS residual. H4's maximum numerical corner residual
is below @H4RES@ pixels on this set. Such interpolation residuals are distinct
from error against manually annotated true corners.

Affine maps preserve parallelism and cannot remove perspective convergence
represented by finite vanishing points. Homographies preserve straight lines
and can map the planar grid's two vanishing directions to infinity. Accurate
corner interpolation alone does not prove that the physical corners were detected.

\section{Affine Versus Homography}
\subsection{Measurements}
All ten photographs are compared. Let the detected TL/TR/BR/BL edge lengths be
$t,r,b,l$. Viewing obliqueness is the image-space proxy
\begin{equation}
\omega=\max(t/b,b/t,l/r,r/l)-1.
\end{equation}
It is invariant to in-plane rotation and uniform scale, but is not a calibrated
camera angle and does not describe all projective distortion.

For each rectification, all ten horizontal and ten vertical lines are attempted.
Canonical line endpoints at $0,50,\ldots,450$ are transferred through
$M H_4^{-1}$ to seed an 11-pixel search strip in the actual rectified image.
Thus search guides come from the detected geometry, not ground truth. Morphological
illumination normalization supplies continuous ink evidence. The strongest
parallel response seeds local pixel tracing. Perpendicular grid intersections
are omitted; robust fitting rejects isolated glyph/shadow outliers. At least
24 supported samples spanning a quarter of the image are required. An absent
line remains missing, including lines clipped by an affine warp.

Position error is mean absolute observed-pixel distance from its ideal x/y line
at multiples of 50 pixels. Spacing error is the absolute deviation from 50 pixels
between adjacent detected lines at the image midline. Straightness is mean
per-line RMS orthogonal residual to a fitted line. To expose clipping bias, a
supplementary position score charges 50 pixels for each missing line, averaged
over all 20 attempts. Raw errors, missing counts, sampled points and overlays
are retained, so absent lines cannot silently improve an average. All three
images receive identical PSM-10 recognition and preparation, including the same
unread retry rule. This offline study has no recognition time cutoff.

\begin{figure}[t]\centering
\includegraphics[width=\columnwidth]{figures/corner_residuals.pdf}
\caption{Automatic-corner interpolation residuals versus the obliqueness proxy.
All ten images are included; the scalar proxy does not uniquely order error.}
\end{figure}
\begin{table}[t]\centering\footnotesize
\caption{Ten-image model comparison. Position, spacing and straightness are in
pixels, averaged per image over observed lines. Missing is the total out of 200.
Accuracy includes all 810 digit and empty cells.}
\begin{tabular}{lrrrrr}\toprule
Model & Position & Spacing & Straight & Missing & OCR (\%)\\\midrule
@MODEL_ROWS@
\bottomrule\end{tabular}
\end{table}
\begin{figure*}[t]\centering
\includegraphics[width=\textwidth]{figures/most_oblique.png}
\caption{Most oblique photograph according to the declared proxy: @MOSTID@,
$\omega=@MOSTOMEGA@$. A3, A4 and H4 use the same automatically selected corners.
The affine images retain sloped/nonuniform grid spacing; the H4 image supports
fixed equal-cell extraction.}
\end{figure*}
\begin{figure*}[t]\centering
\includegraphics[width=\textwidth]{figures/grid_and_ocr.pdf}
\caption{Grid position error with the stated missing-line penalty, and identical
OCR on all three rectifications. Samples are sorted by obliqueness only for
plotting; lines connecting samples do not imply a causal calibration curve.}
\end{figure*}

\subsection{Observed Conditions and Weak Perspective}
H4 achieves @AUTOACC@\% cell accuracy, compared with @A3ACC@\% for A3 and
@A4ACC@\% for A4. H4 line-position and spacing errors average @H4POS@ and
@H4SPACE@ pixels. A3 loses @A3MISSING@ of 200 line attempts through clipping or
insufficient visible support; A4 and H4 retain all 200. The straightness values
are similar: both affine and projective transformations map ideal straight lines
to straight lines. The important observed differences are alignment, spacing
and visibility, not an assertion that an affine map bends lines.

The lowest-obliqueness case is @NEARID@ ($\omega=@NEAROMEGA@$). Here A4 reaches
@NEAROCR@\% versus H4 @NEARH4@\%, with @NEARPOS@-pixel line-position error.
For a practical tolerance of at most one percentage point OCR loss and below
five pixels mean position error, @ACCEPTCOUNT@ of ten A4 cases qualify. This
criterion is an explicit interpretation for this experiment, not a grading rule.
Even modest apparent obliqueness does not guarantee comparable OCR for a fixed
50-pixel cell layout. The greatest A3 BR residual is @MAXA3@ pixels in
@MAXA3ID@, rather than the photograph with the greatest side-ratio proxy.

Under weak perspective, replacing depths by a common mean depth is reasonable
when within-object depth variation is small relative to viewing distance. A
small planar region viewed nearly frontally may then be approximated by an
affine image map. The supplied data support A4 on the least distorted case,
while stronger perspective favors H4. They do not establish a universal
obliqueness cutoff; distance, corner error, print quality and fixed cell margins
also affect recognition.

\section{Recognition and Validity}
H4 is split into 81 cells of $50\times50$ pixels. An 8\% inner margin removes
four pixels on each side. A previously tested 12\% margin clipped low-positioned
glyphs. Grayscale closing with an elliptical 13-pixel kernel estimates full-grid
illumination; division and whitening of normalized intensities above 210 reduce
shadow variation. Per-cell Otsu masks supply connected components. A non-border
component must cover at least 1.8\% of the inner crop and reach 25\% of its
height. Empty/filled classification therefore occurs before OCR.

The largest accepted component is isolated with a one-pixel support halo while
retaining grayscale edges. A two-pixel bounding-box halo avoids clipping. The
glyph is centered on a $128\times128$ white page; only glyphs larger than 40
pixels are reduced on the first pass. Filled cells become pages in one TIFF.
Tesseract 5.4 runs with \texttt{--oem 1 --psm 10}, whitelist \texttt{123456789},
automatic inversion disabled and one CPU thread. Unread cells receive one
optional twofold enlargement retry with the same settings. Raw and prepared
arms share the filled mask and retry policy. The raw arm uses the original
unnormalized inner crop. TSV page numbers preserve cell indexing through blank
OCR pages.

\begin{table}[t]\centering
\caption{PSM ablation on automatic H4 images: 810 cells, accuracy (\%).}
\begin{tabular}{crr}\toprule
PSM & Raw & Prepared\\\midrule
@PSM_ROWS@
\bottomrule\end{tabular}
\end{table}
PSM 7 and 10 tie on prepared cells; PSM 10 is retained as a single-character
setting. On automatic H4, raw PSM-10 accuracy is @RAWAUTO@\%, compared with
@AUTOACC@\% after preparation. With independent manual reference boundaries,
the corresponding values are @RAWMANUAL@\% and @PREPMANUAL@\%. These two
experiments are kept separate: the manual run isolates downstream recognition
and is not an automatic detector score.

The validity stage checks duplicate givens in every row, column and $3\times3$
box and marks conflicting cells. Zero denotes an empty cell in the grid file;
unread filled cells also receive zero but are separately listed in JSON.
A valid verdict does not prove accurate OCR, solvability or a unique solution.

\section{Results and Failure Analysis}
Automatic processing succeeds on @N@/10 images. Mean corner error is @CORNER@\%
of the reference side length, with ten scored and no missing corner sets.
Empty-positive and filled-positive F1 both equal 1.000. Exact grid match is
@EXACT@/10. Runtime is @TMIN@--@TMAX@ seconds per image on this CPU, including
selection, orientation, OCR and output writing. All ten satisfy the 20-second
limit on this run. The @TESTS@ tests cover transformations, least-squares
optimality, Harris provenance, missing/no-puzzle inputs, Unicode paths,
shadowed cell detection, OCR indexing, orientation and measured grid geometry.
A blank image cannot acquire line measurements merely from search guides.

\begin{table}[t]\centering\small
\caption{Provisional, overlapping condition subsets. Automatic H4 results.}
\begin{tabular}{crrr}\toprule
Condition & Images & Cells (\%) & Exact grids (\%)\\\midrule
@CONDITION_ROWS@
\bottomrule\end{tabular}
\end{table}
The @ERRORS@ remaining H4 errors are unread filled cells. The most frequent
confusions are @CONFUSIONS@. Four real cases in distinct images appear in
Fig.~\ref{fig:failures}. Each passes the filled criterion but produces no
whitelisted digit after retry, so these examples localize failure to preparation
or OCR rather than the empty decision. Shadow transitions, faint rasterized
print and small glyphs are visible; the present experiment does not isolate
their causal contributions. No error is repaired from reference labels.
\begin{figure}[t]\centering
\includegraphics[width=\columnwidth]{figures/failures.pdf}
\caption{Four automatic-H4 failures. Each pair shows raw crop (left) and prepared
page (right). Zero is the unread prediction.}\label{fig:failures}
\end{figure}

\section{Conclusion and Limitations}
The complete computational pipeline and the three-model comparison execute
without manual interaction. H4 performs best for equal-cell extraction on these
ten development images; A4 can be adequate for a sufficiently mild perspective
case. Pixel-supported spacing and position measurements connect geometry to
recognition, while similar straightness residuals are consistent with line
preservation by all models. These photographs were also used during development;
reference annotations remain subject to student review, and no hidden-set
performance is claimed. Unrecorded puzzle sources and absent original EXIF are
data-provenance limitations independent of whether the program runs.

\begin{thebibliography}{4}
\bibitem{brief} COMP 482, ``Project 1: SudokuScan,'' Fall 2026, supplied assignment brief.
\bibitem{harris} OpenCV, ``Feature Detection.'' [Online]. Available:
\url{https://docs.opencv.org/4.x/dd/d1a/group__imgproc__feature.html}
\bibitem{transforms} OpenCV, ``Geometric Image Transformations.'' [Online]. Available:
\url{https://docs.opencv.org/4.x/da/d54/group__imgproc__transform.html}
\bibitem{ocr} Tesseract, ``Command Line Usage.'' [Online]. Available:
\url{https://tesseract-ocr.github.io/tessdoc/Command-Line-Usage.html}
\end{thebibliography}

\appendices
\section{Dataset and Per-Image Results}
For data collection, I selected three Sudoku puzzles, assembled their printable
documents, prepared the printouts and took ten photographs in a 3/3/4 distribution.
I added the handwritten student number and date outside the grid. The received
archive contains ten JPEG files; they are preserved byte for byte with SHA-256
hashes in the manifest. Decoded RGB pixels match the earlier supplied PNG copies
exactly. All ten JPEGs contain zero EXIF fields, so retained original phone
metadata cannot be verified; none was invented or inserted. The print documents
used online puzzles, but their three original web sources were not recorded.
Condition labels and manual annotations are provisional. Handwriting is visible
on the sheet; the brief's separate-card wording still requires a submission check.

\begin{table*}[t]\centering\small
\caption{All ten automatic-boundary model experiments. Corner residuals are pixels;
OCR entries are cell accuracy (\%). Full measured line points and grids are in JSON/CSV.}
\begin{tabular}{crrrrrr}\toprule
Photo & $\omega$ & A3 BR error & A4 RMS & A3 OCR & A4 OCR & H4 OCR\\\midrule
@IMAGE_ROWS@
\bottomrule\end{tabular}
\end{table*}

\section{Reproducibility}
Windows CPU; Python 3.11; OpenCV 4.10.0; NumPy 2.4.1; Pillow 11.1.0;
pytesseract 0.3.13; Tesseract 5.4.0.20240606. The public source and separate
private dataset/results archive reproduce the computations. Use
\texttt{python sudoku\_scan.py --batch images --outdir results}, then the
\texttt{evaluate.py}, \texttt{compare\_models.py}, \texttt{ocr\_study.py},
\texttt{harris\_study.py} and \texttt{preview\_annotations.py} tools with the
paths documented in the README. \texttt{deneyler.ps1} runs the sequence;
\texttt{calistir.cmd} launches ordinary scanning. Offline experiments are
separate from the timed grading command. Source commits record actual work;
no historical commit dates or phone metadata were fabricated.

\section{AI-Use Disclosure}
The student's physical work comprises puzzle selection, printable-document
preparation, printing, photography under different viewing/lighting conditions,
and handwritten identification/date marking. Software and report assistance is
recorded below. Reference annotation review is pending.
\begin{center}\footnotesize\setlength{\tabcolsep}{3pt}
\begin{tabular}{>{\raggedright\arraybackslash}p{.12\columnwidth}>{\raggedright\arraybackslash}p{.18\columnwidth}>{\raggedright\arraybackslash}p{.24\columnwidth}>{\raggedright\arraybackslash}p{.32\columnwidth}}\toprule
Tool & Purpose / stage & Requested help & Retained contribution\\\midrule
OpenAI Codex & Core code & Pipeline, OCR, validity, CLI and tests &
Generated modules, preparation changes and tests retained.\\
OpenAI Codex & Data support & Draft corner/grid references and evaluation &
Draft annotations, archive audit and measured experiments retained; student review pending.\\
OpenAI Codex & Stage 2 & Automatic Harris-candidate selection &
Generated region proposals, candidate search, grid score and tests retained.\\
OpenAI Codex & Stage 4 / report & Cross-model measurements, interpretation and report &
Generated comparison code, actual experiments, plots, interpretation and this manuscript retained.\\\bottomrule
\end{tabular}
\end{center}
The brief's independent student-authorship condition for Stages 2 and 4 is not
met by these AI-generated components. Any final authorship declaration must
reflect the contributions above and be completed personally; no signature has
been applied by the assistant.
\end{document}
'''
    replacements = {'@STUDENT@': tex_escape(student_number), '@CORRECT@': str(round(auto['cell_accuracy'] * 810)),
        '@AUTOACC@': f"{100*auto['cell_accuracy']:.2f}", '@EXACT@': str(round(auto['grid_exact_match'] * 10)),
        '@CORNER@': f"{auto['corner_error_percent']:.3f}", '@N@': str(round(auto['processing_success'] * 10)),
        '@A3ACC@': f"{100*comparison['summary']['A3']['cell_accuracy']:.2f}",
        '@A4ACC@': f"{100*comparison['summary']['A4']['cell_accuracy']:.2f}",
        '@H4RES@': f'{max_h4_residual:.1e}', '@HARRIS_ROWS@': '\n'.join(harris_rows),
        '@MODEL_ROWS@': '\n'.join(model_rows), '@MOSTID@': tex_escape(high['image']),
        '@MOSTOMEGA@': f"{high['obliqueness']:.3f}", '@H4POS@': f"{comparison['summary']['H4']['position_mae_px']:.2f}",
        '@H4SPACE@': f"{comparison['summary']['H4']['spacing_mae_px']:.2f}",
        '@A3MISSING@': str(comparison['summary']['A3']['missing_lines_total']),
        '@NEARID@': tex_escape(near['image']), '@NEAROMEGA@': f"{near['obliqueness']:.3f}",
        '@NEAROCR@': f"{100*near['models']['A4']['ocr']['cell_accuracy']:.2f}",
        '@NEARH4@': f"{100*near['models']['H4']['ocr']['cell_accuracy']:.2f}",
        '@NEARPOS@': f"{near['models']['A4']['geometry']['position_mae_px']:.2f}",
        '@ACCEPTCOUNT@': str(len(a4_ok)), '@MAXA3@': f"{largest_a3['a3_corner_err_px']:.1f}",
        '@MAXA3ID@': tex_escape(largest_a3['image']), '@PSM_ROWS@': '\n'.join(psm_rows),
        '@RAWAUTO@': f'{psm_accuracy[10][0]:.2f}', '@RAWMANUAL@': f"{stats['raw']:.2f}",
        '@PREPMANUAL@': f"{stats['prepared']:.2f}", '@TMIN@': f'{min(auto_times):.2f}',
        '@TMAX@': f'{max(auto_times):.2f}', '@TESTS@': '28', '@CONDITION_ROWS@': '\n'.join(condition_rows),
        '@ERRORS@': str(810 - round(auto['cell_accuracy'] * 810)), '@CONFUSIONS@': tex_escape(confusion),
        '@IMAGE_ROWS@': '\n'.join(image_rows)}
    for key, value in replacements.items():
        body = body.replace(key, value)
    if re.search(r'@[A-Z_]+@', body):
        raise ValueError('Unfilled report placeholders')
    (folder / 'report.tex').write_text(body, encoding='utf-8')
    print(folder / 'report.tex')
    print(json.dumps({'automatic_cells': auto['cell_accuracy'], 'model_comparison': comparison['summary'],
                      'all_JPEGs_have_EXIF': all(row['exif_count'] for row in manifest['entries']),
                      'failure_examples': failure_labels}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--student-number', default='STUDENT NUMBER')
    parser.add_argument('--dataset', type=Path, default=ROOT / 'data/received_20261109_zip')
    parser.add_argument('--automatic-results', type=Path, default=ROOT / 'results/zip_automatic')
    parser.add_argument('--comparison-results', type=Path, default=ROOT / 'results/model_comparison')
    args = parser.parse_args()
    generate(args.student_number, args.dataset, args.automatic_results, args.comparison_results)
