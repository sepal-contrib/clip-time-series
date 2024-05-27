import shutil
import sys
import os
import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from component.scripts.utils import get_pdf_path
from pathlib import Path
import tempfile
from component.scripts.export import get_pdf
from component.scripts.gee import get_ee_image, get_gee_vrt
from test.gee_results import *
from component import parameter as cp

# Test different parameters
parameters = [
    (*a_inputs, a_expected_vrt_list, a_expected_title_list),
    (*b_inputs, b_expected_vrt_list, b_expected_title_list),
    (*c_inputs, c_expected_vrt_list, c_expected_title_list),
    (*d_inputs, d_expected_vrt_list, d_expected_title_list),
]


@pytest.mark.parametrize(
    "mosaics, image_size, sources, bands, square_size, expected_vrt_list, expected_title_list",
    parameters,
)
def test_get_gee_vrt(
    geometries,
    alert,
    mosaics,
    image_size,
    sources,
    bands,
    square_size,
    expected_vrt_list,
    expected_title_list,
):

    try:
        tmp_dir = Path(tempfile.mkdtemp())
        input_file_path = tmp_dir / "test_points.csv"

        pdf_filepath = get_pdf_path(
            input_file_path.stem, sources, bands, square_size, image_size
        )

        vrt_list, title_list = get_gee_vrt(
            geometries,
            mosaics,
            image_size,
            pdf_filepath.stem,
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
        shutil.rmtree(tmp_dir)


def test_get_pdf(geometries, alert):

    try:
        tmp_dir = Path(tempfile.mkdtemp())
        input_file_path = tmp_dir / "test_points.csv"
        mosaics = [2024]
        image_size = 10000
        sources = ["landsat"]
        bands = "Red, Green, Blue"
        square_size = 90

        pdf_filepath = get_pdf_path(
            input_file_path.stem, sources, bands, square_size, image_size
        )

        vrt_list, title_list = get_gee_vrt(
            geometries,
            mosaics,
            image_size,
            pdf_filepath.stem,
            bands,
            sources,
            alert,
            tmp_dir,
        )

        pdf_file = get_pdf(
            pdf_filepath=pdf_filepath,
            mosaics=mosaics,
            image_size=image_size,
            square_size=square_size,
            vrt_list=vrt_list,
            title_list=title_list,
            band_combo=bands,
            geometry=geometries,
            output=alert,
            tmp_dir=tmp_dir,
        )

        assert pdf_file == pdf_filepath

    except Exception as e:
        raise e
    finally:
        shutil.rmtree(tmp_dir)


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
