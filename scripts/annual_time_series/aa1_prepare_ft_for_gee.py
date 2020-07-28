import pandas as pd
import accuracy-assessment.scripts.utils.parameters as pm
from math import cos, pi, asin
import shapely.geometry as sg
import geopandas as gdp
from osgeo import osr


def prepare_for_gee(point_file):
    
    ###########################################################
    ####   create square boxes around the sampling points   ###
    ###########################################################
    
    # transform the file into pdt
    pts = pd.read_csv(point_file)
    
    # sanitize the file 
    if not isConform(pts):
        return pm.UNCONFORM_FILE
    
    # create the gpdf of boxes around each point
    lp = []
    for index, row in pts.iterrows():
        lp.append(createBox(row['YCoordinate'], row['XCoordinate']))
        
    boxes = gdp.GeoDataFrame(pts, geometry=lp)
    
    # add crs 
    spatialRef = osr.SpatialReference()
    spatialRef.ImportFromProj4('+proj=longlat +datum=WGS84 +no_defs +ellps=WGS84 +towgs84=0,0,0') 
    boxes.set_crs(spatialRef)
    
    # export to shapefile
    pathname =  pm.getDwnDir() + 'pts_2km_boxes.shp'
    boxes.to_file(pathname, layer='pts_2km_boxes', driver='ESRI Shapefile')
    
    ##############################################################
    ### create rectangular grid to export in gee-api landsat   ###
    ##############################################################
    
    grid_size = 2 # for Landsat  @ 30m spatial resolution
    
    
    
    
    
    
    

def isConform(df):
    """check if the provided dataframe is conform to an annual time serie input"""
    
    #check the columns names
    if not  pm.getHeader() == df.columns.values.tolist():
        return 0
    
    #separated to avoid the error if 'id' column doesn't exist
    #check that ids are unique
    if not df.id.is_unique:
        return 0
    
    return 1

def createBox(lat, lng):
    """create a box of 2km around the provided point"""
    
    #add 100 meters in each N/S direction : 
    ysize = 1000/111321 # 1km/len(1°)  
    xsize = 1000/(111321*cos(lat*pi/180))
      
    
    ymin = lat - ysize
    ymax = lat + ysize
    xmin = lng - xsize
    xmax = lng + xsize
    
    lon_point_list = [xmin, xmax, xmax, xmin]
    lat_point_list = [ymax, ymax, ymin, ymin]
    
    return sg.Polygon(zip(lon_point_list, lat_point_list))
    
    