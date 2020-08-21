import pandas as pd 
import os
from utils import messages as ms
from sepal_ui.scripts import mapping
import geemap

def isConform(file):
    """perform several checks on the file given by the user retrun an error message if something is wrong else 0"""
    
    #check if the file exist
    if not os.path.isfile(file):
        return ms.NOT_A_FILE.format(file)
    
    #try to read the file 
    try:
        df = pd.read_csv(file)
    except:
        return ms.ERROR_READING_FILE.format(file)
    
    #check headers 
    #headers = ['lat', 'lng']
    #if not list(df.columns) == headers:
    #    return ms.WRONG_HEADERS
    
    #validate
    return 0

def setMap(file, m):
    """create a map and a df list of points"""
    
    pts = pd.read_csv(file)
    
    #add the pts on the map
    markers, popups = [], []
    for index, row in pts.iterrows():
        marker = geemap.Marker(location=(row['lat'], row['lng']), draggable=False)
        markers.append(marker)
        popups.append(index)
        
    #display on the map
    marker_cluster = geemap.MarkerCluster(markers=tuple(markers), popups=popups)
    m.add_layer(marker_cluster)

    return pts