from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class Config:
    detection_max_side: int = 1400
    blur_fraction: float = 0.003
    illumination_fraction: float = 0.045
    adaptive_fraction: float = 0.035
    adaptive_c: float = 8.0
    harris_block_fraction: float = 0.003
    harris_ksize: int = 3
    harris_k: float = 0.04
    harris_threshold: float = 0.01
    nms_fraction: float = 0.007
    max_candidates: int = 2500
    target_size: int = 450
    cell_margin: float = 0.08
    cell_background_fraction: float = 0.26
    cell_max_ink_gray: int = 210
    component_area_fraction: float = 0.018
    component_height_fraction: float = 0.25
    ocr_psm: int = 10
    ocr_retry_unread: bool = True
    ocr_timeout_s: float = 12.0
    image_budget_s: float = 19.0

    def __post_init__(self):
        if self.detection_max_side < 100 or self.target_size < 90 or self.target_size % 9:
            raise ValueError("Detection size must be >=100; target_size must be >=90 and divisible by 9")
        if not 0 < self.harris_threshold < 1 or not 0 < self.harris_k < 0.25:
            raise ValueError("Invalid Harris threshold or k")
        if self.harris_ksize not in (3, 5, 7):
            raise ValueError("Harris ksize must be 3, 5 or 7")
        if not 0 <= self.cell_margin < 0.4:
            raise ValueError("cell_margin must lie in [0, 0.4)")
        if not 0 < self.cell_background_fraction < 1 or not 1 <= self.cell_max_ink_gray <= 254:
            raise ValueError("Invalid cell illumination parameters")
        if min(self.blur_fraction, self.illumination_fraction, self.adaptive_fraction,
               self.harris_block_fraction, self.nms_fraction) <= 0:
            raise ValueError("Kernel fractions must be positive")
        if self.max_candidates < 4 or self.ocr_timeout_s <= 0 or self.image_budget_s <= 0:
            raise ValueError("Invalid candidate count or time budget")
        if self.ocr_psm not in (7, 8, 10, 13):
            raise ValueError("Use PSM 7, 8, 10 or 13 for the OCR study")

    def as_dict(self):
        return asdict(self)
