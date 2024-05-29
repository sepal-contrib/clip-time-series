from typing import Literal

AdjustmentType = Literal[
    "histogram_equalization",
    "contrast_stretching",
    "adaptive_equalization",
    "standard_deviation",
    "percent_clip",
    "min_max",
]
