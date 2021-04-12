# this file will be used as a singleton object in the explorer tile 

import requests
from types import SimpleNamespace

from planet import api
from ipyleaflet import TileLayer

from component.message import cm
from component import parameter as cp

planet = SimpleNamespace()

# parameters
planet.url = 'https://api.planet.com/auth/v1/experimental/public/my/subscriptions'
planet.basemaps = "https://tiles.planet.com/basemaps/v1/planet-tiles/{mosaic_name}/gmap/{{z}}/{{x}}/{{y}}.png?api_key={key}&proc={color}"
planet.attribution = "Imagery © Planet Labs Inc."

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
    
    planet.key = key
    
    out.add_msg(cm.planet.valid_key, 'success')
    
    return 

def order_basemaps(key, out):
    """check the apy key and then order the basemap to update the select list"""
    
    # checking the key validity
    validate_key(key, out)
    
    out.add_msg(cm.planet.load_mosaics)
    
    # autheticate to planet
    planet.client = api.ClientV1(api_key=planet.key)
    
    # get the basemap names 
    mosaics = [m['name'] for m in planet.client.get_mosaics().get()['mosaics']]
    
    out.add_msg(cm.planet.mosaic_loaded, 'success')
    
    return mosaics

def display_basemap(mosaic_name, m, out, color=None):
    """display the planet mosaic basemap on the map"""
    
    out.add_msg(cm.map.tiles)
    
    # set the color if necessary 
    if not color:
        color = cp.planet_colors[0]
    
    # remove the existing layers with planet attribution 
    for layer in m.layers:
        if layer.attribution == planet.attribution: 
            m.remove_layer(layer)
            
    # create a new Tile layer on the map 
    layer = TileLayer(
        url=planet.basemaps.format(key=planet.key, mosaic_name=mosaic_name, color=color),
        name="Planet© Mosaic",
        attribution=planet.attribution,
        show_loading = True
    )
    
    # insert the mosaic bewteen CardoDB and the country border ie position 1
    # we have already removed the planet layers so I'm sure that nothing is in 
    # The grid and the country are build before and if we are here I'm also sure that there are 3 layers in the map
    tmp_layers = list(m.layers)
    tmp_layers.insert(1, layer)
    m.layers = tuple(tmp_layers)
    
    return

def download_quads(aoi_name, mosaic_name, grid, out):
    """export each quad to the appropriate folder"""
    
    out.add_msg(cm.planet.export)
    
    # get the mosaic from the mosaic name 
    mosaics = planet.client.get_mosaics().get()['mosaics'] 
    mosaic_names = [m['name'] for m in mosaics]
    mosaic = mosaics[mosaic_names.index(mosaic_name)]
    
    # construct the quad list 
    quads = []
    for i, row in grid.iterrows():
        quads.append(f'{int(row.x):04d}-{int(row.y):04d}')
        
    
    for quad_id in quads:
        
        # check file existence 
        res_dir = cp.get_mosaic_dir(aoi_name, mosaic_name)
        file = res_dir.joinpath(f'{quad_id}.tif')
        
        if file.is_file():
            out.add_msg(cm.planet.file_exist.format(file))
            continue
            
        out.add_msg(cm.planet.down_file.format(file))
        quad = planet.client.get_quad_by_id(mosaic, quad_id).get()
        planet.client.download_quad(quad).get_body().write(file)
        
    out.add_msg(cm.planet.down_end.format(res_dir), "success")
    
    return
    
    
    
    
    
    


    
    
    


    
    
    
    
    