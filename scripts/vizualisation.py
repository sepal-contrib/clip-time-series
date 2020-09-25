import geemap
from ipywidgets import Layout
import shapely.geometry as sg
import geopandas as gpd
import ee 

from utils import parameters as pm

ee.Initialize()

def getImage(sources, bands, mask, year):
    
    start = str(year) + '-01-01'
    end = str(year) + '-12-31'
    
    satelite = None
    #priority selector for satellites
    for sateliteId in pm.getSatellites(sources):
        dataset = ee.ImageCollection(pm.getSatellites(sources)[sateliteId]) \
            .filterDate(start, end) \
            .filterBounds(mask) \
            .map(pm.getCloudMask(sateliteId))
        
        if dataset.size().getInfo() > 0:
            satelite = sateliteId
            break
        
    if dataset.size().getInfo():
        viz_band = pm.getAvailableBands()[bands][sateliteId]
        clip = dataset.median().clip(mask)
    else:
        clip = mask
        viz_band = None    
    
    return (clip, satelite, viz_band)
    

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
    
    output.add_live_msg('create buffers')
    size = 2000  # 2km
    geoms = [[pts.loc[pt]['lng'], pts.loc[pt]['lat']] for pt in range(len(pts))]
    ee_pts = [ee.Geometry.Point(geom) for geom in geoms]
    ee_buffers = [ee_pt.buffer(size).bounds() for ee_pt in ee_pts]
    ee_multiPolygon = ee.Geometry.MultiPolygon(ee_buffers).dissolve(maxError=100)
    
    cpt_map = 0
    ################################################
    ##     create the layers from 2005 to 2020    ##
    ################################################
    
    for year in range(pm.start_year, pm.end_year + 1):
        
        output.add_live_msg('load {} images'.format(year))
        clip, satelite, viz_band = getImage(sources, bands, ee_multiPolygon, year)
        
        #stretch colors
        output.add_live_msg('strectch colors for {}'.format(year))
        viz_params =pm.vizParam(viz_band, ee_multiPolygon, clip, satelite)
            
        output.add_live_msg('display {}'.format(year))
        maps[cpt_map].addLayer(clip, viz_params, 'viz')
            
        cpt_map += 1
        
    return
    
    
    
    
    