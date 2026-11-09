"""STUDENT-AUTHORED SECTION - Project PDF, Section 11.

This function is deliberately unfinished. The provided course brief does not
permit generative AI to write the outer-corner selection logic.

Inputs use the working-image coordinate system:
    pre.color / pre.normalized / pre.ink: preprocessed images
    harris.candidates: (N,2) float32 array of discrete Harris coordinates
    harris.scores: response value of each candidate
    config: common parameters; never use per-image constants

Return four DISTINCT INTEGER INDICES into harris.candidates, ordered
top-left, top-right, bottom-right, bottom-left; or None if no puzzle is found.
The pipeline validates provenance and applies optional cornerSubPix refinement.

Do not load annotations, inspect filenames, use clicks or output contour-derived
coordinates here. Ground-truth annotations belong exclusively to the tools.
Write and explain your own rule before using the automatic grading interface.
"""


def select_outer_corners(pre, harris, config):
    raise NotImplementedError(
        "Student Stage 2 is unfinished: implement select_outer_corners in student_corner_selection.py"
    )
