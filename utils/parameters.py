#hard coded parameters 

import os
import glob

def getAvailableBands():
    """give the bands composition for each name. 0 being the landsat composition and 1 the sentinel"""
    
    bands = {
        'Red, Green, Blue' : [['B3', 'B2', 'B1'], ['B4', 'B3', 'B2']],
        'Nir, Red, Green' : [['B4', 'B3', 'B2'], ['B8', 'B4', 'B3']],
        'Nir, Swir1, Red' : [['B4', 'B5', 'B3'], ['B8', 'B11', 'B4']],
        'Swir2, Nir, Red' : [['B7', 'B4', 'B3'], ['B12', 'B8', 'B4']],
        'Swir2, Swir1, Red' : [['B7', 'B5', 'B3'], ['B12', 'B11', 'B4']],
        'Swir2, Nir, Green' : [['B7', 'B4', 'B2'], ['B12', 'B8', 'B3']]
    }
    
    return bands

def getSources():
    
    return {
        'landsat 7': 'LANDSAT/LE07/C01/T1_SR', 
        'sentinel 2': 'COPERNICUS/S2_SR'
    }

def getTxt():
    """get all the txt files available in th folders"""
    root_dir = os.path.expanduser('~')
    raw_list = glob.glob(root_dir + "/**/*.txt", recursive=True)
    
    return raw_list

def sentinelVizParam(bands):
    return {
        'min': 0.0,
        'max': 0.3,
        'bands': bands
    }

def landsatVizParam(bands):
    return {
        'min': 0,
        'max': 3000,
        'bands': bands
    }

def getnbIntervals():
    return sentinel_end - landsat_start + 1

landsat_start = 2005
sentinel_start = 2016
sentinel_end = 2019