# this file will be used as a singleton object in the explorer tile 
from pathlib import Path
import requests
from types import SimpleNamespace
from itertools import product
import threading
from concurrent import futures
from functools import partial

from planet import api
from ipyleaflet import TileLayer
from shapely import geometry as sg
from shapely.ops import unary_union
from pyproj import CRS, Transformer
import numpy as np
import rasterio as rio
from rasterio.warp import calculate_default_transform, reproject, Resampling
import geopandas as gpd
from osgeo import gdal

from component.message import cm
from component import parameter as cp

planet = SimpleNamespace()

# parameters
planet.url = 'https://api.planet.com/auth/v1/experimental/public/my/subscriptions'
planet.mosaic_name = "planet_medres_normalized_analytic_{}_mosaic"
planet.data = "Planet MedRes"

# attributes

planet.valid = False
planet.key = None
planet.client = None

def check_key():
    """raise an error if the key is not validataed"""
    
    if not planet.valid:
        raise Exception(cm.planet.invalid_key)
    
    return

def validate_key(key, out):
    """Validate the API key and save it the key variable"""
    
    out.add_msg(cm.planet.test_key)
    
    # get all the subscriptions 
    resp = requests.get(planet.url, auth=(key, ''))
    subs = resp.json()
    
    # only continue if the resp was 200
    if resp.status_code != 200:
        raise Exception(subs['message'])
    
    # check the subscription validity 
    # stop the execution if it's not the case
    planet.valid = any([True for sub in subs if sub['state'] == 'active'])
    check_key()
    
    # autheticate to planet
    planet.client = api.ClientV1(api_key=key)
    
    planet.key = key
    
    out.add_msg(cm.planet.valid_key, 'success')
    
    return

def get_planet_vrt(pts, start, end, square_size, file, bands, semester, out):
    
    # get the filename
    filename = Path(file).stem
    
    # create a range_year element to simplyfy next for loops
    range_year = [y for y in range(start, end + 1)]
    
    # create the buffer grid 
    gdf_buffers = pts.to_crs("EPSG:3857")
    gdf_buffers['geometry'] = gdf_buffers.buffer(square_size/2, cap_style = 3)
    gdf_buffers = gdf_buffers.to_crs("EPSG:4326") 
    
    # find all the quads that should be downloaded and serve them as a grid 
    planet_grid = get_planet_grid(gdf_buffers['geometry'], out)
    
    # create a vrt for each year 
    vrt_list = {}
    nb_points = max(1, len(planet_grid)-1)
    total_img = (end - start + 1) * nb_points
    out.reset_progress(total_img, 'Image loaded')
    for i, year in enumerate(range_year):
        
        # get the mosaic from the mosaic name
        mosaic_name = planet.mosaic_name.format(cp.planet_date_ranges[year][semester])
        mosaics = planet.client.get_mosaics().get()['mosaics'] 
        mosaic_names = [m['name'] for m in mosaics]
        mosaic = mosaics[mosaic_names.index(mosaic_name)]
    
        # construct the quad list 
        quads = [f'{int(row.x):04d}-{int(row.y):04d}' for i, row in planet_grid.iterrows()]
        
        download_params = {
            'filename': filename,
            'year': year,
            'mosaic': mosaic,
            'bands': bands, 
            'file_list': [],
            'out': out,
            'lock': threading.Lock()
        }
        # download the requested images 
        with futures.ThreadPoolExecutor() as executor: # use all the available CPU/GPU
            executor.map(partial(get_quad, **download_params), quads)  
        file_list = download_params['file_list']
        
        if file_list == []:
            raise Exception("No image have been found on Planet lab servers")
        
        # create a vrt out of it 
        vrt_path = cp.tmp_dir.joinpath(f'{filename}_{year}.vrt')
        ds = gdal.BuildVRT(str(vrt_path), file_list)
        ds.FlushCache()
        
        # check that the file was effectively created (gdal doesn't raise errors)
        if not vrt_path.is_file():
            raise Exception(f"the vrt {vrt_path} was not created")
        
        vrt_list[year] = vrt_path
        
    # create a title list to be consistent
    title_list = {y: {i: f'{planet.data} {cp.planet_semesters[semester]}' for i in range(len(gdf_buffers))} for y in range_year}
    
    return vrt_list, title_list
        
def get_planet_grid(squares, out):
    """create a grid adapted to the points and to the planet initial grid"""
    
    out.add_msg(cm.planet.grid)
    
    # get the shape of the aoi in EPSG:3857 proj 
    aoi_shp = unary_union(squares)
    aoi_gdf = gpd.GeoDataFrame({'geometry': [aoi_shp]}, crs="EPSG:4326").to_crs('EPSG:3857')
        
    # extract the aoi shape 
    aoi_shp_proj = aoi_gdf['geometry'][0]
    
    # retreive the bb 
    aoi_bb = sg.box(*aoi_gdf.total_bounds)
        
    # compute the longitude and latitude in the apropriate CRS
    crs_4326 = CRS.from_epsg(4326)
    crs_3857 = CRS.from_epsg(3857)
    crs_bounds = crs_3857.area_of_use.bounds

    proj = Transformer.from_crs(4326, 3857, always_xy=True)
    bl = proj.transform(crs_bounds[0], crs_bounds[1])
    tr = proj.transform(crs_bounds[2], crs_bounds[3])

    # the planet grid is constructing a 2048x2048 grid of SQUARES. 
    # The latitude extends is bigger (20048966.10m VS 20026376.39) so to ensure the "squariness"
    # Planet lab have based the numerotation and extends of it square grid on the longitude only. 
    # the extreme -90 and +90 band it thus exlucded but there are no forest there so we don't care
    longitudes = np.linspace(bl[0], tr[0], 2048+1)

    # the planet grid size cut the world in 248 squares vertically and horizontally
    box_size = (tr[0]-bl[0])/2048

    # filter with the geometry bounds
    bb = aoi_gdf.total_bounds

    # filter lon and lat 
    lon_filter = longitudes[(longitudes > (bb[0] - box_size)) & (longitudes < bb[2] + box_size)]
    lat_filter = longitudes[(longitudes > (bb[1] - box_size)) & (longitudes < bb[3] + box_size)]

    # get the index offset 
    x_offset = np.nonzero(longitudes == lon_filter[0])[0][0]
    y_offset = np.nonzero(longitudes == lat_filter[0])[0][0]
    
    # create the grid
    x = []
    y = []
    names = []
    squares = []
    for coords in product(range(len(lon_filter)-1), range(len(lat_filter)-1)):
    
        # get the x and y index 
        ix = coords[0]
        iy = coords[1]
        
        # fill the grid values 
        x.append(ix + x_offset)
        y.append(iy + y_offset)
        names.append(f'L15-{x[-1]:4d}E-{y[-1]:4d}N.tif')
        squares.append(sg.box(lon_filter[ix], lat_filter[iy], lon_filter[ix+1], lat_filter[iy+1]))
    
    # create a buffer grid in 3857
    grid = gpd.GeoDataFrame({'x':x, 'y':y, 'names':names, 'geometry':squares}, crs='EPSG:3857')

    # cut the grid to the aoi extends 
    mask = grid.intersects(aoi_shp_proj)
    grid = grid.loc[mask]
    
    # project back to 4326
    grid_gdf = grid.to_crs('EPSG:4326')
    
    return grid_gdf

def get_quad(quad_id, filename, year, mosaic, bands, file_list, out, lock = None):
    """get one single quad from parameters"""
        
    # check file existence 
    file = cp.tmp_dir.joinpath(f'{filename}_{year}_{quad_id}.tif')
        
    if file.is_file():
        if lock:
            with lock:
                file_list.append(str(file))
            
    else:
        
        tmp_file = cp.tmp_dir.joinpath(f'{filename}_{year}_{quad_id}_tmp.tif')
        
        # to avoid the downloading of non existing quads
        try:
            quad = planet.client.get_quad_by_id(mosaic, quad_id).get()
            file_list.append(str(file))
        except Exception as e:
            out.add_msg(f'{e}', 'error')
            return 
            
        planet.client.download_quad(quad).get_body().write(tmp_file)
            
        with rio.open(tmp_file) as src:
                
            # adapt the file to only keep the 3 required bands
            data = src.read(cp.planet_bands_combo[bands])
                
            # reproject the image in EPSG:4326
            dst_crs = 'EPSG:4326'
            transform, width, height = calculate_default_transform(
                src.crs, 
                dst_crs, 
                src.width, 
                src.height, 
                *src.bounds
            )
                
            kwargs = src.meta.copy()
            kwargs.update({
                'count': 3,
                'crs': dst_crs,
                'transform': transform,
                'width': width,
                'height': height
            })
            
            with rio.open(file, 'w', **kwargs) as dst:
                dst.write(data)
                    
        # remove the tmp file
        tmp_file.unlink()
        
    # update the loading bar 
    out.update_progress()
    
    return 
    
    
    
    
    
    
    


    
    
    


    
    
    
    
    