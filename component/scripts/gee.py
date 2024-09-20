import concurrent.futures
import threading
import zipfile
from pathlib import Path
from typing import List, Literal, Tuple
from urllib.request import urlretrieve

import ee
from osgeo import gdal
from sepal_ui.scripts.utils import init_ee

from component import parameter as cp
from component import widget as cw

from .utils import get_buffers, get_vrt_filename

init_ee()

from typing import TypedDict


class Params(TypedDict):
    link: str  # The URL link to download the image from
    description: str  # A description of the image
    tmp_dir: str  # The temporary directory to store the downloaded image


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

    # Create a filename list
    descriptions = {year: f"{filename}_{year}" for year in mosaics}

    nb_points = max(1, len(ee_buffers))
    total_images = len(mosaics) * nb_points
    output.reset_progress(total_images, "Progress")

    # Collect EE API results
    ee_results, satellites = collect_ee_results(
        mosaics, ee_buffers, descriptions, sources, bands, tmp_dir
    )

    # Download images in parallel and get the downloaded file paths
    downloaded_files = download_images_in_parallel(ee_results, output)

    # Create VRT files per year using the downloaded file paths and descriptions
    vrt_list = create_vrt_per_year(downloaded_files, descriptions, tmp_dir)

    # Generate title list
    title_list = generate_title_list(mosaics, satellites, ee_buffers)

    # Return the file
    return vrt_list, title_list


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


def get_image(
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


def collect_ee_results(
    mosaics,
    ee_buffers,
    descriptions,
    sources,
    bands,
    tmp_dir,
) -> Tuple[dict[int, List[Params]], dict]:
    """
    Collect Earth Engine API results for each buffer and year.

    Returns:
        ee_results: A dictionary containing download parameters per year.
        satellites: A dictionary tracking the satellites used per year and buffer.
    """
    satellites = {}
    ee_results = {}
    for year in mosaics:

        satellites[year] = [None] * len(ee_buffers)
        ee_results[year] = []

        for j, buffer in enumerate(ee_buffers):

            image, sat = get_image(sources, bands, buffer, year)
            if sat is None:
                print(f"Year: {year}, Buffer index: {j}")

            satellites[year][j] = sat

            description = f"{descriptions[year]}_{j}"
            name = f"{description}_zipimage"

            # Get the download URL
            link = image.getDownloadURL(
                {
                    "name": name,
                    "region": buffer,
                    "filePerBand": False,
                    "scale": cp.getScale(sat),
                }
            )

            # Store the necessary information for downloading
            ee_results[year].append(
                {
                    "link": link,
                    "description": description,
                    "tmp_dir": tmp_dir,
                }
            )

    return ee_results, satellites


def download_images_in_parallel(ee_results: dict[int, Params], output):
    """
    Download images in parallel using ThreadPoolExecutor.

    Returns:
        downloaded_files: A dictionary mapping each year to a list of downloaded file paths.
    """
    # Create a lock for thread-safe progress updates
    progress_lock = threading.Lock()
    downloaded_files = {}  # To store the downloaded file paths

    for year, download_params_list in ee_results.items():
        downloaded_files[year] = []
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = {
                executor.submit(download_image, params, progress_lock, output): params
                for params in download_params_list
            }

            # Collect results as they complete
            for future in concurrent.futures.as_completed(futures):
                e = future.exception()
                if e:
                    raise e  # Rethrow the first exception encountered

                # Get the result (downloaded file path) and store it
                file_path = future.result()
                downloaded_files[year].append(file_path)

    return downloaded_files


def create_vrt_per_year(downloaded_files, descriptions, tmp_dir):
    """
    Create a VRT file for each year by combining the downloaded TIFF files.

    Args:
        downloaded_files: A dictionary mapping each year to a list of downloaded file paths.
        descriptions: A dictionary mapping each year to its base filename.
        tmp_dir: The temporary directory where files are stored.

    Returns:
        vrt_list: A dictionary mapping each year to its VRT file path.
    """
    vrt_list = {}
    for year, filepaths in downloaded_files.items():
        # Ensure all file paths are strings
        filepaths = [str(f) for f in filepaths]

        # Define the VRT path using the descriptions to match the expected filenames
        vrt_filename = f"{descriptions[year]}.vrt"
        vrt_path = tmp_dir / vrt_filename

        # Build the VRT
        ds = gdal.BuildVRT(str(vrt_path), filepaths)

        # Check if the dataset was properly created
        if ds is None:
            raise Exception(f"Failed to create VRT for year {year}")

        ds = None  # Close the dataset

        # Ensure the VRT file exists
        if not vrt_path.is_file():
            raise Exception(f"The VRT {vrt_path} was not created")

        vrt_list[year] = vrt_path
    return vrt_list


def generate_title_list(mosaics, satellites, ee_buffers):
    """
    Generate a title list mapping each year and buffer index to the satellite name.

    Returns:
        title_list: A nested dictionary containing titles per year and buffer index.
    """
    title_list = {
        y: {
            j: f"{y} {cp.getShortname(satellites[y][j])}"
            for j in range(len(ee_buffers))
        }
        for y in mosaics
    }
    return title_list


def download_image(params: Params, progress_lock=None, output=None):
    """
    Download a single image and update progress.

    Args:
        params: A dictionary containing 'link', 'description', 'tmp_dir'.
        progress_lock: A threading.Lock() instance for thread-safe progress updates.
        output: The output alert object to update progress.

    Returns:
        dst: The path to the downloaded TIFF file.
    """
    print(params)
    link = params["link"]
    description = params["description"]
    tmp_dir = params["tmp_dir"]

    dst = tmp_dir / f"{description}.tif"

    if not dst.is_file():
        name = f"{description}_zipimage"

        tmp = tmp_dir.joinpath(f"{name}.zip")
        urlretrieve(link, tmp)

        # Unzip the file
        with zipfile.ZipFile(tmp, "r") as zip_:
            data = zip_.read(zip_.namelist()[0])
            dst.write_bytes(data)

        # Remove the zip file
        tmp.unlink()

    # Update the output progress safely (if provided)
    if progress_lock and output:
        with progress_lock:
            output.update_progress()

    return dst
