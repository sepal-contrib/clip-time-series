import shutil
import os
from pathlib import Path
import time
from glob import glob
from urllib.request import urlretrieve
import zipfile

import pandas as pd
import ee 
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.pyplot as plt
import rasterio as rio
from rasterio.mask import mask
from rasterio.merge import merge
from rasterio.windows import from_bounds
from rasterio.profiles import DefaultGTiffProfile
import numpy as np
from shapely.geometry import box
from PyPDF2 import PdfFileMerger, PdfFileReader
import ipyvuetify as v
from osgeo import gdal


from .gdrive import gdrive
from .gee import custom_wait_for_completion
from component import parameter as cp

ee.Initialize()

def getNDVI(sources, satellite, bands, mask, year):
    
    start = str(year) + '-01-01'
    end = str(year) + '-12-31'
    
    #select the images from the appropriate satellite
    image = ee.ImageCollection(cp.getSatellites(sources)[satellite]) \
            .filterDate(start, end) \
            .filterBounds(mask) \
            .map(cp.getCloudMask(satellite)) \
            .mosaic()
    
    nir = image.select(cp.getAvailableBands()['ndvi'][satellite][0])
    red = image.select(cp.getAvailableBands()['ndvi'][satellite][1])
    
    ndvi = nir.subtract(red).divide(nir.add(red)).rename('NDVI')
    
    reducer = ndvi.reduceRegion(**{
        'reducer': ee.Reducer.mean(),
        'geometry': mask,
        'scale': 30
    }).getInfo()
    
    return reducer['NDVI']
    
def getNDWI(sources, satellite, bands, mask, year):
    
    start = str(year) + '-01-01'
    end = str(year) + '-12-31'
    
    #select the images from the appropriate satellite
    image = ee.ImageCollection(cp.getSatellites(sources)[satellite]) \
            .filterDate(start, end) \
            .filterBounds(mask) \
            .map(cp.getCloudMask(satellite)) \
            .mosaic()
    
    nir = image.select(cp.getAvailableBands()['ndwi'][satellite][0])
    swir = image.select(cp.getAvailableBands()['ndwi'][satellite][1])
    
    ndwi = nir.subtract(swir).divide(nir.add(swir)).rename('NDWI')
    
    reducer = ndwi.reduceRegion(**{
        'reducer': ee.Reducer.mean(),
        'geometry': mask,
        'scale': 30
    }).getInfo()
    
    return reducer['NDWI']
    

def getImage(sources, bands, mask, year):
    
    start = str(year) + '-01-01'
    end = str(year) + '-12-31'
    
    #priority selector for satellites
    satellites = cp.getSatellites(sources, year)
    for satelliteId in satellites:
        dataset = ee.ImageCollection(satellites[satelliteId]) \
            .filterDate(start, end) \
            .filterBounds(mask) \
            .map(cp.getCloudMask(satelliteId))
        
        if dataset.size().getInfo() > 0:
            satellite = satelliteId
            break
            
    clip = dataset.median().clip(mask).select(cp.getAvailableBands()[bands][satelliteId])
    
    return (clip, satelliteId)
    

def run(file, pts, bands, sources, start, end, square_size, output):
    
    # check dates 
    start_year = max(start, cp.min_start_year)
    end_year = min(end, cp.max_end_year)
    
    # get the filename
    filename = Path(file).stem
    
    # extract the bands to use them in names 
    name_bands = '_'.join(bands.split(', '))
    
    # pdf name 
    pdf_file = cp.result_dir.joinpath(f'{filename}_{name_bands}_{start_year}_{end_year}.pdf')
    
    if pdf_file.is_file():
        output.add_live_msg('Pdf already exist', 'success')
        return pdf_file
    
    # start the drive handler 
    drive_handler = gdrive()
    
    # transform the stored points into ee points 
    ee_pts = {pts.iloc[i].name: ee.Geometry.Point(pts.iloc[i]['lng'], pts.iloc[i]['lat']) for i in range(len(pts))}
    
    # create the square buffers 
    ee_buffers = {i: ee_pts[i].buffer(square_size).bounds() for i in ee_pts}
    
    # create a multipolygon mask
    ee_multiPolygon = ee.Geometry.MultiPolygon([ee_pts[i].buffer(square_size).bounds() for i in ee_pts]).dissolve(maxError=100)     
            
    # create a filename list 
    descriptions = {}
    for year in range(start_year, end_year + 1):
        descriptions[year] = f'{filename}_{name_bands}_{year}'
        
    # load the data directly in SEPAL
    satellites = {} # contain the names of the used satellites
    task_list = []
    total_images = (end_year-start_year + 1)*len(ee_buffers)
    for i, year in enumerate(range(start_year, end_year + 1)):
        
        image, satellites[year] = getImage(sources, bands, ee_multiPolygon, year)
        
        for j, key in enumerate(ee_buffers):
            
            description = f"{descriptions[year]}_{j}"
            
            dst = cp.tmp_dir.joinpath(f'{description}.tif')
            
            if not dst.is_file():
                
                name = 'zipimage'
                
                link = image.getDownloadURL({
                    'name': name,
                    'region': ee_buffers[key],
                    'filePerBand': False,
                    'scale': cp.getScale(satellites[year])
                })
                
                tmp = cp.tmp_dir.joinpath(f'{name}.zip')
                urlretrieve (link, tmp)
                
                # unzip the file 
                with zipfile.ZipFile(tmp,"r") as zip_:
                    data = zip_.read(zip_.namelist()[0])
                    
                    with dst.open('wb') as f:
                        f.write(data)
                
                # remove the zip 
                tmp.unlink()
            
            output.update_progress((i*len(ee_buffers) + j)/total_images, msg='Image loaded')
            
            #if drive_handler.get_files(description) == []:
            #
            #    task_config = {
            #        'image':image,
            #        'description': description,
            #        'scale': cp.getScale(satellites[year]),
            #        'region': ee.Geometry(polygon),
            #        'maxPixels': 10e12
            #    }
            #
            #    task = ee.batch.Export.image.toDrive(**task_config)
            #    task.start()
            #    task_list.append(description)
        
        
        
    
    #check the exportation evolution     
    #state = custom_wait_for_completion(task_list, output)
    #output.add_live_msg('Download to drive finished', 'success')
    #time.sleep(2)
    
    #output.add_live_msg('Retreive to sepal')
    #retreive all the file ids 
    #filesId = []
    #for year in descriptions:
    #    filesId += drive_handler.get_files(descriptions[year])
    
    #download the files   
    #output.add_live_msg('Download files')
    #drive_handler.download_files(filesId, cp.tmp_dir)  
    
    #remove the files from gdrive 
    #output.add_live_msg('Remove from gdrive')
    #drive_handler.delete_files(filesId)     
    
    #merge them into a single file per year
    #for year in range(start_year, end_year + 1):
    #    output.add_live_msg(f'merge the files for year {year}')
    #    merge_tiles(cp.tmp_dir, descriptions[year], output)
    
    # create a single vrt per year 
    for year in range(start_year, end_year + 1):
        # retreive the vrt 
        vrt_path = cp.tmp_dir.joinpath(f'{descriptions[year]}.vrt')
        
        # retreive the filepaths
        filepaths = [str(f) for f in cp.tmp_dir.glob(f'{descriptions[year]}_*.tif')]
        
        # build the vrt
        ds = gdal.BuildVRT(str(vrt_path), filepaths)
        ds.FlushCache()
        
        # check that the file was effectively created (gdal doesn't raise errors)
        if not vrt_path.is_file():
            raise Exception(f"the vrt {vrt_path} was not created")
        
    nb_col, nb_line = cp.get_dims(end_year - start_year)
    
    pdf_tmps = []
    output.update_progress(0, msg='Pdf page created')
    for index, row in pts.iterrows():
        pdf_tmp = cp.tmp_dir.joinpath(f'{filename}_{name_bands}_tmp_pts_{row["id"]}.pdf')
        pdf_tmps.append(pdf_tmp)
    
        # create the resulting pdf
        with PdfPages(pdf_tmp) as pdf:        
            
            page_title = f"Pt_{row['id']} (lat:{row['lat']:.5f}, lng:{row['lng']:.5f})"
                  
            fig, axes = plt.subplots(nb_line, nb_col, figsize=(11.69,8.27), dpi=500)
            fig.suptitle(page_title, fontsize=16, fontweight ="bold")
            fig.set_tight_layout(True) 
            # display the images in a fig and export it as a pdf page
            placement_id = 0
            for year in range(start_year, end_year + 1):
                
                # load the file 
                file = cp.tmp_dir.joinpath(f'{descriptions[year]}.vrt')
                
                # extract the buffer bounds 
                coords = ee_buffers[index].coordinates().get(0).getInfo()
                bl, tr = coords[0], coords[2]

                # Create the bounding box
                shape = box(bl[0], bl[1], tr[0], tr[1])
            
                with rio.open(file) as f:
                    data = f.read(window=from_bounds(bl[0], bl[1], tr[0], tr[1], f.transform))
                
                bands = [] 
                for i in range(3):
                    band = data[i]
                    # remove the NaN from the analysis
                    h_, bin_ = np.histogram(band[np.isfinite(band)].flatten(), 3000, density=True) 
    
                    cdf = h_.cumsum() # cumulative distribution function
                    cdf = 3000 * cdf / cdf[-1] # normalize
    
                    # use linear interpolation of cdf to find new pixel values
                    band_equalized = np.interp(band.flatten(), bin_[:-1], cdf)
                    band_equalized = band_equalized.reshape(band.shape)
        
                    bands.append(band_equalized)
    
                data = np.stack( bands, axis=0 )

                data = data/3000
                data = data.clip(0, 1)
                data = np.transpose(data,[1,2,0])
            
                place = cp.getPositionPdf(placement_id, nb_col) 
                ax = axes[place[0], place[1]]
                ax.imshow(data, interpolation='nearest')
                ax.set_title(str(year) + ' ' + cp.getShortname(satellites[year]), x=.0, y=.9, fontsize='small', backgroundcolor='white', ha='left')
                ax.axis('off')
                ax.set_aspect('equal', 'box')
                
                # increment the placement image 
                placement_id += 1
            
            # finish the file with empty plots if needed
            while placement_id < nb_line * nb_col:
                place = cp.getPositionPdf(placement_id, nb_col) 
                ax = axes[place[0], place[1]]
                ax.axis('off')
                ax.set_aspect('equal', 'box')
                
                placement_id += 1
            
            # save the page
            pdf.savefig(fig)
            plt.close('all')
           
        progress = index/(len(pts) - 1) if len(pts) > 1 else 1
        output.update_progress(progress, msg='Pdf page created')
        
    # merge all the pdf files 
    output.add_live_msg('merge all pdf files')
    mergedObject = PdfFileMerger()
    for pdf in pdf_tmps:
        mergedObject.append(PdfFileReader(str(pdf), 'rb'))
        pdf.unlink()
    mergedObject.write(str(pdf_file))
    
    # flush the tmp repository 
    for file in cp.tmp_dir.glob('*.*'):
        file.unlink()
    cp.tmp_dir.rmdir()
    
    output.add_live_msg('PDF output finished', 'success')
    
    return pdf_file
    
def merge_tiles(folder, basename, output):
    """merge the tile from the folder with the parameter basename pattern"""
    
    # construct the pattern
    pattern = f'{basename}_*.tif'
    output_file = folder.joinpath(f'{basename}.tif')
    
    if output_file.is_file():
        return
    
    # get all the files that need to be merged
    files = [file for file in folder.glob(pattern)]
        
    #run the merge process
    output.add_live_msg('Merging the GEE tiles')
    
    #manual open and close because I don't know how many file there are
    sources = [rio.open(file) for file in files]

    data, output_transform = merge(sources)
    
    out_meta = sources[0].meta.copy()    
    out_meta.update(
        driver    = "GTiff",
        height    =  data.shape[1],
        width     =  data.shape[2],
        transform = output_transform,
        compress  = 'lzw'
    )
    
    with rio.open(output_file, "w", **out_meta) as dest:
        dest.write(data)
    
    #manually close the files
    [src.close() for src in sources]
    
    #delete local files
    [os.remove(file) for file in files]
    
    return
    