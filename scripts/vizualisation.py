import traitlets

import ipyvuetify as v
from pathlib import Path
from pyproj import Proj
from shapely.geometry import shape

def set_msg(pts, bands_combo, source_name, basename):
    
    nb_pts = len(pts)    
    
    #compute surface (use total_bounds when pts will be a geopandas)
    minx = pts['lng'].to_numpy().min()
    maxx = pts['lng'].to_numpy().max()
    miny = pts['lat'].to_numpy().min()
    maxy = pts['lat'].to_numpy().max()
    
    lon = (maxx, maxx, minx, minx)
    lat = (maxy, miny, miny, maxy)
    
    pa = Proj("ESRI:54009") #equal surface mollweide
    x, y = pa(lon, lat)
    cop = {"type": "Polygon", "coordinates": [zip(x, y)]}
    surface = shape(cop).area/10e6
    
    msg = """
        <div>
            <p>
                You're about to launch the following downloading :
            <p>
            <ul>
                <li>
                    <b>{}</b> points distributed on <b>{:.2f}</b> km\u00B2
                </li>
                <li>
                    Using the images coming from <b>{}</b> satellites
                <li>
                    Using the <b>{}</b> band combination
                </li>
                <li>
                    Saved in a file using <b>{}</b> as a basename
                </li>
            </ul>
            
            <p>
                If you agree with these input you can start the downloading, if not please change the inputs in the previous tiles
            </p>
        </div>
    """.format(nb_pts, surface, source_name, bands_combo, basename)
    
    #create a Html widget
    class MyHTML(v.VuetifyTemplate):
        template = traitlets.Unicode(msg).tag(sync=True)
    
    
    return MyHTML()
    
    
    
    
    