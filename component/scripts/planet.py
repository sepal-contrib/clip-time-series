# this file will be used as a singleton object in the explorer tile
import re
import threading
from concurrent import futures
from datetime import datetime
from functools import partial
from itertools import product
from pathlib import Path

import geopandas as gpd
import numpy as np
import planet
import rasterio as rio
import requests
from osgeo import gdal
from pyproj import CRS, Transformer
from rasterio.warp import calculate_default_transform
from sepal_ui.planetapi import PlanetModel
from shapely import geometry as sg
from shapely.ops import unary_union

from component import parameter as cp
from component.message import cm

from .utils import min_diagonal

planet_model = PlanetModel()

# create the regex to match the different know planet datasets
VISUAL = re.compile("^planet_medres_visual")  # will be removed from the selection
ANALYTIC_MONTHLY = re.compile(
    r"^planet_medres_normalized_analytic_\d{4}-\d{2}_mosaic$"
)  # NICFI monthly
ANALYTIC_BIANUAL = re.compile(
    r"^planet_medres_normalized_analytic_\d{4}-\d{2}_\d{4}-\d{2}_mosaic$"
)  # NICFI bianual


def check_key():
    """raise an error if the key is not validated."""
    if not planet_model.active:
        raise Exception(cm.planet.invalid_key)

    return


def mosaic_name(mosaic):
    """
    Give back the shorten name of the mosaic so that it can be displayed on the thumbnails.

    Args:
        mosaic (str): the mosaic full name

    Return:
        (str, str): the type and the shorten name of the mosaic
    """
    if ANALYTIC_MONTHLY.match(mosaic):
        year = mosaic[34:38]
        start = datetime.strptime(mosaic[39:41], "%m").strftime("%b")
        res = f"{start} {year}"
        type_ = "ANALYTIC_MONTHLY"
    elif ANALYTIC_BIANUAL.match(mosaic):
        year = mosaic[34:38]
        start = datetime.strptime(mosaic[39:41], "%m").strftime("%b")
        end = datetime.strptime(mosaic[47:49], "%m").strftime("%b")
        res = f"{start}-{end} {year}"
        type_ = "ANALYTIC_BIANUAL"
    elif VISUAL.match(mosaic):
        res = None  # ignored in this module
        type_ = "VISUAL"
    else:
        res = mosaic[:15]  # not optimal but that's the max
        type_ = "OTHER"

    return type_, res


def validate_key(key: str) -> bool:
    """Validate the API key and save it the key variable."""

    # save the key until solving
    # https://github.com/12rambau/sepal_ui/issues/805
    planet_model.credentials = [key]

    # init session
    # avoid the error the no validation will be checked anyway
    try:
        planet_model.init_session(key)
    except Exception:
        pass

    return planet_model.active


def list_mosaics():
    """get all the mosaics available in a client without pagination limitations."""

    BASE_URL = "https://api.planet.com/basemaps/v1/mosaics?api_key={}"
    res = requests.get(BASE_URL.format(planet_model.credentials[0]))

    return res.json()["mosaics"]


def get_mosaics():
    """Return the available mosaics as a list of items for a v.Select object, retur None if not valid."""
    # init the results from the begining
    res = []

    # exit if the key is not valid
    if not planet_model.active:
        return res

    # filter the mosaics in 3 groups
    bianual, monthly, other = [], [], []
    for m in list_mosaics():
        name = m["name"]
        type_, short = mosaic_name(name)

        if type_ == "ANALYTIC_MONTHLY":
            monthly.append({"text": short, "value": name})
        elif type_ == "ANALYTIC_BIANUAL":
            bianual.append({"text": short, "value": name})
        elif type_ == "OTHER":
            monthly.append({"text": short, "value": name})

    # fill the results with the found mosaics
    if len(other):
        res += [{"header": "other"}] + other
    if len(monthly):
        res += [{"header": "NICFI monthly"}] + monthly
    if len(bianual):
        res += [{"header": "NICFI bianual"}] + bianual

    return res


def get_planet_grid(squares, out):
    """create a grid adapted to the points and to the planet initial grid."""
    out.add_msg(cm.planet.grid)

    # get the shape of the aoi in EPSG:3857 proj
    aoi_shp = unary_union(squares)
    aoi_gdf = gpd.GeoDataFrame({"geometry": [aoi_shp]}, crs="EPSG:4326").to_crs(
        "EPSG:3857"
    )

    # extract the aoi shape
    aoi_shp_proj = aoi_gdf["geometry"][0]

    # retreive the bb
    sg.box(*aoi_gdf.total_bounds)

    # compute the longitude and latitude in the apropriate CRS
    crs_bounds = CRS.from_epsg(3857).area_of_use.bounds

    proj = Transformer.from_crs(4326, 3857, always_xy=True)
    bl = proj.transform(crs_bounds[0], crs_bounds[1])
    tr = proj.transform(crs_bounds[2], crs_bounds[3])

    # the planet grid is constructing a 2048x2048 grid of SQUARES.
    # The latitude extends is bigger (20048966.10m VS 20026376.39) so to ensure the "squariness"
    # Planet lab have based the numerotation and extends of it square grid on the longitude only.
    # the extreme -90 and +90 band it thus exlucded but there are no forest there so we don't care
    longitudes = np.linspace(bl[0], tr[0], 2048 + 1)

    # the planet grid size cut the world in 248 squares vertically and horizontally
    box_size = (tr[0] - bl[0]) / 2048

    # filter with the geometry bounds
    bb = aoi_gdf.total_bounds

    # filter lon and lat
    lon_filter = longitudes[
        (longitudes > (bb[0] - box_size)) & (longitudes < bb[2] + box_size)
    ]
    lat_filter = longitudes[
        (longitudes > (bb[1] - box_size)) & (longitudes < bb[3] + box_size)
    ]

    # get the index offset
    x_offset = np.nonzero(longitudes == lon_filter[0])[0][0]
    y_offset = np.nonzero(longitudes == lat_filter[0])[0][0]

    # create the grid
    x, y, names, squares = [], [], [], []
    for coords in product(range(len(lon_filter) - 1), range(len(lat_filter) - 1)):

        # get the x and y index
        ix = coords[0]
        iy = coords[1]

        # fill the grid values
        x.append(ix + x_offset)
        y.append(iy + y_offset)
        names.append(f"L15-{x[-1]:4d}E-{y[-1]:4d}N.tif")
        squares.append(
            sg.box(
                lon_filter[ix], lat_filter[iy], lon_filter[ix + 1], lat_filter[iy + 1]
            )
        )

    # create a buffer grid in 3857
    grid = gpd.GeoDataFrame(
        {"x": x, "y": y, "names": names, "geometry": squares}, crs="EPSG:3857"
    )

    # cut the grid to the aoi extends
    mask = grid.intersects(aoi_shp_proj)
    grid = grid.loc[mask]

    # project back to 4326
    grid_gdf = grid.to_crs(4326)

    return grid_gdf


def get_planet_vrt(geometry, mosaics, size, file, bands, out):

    # get the filename
    filename = Path(file).stem

    # extract the points coordinates
    pts = geometry.copy()
    pts.geometry = pts.geometry.centroid

    # build the size dictionary
    size_dict = {
        r.id: min_diagonal(r.geometry, size)
        for _, r in geometry.to_crs(3857).iterrows()
    }

    # create the buffer grid
    buffers = pts.to_crs(3857)
    buffers.geometry = buffers.apply(
        lambda r: r.geometry.buffer(size_dict[r.id] / 2, cap_style=3), axis=1
    )
    buffers = buffers.to_crs(4326)

    # find all the quads that should be downloaded and serve them as a grid
    planet_grid = get_planet_grid(buffers.geometry, out)

    # create a vrt for each year
    vrt_list = {}
    nb_points = max(1, len(planet_grid) - 1)
    total_img = len(mosaics) * nb_points
    mosaic_list = list_mosaics()
    out.reset_progress(total_img, "Image loaded")
    for m in mosaics:

        # get the mosaic from the mosaic name
        mosaic = next(i for i in mosaic_list if i["name"] == m)

        # construct the quad list
        quads = [
            f"{int(row.x):04d}-{int(row.y):04d}" for i, row in planet_grid.iterrows()
        ]

        download_params = {
            "filename": filename,
            "name": m,
            "mosaic": mosaic,
            "bands": bands,
            "file_list": [],
            "out": out,
            "lock": threading.Lock(),
        }

        # debugging
        # for quad in quads:
        #    get_quad(quad, **download_params)

        # download the requested images
        # use all the available CPU/GPU
        with futures.ThreadPoolExecutor() as executor:
            executor.map(partial(get_quad, **download_params), quads)
        file_list = download_params["file_list"]

        if file_list == []:
            raise Exception("No image have been found on Planet lab servers")

        # create a vrt out of it
        vrt_path = cp.tmp_dir.joinpath(f"{filename}_{m}.vrt")
        ds = gdal.BuildVRT(str(vrt_path), file_list)
        ds.FlushCache()

        # check that the file was effectively created (gdal doesn't raise errors)
        if not vrt_path.is_file():
            raise Exception(f"the vrt {vrt_path} was not created")

        vrt_list[m] = vrt_path

    # create a title list to be consistent
    title_list = {
        m: {i: f"{planet.data} {mosaic_name(m)[1]}" for i in range(len(buffers))}
        for m in mosaics
    }

    return vrt_list, title_list


def get_quad_by_id(mosaic: dict, quad_id: str):
    """Get a quad response for a specific mosaic and quad.

    Args:
    mosaic: A mosaic representation from the API
    quad_id: A quad id (typically <xcoord>-<ycoord>)

    Returns:
        `planet.api.models.JSON`

    Raises:
        planet.api.exceptions.APIException: On API error.
    """

    url = "https://api.planet.com/basemaps/v1/mosaics/{}/quads/{}?api_key={}"
    res = requests.get(url.format(mosaic["id"], quad_id, planet_model.credentials[0]))

    return res.json()


def get_quad(quad_id, filename, name, mosaic, bands, file_list, out, lock=None):
    """get one single quad from parameters."""
    # check file existence
    file = cp.tmp_dir.joinpath(f"{filename}_{name}_{quad_id}.tif")

    if file.is_file():
        if lock:
            with lock:
                file_list.append(str(file))

    else:

        tmp_file = cp.tmp_dir.joinpath(f"{filename}_{name}_{quad_id}_tmp.tif")

        # to avoid the downloading of non existing quads
        try:
            quad = get_quad_by_id(mosaic, quad_id)
            file_list.append(str(file))
        except Exception as e:
            out.add_msg(f"{e}", "error")
            return

        r = requests.get(quad["_links"]["download"])
        tmp_file.write_bytes(r.content)

        with rio.open(tmp_file) as src:

            # adapt the file to only keep the 3 required bands
            data = src.read(cp.planet_bands_combo[bands])

            # reproject the image in EPSG:4326
            dst_crs = "EPSG:4326"
            transform, width, height = calculate_default_transform(
                src.crs, dst_crs, src.width, src.height, *src.bounds
            )

            kwargs = src.meta.copy()
            kwargs.update(
                {
                    "count": 3,
                    "crs": dst_crs,
                    "transform": transform,
                    "width": width,
                    "height": height,
                }
            )

            with rio.open(file, "w", **kwargs) as dst:
                dst.write(data)

        # remove the tmp file
        tmp_file.unlink()

    # update the loading bar
    out.update_progress()

    return
