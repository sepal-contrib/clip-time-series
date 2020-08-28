#hard coded parameters
import os
import glob
import ee

ee.Initialize()

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
    positionsRow = [[int(i/5), i%5] for i in range(15)]
    
    return positionsRow[i]

##########################
##       function       ##
##########################

def getSatelites(sources):
    
    satelites = {}
    
    if 'sentinel' in sources:
        satelites.update({'sentinel_2': 'COPERNICUS/S2_SR'})
        
    if 'landsat' in sources:
        satelites.update({
            'landsat_8': 'LANDSAT/LC08/C01/T1_SR',
            'landsat_5': 'LANDSAT/LT05/C01/T1_SR',
            'landsat_7': 'LANDSAT/LE07/C01/T1_SR',
        })
        
    return satelites
        

def getAvailableBands():
    """give the bands composition for each name. 
    0 being the landsat 7, 
    1 landsat 5, 
    2, landsat 8 
    3: sentinel 2"""
    
    bands = {
        'Red, Green, Blue' : {
            'landsat_7': ['B3', 'B2', 'B1'], 
            'landsat_5': ['B3', 'B2', 'B1'],
            'landsat_8': ['B4', 'B3', 'B2'],
            'sentinel_2': ['B4', 'B3', 'B2']
        },
        'Nir, Red, Green' : {
            'landsat_7': ['B4', 'B3', 'B2'], 
            'landsat_5': ['B4', 'B3', 'B2'],
            'landsat_8': ['B5', 'B4', 'B3'],
            'sentinel_2': ['B8', 'B4', 'B3']
        },
        'Nir, Swir1, Red' : {
            'landsat_7': ['B4', 'B5', 'B3'],
            'landsat_5': ['B4', 'B5', 'B3'],
            'landsat_8': ['B5', 'B6', 'B4'],
            'sentinel_2': ['B8', 'B11', 'B4']
        },
        'Swir2, Nir, Red' : {
            'landsat_7': ['B7', 'B4', 'B3'], 
            'landsat_5': ['B7', 'B4', 'B3'],
            'landsat_8': ['B7', 'B5', 'B4'],
            'sentinel_2': ['B12', 'B8', 'B4']
        },
        'Swir2, Swir1, Red' : {
            'landsat_7': ['B7', 'B5', 'B3'], 
            'landsat_5': ['B7', 'B5', 'B3'],
            'landsat_8': ['B7', 'B6', 'B4'],
            'sentinel_2': ['B12', 'B11', 'B4']
        },
        'Swir2, Nir, Green' : {
            'landsat_7': ['B7', 'B4', 'B2'], 
            'landsat_5': ['B7', 'B4', 'B2'],
            'landsat_8': ['B7', 'B5', 'B3'],
            'sentinel_2': ['B12', 'B8', 'B3']
        }
    }
    
    return bands

def getSources():
    
    return [
        'landsat',
        'sentinel'
    ]

def getTxt():
    """get all the txt files available in th folders"""
    root_dir = os.path.expanduser('~')
    raw_list = glob.glob(root_dir + "/**/*.txt", recursive=True)
    
    return raw_list

def vizParam(bands, buffer, image):
    
    if not bands: #didn't find images for the sample
        return {}
    
    params = image.select(bands).reduceRegion(**{
        'reducer': ee.Reducer.percentile([5, 95]), 
        'geometry': buffer, 
        'scale': 30
    })
    
    viz_max = max(
        params.get('{}_p95'.format(bands[0])).getInfo(), 
        params.get('{}_p95'.format(bands[1])).getInfo(), 
        params.get('{}_p95'.format(bands[2])).getInfo()
    )

    viz_min = min(
        params.get('{}_p5'.format(bands[0])).getInfo(),
        params.get('{}_p5'.format(bands[1])).getInfo(),
        params.get('{}_p5'.format(bands[2])).getInfo()
    )
    
    return {
        'min': [
            params.get('{}_p5'.format(bands[0])).getInfo(), 
            params.get('{}_p5'.format(bands[1])).getInfo(), 
            params.get('{}_p5'.format(bands[2])).getInfo()
        ],
        'max': [
            params.get('{}_p95'.format(bands[0])).getInfo(), 
            params.get('{}_p95'.format(bands[1])).getInfo(), 
            params.get('{}_p95'.format(bands[2])).getInfo()
        ],
        'bands': bands
    }

def getCloudMask(satelliteId):
    """ return the cloud masking function adapted to the apropriate satellite"""
    
    if satelliteId in ['landsat_5', 'landsat_7']:
        def cloudMask(image):
            qa = image.select('pixel_qa')
            # If the cloud bit (5) is set and the cloud confidence (7) is high
            # or the cloud shadow bit is set (3), then it's a bad pixel.
            cloud = qa.bitwiseAnd(1 << 5).And(qa.bitwiseAnd(1 << 7)).Or(qa.bitwiseAnd(1 << 3))
            # Remove edge pixels that don't occur in all bands
            mask2 = image.mask().reduce(ee.Reducer.min())
            
            return image.updateMask(cloud.Not()).updateMask(mask2)
    elif satelliteId == 'landsat_8':
        def cloudMask(image):
            # Bits 3 and 5 are cloud shadow and cloud, respectively.
            cloudShadowBitMask = (1 << 3)
            cloudsBitMask = (1 << 5)
            # Get the pixel QA band.
            qa = image.select('pixel_qa')
            # Both flags should be set to zero, indicating clear conditions.
            mask = qa.bitwiseAnd(cloudShadowBitMask).eq(0).And(qa.bitwiseAnd(cloudsBitMask).eq(0))
            
            return image.updateMask(mask)
    elif satelliteId == 'sentinel_2':
        def cloudMask(image):
            qa = image.select('QA60')
            #Bits 10 and 11 are clouds and cirrus, respectively.
            cloudBitMask = (1 << 10)
            cirrusBitMask = (1 << 11)
            #Both flags should be set to zero, indicating clear conditions.
            mask = qa.bitwiseAnd(cloudBitMask).eq(0).And(qa.bitwiseAnd(cirrusBitMask).eq(0))

            return image.updateMask(mask).divide(10000)
    
    return cloudMask

def getnbIntervals():
    return sentinel_end - landsat_start + 1

landsat_start = 2005
sentinel_start = 2016
sentinel_end = 2019