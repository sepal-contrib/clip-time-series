import os
import sys

import ee
import rasterio

from component.scripts.gee import download_image, get_ee_tasks

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import tempfile
from pathlib import Path
from test.gee_results import *

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
    tmp_dir = Path(tempfile.mkdtemp())
    alert.reset_progress(len(ee_buffers), "Progress")

    ee_tasks, _ = get_ee_tasks(
        [year], ee_buffers, descriptions, sources, bands, tmp_dir, alert
    )

    # Get the first year
    year, params = next(iter(ee_tasks.items()))

    # Get the first buffer
    params = params[0]

    image = download_image(params=params)

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
