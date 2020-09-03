import pandas as pd
from utils import gdrive
from utils import utils
import ee 
from pathlib import Path
from sepal_ui.scripts import utils as su
from matplotlib.backends.backend_pdf import PdfPages
from utils import parameters as pm
import time
import matplotlib.pyplot as plt
import rasterio as rio
import numpy as np
import os
import gdal
import shutil

ee.Initialize()

def getImage(sources, bands, mask, year):
    
    start = str(year) + '-01-01'
    end = str(year) + '-12-31'
    
    #priority selector for satellites
    for sateliteId in pm.getSatelites(sources):
        dataset = ee.ImageCollection(pm.getSatelites(sources)[sateliteId]) \
            .filterDate(start, end) \
            .filterBounds(mask) \
            .map(pm.getCloudMask(sateliteId))
        
        if dataset.size().getInfo() > 0:
            satelite = sateliteId
            break
            
    clip = dataset.median().clip(mask)
    
    return (clip, sateliteId)
    

def run(file, pts, bands, sources, output):
    
    start_year = 2005
    end_year = 2020
    
    #get the filename
    filename = Path(file).stem
    
    #extract the bands to use them in names 
    name_bands = '_'.join(bands.split(', '))
    
    #pdf name 
    pdf_file = pm.getResultDir() + '{}_{}.pdf'.format(filename, name_bands)
    
    if os.path.isfile(pdf_file):
        return pdf_file
    
    #start the drive handler 
    drive_handler = gdrive.gdrive()
    
    #transform them in ee points 
    ee_pts = [ee.Geometry.Point(pts.loc[i]['lng'], pts.loc[i]['lat']) for i in range(len(pts))]
    
    #create the buffers 
    ee_buffers = [ee_pt.buffer(2000).bounds() for ee_pt in ee_pts]
    
    #create a multipolygon mask 
    ee_multiPolygon = ee.Geometry.MultiPolygon(ee_buffers).dissolve(maxError=100)
    
    #create a filename list 
    descriptions = {}
    for year in range(start_year, end_year):
        descriptions[year] = '{}_{}_{}'.format(filename, name_bands, year)
    
    #load all the data in gdrive 
    satelites = {} #contain the names of the used satelites
    for year in range(start_year, end_year):
            
        image, satelites[year] = getImage(sources, bands, ee_multiPolygon, year)
        
        task_config = {
            'image':image,
            'description': descriptions[year],
            'scale': 30,
            'region': ee_multiPolygon
        }
            
        task = ee.batch.Export.image.toDrive(**task_config)
        task.start()
        su.displayIO(output, 'exporting year: {}'.format(year))
    
    #check the exportation evolution 
    task_list = []
    for year in range(start_year, end_year):
        task_list.append(descriptions[year])
            
    state = utils.custom_wait_for_completion(task_list, output)
    su.displayIO(output, 'Export to drive finished', 'success')
    time.sleep(2)
    
    su.displayIO(output, 'Retreive to sepal')
    #retreive all the file ids 
    filesId = []
    for year in range(start_year, end_year):
        filesId += drive_handler.get_files(descriptions[year])
    
    #download the files        
    drive_handler.download_files(filesId, pm.getTmpDir())     
    
    #remove the files from gdrive 
    drive_handler.delete_files(filesId)
    
    #create the resulting pdf
    with PdfPages(pdf_file) as pdf:
        #each point is display on one single page
        for index, row in pts.iterrows():
            
            page_title = "Pt_{} (lat:{:.5f}, lng:{:.5f})".format(
                int(row['id']), 
                row['lat'], 
                row['lng']
            )
            
            su.displayIO(output, 'Creating page for pt {}'.format(int(row['id'])))
                  
            fig, axes = plt.subplots(3, 5, figsize=(11.69,8.27))
            fig.suptitle(page_title, fontsize=16, fontweight ="bold")
            
            #display the images in a fig and export it as a pdf page
            for year in range(start_year, end_year):
                
                #laod the file 
                file = pm.getTmpDir() + descriptions[year] + '.tif'
                
                #create the tmp tif image cuted to buffer size
                tmp_file = pm.getTmpDir() + descriptions[year] + '_pt_{}.tif'.format(row['id'])
                
                #extract the buffer bounds 
                listCoords = ee.Array.cat(ee_buffers[index].coordinates(), 1) 
                
                xCoords = listCoords.slice(1, 0, 1)
                yCoords = listCoords.slice(1, 1, 2)
                
                xMin = xCoords.reduce('min', [0]).get([0,0]).getInfo()
                xMax = xCoords.reduce('max', [0]).get([0,0]).getInfo()
                yMin = yCoords.reduce('min', [0]).get([0,0]).getInfo()
                yMax = yCoords.reduce('max', [0]).get([0,0]).getInfo()
                
                bounds = (xMin, yMin, xMax, yMax)
                
                #crop the image
                gdal.Warp(tmp_file, file, outputBounds=bounds)
                
    
                with rio.open(tmp_file) as f:
                    data = f.read([1, 2, 3], masked=True)
                
                min_ = np.percentile(data, 5, axis=(1,2))
                max_ = np.percentile(data, 95, axis=(1,2))
                
                min_ = np.expand_dims(np.expand_dims(min_, axis=1), axis=2)
                max_ = np.expand_dims(np.expand_dims(max_, axis=1), axis=2)
                
                data = (data-min_)/(max_-min_)
                data = data.clip(0, 1)
                data = np.transpose(data,[1,2,0])
            
                i = year - start_year
                ax = axes[pm.getPositionPdf(i)[0], pm.getPositionPdf(i)[1]]
                ax.imshow(data)
                ax.set_title(str(year) + ' ' + satelites[year])
                ax.axis('off')
                ax.set_aspect('equal', 'box')
            
                #delete the tmp file
                #done on the fly to not exceed sepal memory limits
                os.remove(tmp_file)
                
            plt.tight_layout()
            
            #save the page 
            pdf.savefig(fig)
            plt.close()
            
    #flush the tmp repository 
    shutil.rmtree(pm.getTmpDir())
    
    su.displayIO(output, 'PDF output finished', 'success')
    
    return pdf_file
    
    
    