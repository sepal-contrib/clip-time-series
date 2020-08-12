import geemap
from ipywidgets import Layout
import shapely.geometry as sg
import geopandas as gpd
import ee 
from utils import parameters as pm

ee.Initialize()

def setVizMap():
    
    center = [0, 0]
    zoom = 2
    
    #create the map
    m = geemap.Map(center=center, zoom=zoom)
    
    #remove everything
    m.clear_layers()
    m.clear_controls()
    
    #prevent all the handler 
    m.dragging = False
    m.keyboard = False
    m.scroll_wheel_zoom = False
    m.tap = False
    m.touch_zoom = False
    m.zoom_control = False
    m.double_click_zoom = False
    
    #define map size 
    display = Layout(width='200px', height='200px', padding="1%")
    m.layout = display
    
    return m

def setLayer(maps, pts):
    
    size = 2000  # 2km
    geoms = [[pts.loc[pt]['lng'], pts.loc[pt]['lat']] for pt in range(len(pts))]
    multiPoint = ee.Geometry.MultiPoint(geoms);
    
    #creates buffers
    buffer = multiPoint.buffer(size)
    
    #pour l'instant que du landsat
    start_landsat = 2005
    end_landsat = 2019
    dataset_source = pm.getSources()['landsat']
    bands = pm.getAvailableBands()['Red, Green, Blue'][0]
    
    layers = []
    for year in range(start_landsat, end_landsat+1):
        start = str(year) + '-01-01';
        end = str(year) + '-12-31';
        
        dataset = ee.ImageCollection(dataset_source).filterDate(start, end)
        clip = dataset.mean().clip(buffer)
        
        layers.append(clip)
        
    [maps[i].addLayer(layers[i], pm.landsatVizParam(bands), 'viz') for i in range(len(maps))]
    
    return
    
    
    
    
    