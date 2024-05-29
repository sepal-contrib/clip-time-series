import os
import sys

import rasterio

from component.scripts.gee import down_buffer

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import tempfile
from pathlib import Path
from test.gee_results import *

from component import parameter as cp
from component.scripts.utils import enhance_band


def test_enhance_band(alert):

    buffer = ee.Geometry.Polygon(
        [
            [
                [13.024513100356552, 5.333572819469696],
                [13.026757769061255, 5.333572819469696],
                [13.026757769061255, 5.335822103684232],
                [13.024513100356552, 5.335822103684232],
                [13.024513100356552, 5.333572819469696],
            ]
        ]
    )

    sources = ["sentinel"]
    bands = "Nir, Swir1, Red"
    ee_buffers = [buffer]
    year = 2021
    descriptions = {2021: "test_2021"}
    satellites = cp.getSatellites(sources, year)
    tmp_dir = Path(tempfile.mkdtemp())
    alert.reset_progress(len(ee_buffers), "Progress")

    image = down_buffer(
        buffer,
        sources,
        bands,
        ee_buffers,
        year,
        descriptions,
        alert,
        satellites,
        tmp_dir,
    )

    print("####### Image path", image)

    # open and test the enhance function
    enhance_methods = [
        "histogram_equalization",
        "contrast_stretching",
        "adaptive_equalization",
        "standard_deviation",
        "percent_clip",
        "min_max",
    ]
    for method in enhance_methods:
        with rasterio.open(image) as src:
            data = src.read()
            enhanced = enhance_band(data, method)

            assert enhanced.shape == data.shape
            assert enhanced.dtype == data.dtype
            assert enhanced.max() <= 1
            assert enhanced.min() >= 0
