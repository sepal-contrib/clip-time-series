#hard coded parameters
import os
import glob



#########################
##       folders       ##
#########################

def create_folder(pathname):
    if not os.path.exists(pathname):
        os.makedirs(pathname)
    return pathname

def getResultDir():
    pathname = os.path.join(os.path.expanduser('~'), 'time_series_results') + '/'
    return create_folder(pathname)

def getTmpDir():
    pathname = os.path.join(getResultDir(), 'tmp') + '/'
    return create_folder(pathname)

##########################
##      constant        ##
##########################

def getPositionPdf(i):
    postionsSnake = [[0, 0], [1, 0], [2, 0], [3, 0], [4, 0], [4, 1], [3, 1], [2, 1], [1, 1], [0, 1], [0, 2], [1, 2], [2, 2], [3, 2], [4, 2]]
    
    postionsColumn = [[i%5, int(i/5)] for i in range(15)]
    positionsRow = [[int(i/3), i%3] for i in range(15)]
    
    return postionsSnake[i]

##########################
##       function       ##
##########################

def getSatelites(year):
    """return dataset name and integer for the bands"""
    if year < 2012:
        dataset = 'LANDSAT/LT05/C01/T1_SR'
        bandId = 1
    elif year == 2012:
        dataset = 'LANDSAT/LE07/C01/T1_SR'
        bandId = 0
    elif year > 2012:
        dataset = "LANDSAT/LC08/C01/T1_SR"
        bandId = 2
        
    return (dataset, bandId)

def getAvailableBands():
    """give the bands composition for each name. 
    0 being the landsat 7, 
    1 landsat 5, 
    2, landsat 8 
    3: sentinel 2"""
    
    bands = {
        'Red, Green, Blue' : [
            ['B3', 'B2', 'B1'], 
            ['B3', 'B2', 'B1'],
            ['B4', 'B3', 'B2'],
            ['B4', 'B3', 'B2']
        ],
        'Nir, Red, Green' : [
            ['B4', 'B3', 'B2'], 
            ['B4', 'B3', 'B2'],
            ['B5', 'B4', 'B3'],
            ['B8', 'B4', 'B3']
        ],
        'Nir, Swir1, Red' : [
            ['B4', 'B5', 'B3'],
            ['B4', 'B5', 'B3'],
            ['B5', 'B6', 'B4'],
            ['B8', 'B11', 'B4']
        ],
        'Swir2, Nir, Red' : [
            ['B7', 'B4', 'B3'], 
            ['B7', 'B4', 'B3'],
            ['B7', 'B5', 'B4'],
            ['B12', 'B8', 'B4']
        ],
        'Swir2, Swir1, Red' : [
            ['B7', 'B5', 'B3'], 
            ['B7', 'B5', 'B3'],
            ['B7', 'B6', 'B4'],
            ['B12', 'B11', 'B4']
        ],
        'Swir2, Nir, Green' : [
            ['B7', 'B4', 'B2'], 
            ['B7', 'B4', 'B2'],
            ['B7', 'B5', 'B3'],
            ['B12', 'B8', 'B3']
        ]
    }
    
    return bands

def getSources():
    
    return [
        'landsat'
        #'sentinel'
    ]

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