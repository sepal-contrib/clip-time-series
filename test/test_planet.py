import shutil
import sys
import os
import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from component.scripts.utils import (
    get_buffers,
    get_quad_dict,
    get_vrt_filename,
)
from pathlib import Path
import tempfile
from component.scripts.planet import get_planet_grid, get_planet_vrt, get_quad

from test.planet_results import *

# Test different parameters
parameters = [
    (*a_inputs, a_expected_vrt_list, a_expected_title_list),
]


@pytest.mark.parametrize(
    "mosaics, image_size, bands, expected_vrt_list, expected_title_list",
    parameters,
)
def test_get_planet_vrt(
    geometries,
    mosaics,
    image_size,
    bands,
    alert,
    planet_model,
    expected_vrt_list,
    expected_title_list,
):

    try:
        tmp_dir = Path(tempfile.mkdtemp())
        input_file_path = tmp_dir / "test_points.csv"
        sources = ["planet"]

        vrt_list, title_list = get_planet_vrt(
            geometries,
            mosaics,
            image_size,
            input_file_path.stem,
            bands,
            alert,
            tmp_dir,
            planet_model,
        )

        assert vrt_list == expected_vrt_list(tmp_dir)

        # Assert that those files actually exist
        for vrt in vrt_list.values():
            assert vrt.is_file()

        assert title_list == expected_title_list

    except Exception as e:
        raise e
    finally:
        shutil.rmtree(tmp_dir)


def test_get_planet_grid(geometries, alert):

    size = 250
    buffers = get_buffers(gdf=geometries, size=size).geometry
    grid = get_planet_grid(
        squares=buffers,
        out=alert,
    )

    assert grid.loc[1, "names"] == "L15-1097E-1055N.tif"
    assert grid.loc[2, "names"] == "L15-1098E-1054N.tif"

    row = grid.loc[1]

    quad_id_1 = f"{int(row.x):04d}-{int(row.y):04d}"
    assert quad_id_1 == "1097-1055"

    row = grid.loc[2]

    quad_id_2 = f"{int(row.x):04d}-{int(row.y):04d}"
    assert quad_id_2 == "1098-1054"


def test_get_planet_quad(planet_model, alert):
    """Test the get_ee_image function."""

    try:
        alert.reset_progress(1, "Progress")

        tmp_dir = Path(tempfile.mkdtemp())

        quad_id = "1097-1055"
        filename = "test_points"

        # name is the name of the mosaic
        mosaics = ["planet_medres_normalized_analytic_2020-10_mosaic"]
        quad_ids = [quad_id]
        quads_dict = get_quad_dict(planet_model, mosaics, quad_ids)

        mosaic_name = mosaics[0]
        mosaic_quads = quads_dict[mosaic_name]

        bands = "rgb"  # or cir
        file_list = []

        quad = get_quad(
            quad_ids[0],
            filename,
            mosaic_quads,
            mosaic_name,
            bands,
            file_list,
            alert,
            None,
            tmp_dir,
        )

        assert (
            quad
            == tmp_dir
            / "test_points_planet_medres_normalized_analytic_2020-10_mosaic_1097-1055.tif"
        )
    except Exception as e:
        raise e
    finally:
        shutil.rmtree(tmp_dir)
