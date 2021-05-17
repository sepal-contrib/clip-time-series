from pathlib import Path
from urllib.request import urlretrieve
import zipfile

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

            #nb_images = dataset.size().getInfo()
            if satelliteId == 'landsat_7' or visible > 50:
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
    
    # create a multipolygon mask
    ee_multiPolygon = ee.Geometry.MultiPolygon(ee_buffers).dissolve(maxError=100)     
    
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
    for i, year in enumerate(range_year):
        
        #image, satellites[year] = getImage(sources, bands, ee_multiPolygon, year)
        
        satellites[year] = [None] * len(ee_buffers)
        
        for j, buffer in enumerate(ee_buffers):
            
            # get the image 
            image, satellites[year][j] = getImage(sources, bands, buffer, year)
            
            description = f"{descriptions[year]}_{j}"
            
            dst = cp.tmp_dir.joinpath(f'{description}.tif')
            
            if not dst.is_file():
                
                name = 'zipimage'
                
                link = image.getDownloadURL({
                    'name': name,
                    'region': buffer,
                    'filePerBand': False,
                    'scale': cp.getScale(satellites[year][j])
                })
                
                tmp = cp.tmp_dir.joinpath(f'{name}.zip')
                urlretrieve (link, tmp)
                
                # unzip the file 
                with zipfile.ZipFile(tmp,"r") as zip_:
                    data = zip_.read(zip_.namelist()[0])
                    
                    dst.write_bytes(data)
                    #with dst.open('wb') as f:
                    #    f.write(data)
                
                # remove the zip 
                tmp.unlink()
            
            output.update_progress((i * nb_points + j)/total_images, msg='Image loaded')
    
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