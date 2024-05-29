import os
import sys

import ee
import pytest
import rasterio

from component.scripts.utils import remove_tmp_dir

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import tempfile
from pathlib import Path
from test.gee_results import *

from component import parameter as cp
from component.scripts.gee import down_buffer, get_ee_image, get_gee_vrt

# Test different parameters
parameters = [
    (*a_inputs, a_expected_vrt_list, a_expected_title_list),
    (*b_inputs, b_expected_vrt_list, b_expected_title_list),
    (*c_inputs, c_expected_vrt_list, c_expected_title_list),
    (*d_inputs, d_expected_vrt_list, d_expected_title_list),
]


@pytest.mark.parametrize(
    "mosaics, image_size, sources, bands, expected_vrt_list, expected_title_list",
    parameters,
)
def test_get_gee_vrt(
    geometries,
    alert,
    mosaics,
    image_size,
    sources,
    bands,
    expected_vrt_list,
    expected_title_list,
):

    try:
        tmp_dir = Path(tempfile.mkdtemp())
        filename = tmp_dir / "test_points.csv"

        vrt_list, title_list = get_gee_vrt(
            geometries,
            mosaics,
            image_size,
            filename.stem,
            bands,
            sources,
            alert,
            tmp_dir,
        )

        assert vrt_list == expected_vrt_list(tmp_dir)
        assert title_list == expected_title_list

    except Exception as e:
        raise e
    finally:
        remove_tmp_dir(tmp_dir)


def test_get_ee_image():
    """Test the get_ee_image function."""

    sources = ["sentinel", "landsat"]

    aoi = ee.Geometry.Polygon(
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

    # Test with Sentinel_2
    bands = "Nir, Swir1, Red"
    satellite_id = "sentinel_2"
    year = 2021
    start = str(year) + "-01-01"
    end = str(year) + "-12-31"
    satellites = cp.getSatellites(sources, year)
    dataset, ee_image = get_ee_image(satellites, satellite_id, start, end, bands, aoi)

    assert ee_image.bandNames().getInfo() == ["B8", "B11", "B4"]
    assert dataset.getInfo()

    bands = "Nir, Swir1, Red"
    satellite_id = "landsat_9"
    year = 2023
    start = str(year) + "-01-01"
    end = str(year) + "-12-31"
    satellites = cp.getSatellites(sources, year)
    dataset, ee_image = get_ee_image(satellites, satellite_id, start, end, bands, aoi)

    assert ee_image.bandNames().getInfo() == ["SR_B5", "SR_B6", "SR_B4"]
    assert dataset.getInfo()

    bands = "ndvi"
    satellite_id = "landsat_9"
    year = 2023
    start = str(year) + "-01-01"
    end = str(year) + "-12-31"
    satellites = cp.getSatellites(sources, year)
    dataset, ee_image = get_ee_image(satellites, satellite_id, start, end, bands, aoi)

    assert ee_image.bandNames().getInfo() == ["ndvi"]
    assert dataset.getInfo()

    bands = "ndwi"
    satellite_id = "sentinel_2"
    year = 2023
    start = str(year) + "-01-01"
    end = str(year) + "-12-31"
    satellites = cp.getSatellites(sources, year)
    dataset, ee_image = get_ee_image(satellites, satellite_id, start, end, bands, aoi)

    assert ee_image.bandNames().getInfo() == ["ndvi"]
    assert dataset.getInfo()


def test_down_buffer(alert):

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

    # open the output .tif image with rasterio and assert it has the right bands
    with rasterio.open(image) as src:
        array = src.read()
        assert array.shape[0] == 3
        assert src.meta["driver"] == "GTiff"

    # now test with ndvi and ndwi

    sources = ["sentinel"]
    bands = "ndwi"
    ee_buffers = [buffer]
    year = 2021
    descriptions = {2021: "sentinel_ndwi_2021"}
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

    with rasterio.open(image) as src:
        array = src.read()
        assert array.shape[0] == 1
        assert src.meta["driver"] == "GTiff"

    sources = ["landsat"]
    bands = "ndvi"
    ee_buffers = [buffer]
    year = 2021
    descriptions = {2021: "sentinel_ndwi_2021"}
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

    with rasterio.open(image) as src:
        array = src.read()
        assert array.shape[0] == 1
        assert src.meta["driver"] == "GTiff"
