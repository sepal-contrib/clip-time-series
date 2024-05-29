from math import sqrt
from typing import Union

import ee
import geopandas as gpd
import numpy as np
import rasterio as rio
from rasterio import warp
from rasterio.crs import CRS
from rasterio.windows import from_bounds
from skimage import exposure, img_as_float

from component.parameter.directory import result_dir
from component.typings.custom_types import AdjustmentType


def min_diagonal(polygon, square_size):
    """
    Return the min diameter of the smallest circle around the shape in 3857.

    Args:
        polygon (shapely geometry): the polygon in 3857
        square_size (int): the size of the desired buffer around the polygon
    """
    minx, miny, maxx, maxy = polygon.bounds

    # get the diagonal
    return max(square_size, sqrt((maxx - minx) ** 2 + (maxy - miny) ** 2))


def get_pdf_path(
    folder_name: str, sources: list, bands: str, image_size: int, enhance_method: str
):

    output_folder = result_dir / folder_name
    output_folder.mkdir(exist_ok=True)

    # Create a pdf file path with sensors and bands
    sensors = "_".join(sources) if len(sources) else "planet"
    str_bands = "_".join(bands.split(", "))

    return (
        output_folder
        / f"{folder_name}_{sensors}_{str_bands}_{enhance_method}_size{image_size}.pdf"
    )


def get_vrt_filename(folder_name: str, sources: list, bands: str, image_size: int):

    output_folder = result_dir / folder_name
    output_folder.mkdir(exist_ok=True)

    # Create a pdf file path with sensors and bands
    sensors = "_".join(sources) if len(sources) else "planet"
    str_bands = "_".join(bands.split(", "))

    return f"{folder_name}_{sensors}_{str_bands}_size{image_size}"


def enhance_band(band: np.array, adjustment_type: AdjustmentType) -> np.array:
    """Process a single image band by applying a specified adjustment for visualization.

    Parameters:
    - band (np.ndarray): The input image band as a numpy array.
    - adjustment_type (str): The type of contrast adjustment to apply.

    """

    # Convert to float
    band = img_as_float(band)

    # Normalize data if necessary (especially for float images not in [0, 1])
    if band.dtype == float and (np.min(band) < 0 or np.max(band) > 1):
        band = (band - np.min(band)) / (np.max(band) - np.min(band))

    # Handle NaN values by replacing them with the minimum
    band[np.isnan(band)] = np.min(band)

    if adjustment_type == "histogram_equalization":
        h, bin_edges = np.histogram(band.flatten(), bins=3000, density=True)
        cdf = h.cumsum()
        cdf_normalized = cdf / cdf[-1]  # Normalize CDF
        data = np.interp(band.flatten(), bin_edges[:-1], cdf_normalized).reshape(
            band.shape
        )

    elif adjustment_type == "contrast_stretching":
        p2, p98 = np.percentile(band, (2, 98))
        data = exposure.rescale_intensity(band, in_range=(p2, p98))

    elif adjustment_type == "adaptive_equalization":
        data = exposure.equalize_adapthist(band, clip_limit=0.03)

    elif adjustment_type == "standard_deviation":
        mean = np.mean(band)
        std = np.std(band)
        data = (band - mean) / std  # Normalize by standard deviation

    elif adjustment_type == "percent_clip":
        p1, p99 = np.percentile(band, (1, 99))
        data = np.clip(band, p1, p99)

    elif adjustment_type == "min_max":
        min_val = np.min(band)
        max_val = np.max(band)
        data = (band - min_val) / (max_val - min_val)

    else:
        raise ValueError("Unsupported adjustment type")

    # Ensure all data is normalized to [0, 1] regardless of method
    # we need this to plot the data
    return (data - np.min(data)) / (np.max(data) - np.min(data))


def get_buffers(
    gdf: gpd.GeoDataFrame, size: int, gee: bool = False
) -> Union[gpd.GeoDataFrame, list[ee.Geometry]]:
    """Get the buffers of the geometries in the gdf."""

    geometry = gdf.copy()

    # Reproject to a projected CRS before computing centroids
    geometry_projected = geometry.to_crs(3857)

    # extract the points coordinates
    pts = geometry_projected.copy()
    pts.geometry = pts.geometry.centroid

    # build the size dictionary
    size_dict = {
        row.id: min_diagonal(row.geometry, size)
        for _, row in geometry_projected.iterrows()
    }

    # create the buffer grid
    buffers = pts
    buffers.geometry = buffers.apply(
        lambda r: r.geometry.buffer(size_dict[r.id] / 2, cap_style=3), axis=1
    )
    buffers = buffers.to_crs(4326)

    if gee:
        buffers = [
            ee.Geometry.Polygon(row.geometry.__geo_interface__["coordinates"])
            for _, row in buffers.iterrows()
        ]

    return buffers


def reproject(image_path: str, bounds: list) -> np.array:
    """Reproject the image to 3857 and extract the data in the bounds."""
    print("########## reproject")
    print(image_path, bounds)

    with rio.open(image_path) as f:
        data = f.read(window=from_bounds(*bounds, f.transform))

        # reproject to 3857
        # I want the final image to be as square not a rectangle
        src_crs = CRS.from_epsg(4326)
        dst_crs = CRS.from_epsg(3857)
        data, _ = warp.reproject(
            data,
            src_transform=f.transform,
            src_crs=src_crs,
            dst_crs=dst_crs,
        )

        # extract all the value separately, matplotlib uses
        # a different convention
        return data, warp.transform_bounds(src_crs, dst_crs, *bounds)


def get_quad_dict(planet_model, mosaics: list, quad_ids: list) -> dict:
    """Get a dictionary of quads for each mosaic and quad_id."""

    mosaic_list = planet_model.get_mosaics()
    quads_dict = {}
    mosaic_dict = {m["name"]: m for m in mosaic_list}

    for mosaic in mosaics:
        if mosaic not in mosaic_dict:
            continue  # Skip if mosaic is not in mosaic_list

        for quad_id in quad_ids:
            if mosaic not in quads_dict:
                quads_dict[mosaic] = {}
            if quad_id not in quads_dict[mosaic]:
                quads_dict[mosaic][quad_id] = []

            quads_dict[mosaic][quad_id].append(
                planet_model.get_quad(mosaic_dict[mosaic], quad_id)
            )

    return quads_dict
