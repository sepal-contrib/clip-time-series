import os
import csv
import ee 
import geemap
import math
import shapely.geometry as sg
import gdal
import pandas
import numpy as np
import geopandas as gpd

ee.Initialize()

def get_bounding_box(assetID):
    """return a list of str of the (minx, miny, maxx, maxy) of the asset
    """
    aoi = ee.FeatureCollection('users/bornToBeAlive/aoi_PU')
    aoiJson = geemap.ee_to_geojson(aoi)
    aoiShp = sg.shape(aoiJson['features'][0]['geometry'])
    
    bb = {}
    bb['minx'], bb['miny'], bb['maxx'], bb['maxy'] = aoiShp.bounds
    
    bb['minx'] = str(math.floor(bb['minx']))
    bb['miny'] = str(math.floor(bb['miny']))
    bb['maxx'] = str(math.ceil(bb['maxx']))
    bb['maxy'] = str(math.ceil(bb['maxy']))
    
    return bb
  
def make_grid(points, spacing):

    xmin,ymin,xmax,ymax = points.total_bounds

    cols = list(range(int(np.floor(xmin)), int(np.ceil(xmax)), spacing))
    rows = list(range(int(np.floor(ymin)), int(np.ceil(ymax)), spacing))
    rows.reverse()

    polygons = []
    for x in cols:
        for y in rows:
            polygons.append( sg.Polygon([(x,y), (x+spacing, y), (x+spacing, y-spacing), (x, y-spacing)]) )

    grid = gpd.GeoDataFrame({'geometry':polygons})
    
    return grid