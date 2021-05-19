from pathlib import Path
from urllib.request import urlretrieve
import zipfile
import threading
from concurrent import futures
from functools import partial

import ee 
from osgeo import gdal

from component import parameter as cp

ee.Initialize()

def getImage(sources, bands, mask, year):
    
    start = str(year) + '-01-01'
    end = str(year) + '-12-31'
    
    # priority selector for satellites
    satellites = cp.getSatellites(sources, year)
    for satelliteId in satellites:
        dataset = ee.ImageCollection(satellites[satelliteId]) \
            .filterDate(start, end) \
            .filterBounds(mask) \
            .map(cp.getCloudMask(satelliteId))
        
        clip = dataset.median().clip(mask).select(cp.getAvailableBands()[bands][satelliteId])
        
        visible = 0
        if dataset.size().getInfo():
            # retreive the name of the first band
            band = cp.getAvailableBands()[bands][satelliteId][0]
            scale = cp.getScale(satelliteId)

            # get the number of masked pixel 
            pixel_masked = clip.select(band).reduceRegion(
                reducer=ee.Reducer.count(),
                geometry=mask,
                scale=scale,
            ).get(band)

            # get the number of pixel in the image 
            pixel = clip.select(band).unmask().reduceRegion(
                reducer=ee.Reducer.count(),
                geometry=mask,
                scale=scale
            ).get(band)

            # proportion of masked pixels
            visible = ee.Number(pixel_masked).divide(ee.Number(pixel)).multiply(100).getInfo()
        
        # if its the last one I'll keep it anyway
        if visible > 50:
            break
            
    return (clip, satelliteId)

def get_gee_vrt(pts, start, end, square_size, file, bands, sources, output):
    
    # get the filename
    filename = Path(file).stem
    
    # create a range_year element to simplify next for loops
    range_year = [y for y in range(start, end + 1)]
    
    # transform the stored points into ee points 
    ee_pts = [ ee.Geometry.Point(row.lng, row.lat) for _, row in pts.iterrows()]
    
    # create the square buffers 
    ee_buffers = [ee_pt.buffer(square_size).bounds() for ee_pt in ee_pts] 
    
    # extract the bands to use them in names 
    name_bands = '_'.join(bands.split(', '))
            
    # create a filename list 
    descriptions = {}
    for year in range_year:
        descriptions[year] = f'{filename}_{name_bands}_{year}'
        
    # load the data directly in SEPAL
    satellites = {} # contain the names of the used satellites
    
    nb_points = max(1, len(ee_buffers)-1)
    total_images = (end - start + 1) * nb_points
    output.reset_progress(total_images, 'Image loaded')
    for i, year in enumerate(range_year):
        
        satellites[year] = [None] * len(ee_buffers)
        
        download_params = {
            'sources': sources,
            'bands': bands, 
            'ee_buffers': ee_buffers,
            'year': year,
            'descriptions': descriptions,
            'output': output,
            'satellites': satellites,
            'lock': threading.Lock()
        }
        
        # download the images in parralel fashion
        with futures.ThreadPoolExecutor() as executor: # use all the available CPU/GPU
            executor.map(partial(down_buffer, **download_params), ee_buffers)   
            
    #print(satellites)
    
    # create a single vrt per year 
    vrt_list = {}
    for year in range_year:
        
        # retreive the file names
        vrt_path = cp.tmp_dir.joinpath(f'{descriptions[year]}.vrt')
        filepaths = [str(f) for f in cp.tmp_dir.glob(f'{descriptions[year]}_*.tif')]
        
        # build the vrt
        ds = gdal.BuildVRT(str(vrt_path), filepaths)
        ds.FlushCache()
        
        # check that the file was effectively created (gdal doesn't raise errors)
        if not vrt_path.is_file():
            raise Exception(f"the vrt {vrt_path} was not created")
        
        vrt_list[year] = vrt_path
    
    title_list = {y: {j: cp.getShortname(satellites[y][j]) for j in range(len(ee_buffers))} for y in range_year}
    
    # return the file 
    return vrt_list, title_list

def down_buffer(buffer, sources, bands, ee_buffers, year, descriptions, output, satellites, lock=None):
    """download the image for a specific buffer"""
    
    # get back the image index 
    j = ee_buffers.index(buffer)

    # get the image 
    image, sat = getImage(sources, bands, buffer, year)
    
    if sat == None: 
        print (f'year: {year}, j: {j}')
    
    if lock: 
        with lock:
            satellites[year][j] = sat
            
    description = f"{descriptions[year]}_{j}"
            
    dst = cp.tmp_dir/f'{description}.tif'
            
    if not dst.is_file():
                
        name = f'{description}_zipimage'
                
        link = image.getDownloadURL({
            'name': name,
            'region': buffer,
            'filePerBand': False,
            'scale': cp.getScale(sat)
        })
                
        tmp = cp.tmp_dir.joinpath(f'{name}.zip')
        urlretrieve (link, tmp)
                
        # unzip the file 
        with zipfile.ZipFile(tmp,"r") as zip_:
            data = zip_.read(zip_.namelist()[0])
                    
            dst.write_bytes(data)
                
        # remove the zip 
        tmp.unlink()

    # update the output 
    output.update_progress()
    
    return
        