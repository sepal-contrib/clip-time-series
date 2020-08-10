#hard coded parameters 

import os
import glob

def getAvailableBands():
    """give the bands composition for each name. 0 being the landsat compostiotn and 1 the sentinel"""
    
    bands = {
        'Red, Green, Blue' : [],
        'Nir, Red, Green' : [],
        'Nir, Swir1, Red' : [],
        'Swir2, Nir, Red' : [],
        'Swir2, Swir1, Red' : [],
        'Swir2, Nir, Green' : []
    }
    
    return bands

def getSources():
    
    return ['landsat', 'sentinel']

def getTxt():
    """get all the txt files available in th folders"""
    root_dir = os.path.expanduser('~')
    raw_list = glob.glob(root_dir + "/**/*.txt", recursive=True)
    
    return raw_list