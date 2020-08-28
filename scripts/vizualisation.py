import geemap
from ipywidgets import Layout
import shapely.geometry as sg
import geopandas as gpd
import ee 
from utils import parameters as pm
from sepal_ui.scripts import utils as su

ee.Initialize()

def getImage(sources, bands, mask, year):
    
    start = str(year) + '-01-01'
    end = str(year) + '-12-31'
    
    #priority selector for satellites
    for satteliteID in pm.getSatelites():
        dataset = ee.ImageCollection(pm.getSatelites()[satteliteID]) \
            .filterDate(start, end) \
            .filterBounds(mask) \
            .map(pm.getCloudMask(satteliteID))
        
        if dataset.size().getInfo() > 0:
            break
        
    
    viz_band = pm.getAvailableBands()[bands][satteliteID]
    clip = dataset.median().clip(mask)
    
    return (clip, viz_band)
    

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

def setLayer(maps, pts, bands, sources, output):
    
    su.displayIO(output, 'create buffers')
    size = 2000  # 2km
    geoms = [[pts.loc[pt]['lng'], pts.loc[pt]['lat']] for pt in range(len(pts))]
    ee_pts = [ee.Geometry.Point(geom) for geom in geoms]
    ee_buffers = [ee_pt.buffer(size).bounds() for ee_pt in ee_pts]
    ee_multiPolygon = ee.Geometry.MultiPolygon(ee_buffers).dissolve(maxError=100)
    
    cpt_map = 0
    ################################################
    ##     create the layers from 2005 to 2020    ##
    ################################################
    start_year = 2005
    end_year = 2020
    
    for year in range(start_year, end_year):
        
        su.displayIO(output, 'load {} images'.format(year))
        clip, viz_band = getImage(sources, bands, ee_multiPolygon, year)
        
        #stretch colors
        su.displayIO(output, 'strectch colors for {}'.format(year))
        viz_params =pm.vizParam(viz_band, ee_multiPolygon, clip)
            
        su.displayIO(output, 'display {}'.format(year))
        maps[cpt_map].addLayer(clip, viz_params, 'viz')
            
        cpt_map += 1
        
    return
    
    
    
    
    