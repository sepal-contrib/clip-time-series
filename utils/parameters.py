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

def getSatelites(year):
    """return dataset name and integer for the bands"""
    #if year < 2012:
    #    dataset = 'LANDSAT/LT05/C01/T1_SR'
    #    bandId = 1
    if year <= 2012:
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

def sentinelVizParam(bands, buffer, image):
    
    params = image.select(bands).reduceRegion(**{
        'reducer': ee.Reducer.percentile([5, 95]), 
        'geometry': buffer, 
        'scale': Map.getScale(),
    })
    
    viz_max = max(
        params.get('{}_p95'.format(bands[0])).getInfo(), 
        params.get('{}_p95'.format(bands[1])).getInfo(), 
        params.get('{}_p95'.format(bands[2])).getInfo()
    )

    viz_min = Math.min(
        params.get('{}_p5'.format(bands[0])).getInfo(),
        params.get('{}_p5'.format(bands[1])).getInfo(),
        params.get('{}_p5'.format(bands[2])).getInfo()
    )
    
    return {
        'min': viz_min,
        'max': viz_max,
        'bands': bands
    }

def landsatVizParam(bands, buffer, image):
    
    params = image.select(bands).reduceRegion(**{
        'reducer': ee.Reducer.percentile([5, 95]), 
        'geometry': buffer,
        'scale': 30
    })
    
    #viz_max = max(
    #    params.get('{}_p95'.format(bands[0])).getInfo(), 
    #    params.get('{}_p95'.format(bands[1])).getInfo(), 
    #    params.get('{}_p95'.format(bands[2])).getInfo()
    #)
    #
    #viz_min = min(
    #    params.get('{}_p5'.format(bands[0])).getInfo(),
    #    params.get('{}_p5'.format(bands[1])).getInfo(),
    #    params.get('{}_p5'.format(bands[2])).getInfo()
    #)
    
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

def getCloudMask(bandId):
    """ return the cloud masking function adapted to the apropriate satellite"""
    
    if bandId in [0, 1]:
        def cloudMask(image):
            qa = image.select('pixel_qa')
            # If the cloud bit (5) is set and the cloud confidence (7) is high
            # or the cloud shadow bit is set (3), then it's a bad pixel.
            cloud = qa.bitwiseAnd(1 << 5).And(qa.bitwiseAnd(1 << 7)).Or(qa.bitwiseAnd(1 << 3))
            # Remove edge pixels that don't occur in all bands
            mask2 = image.mask().reduce(ee.Reducer.min())
            
            return image.updateMask(cloud.Not()).updateMask(mask2)
    elif bandId == 2:
        def cloudMask(image):
            # Bits 3 and 5 are cloud shadow and cloud, respectively.
            cloudShadowBitMask = (1 << 3);
            cloudsBitMask = (1 << 5);
            # Get the pixel QA band.
            qa = image.select('pixel_qa');
            # Both flags should be set to zero, indicating clear conditions.
            mask = qa.bitwiseAnd(cloudShadowBitMask).eq(0).And(qa.bitwiseAnd(cloudsBitMask).eq(0));
            
            return image.updateMask(mask)
    
    return cloudMask

def getnbIntervals():
    return sentinel_end - landsat_start + 1

landsat_start = 2005
sentinel_start = 2016
sentinel_end = 2019