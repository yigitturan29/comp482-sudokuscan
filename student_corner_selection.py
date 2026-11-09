"""Select a Sudoku boundary using Harris candidates and grid evidence.

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
Contours propose search regions only. Every returned coordinate is an existing
Harris candidate; the caller may subsequently refine it with cornerSubPix.
"""

import cv2
import numpy as np


def _ordered_quad(points):
    points = np.asarray(points, np.float32).reshape(4, 2)
    center = points.mean(axis=0)
    angle = np.arctan2(points[:, 1] - center[1], points[:, 0] - center[0])
    points = points[np.argsort(angle)]
    edges = np.roll(points,-1,axis=0)-points
    horizontalness = np.abs(edges[:,0])/np.maximum(np.linalg.norm(edges,axis=1),1e-6)
    parity = 0 if horizontalness[[0,2]].mean() >= horizontalness[[1,3]].mean() else 1
    choices = (parity,parity+2)
    top_edge = min(choices,key=lambda i:float((points[i,1]+points[(i+1)%4,1])/2))
    return np.roll(points,-top_edge,axis=0)


def _region_proposals(pre):
    """Find possible planar grid regions, including rotated and oblique ones."""
    height, width = pre.ink.shape
    reference = min(height, width)
    gap = max(3, round(reference * 0.004) | 1)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (gap, gap))
    images = [pre.ink, cv2.morphologyEx(pre.ink, cv2.MORPH_CLOSE, kernel)]
    proposals = []
    for mask in images:
        contours, _ = cv2.findContours(mask, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        contours = sorted(contours, key=cv2.contourArea, reverse=True)
        for contour in contours[:160]:
            area = cv2.contourArea(contour)
            if area < height * width * 0.018:
                break
            perimeter = cv2.arcLength(contour, True)
            for fraction in (0.012, 0.025, 0.045):
                polygon = cv2.approxPolyDP(contour, fraction * perimeter, True)
                if len(polygon) != 4 or not cv2.isContourConvex(polygon):
                    continue
                quad = _ordered_quad(polygon)
                lengths = np.linalg.norm(np.roll(quad, -1, axis=0) - quad, axis=1)
                if lengths.min() < reference * 0.12 or lengths.max() / lengths.min() > 5:
                    continue
                # Deduplicate the same boundary from different masks/epsilons.
                if any(np.mean(np.linalg.norm(quad-other, axis=1)) < reference * 0.008 for other in proposals):
                    continue
                proposals.append(quad)
                break
    return proposals


def _grid_score(ink, quad):
    """Measure long lines at all 10 expected positions after a test homography.

    A page edge, a text rectangle, or a gray frame can look quadrilateral, but
    usually does not produce two families of 10 evenly spaced continuous lines.
    A five-pixel target border keeps both outer grid lines inside the raster.
    """
    quad = np.asarray(quad, np.float32)
    if not cv2.isContourConvex(quad.reshape(4,1,2)) or cv2.contourArea(quad) < 25:
        return -1.0
    target = np.array([[5,5],[185,5],[185,185],[5,185]], np.float32)
    transform = cv2.getPerspectiveTransform(quad, target)
    warped = cv2.warpPerspective(ink, transform, (191,191), flags=cv2.INTER_NEAREST,
                                  borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    horizontal = cv2.morphologyEx(warped, cv2.MORPH_OPEN, np.ones((1,9),np.uint8))
    vertical = cv2.morphologyEx(warped, cv2.MORPH_OPEN, np.ones((9,1),np.uint8))
    horizontal_profile = horizontal[:,5:186].mean(axis=1) / 255.0
    vertical_profile = vertical[5:186,:].mean(axis=0) / 255.0
    samples = []
    coverage = []
    for profile in (horizontal_profile, vertical_profile):
        peaks = np.array([profile[position-2:position+3].max() for position in range(5,186,20)])
        middle = np.array([profile[position-2:position+3].max() for position in range(15,176,20)])
        coverage.append(int(np.count_nonzero(peaks > 0.10)))
        # Reward minor lines too; four strong box borders alone are insufficient.
        samples.append(float(0.65*peaks.mean() + 0.35*np.quantile(peaks,0.25) - 0.25*middle.mean()))
    score = min(samples) * 0.6 + np.mean(samples) * 0.4
    # Keep a continuous objective for local search: a one-pixel raster shift
    # should not discard a thin-line grid before nearby Harris alternatives are tried.
    return float(score if min(coverage) >= 4 else score * 0.35)


def _nearby_indices(quad, candidates):
    scale = np.linalg.norm(np.roll(quad, -1, axis=0)-quad, axis=1).mean()
    radius = max(6.0, scale * 0.055)
    distances = np.linalg.norm(quad[:,None,:] - candidates[None,:,:],axis=2)
    alternatives = []
    for row in distances:
        ordered = np.argsort(row, kind="stable")[:7]
        options = ordered[row[ordered] <= radius]
        if not len(options):
            return None
        alternatives.append(options)
    selected = np.array([options[0] for options in alternatives],dtype=int)
    if len(np.unique(selected)) != 4:
        return None
    return selected, alternatives


def select_outer_corners(pre, harris, config):
    """Return four candidate indices in geometric TL/TR/BR/BL order, or None.

    No filenames, annotations, manual coordinates, OCR results or per-image
    parameters are used. The search and score are the same for every input.
    """
    if len(harris.candidates) < 4:
        return None
    proposals = _region_proposals(pre)
    scored = []
    for proposal in proposals:
        snapped = _nearby_indices(proposal, harris.candidates)
        if snapped is None:
            continue
        indices, alternatives = snapped
        score = _grid_score(pre.ink, harris.candidates[indices])
        if score > 0:
            scored.append((score, indices, alternatives))
    scored.sort(key=lambda item:item[0], reverse=True)
    best_score, best_indices = -1.0, None
    # Local coordinate descent changes indices only, never invents coordinates.
    # Limiting refinement to the best three regions keeps CPU work bounded.
    for initial_score, indices, alternatives in scored[:3]:
        indices = indices.copy()
        score = initial_score
        for _ in range(2):
            changed = False
            for corner, options in enumerate(alternatives):
                for candidate_index in options:
                    trial = indices.copy()
                    trial[corner] = candidate_index
                    if len(np.unique(trial)) != 4:
                        continue
                    trial_score = _grid_score(pre.ink, harris.candidates[trial])
                    if trial_score > score + 1e-5:
                        indices, score, changed = trial, trial_score, True
            if not changed:
                break
        if score > best_score:
            best_score, best_indices = score, indices.copy()
    harris.selection_debug = {"region_proposals":len(proposals),"scored_regions":len(scored),
                              "grid_score":float(best_score),"corner_source":"Harris candidate indices"}
    return best_indices if best_score >= 0.24 else None
