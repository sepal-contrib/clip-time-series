import threading
import concurrent.futures

from typing import Literal, Tuple
import zipfile
from functools import partial
from pathlib import Path
from urllib.request import urlretrieve

import ee
from osgeo import gdal
from sepal_ui import sepalwidgets as sw
from sepal_ui.scripts.utils import init_ee

from component import parameter as cp
from component import widget as cw
from component.message import cm

from .utils import get_buffers, get_vrt_filename, min_diagonal

init_ee()


def get_ee_image(
    satellites: dict,
    satellite_id: Literal["sentinel_2", "landsat_5", "landsat_7", "landsat_8"],
    start: str,
    end: str,
    str_bands: str,
    aoi: ee.geometry.Geometry,
) -> Tuple[ee.ImageCollection, ee.Image]:

    # create the feature collection name
    dataset = (
        ee.ImageCollection(satellites[satellite_id])
        .filterDate(start, end)
        .filterBounds(aoi)
        .map(cp.getCloudMask(satellite_id))
    )

    bands = cp.getAvailableBands()[str_bands][satellite_id]
    ee_image = dataset.median().clip(aoi).select(bands)

    # calculate the NDVI or NDWI if needed
    # Bands are in the correct order to do the index calculation
    if "ndvi" in str_bands or "ndwi" in str_bands:
        ee_image = ee_image.normalizedDifference(bands).rename("ndvi")

    return dataset, ee_image


def visible_pixel(ee_image: ee.Image, aoi: ee.geometry.Geometry, scale: int) -> float:
    """get the proportion of visible pixel in the image."""

    # get the number of masked pixel
    pixel_masked = (
        ee_image.select(0)
        .reduceRegion(
            reducer=ee.Reducer.count(),
            geometry=aoi,
            scale=scale,
        )
        .values()
        .get(0)
    )

    # get the number of pixel in the image
    pixel = (
        ee_image.select(0)
        .unmask()
        .reduceRegion(
            reducer=ee.Reducer.count(),
            geometry=aoi,
            scale=scale,
        )
        .values()
        .get(0)
    )

    return ee.Number(pixel_masked).divide(ee.Number(pixel)).multiply(100).getInfo()


def getImage(
    sources: Literal["sentinel", "landsat"],
    bands: str,
    aoi: ee.geometry.Geometry,
    year: int,
):
    # print("get_image", sources, bands, aoi, year)
    start = str(year) + "-01-01"
    end = str(year) + "-12-31"

    # priority selector for satellites
    satellites = cp.getSatellites(sources, year)

    for satellite_id in satellites:

        dataset, ee_image = get_ee_image(
            satellites, satellite_id, start, end, bands, aoi
        )

        scale = cp.getScale(satellite_id)

        visible = 0
        if dataset.size().getInfo():

            # get the proportion of visible pixel
            visible = visible_pixel(ee_image, aoi, scale)
            # print(visible, satellite_id)

        # if its the last one I'll keep it anyway
        if visible > 50:
            break

    return (ee_image, satellite_id)


def get_gee_vrt(
    geometry,
    mosaics,
    image_size,
    filename: str,
    bands: str,
    sources,
    output: cw.CustomAlert,
    tmp_dir: Path,
):

    filename = get_vrt_filename(filename, sources, bands, image_size)
    ee_buffers = get_buffers(gdf=geometry, size=image_size, gee=True)

    # create a filename list
    descriptions = {}
    for year in mosaics:
        descriptions[year] = f"{filename}_{year}"
    # load the data directly in SEPAL
    satellites = {}  # contain the names of the used satellites

    nb_points = max(1, len(ee_buffers))
    total_images = len(mosaics) * nb_points
    output.reset_progress(total_images, "Progress")

    for year in mosaics:
        satellites[year] = [None] * len(ee_buffers)

        download_params = {
            "sources": sources,
            "bands": bands,
            "ee_buffers": ee_buffers,
            "year": year,
            "descriptions": descriptions,
            "output": output,
            "satellites": satellites,
            "lock": threading.Lock(),
            "tmp_dir": tmp_dir,
        }

        # for buffer in ee_buffers:
        #    down_buffer(buffer, **download_params)

        # download the images in parralel fashion
        with concurrent.futures.ThreadPoolExecutor() as executor:  # use all the available CPU/GPU
            # executor.map(partial(down_buffer, **download_params), ee_buffers)

            futures = {
                executor.submit(
                    partial(down_buffer, **download_params), ee_buffer
                ): ee_buffer
                for ee_buffer in ee_buffers
            }

            # Check if any future has raised an exception
            for future in concurrent.futures.as_completed(futures):
                e = future.exception()
                if e:
                    raise e  # Rethrow the first exception encountered

    # print(satellites)

    # create a single vrt per year
    vrt_list = {}
    for year in mosaics:

        # retreive the file names
        vrt_path = tmp_dir / f"{descriptions[year]}.vrt"
        filepaths = [str(f) for f in tmp_dir.glob(f"{descriptions[year]}_*.tif")]

        # build the vrt
        ds = gdal.BuildVRT(str(vrt_path), filepaths)

        # if there is no cahe to empty it means that one of the dataset was empty
        try:
            ds.FlushCache()
        except AttributeError:
            raise Exception(cm.export.empty_dataset)

        # check that the file was effectively created (gdal doesn't raise errors)
        if not vrt_path.is_file():
            raise Exception(f"the vrt {vrt_path} was not created")

        vrt_list[year] = vrt_path

    title_list = {
        y: {
            j: f"{y} {cp.getShortname(satellites[y][j])}"
            for j in range(len(ee_buffers))
        }
        for y in mosaics
    }

    # return the file
    return vrt_list, title_list


def down_buffer(
    buffer,
    sources,
    bands,
    ee_buffers: list,
    year,
    descriptions,
    output: sw.Alert,
    satellites,
    tmp_dir: str,
    lock=None,
):
    """download the image for a specific buffer."""
    # get back the image index
    j = ee_buffers.index(buffer)

    # get the image
    image, sat = getImage(sources, bands, buffer, year)

    if sat is None:
        print(f"year: {year}, j: {j}")

    if lock:
        with lock:
            satellites[year][j] = sat

    description = f"{descriptions[year]}_{j}"

    dst = tmp_dir / f"{description}.tif"

    if not dst.is_file():

        name = f"{description}_zipimage"

        link = image.getDownloadURL(
            {
                "name": name,
                "region": buffer,
                "filePerBand": False,
                "scale": cp.getScale(sat),
            }
        )

        tmp = tmp_dir.joinpath(f"{name}.zip")
        urlretrieve(link, tmp)

        # unzip the file
        with zipfile.ZipFile(tmp, "r") as zip_:
            data = zip_.read(zip_.namelist()[0])

            dst.write_bytes(data)

        # remove the zip
        tmp.unlink()

    # update the output
    output.update_progress()

    return dst
